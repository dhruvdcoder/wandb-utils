from typing import List, Tuple, Union, Dict, Any, Optional
import click
import wandb
import pandas as pd
import pathlib
import sys
from wandb_utils.misc import all_data_df
from .wandb_utils import (
    pass_api_wrapper,
    pass_api_and_info,
    processor,
    apply_decorators,
    DICT,
    config_file_decorator,
)
from .utils import read_df, to_csv
from .utils import query as df_query
import logging

logger = logging.getLogger(__name__)


@click.command(name="filter_df")
@click.option(
    "-f",
    "--fields",
    default=[],
    multiple=True,
    type=str,
    help="Fields to keep in the final dataframe. If not given, all fields are kept.",
)
@click.option(
    "-i",
    "--index",
    default=None,
    type=str,
    help="Field that is unique and can be used as index.",
)
@click.option(
    "--query",
    type=str,
)
@processor
@config_file_decorator()
def filter_df_chained(
    df: pd.DataFrame,
    fields: Tuple[str, ...],
    index: str,
    query: str,
) -> pd.DataFrame:
    """Apply a filter using `pandas.query`.

    QUERY is a pandas query string prepended with + (include) or - (exclude)
        For example to take only those rows that have 'sweep_name' column that contains 'best', the query string will be '+sweep_name.str.contains("best")'
        See https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.query.html#pandas.DataFrame.query for details
        See https://jakevdp.github.io/PythonDataScienceHandbook/03.12-performance-eval-and-query.html for examples of query strings.
    """
    f = list(fields)  # type:ignore

    if query:
        df = df_query(df, query)
    logger.debug(f"Filtered contents:\n{df}")

    if index:
        df = df.set_index(index)

        if f and index in f:
            f.remove(index)

    if f:
        df = df[list(f)]

    return df
