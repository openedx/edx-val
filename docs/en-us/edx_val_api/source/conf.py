# -*- coding: utf-8 -*-
#


import sys, os
from path import path

# on_rtd is whether we are on readthedocs.org, this line of code grabbed from docs.readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

sys.path.append(os.path.abspath('../../../'))
sys.path.append(os.path.abspath('../../'))

#from docs.shared.conf import *

root = path('../../../..').abspath()
sys.path.insert(0, root)
sys.path.append(root / "edxval/")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "edxval.settings")

master_doc = 'index'

extensions = [
    'sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.intersphinx',
    'sphinx.ext.todo', 'sphinx.ext.coverage', 'sphinx.ext.pngmath',
    'sphinx.ext.mathjax', 'sphinx.ext.viewcode', 'sphinxcontrib.napoleon']

project = u'edX VAL API Guide'
copyright = u'2014, edX'

# The short X.Y version.
version = ''
# The full version, including alpha/beta/rc tags.
release = ''

#Added to turn off smart quotes so users can copy JSON values without problems.
html_use_smartypants = False