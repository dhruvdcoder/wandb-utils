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


# bunch of useful functions that can be used in pd-eval calls.
def rmax(A, B):
    return pd.concat([A, B], axis=1).max(axis=1)


def __python_exec(df: pd.DataFrame, q: str) -> pd.DataFrame:
    exec(q)  # exec does not return anything
    return df


def __python_eval(df: pd.DataFrame, q: str) -> pd.DataFrame:
    df = eval(q)
    return df


def __pd_eval(df: pd.DataFrame, q: str, engine: str = "python") -> pd.DataFrame:
    try:
        df = pd.eval(q, engine=engine)
    except Exception as e:
        logger.warning(f"pd.eval failed with {e} without a target. Trying with a target.")
        df = pd.eval(q, engine=engine, target=df)
    return df


def __query(df: pd.DataFrame, q: str, engine: str = "python") -> pd.DataFrame:
    try:
        df = df.query(q, engine=engine)
    except Exception as e:
        logger.warning(f"df.query failed with {e}.")
        logger.warning("Trying df.query with target.")
        df = df.query(q, engine=engine, target=df)
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
    help=("Query string passed to df.query. "
          "See https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.query.html for details"),
)
@click.option(
    "--pd-eval",
    type=str,
    help=("String to pass to pd.eval"
          "See https://pandas.pydata.org/docs/reference/api/pandas.eval.html#pandas.eval for details.")
)
@click.option(
    "--python-eval",
    type=str,
    help=("String to passed to python's eval `df = eval(python_eval)`")
)
@click.option(
    "--python-exec",
    type=str,
    help=("String to pass to python's exec")
)
@processor
@config_file_decorator()
def filter_df(
        df: pd.DataFrame,
        fields: Tuple[str, ...],
        index: str,
        query: str,
        pd_eval: str,
        python_eval: str,
        python_exec: str,
) -> pd.DataFrame:
    """Apply a processor using `pandas.query`, `pandas.eval`, `python eval` or `python exec`.

    No more than one of the processors should be provided at a time.
    """
    f = list(fields)  # type:ignore
    processors = [(query, __query, "query"), (pd_eval, __pd_eval, "pd-eval"),
                  (python_eval, __python_eval, "python-eval"),
                  (python_exec, __python_exec, "python-exec")]
    selected_processor = None
    for i, s in enumerate(processors):
        if s[0]:
            selected_processor = s
            for j in range(i + 1, len(processors)):
                if processors[j][0]:
                    raise ValueError("Only one of the processors should be set."
                                     f"You provided {s[-1]} and {processors[j][-1]}.")
            break
    if selected_processor is not None:
        df = selected_processor[1](df, selected_processor[0])
        logger.debug(f"Filtered contents:\n{df}")

    if index:
        df = df.set_index(index)

        if f and index in f:
            f.remove(index)
    if f:
        df = df[list(f)]

    return df
