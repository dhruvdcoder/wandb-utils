from typing import List, Tuple, Union, Dict, Any, Optional, cast
import pandas as pd
import logging
import pathlib
import sys
from ruamel.yaml import YAML
import click
import re
from copy import deepcopy

logger = logging.getLogger(__name__)


def to_csv(df: pd.DataFrame) -> str:
    return df.to_csv(sep="\t")


def write_df(
    df: pd.DataFrame, output_file: Optional[pathlib.Path], skip_writing: bool
) -> None:
    if output_file and not skip_writing:
        with open(output_file, "w") as f:
            logger.debug(f"Writing to {output_file}.")
            output = to_csv(df)
            f.write(output)
    elif not skip_writing:
        logger.debug(f"No output file, printing on stdout.")
        output = to_csv(df)
        sys.stdout.write(output)
    else:
        logger.debug("Not writing/printing because skip_writing=True")


def read_df(path: pathlib.Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t")


def get_local_run_dir(run: str, wandb_dir: pathlib.Path):
    pass


def __query(df: pd.DataFrame, q: str, engine: str = "python") -> pd.DataFrame:
    try:
        df = df.query(q, engine=engine)
    except Exception as e:
        logger.warning(f"df.query failed with {e}")
        logger.warning("trying pd.eval")
        try:
            df = pd.eval(q, engine=engine)
        except Exception as e:
            logger.warning(f"pd.eval failed with {e}")
            logger.warning("trying python's eval")
            df = eval(q)

    return df


def query(
    df: pd.DataFrame, df_filter: str, engine: str = "python"
) -> pd.DataFrame:
    logger.debug(f"Filtering using {df_filter}")

    if df_filter.startswith("-"):  # remove the filter results
        df_ = __query(df, df_filter[1:], engine=engine)
        df = df[~df.index.isin(df_.index)]
    elif df_filter.startswith("+"):  # keep only the filter results
        df = __query(df, df_filter[1:], engine=engine)
    else:
        df = __query(df, df_filter, engine=engine)

    if not isinstance(df, pd.DataFrame):
        if isinstance(df, pd.Series):
            df = pd.DataFrame(df).T

    return df


DEFAULT_CONFIG: Dict = {"wandb_utils": {}, "wandb_utils_chain": {}}
LOCAL_CONFIG_FILENAME = ".wandb_utils_config.yaml"
GLOBAL_CONFIG_FILENAME = str(
    pathlib.Path(click.get_app_dir("wandb_utils")) / "config.yaml"
)

RAW_CONFIG: Optional[Dict] = None
GLOBAL_SETTINGS: Optional[Dict] = None


def update_config(config: Dict, local: bool = True):
    pass


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
