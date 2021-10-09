from typing import (
    List,
    Tuple,
    Union,
    Dict,
    Any,
    Optional,
    cast,
    TypeVar,
    Callable,
)
import logging
import pathlib
from ruamel.yaml import YAML
import click
from copy import deepcopy
import click_config_file

logger = logging.getLogger(__name__)


DEFAULT_CONFIG: Dict = {"wandb-utils": {}, "wandb-slurm": {}}
LOCAL_CONFIG_FILENAME = ".wandb_utils_config.yaml"
GLOBAL_CONFIG_FILENAME = str(
    pathlib.Path(click.get_app_dir("wandb_utils", force_posix=True))
    / "config.yaml"
)


RAW_CONFIG: Optional[Dict] = None
GLOBAL_SETTINGS: Optional[Dict] = None


def load_commands_config(
    config_file: Optional[Union[str, pathlib.Path]] = None,
    cmd_name: Optional[str] = None,
) -> Dict:

    return load_config(config_file, cmd_name)[0]


def __load_config(
    config_file: Union[str, pathlib.Path],
) -> None:
    assert config_file is not None
    global RAW_CONFIG
    global GLOBAL_SETTINGS

    if not pathlib.Path(config_file).exists():
        RAW_CONFIG = DEFAULT_CONFIG
        GLOBAL_SETTINGS = {}
        logger.info("config for wandb-utils does not exist")
        logger.info(f"storing default config for the project in {config_file}")
        with open(pathlib.Path(config_file), "w") as f:
            yaml = YAML()
            yaml.dump(RAW_CONFIG, f)
    else:

        yaml = YAML()

        logger.debug(f"Read config from {config_file}")
        RAW_CONFIG = yaml.load(pathlib.Path(config_file))
        RAW_CONFIG = cast(Dict, RAW_CONFIG)
        GLOBAL_SETTINGS = RAW_CONFIG.pop("global", {})


def load_config(
    config_file: Optional[Union[str, pathlib.Path]] = None,
    cmd_name: Optional[str] = None,
) -> Tuple[Dict, Dict]:
    if RAW_CONFIG is None:
        __load_config(config_file)
    assert RAW_CONFIG is not None
    assert GLOBAL_SETTINGS is not None

    return (
        deepcopy(RAW_CONFIG.get(cmd_name, {}))
        if cmd_name
        else deepcopy(RAW_CONFIG),
        deepcopy(GLOBAL_SETTINGS),
    )


F = TypeVar("F", bound=Callable[..., Any])


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
