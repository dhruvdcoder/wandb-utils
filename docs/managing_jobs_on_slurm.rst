Manging wandb agents on a slurm cluster
====================================

The `wandb-slurm` top-level command can be used to perform various actions on slurm like submitting a job that starts wandb sweep agents, stop existing agents for a sweep, etc.

Starting agents for a sweep
----------------------------------


.. code-block:: console

   Usage: wandb-slurm start-agents [OPTIONS]

   Options:
     --inform-before-time INTEGER  How many seconds before should the agents be
                                   informed before shutting them down?
     --signals LIST                Signals to handle seperated buy '|' for
                                   example 'TERM|INT|CONT'  (default:
                                   'TERM|INT').
     --mem TEXT                    #SBATCH --mem=
     --run-count INTEGER           Runs per agent, ie `wandb agent --count <run-
                                   count> sweep_id`. (default: unlimited).
     --cpus-per-task INTEGER       #SBATCH --cpus-per-task=
     --partition TEXT              #SBATCH --partition=
     --num-gpus INTEGER            #SBATCH --gres=gpu:
     --num-agents INTEGER
     --edit / --no-edit            Edit final sbatch.sh
     --chain / --no-chain          Insert dependencies between jobs by starting
                                   num-agents serially.
     --dependency TEXT             Dependency types:

                                       after:jobid[:jobid...]      job can begin
                                       after the specified jobs have started

                                       afterany:jobid[:jobid...]   job can begin
                                       after the specified jobs have terminated

                                       afternotok:jobid[:jobid...] job can begin
                                       after the specified jobs have failed

                                       afterok:jobid[:jobid...]    job can begin
                                       after the specified jobs have run to
                                       completion with an exit code of zero (see
                                       the user guide for caveats).

                                       singleton   jobs can begin execution after
                                       all previously launched jobs with the same
                                       name and user have ended. This is useful
                                       to collate results of a swarm or to send a
                                       notification at the end of a swarm.

                                           See `sbatch <https://slurm.schedmd.com
                                           /sbatch.html>`_ doc for details.
     --verbatim-args LIST          arguments in kw=value seperated by | form to
                                   drop verbatim in sbatch.sh. For example
                                   'exclude=node003,node004|account=abc
     --dry-run                     Only create files and show command but do not
                                   submit jobs.
     --confirm                     Whether to ask for confirmation before
                                   submitting.
     --help                        Show this message and exit.




Following is an example invocation:

.. code-block:: console

   $ wandb-slurm \
   --entity wandb_team_or_username \
   --project wandb_project_name \
   --sweep 216pxkwa \
   start-agents \
   --mem 10GB \
   --run-count 10 \
   --cpus-per-task 6 \
   --partition titanx-long \
   --num-gpus 1 \
   --num-agents 2 \
   --verbatim-args "exclude=node030,node095,node029"
