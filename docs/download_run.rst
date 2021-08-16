Downloading files for runs from wandb
================================

Use `files` command to download run files either for a single run or a bunch of runs through chaining.

Downloading files for a single run
----------------------------------

.. code-block:: console

   $ wandb-utils \
   files \
   -f "+ *log*|- *output*" \
   --base-path tests/commands/assets \
   --destination local \
   --action move \
   --overwrite \
   yn7uvkia
