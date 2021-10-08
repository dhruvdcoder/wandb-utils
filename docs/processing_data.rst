Processing data
===============


You can chain `filter-df` command after the `all-data` command or `from-file` command to apply various finds of processing to the data obtained through your query.
For example, the following invocation will give you the data corresponding to the best runs (using metric best_validation_fixed_f1 as higher the better) in sweeps `5pfpcetn` and `abcd12345`.

.. code-block:: console

   $ wandb-utils \
   -e username_or_team \
   -p project_name \
   all-data \
   --filters "{\"sweep\":{\"\$in\":[\"5pfpcetn\", \"abcd12345\"]}}" \
   filter-df -f sweep_name -f sweep -f run -f path -f test_fixed_f1 -f best_validation_fixed_f1 -i path \
   --query "df.sort_values('best_validation_fixed_f1', ascending=False).drop_duplicates(['sweep_name'])" \
   print
