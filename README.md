# Weights and Biases utilities

1. Get the metrics of all runs

2. Get the best runs in each sweep

3. Delete local copies of the runs, except a pre-specified set of runs.

# Usage

1. Creating a sweep for best runs

```
multiple_runs_sweep -e iesl-boxes -p multilabel-learning-datasets -t bibtex-best-vector -o model_configs/best_models_configs/bibtex-vector.jsonnet -s hizo9wjs -m best_validation_MAP --maximum --seed_parameters pytorch_seed numpy_seed random_seed --fixed_overrides "{\"type\": \"train_test_log_to_wandb\"}" --include_packages multilabel_learning
```

```
multiple_runs_sweep -e iesl-boxes -p multilabel-learning-datasets -r x05gzdqy -o temp/temp1/config.json --wandb_tags dryrun extra --sweep_name temp
```




# Author(s)

0 [Dhruvesh Patel](https://github.com/dhruvdcoder)

