from typing import List, Tuple, Union, Dict, Any, Optional, Literal
import click
import wandb
import pandas as pd
import pathlib
import tqdm

import sys
from textwrap import dedent
from .wandb_utils import (
    pass_api_wrapper,
    pass_api_and_info,
    processor,
    apply_decorators,
    DICT,
    config_file_decorator,
)
import logging
from wandb_utils.commands.common import GlobBasedFileFilter
import glob
import itertools

logger = logging.getLogger(__name__)
from click_option_group import OptionGroup, RequiredAnyOptionGroup


def files_on_wandb(
    api: wandb.PublicApi,
    entity: str,
    project: str,
    run: str,
    output_dir: Optional[pathlib.Path],
    include_filter: Optional[List[str]] = None,
    exclude_filter: Optional[List[str]] = None,
    overwrite: bool = False,
    action: Literal["copy", "move", "delete"] = "copy",
) -> None:
    run_ = api.run(f"{entity}/{project}/{run}")

    if action in ["copy", "move"] and output_dir is None:
        raise ValueError("For 'copy' or 'move' output_dir cannot be None")

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=overwrite)

    ff = GlobBasedFileFilter(
        include_filter=include_filter, exclude_filter=exclude_filter
    )

    if action in ["move", "delete"]:

        def delete(f: wandb.apis.public.File) -> None:
            logger.debug(f"Deleting {f.name} from wandb server.")
            f.delete()

    else:

        def delete(f: wandb.apis.public.File) -> None:
            return None

    if action in ["move", "copy"]:

        def download(f: wandb.apis.public.File) -> None:
            logger.debug(f"Downloading: {f.name} to {output_dir}")
            f.download(output_dir, replace=overwrite)

    else:

        def download(f: wandb.apis.public.File) -> None:
            return None

    for file_ in run_.files():

        if ff(file_):
            download(file_)
            delete(file_)


files_input = OptionGroup(
    "Input", help="The file globs to include and/or exclude."
)


@click.command(name="files")
@click.argument("run", type=str)
@files_input.option(
    "-f",
    "--files",
    default=None,
    type=str,
    help=dedent(
        """
        File globs to include (+) and exclude (-) files split using '|'.
        For example, to include all files with extension .json and important.txt, but ignoring all other .txt files and extra.json,
        in the 'serialization_dir' folder,
        one can pass --files as '+ serialization_dir/*.json|serialization_dir/important.txt|- serialization_dir/*.txt|- serialization_dir/extra.json'.

        Note:

            1. There should be exactly one space space between +/- and the glob. If neither + nor - are given,
                we assume it to be +.
            2. There should be no space around the seperator '|'.
        """
    ),
)
@click.option(
    "-F",
    "--files-from-file",
    default=None,
    type=str,
    help="File containing include and/or exclude globs with one glob per line. "
    "The format of the globs remains the same as --files option i.e., '[+-] glob'.",
)
@click.option(
    "--base-path",
    type=click.Path(path_type=pathlib.Path),
    help=dedent(
        """
        By default the full path of the files is preseved on wandb.
        For instance, if you save 'serialization_dir/configs/config.json',
        it will save config.json under 'serialization_dir/configs/' on wandb.
        If instead, you wish to save config.json in the root directory of the run
        on wandb, you can provide --base-path="serialization_dir/configs" and
        --files="serialization_dir/configs/config.json".
        """
    ),
)
@click.option(
    "--destination",
    type=click.Choice(["wandb", "local"]),
    default="wandb",
    help="Wheter to upload to or download from wandb.",
)
@click.option(
    "--overwrite",
    default=False,
    is_flag=True,
    help="What to do when file/folder already exists.",
)
@click.option(
    "--action",
    type=click.Choice(["move", "copy", "delete"]),
    default="copy",
    help="Whether to move the file, delete it or copy. Default is copy.",
)
@pass_api_and_info
@processor
@config_file_decorator()
def files_command(
    df: pd.DataFrame,
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    run: str,
    files: Optional[str],
    files_from_file: Optional[pathlib.Path],
    base_path: Optional[pathlib.Path],
    destination: Literal["wandb", "local"],
    overwrite: bool = False,
    action: Literal["move", "copy", "delete"] = "copy",
) -> None:
    """
    Add new files to an existing run `run` on wandb or copy files from an existing run to local.

    `run` is the id of an existing. This run should already exist.
        If chaining, the run ids can be obtained from the DataFrame of the previoius command.
        To use chaining, `run` has to be set to 'df' and the DataFrame from the previous command should have
        a column named 'run'.
    """

    if run == "df":
        if df is None:
            raise ValueError(
                "If run=df, the previous command should produce a dataframe with column 'run'"
            )

        if destination == "wandb" and action in ["move", "copy"]:
            raise ValueError(
                "Options run=df, destination=wandb and action=move or copy are not supported together"
            )
        try:
            
            for idx, row in tqdm.tqdm(df.iterrows(),total=len(df)):
                process_run(
                    api,
                    entity,
                    project,
                    row["run"],
                    files,
                    files_from_file,
                    base_path=base_path / row["run"]
                    if base_path is not None
                    else None,
                    destination=destination,
                    overwrite=overwrite,
                    action=action,
                )
        except KeyError as ke:
            if "run" in str(ke):
                logger.warn("The df does not have a 'run' column.")
            raise ke
    else:
        process_run(
            api,
            entity,
            project,
            run,
            files,
            files_from_file,
            base_path=base_path,
            destination=destination,
            overwrite=overwrite,
            action=action,
        )


def process_run(
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    run: str,
    files: Optional[str],
    files_from_file: Optional[pathlib.Path],
    base_path: Optional[pathlib.Path],
    destination: Literal["wandb", "local"],
    overwrite: bool = False,
    action: Literal["move", "copy", "delete"] = "copy",
) -> None:
    logger.debug(f"Processing run {entity}/{project}/{run}")
    glob_wrappers: List[str] = []

    if files:
        glob_wrappers += files.split("|")

    if files_from_file:
        with open(files_from_file) as f:
            for line in f.readlines():
                glob_wrappers.append(line.strip())
    assert glob_wrappers, "No globs provided."
    include_globs, exclude_globs = get_globs(glob_wrappers)
    logger.debug(f"Include Glob: {include_globs}")
    logger.debug(f"Exclude Glob: {exclude_globs}")

    if (destination == "local" and action in ["copy", "move"]) or (
        destination == "wandb" and action in ["delete"]
    ):  # download
        assert entity
        assert project

        files_on_wandb(
            api,
            entity,
            project,
            run=run,
            output_dir=base_path,
            include_filter=include_globs,
            exclude_filter=exclude_globs,
            overwrite=overwrite,
            action=action,
        )

    elif (destination == "wandb" and action in ["copy", "move"]) or (
        destination == "local" and action in ["delete"]
    ):  # upload

        files_ = get_files(include_globs, exclude_globs)

        if len(files_) == 0:
            logger.debug("No file matched the globs")

        if action not in ["delete"]:
            add_files(api, entity, project, run, files_, base_path)

        if action in ["move", "delete"]:
            for file_ in files_:
                pathlib.Path(file_).unlink()


def get_globs(
    globs: List[str],
) -> Tuple[List[str], List[str]]:
    """
    Create list of final paths to include.
    """
    include_filter: List[str] = []
    exclude_filter: List[str] = []

    for glob_wrapper in globs:
        if glob_wrapper[0] in ["-", "+"]:
            if glob_wrapper[0] == "+":
                include_filter.append(glob_wrapper[1:].strip())
            else:
                exclude_filter.append(glob_wrapper[1:].strip())
        else:
            include_filter.append(glob_wrapper)

    return include_filter, exclude_filter


def get_files(
    include_filter: List[str], exclude_filter: List[str]
) -> List[pathlib.Path]:
    filter_ = GlobBasedFileFilter(
        include_filter=include_filter, exclude_filter=exclude_filter
    )
    files = [
        pathlib.Path(file_)
        for file_ in itertools.chain(
            *map(lambda x: glob.iglob(x, recursive=True), include_filter)
        )
        if filter_(file_)
    ]

    return files


def add_files(
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    run: str,
    files: List[pathlib.Path],
    base_path: Optional[pathlib.Path],
) -> None:
    wandb.init(id=run, resume="must", entity=entity, project=project)

    for file_ in files:
        logger.debug(f"Saving {file_}")
        wandb.save(str(file_), base_path)  # type: ignore
