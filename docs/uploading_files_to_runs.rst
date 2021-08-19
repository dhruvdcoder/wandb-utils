Uploading files for runs to wandb
================================

Use `files` command to upload files to existing runs.

Uploading files for a single run
----------------------------------

.. code-block:: console

   $ wandb-utils \
   files \
   -f "+ tests/commands/assets/log*.txt|- tests/commands/assets/*not*" \
   --base-path tests/commands/assets \
   --destination wandb \
   --action copy \
   yn7uvkia
