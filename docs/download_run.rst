Downloading files for runs from wandb
=======================================

Use `files` command to download run files either for a single run or a bunch of runs through chaining.

Downloading files for a single run
--------------------------------------

.. code-block:: console

   $ wandb-utils \
   files \
   -f "+ *log*|- *output*" \
   --base-path tests/commands/assets \
   --destination local \
   --action move \
   --overwrite \
   yn7uvkia


Downloading files for multiple runs
-------------------------------------

Chaining can be used to download/delete files for multiple runs.

.. code-block:: console

   $ wandb-utils \     # main command
   all-data --filters "{\"sweep\": {\"\$in\": [\"vg17h6fd\"]} }" \         # dataframe of runs with specific sweep
   filter-df -f run \       # keep only the run column
   files -f "+ *.json" --destination local --action copy --base-path temp df        # download all json files in temp dir


.. note::
   If the :code:`--action` is :code:`move` instead of :code:`copy`, then after downloading, the file on wandb server will be deleted.

Similarly :code:`--action delete` can be used to delete files from wandb server.

.. code-block:: console

   $ wandb-utils \     # main command
   all-data --filters "{\"sweep\": {\"\$in\": [\"vg17h6fd\"]} }" \     # dataframe of runs with specific sweep
   filter-df -f run \                   # keep only the run column
   files -f "+ *.json" --destination wandb --action delete df        # delete all json files on wandb
