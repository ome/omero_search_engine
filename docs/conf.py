# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

import datetime
import os
import sys
path=os.path.abspath('..')
sys.path.insert(0, path)
sys.path.append(os.path.abspath(os.path.join(path, '..')))


project = 'OMERO Search Engine'
# General information about the project.
author = u'The Open Microscopy Environment'
copyright = u'2022-%d, ' % datetime.datetime.now().year + author


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.extlinks']

autodoc_mock_imports=[]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'config']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'default'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
#html_static_path = ['_static']

# Variables used to define other extlinks
github_root = 'https://github.com/'
ome_github_root = github_root + '/ome/'

extlinks = {
  # GitHub links
    'omero_search_engine': (ome_github_root + 'omero_search_engine/blob/main/' + '%s', None),
}

rst_epilog = """
.. _ElasticSearch: https://www.elastic.co/

 """
 