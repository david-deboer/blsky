#! /usr/bin/env python
from os import path, getcwd
import shutil


if getcwd().endswith('blsky'):
    shutil.copy('satpos/satpos', path.dirname(__file__))
else:
    print("Must be in blsky directory.")

print("Run satpos in a directory containing satpos.obs and satpos.cfg.")
