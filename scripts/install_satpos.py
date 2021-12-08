#! /usr/bin/env python
from os import path
import shutil


print("Check that cwd endswith blsky")
shutil.copy('blsky/satpos/satpos', path.dirname(__file__))
shutil.copy('blsky/satpos.obs', path.dirname(__file__))
shutil.copy('blsky/satpos.cfg', path.dirname(__file__))
