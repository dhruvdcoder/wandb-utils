#!/bin/bash
echo "=======Creating virtual env========="
virtualenv -p `which python3` .venv_<<[.custom.project.package_name]>>
source .venv_<<[.custom.project.package_name]>>/bin/activate

echo "=======Install test requirements======="
pip install test_requirements.txt

echo "=======Install doc requirements======="
pip install doc_requirements.txt

echo "=======Install core requirements======"
pip install core_requirements.txt
