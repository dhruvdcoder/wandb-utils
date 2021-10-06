from typing import (
    List,
    Tuple,
    Union,
    Dict,
    Any,
    Optional,
    TypeVar,
    Callable,
    cast,
)
import wandb
import click
import json
from functools import update_wrapper
import click_config_file
import pathlib
from wandb_utils.config import (
    LOCAL_CONFIG_FILENAME,
    GLOBAL_CONFIG_FILENAME,
    load_commands_config,
)

F = TypeVar("F", bound=Callable[..., Any])


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


class ListParamType(click.ParamType):
    name = "list"

    def __init__(self, sep: str = "|") -> None:
        super().__init__()
        self.sep = sep

    def convert(self, value: str, param, ctx) -> List[str]:  # type:ignore
        if isinstance(value, str):
            return value.split(self.sep)
        elif isinstance(value, list):
            return value
        else:
            raise ValueError


METRIC = MetricParamType()
DICT = DictParamType()
LIST = ListParamType()


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

# moved to config.py
# def use_config(f: F) -> F:
#    """Reads an set the config on the default_map."""
#
#    def new_func(*args, **kwargs):  # type: ignore
#        ctx = click.get_current_context()
#        commands_config, global_config = load_config()
#
#        if ctx.default_map:
#            ctx.default_map.update(commands_config.get(ctx.info_name, {}))
#        else:
#            ctx.default_map = commands_config.get(ctx.info_name)
#
#        return f(*args, **kwargs)
#
#    return update_wrapper(cast(F, new_func), f)
#
#
# def config_file_decorator():
#    return click_config_file.configuration_option(
#        default=LOCAL_CONFIG_FILENAME,
#        implicit=False,
#        provider=load_commands_config,
#        hidden=True,
#    )


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


class FileFilter(object):
    def __call__(
        self,
        run: Union[wandb.apis.public.File, pathlib.Path, pathlib.PurePath],
    ) -> bool:
        """Whether to take the file or not"""

        return True


class GlobBasedFileFilter(FileFilter):
    def __init__(
        self,
        include_filter: Optional[List[str]] = None,
        exclude_filter: Optional[List[str]] = None,
    ):
        self.allowed_globs = set(include_filter or [])
        self.not_allowed_globs = set(exclude_filter or [])

    def match(
        self,
        path: Union[pathlib.Path, pathlib.PurePath],
        globs: List[str],
    ) -> bool:

        for glob in globs:
            if path.match(glob):
                return True

        return False

    def __call__(
        self,
        file_: Union[
            str, wandb.apis.public.File, pathlib.Path, pathlib.PurePath
        ],
    ) -> bool:
        include_match = True
        exclude_match = False
        match = None

        if isinstance(file_, str):
            file_ = pathlib.PurePath(file_)
        elif isinstance(file_, wandb.apis.public.File):
            file_ = pathlib.PurePath(file_.name)

        if self.allowed_globs:
            include_match = self.match(file_, list(self.allowed_globs))

        if self.not_allowed_globs:
            exclude_match = self.match(file_, list(self.not_allowed_globs))
        # 1, 0 => True
        # 1, 1 => False
        # 0, 1 => False
        # 0, 0 => False
        match = include_match and (not exclude_match)

        return match


class RunFilter(object):
    def __call__(self, run: wandb.apis.public.Run) -> bool:
        """Whether to take the run or not"""

        return True


class NameBasedRunFilter(RunFilter):
    def __init__(
        self,
        not_allowed_names: Optional[List[str]] = None,
        allowed_names: Optional[List[str]] = None,
    ):
        super().__init__()

        if bool(not_allowed_names) == bool(allowed_names):
            raise ValueError(
                "Exactly one of not_allowed_names or allowed_names should be passed"
            )
        self.allowed_names = set(allowed_names or [])
        self.not_allowed_names = set(not_allowed_names or [])
        self.allowed_branch = bool(allowed_names)

    def __call__(self, run: wandb.apis.public.Run) -> bool:
        if self.allowed_branch:
            return run.id in self.allowed_names
        else:

            return run.id not in self.not_allowed_names
