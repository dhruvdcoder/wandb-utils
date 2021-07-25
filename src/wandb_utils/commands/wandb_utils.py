from wandb_utils.version import VERSION
from typing import Optional, List, Tuple, TypeVar, Callable, Any, cast, Mapping
import click
from .temp import hello
from .utils import load_config, LOCAL_CONFIG_FILENAME, load_commands_config
import wandb
from functools import update_wrapper
import logging
import os
import sys
import pandas as pd
import json
import click_config_file

if os.environ.get("WANDB_UTILS_DEBUG"):
    LEVEL = logging.DEBUG
else:
    level_name = os.environ.get("WANDB_UTILS_LOG_LEVEL", "INFO")
    LEVEL = logging._nameToLevel.get(level_name, logging.INFO)

logging.basicConfig(
    stream=sys.stderr,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=LEVEL,
)


class Metric(object):
    def __init__(self, name: str, maximum: bool = True):
        self.name = name
        self.maximum = maximum


class MetricParamType(click.ParamType):
    name = "metric"

    def convert(self, value: str, param, ctx) -> Metric:  # type:ignore
        if not isinstance(value, str):
            raise ValueError(f"{value} is not a string")

        if value[0] in ["+", "-"]:
            return Metric(value[1:], value[0] == "+")
        else:
            return Metric(value)


class DictParamType(click.ParamType):
    name = "dict"

    def convert(self, value: str, param, ctx) -> Metric:  # type:ignore
        if isinstance(value, str):
            return json.loads(value)
        elif isinstance(value, dict):
            return value
        else:
            raise ValueError


METRIC = MetricParamType()
DICT = DictParamType()


class WandbAPIWrapper(object):
    """
    Contains an instance of `wandb.Api` or `wandb.PublicApi` and some other information.
    """

    def __init__(
        self, entity: str = None, project: str = None, sweep: str = None
    ):
        self.api = wandb.Api()  # type:ignore
        self.entity = entity
        self.project = project
        self.sweep = sweep


# generate a decorator which will find the instance of WandbAPIWrapper in the context
pass_api_wrapper = click.make_pass_decorator(WandbAPIWrapper)

F = TypeVar("F", bound=Callable[..., Any])


def pass_api_and_info(f: F) -> F:
    """
    Code adopted from `click.make_pass_decorator`.
    Instead of passing an instance of `WandbAPIWrapper`, it passes the following args:
        api: wandb.Api
        entity: Optional[str],
        project: Optional[str],
        sweep: Optional[str]
    """

    def new_func(*args, **kwargs):  # type: ignore
        ctx = click.globals.get_current_context()
        # Tries to find closest instance
        # if not found, creates a default one.
        obj = ctx.ensure_object(WandbAPIWrapper)

        if obj is None:
            raise RuntimeError(
                "Managed to invoke callback without a context"
                f" object of type {object_type.__name__!r}"
                " existing."
            )
        # populate the default values

        return ctx.invoke(
            f, obj.api, obj.entity, obj.project, obj.sweep, *args, **kwargs
        )

    return update_wrapper(cast(F, new_func), f)


# def __override_with_config(ctx: click.Context, config: Mapping) -> Mapping:
#    for param, value in ctx.params.items():
#        if value is None and param in config:
#            ctx.params[param] = config_data[param]
#
#    return ctx


def use_config(f: F) -> F:
    """Reads an set the config on the default_map."""

    def new_func(*args, **kwargs):  # type: ignore
        ctx = click.get_current_context()
        commands_config, global_config = load_config()

        if ctx.default_map:
            ctx.default_map.update(commands_config.get(ctx.info_name, {}))
        else:
            ctx.default_map = commands_config.get(ctx.info_name)

        return f(*args, **kwargs)

    return update_wrapper(cast(F, new_func), f)


def config_file_decorator():
    return click_config_file.configuration_option(
        default=LOCAL_CONFIG_FILENAME,
        implicit=False,
        provider=load_commands_config,
        hidden=True,
    )


@click.group()
@click.version_option(version=VERSION)
@click.option("-e", "--entity", help="Wandb entity (username or team)")
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
    ctx.obj = WandbAPIWrapper(entity=entity, project=project, sweep=sweep)
    # commands_config, global_config = load_config()
    # ctx.default_map = commands_config
    # ctx.default_map = {"temp": {"foo": 100}}


def processor(f: Callable):
    """Helper decorator to rewrite a function so that it returns another
    function from it.
    """

    def new_func(*args, **kwargs):
        def processor(df):
            return f(df, *args, **kwargs)

        return processor

    return update_wrapper(new_func, f)


def apply_decorators(decorators):
    def decorator(f):
        for d in reversed(decorators):
            f = d(f)

        return f

    return decorator


@click.group(chain=True)
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
def wandb_utils_chain(
    ctx: click.Context,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
) -> None:
    ctx.obj = WandbAPIWrapper(entity=entity, project=project, sweep=sweep)
    commands_config, global_config = load_config()
    ctx.default_map = commands_config.get("wandb_utils_chain", {})


@wandb_utils_chain.result_callback()
def process_commands(processors: List[Callable], **extra):
    # Somehow we are getting
    # entity, project, and sweep as args again. We need to swallow them here.
    df = None

    for processor in processors:
        df = processor(df)
