# Weights & Biases Utilities

## What is it?

[Weight & Biases (wandb)](wandb.ai/site) is a experiment management and hyperparameter tuning utility for machine learning experiments. Please refer to [their website](https://wandb.ai/site) for more information. Weights & Biases Utitlities (wandb-utils), is library of some utility functions and command line interface built on top of the official wandb API. This is an unofficial library, meaning that it is not supported by the Weights & Biases team, but is managed by open source contributors and ML researchers.

# Tutorials
## How to use this repo 
1. init your sweep according to the wandb sweep init part [wandb sweep example](https://github.com/wandb/examples/tree/master/examples/keras/keras-cnn-fashion). Notice: save your config.yaml with your repo and remember to use the program to figure which python to run 
2. install this repo using pip 
3. init default wandb-slurm template in the "slurm" dir by running `wandb-slurm `
4. modify the slurm.j2 in slurm dir, especially the conda env 
5. run the wandb-slurm according to your SLURM CLUSTER command 
