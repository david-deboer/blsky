#! /usr/bin/env python
from blsky import satcensus
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('satfile', help="Name of script file for which to count.",
                default='satpos_active.sh', nargs='?')
args = ap.parse_args()


satcensus.find_viewable(args.satfile)
