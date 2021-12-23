#! /usr/bin/env python
# -*- mode: python; coding: utf-8 -*-
# Copyright 2021 David DeBoer
# Licensed under the 2-clause BSD license.

from setuptools import setup
import glob

setup_args = {
    'name': "blsky",
    'description': "various routines for observing etc",
    'license': "BSD",
    'author': "David DeBoer",
    'author_email': "ddeboer@berkeley.edu",
    'version': '0.1',
    'scripts': glob.glob('scripts/*'),
    'packages': ['blsky'],
    # 'package_data': {"blsky": ["data/*"]}
}

if __name__ == '__main__':
    setup(**setup_args)
