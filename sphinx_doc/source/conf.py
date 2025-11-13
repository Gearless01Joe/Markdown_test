# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# 添加 src 目录到 Python 路径，使 Sphinx 能够导入模块
sys.path.insert(0, os.path.abspath('../../src'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Markdown'
copyright = '2025, Liu zidu'
author = 'Liu zidu'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',      # 自动提取文档字符串
    'sphinx.ext.napoleon',     # 支持 Google/NumPy 风格的 docstring
    'sphinx.ext.viewcode',     # 添加源代码链接
]

templates_path = ['_templates']
exclude_patterns = []

language = 'zh_CN'  # 改为中文，或使用 'en' 表示英文

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'bizstyle'
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------

# Napoleon 设置（用于解析 Google/NumPy 风格的 docstring）
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Autodoc 设置
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}
autodoc_mock_imports = ['application.settings']  # 如果导入失败，可以在这里添加需要模拟的模块
