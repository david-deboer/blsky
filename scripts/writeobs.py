#! /usr/bin/env python
from blsky_util import Observatories


obstab = Observatories()
obstab.table_get_meta()
obstab.table_make_header()

with open('satpos.obs', 'w') as fp:
    print(obstab.header_label, file=fp)
    print(obstab.header_unit, file=fp)
    for this_obs in obstab.include:
        row = obstab.table_make_row(this_obs)
        print(row, file=fp)
