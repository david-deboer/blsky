#! /usr/bin/env python
import yaml


class ObsTable:
    def __init__(self, obsfile='satpos_obs.yaml'):
        with open('satpos_obs.yaml', 'r') as fp:
            self.obs = yaml.load(fp, Loader=yaml.Loader)

        cull_keys = []
        for key, val in self.obs.items():
            if key.startswith('__'):
                if key.strip('__') in ['columns', 'include', 'exclude']:
                    val = val.split(',')
                setattr(self, key.strip('__'), val)
                cull_keys.append(key)
        for key in cull_keys:
            del(self.obs[key])
        if self.include[0].lower() == 'all':
            self.include = sorted(self.obs.keys())
        if self.exclude[0].lower() == 'none':
            self.exclude = []

    def get_header_info(self):
        self.h_info = {}
        for hdr in self.columns:
            self.h_info[hdr] = {}
            cin = self.label[hdr].split('|')
            self.h_info[hdr]['w'] = int(cin[0])
            self.h_info[hdr]['j'] = cin[1].lower()
            self.h_info[hdr]['c'] = [x for x in cin[2:]]

    def make_header_line(self, lno, lb, rb):
        if lno == 1:
            header = "#Code \t"
        else:
            header = "#     \t"
        for hdr in self.columns:
            try:
                val = f"{lb}{self.h_info[hdr]['c'][lno - 1]}{rb}"
            except IndexError:
                val = " "
            if lno == 1:
                col = f"{val.ljust(self.h_info[hdr]['w'])}\t"
            else:
                col = f"{val.center(self.h_info[hdr]['w'])}\t"
            header += col
        return header.rstrip()

    def make_row(self, obs):
        this_line = obs.ljust(6) + '\t'
        for col in self.columns:
            if self.h_info[col]['j'] == 'l':
                val = self.obs[obs][col].ljust(self.h_info[col]['w'])
            elif self.h_info[col]['j'] == 'c':
                val = self.obs[obs][col].center(self.h_info[col]['w'])
            elif self.h_info[col]['j'] == 'r':
                val = self.obs[obs][col].rjust(self.h_info[col]['w'])
            print(col, self.obs[obs][col], val)
            this_line += f"{val}\t"
        return this_line.rstrip()


obstab = ObsTable()
obstab.get_header_info()
header1 = obstab.make_header_line(1, '', '')
header2 = obstab.make_header_line(2, '[', ']')

with open('satpos.obs', 'w') as fp:
    print(header1, file=fp)
    print(header2, file=fp)
    for this_obs in obstab.include:
        if this_obs in obstab.exclude:
            continue
        row = obstab.make_row(this_obs)
        print(row, file=fp)
