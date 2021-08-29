from setuptools import setup, find_packages
import os

PATH_ROOT = os.path.dirname(__file__)
with open("README.md", "r") as fh:
    long_description = fh.read()

VERSION = {}  # type: ignore
with open("src/wandb_utils/version.py", "r") as version_file:
    exec(version_file.read(), VERSION)


def load_requirements(path_dir=PATH_ROOT, comment_char="#"):
    with open(os.path.join(path_dir, "core_requirements.txt"), "r") as file:
        lines = [ln.strip() for ln in file.readlines()]
    reqs = []

    for ln in lines:
        # filer all comments

        if comment_char in ln:
            ln = ln[: ln.index(comment_char)]

        if ln:  # if requirement is not empty
            reqs.append(ln)

    return reqs


install_requires = load_requirements()

setup(
    name="wandb_utils",
    version=VERSION["VERSION"],
    author="Dhruvesh Patel",
    author_email="1793dnp@gmail.com",
    description="Utitlity functions and scripts to work with Weights \& Biases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://www.dhruveshp.com/wandb-utils",
    project_urls={
        "Documentation": "https://wandb-utils.readthedocs.io",
        "Source Code": "https://github.com/dhruvdcoder/wandb-utils",
    },
    packages=find_packages(
        where="src",
        exclude=[
            "*.tests",
            "*.tests.*",
            "tests.*",
            "tests",
            "examples",
            "wandb",
        ],
    ),
    package_dir={"": "src"},
    install_requires=install_requires,
    keywords=[
        "AI",
        "ML",
        "Optimization",
        "Machine Learning",
        "Deep Learning",
    ],
    entry_points={
        "console_scripts": [
            "wandb-utils=wandb_utils.__main__:wandb_utils",
            "wandb-slurm=wandb_utils.__main__:wandb_slurm",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
    ],
    python_requires=">=3.7",
)
