from wandb_utils.version import VERSION
from typing import (
    Optional,
    List,
    Tuple,
    TypeVar,
    Callable,
    Any,
    cast,
    Mapping,
    Dict,
)
import click
from .temp import hello
from .utils import load_config, LOCAL_CONFIG_FILENAME, load_commands_config
import wandb
from functools import update_wrapper
import logging
import os
import sys
import pandas as pd
import json
import click_config_file
import pathlib
from wandb_utils.file_filter import FileFilter, GlobBasedFileFilter
import logging

logger = logging.getLogger(__name__)


class WandbAPIWrapper(object):
    """
    Contains an instance of `wandb.Api` or `wandb.PublicApi` and some other information.
    """

    def __init__(
        self, entity: str = None, project: str = None, sweep: str = None
    ):
        self.api = wandb.Api()  # type:ignore
        self.entity = entity
        self.project = project
        self.sweep = sweep

    def all_data_df(
        self,
        sweep: Optional[str] = None,
        filters: Optional[
            Dict
        ] = None,  # see: https://github.com/wandb/client/blob/5a65037a435cbc8a885ab78fe5f23b8d7e10f5d2/wandb/apis/public.py#L428
    ) -> pd.DataFrame:
        """
        Get the data for all the runs.
        """
        api = self.api
        entity = self.entity
        project = self.project
        sweep = self.sweep
        logger.info(f"Querying wandb...")

        if sweep is None:  # get all runs
            runs = api.runs(f"{entity}/{project}", filters=filters)  # type: ignore
        else:
            f_list = [{"sweep": sweep}]

            if filters:
                f_list.append(filters)
            f = {"$and": f_list}
            runs = api.runs(f"{entity}/{project}", filters=f)  # type:ignore
        summary_list = []
        config_list = []
        name_list = []
        sweep_list = []

        for run in runs:
            # run.summary are the output key/values like accuracy.  We call ._json_dict to omit large files
            summary_list.append(
                {k: v for k, v in run.summary._json_dict.items()}
            )

            # run.config is the input metrics.  We remove special values that start with _.
            config_list.append(
                {k: v for k, v in run.config.items() if not k.startswith("_")}
            )

            # run.name is the name of the run.
            name_list.append(
                {
                    "run": run.id,
                    "run_name": run.name,
                    "entity": run.entity,
                    "project": run.project,
                    "path": f"{run.entity}/{run.project}/{run.id}",
                    "tags": "|".join(run.tags),
                }
            )

            # sweep
            sweep_list.append(
                {
                    "sweep": run.sweep.id,
                    "sweep_name": run.sweep.config.get("name", ""),
                }
                if run.sweep
                else {"sweep": "", "sweep_name": ""}
            )

        summary_df = pd.DataFrame.from_records(summary_list)
        config_df = pd.DataFrame.from_records(config_list)
        sweep_df = pd.DataFrame.from_records(sweep_list)
        name_df = pd.DataFrame.from_records(name_list)
        all_df = pd.concat([name_df, sweep_df, config_df, summary_df], axis=1)

        return all_df

    def find_best_models_in_sweeps(
        self,
        metric: str,
        maximum: bool = True,
        sweep: Optional[str] = None,
    ) -> pd.DataFrame:
        api = self.api
        entity = self.entity
        project = self.project
        all_df = self.all_data_df(sweep=sweep)
        # ref: https://stackoverflow.com/questions/32459325/python-pandas-dataframe-select-row-by-max-value-in-group

        if maximum:
            return all_df.loc[
                all_df.groupby("sweep", dropna=True)[metric].idxmax()
            ]
        else:
            return all_df.loc[
                all_df.groupby("sweep", dropna=True)[metric].idxmin()
            ]

    def download_run_from_wandb(
        self,
        run: Optional[str],
        output_dir: pathlib.Path,
        include_filter: Optional[List[str]] = None,
        exclude_filter: Optional[List[str]] = None,
        overwrite: bool = False,
    ) -> None:
        api = self.api
        entity = self.entity
        project = self.project

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


# alias
WandbUtilsClient = WandbAPIWrapper
