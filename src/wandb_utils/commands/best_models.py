from typing import List, Tuple, Union, Dict, Any, Optional
import click
import wandb
import pandas as pd
import argparse
import pathlib
import sys
from wandb_utils.misc import find_best_models_in_sweeps
from .wandb_utils import (
    pass_api_wrapper,
    pass_api_and_info,
    METRIC,
    Metric,
    processor,
    apply_decorators,
)
from .all_data import get_all_data
from wandb_utils.misc import write_df
import logging

logger = logging.getLogger(__name__)

# TODO: read this from a project config file to support append functionallity
# Appending runs to a single csv file will work smoothly if the heads remain constant.
# It is very likely that the set of heads will remain constant for a particular project
DEFAULT_FIELDS = ["sweep", "sweep_name", "run", "tags"]


@click.command(name="best-model")
@click.option(
    "-m",
    "--metric",
    required=True,
    type=METRIC,
    help="Name of the metric to sort by. "
    "Prepend + or - for maximum or minimum, respectively. ",
)
@click.option(
    "-o",
    "--output-file",
    required=False,
    type=click.Path(path_type=pathlib.Path),  # type: ignore
    help="File to which the run names will be written/appended."
    " If not provided, the name will be printed on the console. (default:None)",
)
@click.option(
    "-f",
    "--fields",
    default=[],
    multiple=True,
    type=str,
    help="Fields to keep in the final dataframe.",
)
@click.option(
    "--skip-writing",
    is_flag=True,
    help="Skip writing or printing.",
    default=False,
)
@pass_api_and_info
@processor
def best_model_command(
    df: Optional[pd.DataFrame],
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    metric: Metric,
    output_file: pathlib.Path,
    fields: List[str],
    skip_writing: bool = False,
) -> pd.DataFrame:
    return find_best_model(
        api,
        entity,
        project,
        sweep,
        metric,
        output_file,
        list(set(list(fields) + DEFAULT_FIELDS + [metric.name])),
        skip_writing,
        df,
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
    df_local = (
        get_all_data(
            api,
            entity,
            project,
            sweep,
            None,
            fields=fields,
            index="path",
            skip_writing=True,
        )
        if df is None
        else df[fields]
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
