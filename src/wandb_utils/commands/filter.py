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
from wandb_utils.misc import read_df, to_csv
import logging

logger = logging.getLogger(__name__)


def __query(df: pd.DataFrame, q: str, engine: str = "python") -> pd.DataFrame:
    try:
        df = df.query(q, engine=engine)
    except Exception as e:
        logger.warning(f"df.query failed with {e}")
        logger.warning("trying pd.eval")
        try:
            df = pd.eval(q, engine=engine)
        except Exception as e:
            logger.warning(f"pd.eval failed with {e}")
            logger.warning("trying python's eval")
            df = eval(q)

    return df


def df_query(
    df: pd.DataFrame, df_filter: str, engine: str = "python"
) -> pd.DataFrame:
    logger.debug(f"Filtering using {df_filter}")

    if df_filter.startswith("-"):  # remove the filter results
        df_ = __query(df, df_filter[1:], engine=engine)
        df = df[~df.index.isin(df_.index)]
    elif df_filter.startswith("+"):  # keep only the filter results
        df = __query(df, df_filter[1:], engine=engine)
    else:
        df = __query(df, df_filter, engine=engine)

    if not isinstance(df, pd.DataFrame):
        if isinstance(df, pd.Series):
            df = pd.DataFrame(df).T

    return df


@click.command(name="filter-df")
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
def filter_df(
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
