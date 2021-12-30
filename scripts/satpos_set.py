#! /usr/bin/env python
from blsky import satcensus
import argparse
from blsky.blsky_util import Observatories
import yaml

ap = argparse.ArgumentParser()
ap.add_argument('tlefile', help="Name of tle file for which to generate satpos script.",
                default='active', nargs='?')
ap.add_argument('--cfgfile', help="Name of config file.", default='satpos_cfg.yaml')
ap.add_argument('-n', '--no_config_path', help="Flag to not include tle path from config.",
                action='store_true')
ap.add_argument('-o', '--obs_only', help="Flag to skip satpos script and only update obs",
                action='store_true')
ap.add_argument('-s', '--script_only', help="Flag to skip obs update and only gen satpos script",
                action='store_true')
args = ap.parse_args()

try:
    with open(args.cfgfile, 'r') as fp:
        cfg = yaml.load(fp, Loader=yaml.Loader)
except FileNotFoundError:
    cfg = {'obs_yaml_to_use': '', 'obs_file_to_use': '', 'path_to_tle_files': None}
if args.no_config_path:
    cfg['path_to_tle_files'] = None

# Write script
if not args.obs_only:
    satcensus.satpos_script(args.tlefile, path=cfg['path_to_tle_files'])

# Update observatories
if not args.script_only:
    obstab = Observatories(obsfile=cfg['obs_yaml_to_use'])
    obstab.table_get_meta()
    obstab.table_make_header()

    with open(cfg['obs_file_to_use'], 'w') as fp:
        print(obstab.header_label, file=fp)
        print(obstab.header_unit, file=fp)
        for this_obs in obstab.include:
            row = obstab.table_make_row(this_obs)
            print(row, file=fp)
