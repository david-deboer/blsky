#! /usr/bin/env python
from blsky.blsky_util import Observatories
import yaml


with open('satpos_cfg.yaml', 'r') as fp:
    cfg = yaml.load(fp, Loader=yaml.Loader)


obstab = Observatories(obsfile=cfg['obs_yaml_to_use'])
obstab.table_get_meta()
obstab.table_make_header()

with open(cfg['obs_file_to_use'], 'w') as fp:
    print(obstab.header_label, file=fp)
    print(obstab.header_unit, file=fp)
    for this_obs in obstab.include:
        row = obstab.table_make_row(this_obs)
        print(row, file=fp)
