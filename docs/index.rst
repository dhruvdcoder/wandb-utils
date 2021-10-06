Weights & Biases Utilities
===============================

What is it?
---------------

`Weight & Biases (wandb) <wandb.ai/site>`_ is a experiment management and hyperparameter tuning utility for machine learning experiments. Please refer to `their website <https://wandb.ai/site>`_ for more information. Weights & Biases Utitlities (wandb-utils), is library of some utility functions and command line interface built on top of the official wandb API. This is an unofficial library, meaning that it is not supported by the Weights & Biases team, but is managed by open source contributors and ML researchers.

What can it do?
----------------

1. :doc:`Query data for your experiments<getting_data>` on wandb server using a single command.
2. Apply a chain of multiple :doc:`data processing<processing_data>` commands to your run data.
3. :doc:`Download files for runs<download_run>` using a single command `files`.
4. :doc:`Upload files to runs<uploading_files_to_runs>` **after** its completion using a single command `files`.

.. toctree::
   :hidden:
   :maxdepth: 1

   Getting data <getting_data>
   Processing data <processing_data>
   Downloading run files <download_run>
   Uploading run files <uploading_files_to_runs>
   Manging wandb agents on a slurm cluster <managing_jobs_on_slurm>
   cli
