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


@click.command(name="from-file")
@click.argument(
    "input-file",
    required=True,
    type=click.Path(path_type=pathlib.Path),  # type: ignore
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
    type=str,
    help="Field that is unique and can be used as index.",
)
@click.option(
    "-d",
    "--delimiter",
    type=str,
    default="\t",
    help="Column delimiter (default: TAB)",
)
@processor
@config_file_decorator()
def from_file_command(
    df: Optional[pd.DataFrame],
    input_file: pathlib.Path,
    fields: Tuple[str, ...],
    index: str,
    delimiter: str,
) -> pd.DataFrame:
    """Read the data of runs from a `input-file` created using any wandb-utils command.

    `input-file` is the path to a .csv file.
    """
    df = from_file(input_file, list(fields), index, delimiter)
    logger.debug(f"Filtered contents of {input_file}:\n{df}")

    return df


# TODO: move to api
def from_file(
    input_file: pathlib.Path,
    fields: List[str] = None,
    index: str = None,
    delimiter: str = "\t",
) -> pd.DataFrame:
    df = read_df(input_file, sep=delimiter)

    if index:
        df = df.set_index(index)

        if fields and index in fields:
            fields.remove(index)

    if fields:
        df = df[list(fields)]

    return df
