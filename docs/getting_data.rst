Getting Data
=============

The `all-data` command can be used to get the logged data for your runs from wandb.

.. code-block:: console

   Usage: wandb-utils all-data [OPTIONS]

   Options:
     --filters DICT  Filter used while querying wandb for runs. It uses MongoDB
                     query syntax. See https://docs.wandb.ai/ref/python/public-
                     api/runs and https://github.com/wandb/client/blob/v0.10.31/w
                     andb/apis/public.py#L428 for how the query is used. See
                     https://docs.mongodb.com/manual/reference/operator/query/ to
                     learn about all the query operators in MongoDB query.
     --help          Show this message and exit.



Examples:
-------------

The following invocation will get the data for all the runs associated with any of the listed sweeps in `project_name`.
You can use `--filters` to pass any other query in MongoDB syntax
If you drop the `--filters`, flag it will get the data for all the runs.


.. code-block:: console

   $ wandb-utils \
   --entity username \
   --project project_name \
   all-data \
   --filters "{\"sweep\":{\"$in\":[ \"b3blcsq3\",\"1lt6xnar\",\"gybgwkl0\",\"bpgd2q0a\"]}}


However, to print the fetched data or to save it to file you will have to chain the print command


.. code-block:: console

   $ wandb-utils \
   --entity username \
   --project project_name \
   all-data \
   --filters "{\"sweep\":{\"$in\":[ \"b3blcsq3\",\"1lt6xnar\",\"gybgwkl0\",\"bpgd2q0a\"]}} \
   print -o runs.csv



Here is another example with a finer query.

.. code-block:: console

   $ wandb-utils \
   -e team \
   -p project_name \
   all-data \
   --filters "{\"sweep\": {\"\$nin\":[\"gfqkggbm\"]}, \"username\": {\"\$in\":[\"auser\"]}, \"created_at\":{\"\$gte\": \"2021-08-05 00:00:00\"}}" \
   print


At this point, I don't what database fields are exposed for querying through wandb API, so I just use trial and error to figure out what is available.
