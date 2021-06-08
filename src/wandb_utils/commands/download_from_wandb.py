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
)
from wandb_utils.file_filter import FileFilter, GlobBasedFileFilter
import logging

logger = logging.getLogger(__name__)


def download_run_from_wandb(
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    run: Optional[str],
    output_dir: pathlib.Path,
    df: Optional[pd.DataFrame] = None,
    file_filter: Optional[FileFilter] = None,
):
    pass


def download_runs_from_wandb(
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    runs: List[str],
    output_dir: pathlib.Path,
    df: Optional[pd.DataFrame] = None,
    file_filter: Optional[FileFilter] = None,
):
    pass


@click.command(name="download_run_from_wandb")
@click.option("-r", "--run", required=True, type=str, help="wandb run id")
@click.option(
    "-o",
    "--output_dir",
    required=True,
    type=click.Path(path_type=pathlib.Path),  # type: ignore
    help="Directory in which to save the run data. It will be saved in output_dir/runid",
)
@click.option(
    "--exclude_filter",
    multiple=True,
    type=str,
    help="Files to exclude. See `glob_filter.py` for details.",
)
@click.option(
    "--include_filter",
    multiple=True,
    type=str,
    help="Files to include. See `glob_filter.py` for details.",
)
@pass_api_and_info
def download_run_from_wandb_command(
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    run: Optional[str],
    output_dir: pathlib.Path,
    df: Optional[pd.DataFrame] = None,
    exclude_filter: Optional[List[str]] = None,
    include_filter: Optional[List[str]] = None,
) -> pd.DataFrame:
    return download_run_from_wandb(
        api,
        entity,
        project,
        sweep,
        run,
        output_dir,
        df,
        GlobBasedFileFilter(exclude_filter, include_filter),
    )


def find_best_model(
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    metric: Metric,
    output_file: Optional[pathlib.Path] = None,
    fields: List[str] = None,
    skip_writing: bool = False,
    df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    assert entity is not None
    assert project is not None

    df_local = df or get_all_data(
        api,
        entity,
        project,
        sweep,
        None,
        fields=fields,
        index="path",
        skip_writing=True,
    )
    # find best

    if metric.maximum:
        df_local = df_local.loc[
            df_local.groupby("sweep", dropna=True)[metric.name].idxmax()
        ]
    else:
        df_local = df_local.loc[
            df_local.groupby("sweep", dropna=True)[metric.name].idxmin()
        ]

    write_df(df_local, output_file, skip_writing)

    return df_local
