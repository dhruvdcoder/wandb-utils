from typing import List, Tuple, Union, Dict, Any, Optional
import click
import wandb
import pandas as pd
import argparse
import pathlib
import sys
from .wandb_utils import (
    wandb_utils,
    pass_api_wrapper,
    pass_api_and_info,
    config_file_decorator,
)
from .common import processor
from wandb_utils.file_filter import FileFilter, GlobBasedFileFilter
import logging
import tqdm
import pandas as pd

logger = logging.getLogger(__name__)


def download_run_from_wandb(
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    run: Optional[str],
    output_dir: pathlib.Path,
    include_filter: Optional[List[str]] = None,
    exclude_filter: Optional[List[str]] = None,
    overwrite: bool = False,
    move: bool = False,
) -> None:
    run_ = api.run(f"{entity}/{project}/{run}")
    # pbar = tqdm.tqdm(run_.files(), desc="Downloading files")
    output_dir.mkdir(parents=True, exist_ok=overwrite)

    ff = GlobBasedFileFilter(
        include_filter=include_filter, exclude_filter=exclude_filter
    )

    for file_ in run_.files():

        if ff(file_):
            # pbar.set_description(f"Downloading: {file_.name}")
            logger.debug(f"Downloading: {file_.name}")
            file_.download(output_dir, replace=overwrite)


def download_runs_from_wandb(
    df: pd.DataFrame,
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    output_dir_field: str,
    include_filter: Optional[List[str]] = None,
    exclude_filter: Optional[List[str]] = None,
) -> pd.DataFrame:
    for row in tqdm.tqdm(df.iterrows(), desc="Downloading runs' files"):
        download_run_from_wandb(
            api,
            entity,
            project,
            sweep,
            row["run"],
            pathlib.Path(row[output_dir_field]),
            include_filter,
            exclude_filter,
        )


@click.command(name="download-run-from-wandb")
@click.argument("run", type=str)
@click.option(
    "-o",
    "--output_dir",
    required=True,
    type=click.Path(path_type=pathlib.Path),  # type: ignore
    help="Directory in which to save the run data. It will be saved in output_dir/runid",
)
@click.option(
    "--include_filter",
    multiple=True,
    type=str,
    help="Glob string for files to include (can pass multiple). See `glob_filter.py` for details.",
)
@click.option(
    "--exclude_filter",
    multiple=True,
    type=str,
    help="Glob string for Files to exclude (can pass multiple). See `glob_filter.py` for details.",
)
@click.option("--overwrite", is_flag=True)
@pass_api_and_info
@processor
@config_file_decorator()
def download_run_from_wandb_command(
    df: pd.DataFrame,
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    run: str,
    output_dir: pathlib.Path,
    include_filter: Optional[List[str]] = None,
    exclude_filter: Optional[List[str]] = None,
    overwrite: bool = False,
) -> pd.DataFrame:
    """
    Download single run from wandb server.

    RUN is the unique run id.
    """

    return download_run_from_wandb(
        api,
        entity,
        project,
        sweep,
        run,
        output_dir,
        include_filter,
        exclude_filter,
        overwrite,
    )
