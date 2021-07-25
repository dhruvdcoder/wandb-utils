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
)
from .utils import read_df, to_csv
import logging

logger = logging.getLogger(__name__)


@click.command(name="get_from_file")
@click.argument(
    "input_file",
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
    default="path",
    type=str,
    help="Field that is unique and can be used as index.",
)
def get_from_file_command(
    input_file: pathlib.Path,
    fields: Tuple[str, ...],
    index: str,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read the data of runs from a csv file created using any wandb-utils command.

    INPUT_FILE is the path to a .csv file.
    """
    df = from_file(
        input_file,
        list(fields),
        index,
    )
    logger.debug(f"Filtered contents of {input_file}:\n{df}")

    return df


@click.command(name="get_from_file")
@click.argument(
    "input_file",
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
    default="path",
    type=str,
    help="Field that is unique and can be used as index.",
)
@processor
def get_from_file_chained(
    df: Optional[pd.DataFrame],
    input_file: pathlib.Path,
    fields: Tuple[str, ...],
    index: str,
) -> pd.DataFrame:
    """Read the data of runs from a csv file created using any wandb-utils command.

    INPUT_FILE is the path to a .csv file.
    """
    df = from_file(
        input_file,
        list(fields),
        index,
    )
    logger.debug(f"Filtered contents of {input_file}:\n{df}")

    return df


def from_file(
    input_file: pathlib.Path,
    fields: List[str] = None,
    index: str = None,
) -> pd.DataFrame:
    df = read_df(input_file)

    if index:
        df = df.set_index(index)

        if fields and index in fields:
            fields.remove(index)

    if fields:
        df = df[list(fields)]

    return df
