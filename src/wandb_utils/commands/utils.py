from typing import List, Tuple, Union, Dict, Any, Optional
import pandas as pd
import logging
import pathlib
import sys

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


def __query(df: pd.DataFrame, q: str, engine: str = "python") -> pd.DataFrame:
    breakpoint()
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
