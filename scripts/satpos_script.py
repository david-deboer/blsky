#! /usr/bin/env python
from blsky import satcensus
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('tlefile', help="Name of tle file for which to generate satpos script.",
                default='active')
ap.add_argument('cfgfile', help="Name of config file for default tle path.",
                default='satpos_cfg.yaml')
ap.add_argument('-n', '--no_config_file', help="Flag to not include path from config.",
                action='store_true')
args = ap.parse_args()

if args.no_config_file:
    args.cfgfile = None

satcensus.satpos_script(args.tlefile, cfgfile=args.cfgfile)
