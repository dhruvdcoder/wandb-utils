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


You can also do fairly complex things using `--pd-eval` that uses `pandas.eval` function.
For instance following command performs 4 processing steps

1. `--pd-eval "test_CMAP=rmax(df.test_MAP_max_n, df.test_MAP_min_n)"` creates a new column
named `test_MAP` by taking the max of two existing columns.

2. The second and third steps create two new columns `_dataset` and `_model` by
extracting strings from the `tags` column.

3. The last step `--pd-eval "df.groupby(['_model', '_dataset'], as_index=False).mean()"`
performs grouby followed by taking the mean of groups.

.. code-block:: console

    $ wandb-utils -e USERNAME -p PROJECT \
    all-data \
    filter-df --pd-eval "test_CMAP=rmax(df.test_MAP_max_n, df.test_MAP_min_n)" \
    filter-df --pd-eval "_model=df.tags.str.extract(r'model@([^\|]+)',expand=False)" \
    filter-df --pd-eval "_dataset=df.tags.str.extract(r'dataset@([^\|]+)',expand=False)" \
    filter-df --pd-eval "df.groupby(['_model', '_dataset'], as_index=False).mean()" \
    filter-df -f test_MAP -f test_CMAP -f test_constraint_violation -f _model -f _dataset \
    print


There even more general and powerful ways, `--python-exec` and `--python-eval`, to process the dataframe using python's
native `exec()` and `eval()` functions, respectively, that allow executing arbitrary python code.
