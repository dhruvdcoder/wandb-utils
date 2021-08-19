from wandb_utils.version import VERSION
from typing import Optional, List, Tuple, TypeVar, Callable, Any, cast, Mapping
import click
from wandb_utils.config import (
    load_config,
    LOCAL_CONFIG_FILENAME,
    load_commands_config,
    use_config,
    config_file_decorator,
)
import wandb
from functools import update_wrapper
import logging
import os
import sys
import pandas as pd
import json
import click_config_file
from .common import (
    METRIC,
    DICT,
    Metric,
    MetricParamType,
    DictParamType,
    WandbAPIWrapper,
    pass_api_wrapper,
    pass_api_and_info,
    processor,
    apply_decorators,
)

logger = logging.getLogger(__name__)


@click.group(name="wandb-utils", chain=True)
@click.version_option(version=VERSION)
@click.option(
    "-e", "--entity", type=str, help="Wandb entity (username or team)"
)
@click.option(
    "-p",
    "--project",
    type=str,
    help="Wandb project",
)
@click.option(
    "-s",
    "--sweep",
    type=str,
    help="Wandb sweep (default:None)",
)
@click.pass_context
@config_file_decorator()
def wandb_utils(
    ctx: click.Context,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
) -> None:
    logger.debug(
        f"Create wandb api instance with entity={entity}, project={project}, sweep={sweep}"
    )
    ctx.obj = WandbAPIWrapper(entity=entity, project=project, sweep=sweep)
    commands_config, global_config = load_config()
    ctx.default_map = commands_config.get("wandb_utils", {})


@wandb_utils.result_callback()
def process_commands(processors: List[Callable], **extra):
    # Somehow we are getting
    # entity, project, and sweep as args again. We need to swallow them here.
    df = None

    for processor in processors:
        df = processor(df)
