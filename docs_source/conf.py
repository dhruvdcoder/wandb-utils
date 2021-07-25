# -*- coding: utf-8 -*-
#

import sys
import os

sys.path.insert(0, os.path.abspath('../'))

extensions = [
    'sphinx.ext.autoapi',
    'sphinx.ext.todo',
    'sphinx.ext.napoleon',
    'sphinx.ext.graphviz',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.githubpages',
    'm2r','aafigure.sphinxext'
]
source_suffix = ['.rst', '.md']
# source_suffix = '.rst'
master_doc = 'index'
project = "Weights and Biases utilities"
copyright = "2021, Dhruvesh Patel"
exclude_patterns = ['_build', '**/docs', '**/.docs']
pygments_style = 'sphinx'
html_theme = 'sphinx_rtd_theme'
autoclass_content = "class"
#html_logo = "images/UMass_IESL.png"

# API Generation
autoapi_dirs = ["../src/wandb_utils"]
autoapi_root = "."
autoapi_options = [
    "members",
    "inherited-members",
    "undoc-members",
    "show-inheritance",
    #"show-module-summary",
]
autoapi_add_toctree_entry = False
autoapi_keep_files = True

# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autoclass_content
autoclass_content = "both"

# keep raw ascii in all outputs because aafig interprets text differently producing weird
# svgs
aafig_format = dict(latex=None, html=None, text=None)
