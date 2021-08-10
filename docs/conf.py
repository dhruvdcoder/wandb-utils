# -*- coding: utf-8 -*-
#

import sys
import os

sys.path.insert(0, os.path.abspath("../src"))

extensions = [
    "autoapi.extension",
    "sphinx.ext.todo",
    "sphinx.ext.napoleon",
    "sphinx.ext.graphviz",
    "sphinx.ext.inheritance_diagram",
    "sphinx_click",
    "m2r",
    "aafigure.sphinxext",
]
source_suffix = [".rst", ".md"]
# source_suffix = '.rst'
master_doc = "index"
project = "Weights and Biases utilities"
copyright = "2021, Dhruvesh Patel"
exclude_patterns = ["_build", "**/docs", "**/.docs"]
html_theme = 'alabaster'
autoclass_content = "class"
# html_logo = "images/UMass_IESL.png"

html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'relations.html',
        'searchbox.html',
    ]
}

html_theme_options = {
    "description": "Utitlity functions and scripts to work with Weights \& Biases",
    "github_user": "dhruvdcoder",
    "github_repo": "wandb-utils",
    "fixed_sidebar": True,
}

# API Generation
autoapi_dirs = ["../src/wandb_utils"]
autoapi_options = [
    "members",
    "inherited-members",
    "undoc-members",
    "show-inheritance",
    # "show-module-summary",
]
autoapi_add_toctree_entry = True
autoapi_keep_files = False
autoapi_template_dir = "autoapi_templates"

# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autoclass_content
autoclass_content = "both"

# keep raw ascii in all outputs because aafig interprets text differently producing weird
# svgs
aafig_format = dict(latex=None, html=None, text=None)
