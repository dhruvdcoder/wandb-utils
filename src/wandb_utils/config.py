from typing import List, Tuple, Union, Dict, Any, Optional, cast
import logging
import pathlib
from ruamel.yaml import YAML
import click
from copy import deepcopy

logger = logging.getLogger(__name__)


DEFAULT_CONFIG: Dict = {"wandb_utils": {}, "wandb_utils_chain": {}}
LOCAL_CONFIG_FILENAME = ".wandb_utils_config.yaml"
GLOBAL_CONFIG_FILENAME = str(
    pathlib.Path(click.get_app_dir("wandb_utils")) / "config.yaml"
)

RAW_CONFIG: Optional[Dict] = None
GLOBAL_SETTINGS: Optional[Dict] = None


def load_commands_config(
    config_file: Optional[Union[str, pathlib.Path]] = None,
    cmd_name: Optional[str] = None,
) -> Dict:

    return load_config(config_file, cmd_name)[0]


def __load_config(
    config_file: Optional[Union[str, pathlib.Path]] = None,
) -> None:
    global RAW_CONFIG
    global GLOBAL_SETTINGS

    if config_file is None:
        if pathlib.Path(LOCAL_CONFIG_FILENAME).is_file():
            config_file = LOCAL_CONFIG_FILENAME

    if config_file is None:
        if pathlib.Path(GLOBAL_CONFIG_FILENAME).is_file():
            config_file = GLOBAL_CONFIG_FILENAME

    if config_file is None:
        RAW_CONFIG = DEFAULT_CONFIG
        GLOBAL_SETTINGS = {}
    assert config_file is not None

    if not pathlib.Path(config_file).is_file():
        raise ValueError(f"{config_file} does not exist")
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
