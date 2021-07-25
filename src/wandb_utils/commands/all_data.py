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
from .utils import write_df
import logging

logger = logging.getLogger(__name__)


@click.command(name="get_all_data")
@click.option(
    "-o",
    "--output_file",
    required=False,
    type=click.Path(path_type=pathlib.Path),  # type: ignore
    help="File to which the data will be written"
    " If not provided, the name will be printed on the console. (default:None)",
)
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
    "--df_filter",
    type=str,
    help="""Pandas query string prepended with + (include) or - (exclude)
    For example to take only those rows that have 'sweep_name' column that contains 'best', the filter string will be '+sweep_name.str.contains("best")'
    See https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.query.html#pandas.DataFrame.query for details""",
)
@click.option(
    "--filters",
    type=DICT,
    help="""Filter used while querying wandb for runs. It uses MongoDB query syntax.
    See https://docs.wandb.ai/ref/python/public-api/runs and https://github.com/wandb/client/blob/v0.10.31/wandb/apis/public.py#L428 for how the query is used.
    See https://docs.mongodb.com/manual/reference/operator/query/ to learn about all the query operators in MongoDB query.
    """,
)
@pass_api_and_info
@config_file_decorator()
def get_all_data_command(
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    output_file: pathlib.Path,
    fields: Tuple[str, ...],
    index: str,
    df_filter: str,
    filters: Optional[Dict],
    skip_writing: bool = False,
    df: pd.DataFrame = None,
) -> pd.DataFrame:
    return get_all_data(
        api,
        entity,
        project,
        sweep,
        output_file,
        list(fields),
        index,
        df_filter,
        filters,
        skip_writing,
        df,
    )


@click.command(name="get_all_data")
@click.option(
    "-o",
    "--output_file",
    required=False,
    type=click.Path(path_type=pathlib.Path),  # type: ignore
    help="File to which the data will be written"
    " If not provided, the name will be printed on the console. (default:None)",
    hidden=True,  # use the feature through 'print' command
)
@click.option(
    "-f",
    "--fields",
    default=[],
    multiple=True,
    type=str,
    help="Fields to keep in the final dataframe. If not given, all fields are kept.",
    hidden=True,  # use the feature through 'filter' command
)
@click.option(
    "-i",
    "--index",
    default=None,
    type=str,
    help="Field that is unique and can be used as index.",
    hidden=True,  # use the feature through 'filter' command
)
@click.option(
    "--df_filter",
    type=str,
    help="""Pandas query string prepended with + (include) or - (exclude).
    For example to take only those rows that have 'sweep_name' column that contains 'best', the filter string will be '+sweep_name.str.contains("best")'
    See https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.query.html#pandas.DataFrame.query for details""",
    hidden=True,  # use the feature through 'filter' command
)
@click.option(
    "--filters",
    type=DICT,
    help="""Filter used while querying wandb for runs. It uses MongoDB query syntax.
    See https://docs.wandb.ai/ref/python/public-api/runs and https://github.com/wandb/client/blob/v0.10.31/wandb/apis/public.py#L428 for how the query is used.
    See https://docs.mongodb.com/manual/reference/operator/query/ to learn about all the query operators in MongoDB query.
    """,
)
@pass_api_and_info
@processor
@config_file_decorator()
def get_all_data_command_chained(
    df: pd.DataFrame,
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    output_file: pathlib.Path,
    fields: Tuple[str, ...],
    index: str,
    df_filter: str,
    filters: Optional[Dict],
    skip_writing: bool = True,
) -> pd.DataFrame:
    return get_all_data(
        api,
        entity,
        project,
        sweep,
        output_file,
        list(fields),
        index,
        df_filter,
        filters,
        skip_writing,
        df,
    )


def get_all_data(
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    output_file: Optional[pathlib.Path] = None,
    fields: List[str] = None,
    index: str = None,
    df_filter: str = None,
    filters: Optional[Dict] = None,
    skip_writing: bool = False,
    df: pd.DataFrame = None,
) -> pd.DataFrame:
    assert entity is not None
    assert project is not None
    df = all_data_df(entity, project, sweep, api, filters=filters)

    if df_filter:
        logger.info(f"Filtering using {filter}")

        if df_filter.startswith("-"):  # remove the filter results
            df_ = df.query(df_filter[1:], engine="python")
            df = df[~df.index.isin(df_.index)]
        elif df_filter.startswith("+"):  # keep only the filter results
            df = df.query(df_filter[1:], engine="python")
        else:
            df = df.query(df_filter, engine="python")

    if index:
        df = df.set_index(index)

        if fields and index in fields:
            fields.remove(index)

    if fields:
        df = df[list(fields)]
    write_df(df, output_file, skip_writing)

    return df
