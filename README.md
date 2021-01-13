# Weights and Biases utilities

1. Get the metrics of all runs

2. Get the best runs in each sweep

3. Delete local copies of the runs, except a pre-specified set of runs.

# Usage

1. Creating a sweep for best runs

```
multiple_runs_sweep -e iesl-boxes -p multilabel-learning-datasets -s yufmnnih --metric best_validation_MAP --maximum -o temp/temp1/config.json --wandb_tags dryrun extra --sweep_name temp
```

```
multiple_runs_sweep -e iesl-boxes -p multilabel-learning-datasets -r x05gzdqy -o temp/temp1/config.json --wandb_tags dryrun extra --sweep_name temp
```




# Author(s)

0 [Dhruvesh Patel](https://github.com/dhruvdcoder)

