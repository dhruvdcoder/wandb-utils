from typing import List, Tuple, Union, Dict, Any, Optional, cast
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
from wandb_utils.misc import write_df
import logging

logger = logging.getLogger(__name__)


@click.command(name="print")
@click.option(
    "-o",
    "--output_file",
    type=click.Path(path_type=pathlib.Path),
    help="If given the output is written to the file.",
)
@processor
@config_file_decorator()
def print_command(
    df: pd.DataFrame,
    output_file: Optional[pathlib.Path],
) -> pd.DataFrame:
    """Print the contents of a df and optionally write to a file."""
    write_df(df, output_file, skip_writing=False)

    return df
