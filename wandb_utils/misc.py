import wandb
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def all_data_df(entity: str, project: str)->pd.DataFrame:
    """
    Get the data for all the runs.
    """
    logger.info(f"Querying wandb...")
    api = wandb.Api({'entity':entity, 'project':project})
    runs = api.runs(f'{entity}/{project}')
    summary_list = []
    config_list = []
    name_list = []
    sweep_list = []

    for run in runs:
        # run.summary are the output key/values like accuracy.  We call ._json_dict to omit large files
        summary_list.append(run.summary._json_dict)

        # run.config is the input metrics.  We remove special values that start with _.
        config_list.append({k:v for k,v in run.config.items() if not k.startswith('_')})

        # run.name is the name of the run.
        name_list.append(run.id)

        # sweep
        sweep_list.append(run.sweep.id if run.sweep else "")

    summary_df = pd.DataFrame.from_records(summary_list)
    config_df = pd.DataFrame.from_records(config_list)
    name_df = pd.DataFrame({'run': name_list})
    sweep_df = pd.DataFrame({'sweep': sweep_list})
    all_df = pd.concat([name_df,sweep_df, config_df,summary_df], axis=1)

    return all_df

def find_best_models_in_sweeps(entity: str, project: str, metric: str) -> pd.DataFrame:
    all_df = all_data_df(entity, project)
    # ref: https://stackoverflow.com/questions/32459325/python-pandas-dataframe-select-row-by-max-value-in-group

    return all_df.loc[all_df.groupby('sweep', dropna=True)[metric].idxmax()]
