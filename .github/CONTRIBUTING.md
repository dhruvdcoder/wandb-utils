# Setup

1. In order to contribute you will need to clone/fork the repo and install the test requirements locally.

```
pip install -r core_requirements.txt
pip install -r test_requirements.txt
pip install -r doc_requirements.txt
```

# Workflow

1. Create and checkout new feature branch for your work.

1. Make changes, add a new command!

2. Add a documentation page for its usage in the `docs/` folder.

3. If possible add a test in `tests/` folder.

5. Run pre-commit and tests using `pre-commit run -v` and `pytest -v`

6. Git re-stage the files after fixing the errors and commit. When you commit, `pre-commit` will run once again but only on the changed files

6. Push to remote. Create a PR if your feature is completed.


## Code Styling

We use `flake8` and `black` for code formatting and `darglint` for checking doc-strings.
