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
from .common import processor
import logging

logger = logging.getLogger(__name__)


@click.command(name="run-dir")
@click.argument(
    "run",
    type=str,
)
@click.option(
    "--check_local",
    is_flag=True,
)
@click.option(
    "--wandb_dir",
    type=click.Path(path_type=pathlib.Path),
    default=pathlib.Path("wandb"),
)
@pass_api_and_info
@processor
@config_file_decorator()
def run_dir_command(
    df: Optional[pd.DataFrame],
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    run: str,
    check_local: bool,
    wandb_dir: pathlib.Path,
) -> None:
    potential = list(wandb_dir.glob(f"*{run}"))

    if len(potential) > 1:
        raise NotImplementedError(
            f"Ambiguous run directory because we have multiple: {potential}"
        )

    if len(potential) == 0:
        click.echo(f"{wandb_dir / run}")
    else:
        click.echo(f"{potential[0]}")
