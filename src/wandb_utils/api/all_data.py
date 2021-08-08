from typing import List, Tuple, Union, Dict, Any, Optional
import pathlib
import logging
import pandas as pd
from wandb_utils.misc import all_data_df, write_df
import wandb

logger = logging.getLogger(__name__)


def get_all_data(
    api: wandb.PublicApi,
    entity: Optional[str],
    project: Optional[str],
    sweep: Optional[str],
    output_file: Optional[pathlib.Path] = None,
    fields: List[str] = None,
    index: str = None,
    df_filter: str = None,
    filters: Optional[Dict] = None,
    skip_writing: bool = False,
    df: pd.DataFrame = None,
) -> pd.DataFrame:
    assert entity is not None
    assert project is not None
    df = all_data_df(entity, project, sweep, api, filters=filters)

    if df_filter:
        logger.info(f"Filtering using {filter}")

        if df_filter.startswith("-"):  # remove the filter results
            df_ = df.query(df_filter[1:], engine="python")
            df = df[~df.index.isin(df_.index)]
        elif df_filter.startswith("+"):  # keep only the filter results
            df = df.query(df_filter[1:], engine="python")
        else:
            df = df.query(df_filter, engine="python")

    if index:
        df = df.set_index(index)

        if fields and index in fields:
            fields.remove(index)

    if fields:
        df = df[list(fields)]
    write_df(df, output_file, skip_writing)

    return df
