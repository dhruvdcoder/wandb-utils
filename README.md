
# Weights and Biases utilities

## Features

1. Get the metrics of all runs

2. Get the best runs in each sweep

3. Delete local copies of the runs, except a pre-specified set of runs.

## Installation

```
pip install git+https://github.com/dhruvdcoder/wandb-utils.git
```

## Usage

1. Creating a sweep for best runs

```
multiple_runs_sweep -e iesl-boxes -p multilabel-learning-datasets -t bibtex-best-vector -o model_configs/best_models_configs/bibtex-vector.jsonnet -s hizo9wjs -m best_validation_MAP --maximum --seed_parameters pytorch_seed numpy_seed random_seed --fixed_overrides "{\"type\": \"train_test_log_to_wandb\"}" --include_packages multilabel_learning
```

```
multiple_runs_sweep -e iesl-boxes -p multilabel-learning-datasets3 -t typenet-best-vector -o ./best_models_configs/typenet-vector.jsonnet -r jyaoibd1 -m best_validation_micro_map --seed_parameters pytorch_seed numpy_seed random_seed --fixed_overrides "{\"type\": \"train_test_log_to_wandb\",\"trainer\": {\"patience\":4,\"callbacks\": [\"track_epoch_callback\",\"log_metrics_to_wandb\"],\"checkpointer\":{\"num_serialized_models_to_keep\": 0}},\"model\": {\"add_new_metrics\": true}}" --delete_keys "trainer.tensorboard_writer" "data_loader.pin_memory" "trainer.epoch_callbacks" --include_packages multilabel_learning
```

```
multiple_runs_sweep -e iesl-boxes -p multilabel-learning-datasets -r x05gzdqy -o temp/temp1/config.json --wandb_tags dryrun extra --sweep_name temp
```

2. Remove specific files from the server.

```
remove_files_from_server --help


usage: remove_files_from_server [-h] -e ENTITY -p PROJECT [-s SWEEP] [--allowed_runs ALLOWED_RUNS | --not_allowed_runs NOT_ALLOWED_RUNS] [--allowed_files_globs ALLOWED_FILES_GLOBS | --not_allowed_files_globs NOT_ALLOWED_FILES_GLOBS]

Remove saved files on the server without removing the run. The command supports run and file filters. "Allowed" in the filter means that the filter is of positive type, i.e., it returns true for things that pass that filter. In context of this command, the things that
pass the filter get deleted.

optional arguments:
  -h, --help            show this help message and exit
  -e ENTITY, --entity ENTITY
                        Wandb entity (username or team)
  -p PROJECT, --project PROJECT
                        Wandb project
  -s SWEEP, --sweep SWEEP
                        Wandb sweep (default:None)
  --allowed_runs ALLOWED_RUNS
                        Path to a file containing allowed runs with each run_id on a separate line.
  --not_allowed_runs NOT_ALLOWED_RUNS
                        Path to a file containing not allowed runs with each run_id on a separate line.
  --allowed_files_globs ALLOWED_FILES_GLOBS
                        Path to a file containing allowed globs with each glob on a separate line.
  --not_allowed_files_globs NOT_ALLOWED_FILES_GLOBS
                        Path to a file containing not allowed globs with each glob on a separate line.
```

# Examples of chaining

Note: Don't forget to escape `$` in the mongo query strings.

```
wandb_utils_chain -e iesl-boxes -p multilabel-learning-datasets3  -s piltv95b get_all_data filter_df -f sweep_name -f run -f test_MAP -f path -i path --query "+test_MAP.idxmax()" print

wandb_utils_chain -e iesl-boxes -p multilabel-learning-datasets3 get_all_data --filters "{\"sweep\":{\"\$in\":[\"piltv95b\", \"ks4tcn2s\"]}}" filter_df -f sweep_name -f run -f path -f test_MAP -i path --query "+test_MAP.idxmax()" print
```

Get best runs from a set of sweeps or all sweeps. Note that something similar is possible using `groupby`. However, by using groupby, you will lose the other fields (other than, `sweep_name` and `test_MAP`).

```
wandb_utils_chain -e iesl-boxes -p multilabel-learning-datasets3 get_all_data --filters "{\"sweep\":{\"\$in\":[\"piltv95b\", \"ks4tcn2s\"]}}" filter_df -f sweep_name -f run -f path -f test_MAP -i path --query "df.sort_values('test_MAP', ascending=False).drop_duplicates(['sweep_name'])" print
```

Downloading files for a single run:

```
wandb_utils download_run_from_wandb --include_filter "**/*.json" --exclude_filter "**/metrics.json" -o wandb/8nfcy7xp/files  8nfcy7xp --overwrite
```

Copy to rclone remote.

```
wandb_utils rclone  --filter "'- **/metrics.json'"  --filter "'+ **/*.json'" copy SOURCE REMOTE TARGET
```


# Author(s)

0 [Dhruvesh Patel](https://github.com/dhruvdcoder)
