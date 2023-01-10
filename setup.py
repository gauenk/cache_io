#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import print_function
from setuptools import setup, find_packages
# from distutils.core import setup
import os
import stat
import shutil
import platform
import sys
import site
import glob


# -- file paths --
long_description="""Cache IO: A simple caching system for data related to deep learning projects"""
setup(
    name='cache_io',
    version='1.0.0',
    description='Caching large data results',
    long_description=long_description,
    url='https://github.com/gauenk/hids',
    author='Kent Gauen',
    author_email='gauenk@purdue.edu',
    license='MIT',
    keywords='caching, results, big data ',
    install_requires=['easydict'],
    package_dir={"": "lib"},
    packages=find_packages(""),
    entry_points = {
        'console_scripts': ['lsc=cache_io.lsc:main',
                            'sbatch_py=cache_io.slurm.cmdline:main'],
    }
)
