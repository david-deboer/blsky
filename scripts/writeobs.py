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
        for excl in self.exclude:
            if excl in self.include:
                self.include.remove(excl)

    def get_table_info(self):
        self.info = {}
        for hdr in self.columns:
            self.info[hdr] = {}
            cin = self.label[hdr].split('|')
            self.info[hdr]['width'] = int(cin[0])
            self.info[hdr]['justify'] = cin[1].lower()
            self.info[hdr]['label'] = cin[2]
            try:
                self.info[hdr]['unit'] = cin[3]
            except IndexError:
                self.info[hdr]['unit'] = ' '

    def make_header_lines(self):
        for lna in ['label', 'unit']:
            if lna == 'label':
                header, lb, rb = "#Code \t", '', ''
            else:
                header, lb, rb = "#     \t", '[', ']'
            for hdr in self.columns:
                if len(self.info[hdr][lna].strip()):
                    val = f"{lb}{self.info[hdr][lna]}{rb}"
                else:
                    val = ' '
                if lna == 'label':
                    col = f"{val.ljust(self.info[hdr]['width'])}\t"
                else:
                    col = f"{val.center(self.info[hdr]['width'])}\t"
                header += col
            setattr(self, f"header_{lna}", header.rstrip())

    def make_row(self, obs):
        this_line = obs.ljust(6) + '\t'
        for col in self.columns:
            if self.info[col]['justify'] == 'l':
                val = self.obs[obs][col].ljust(self.info[col]['width'])
            elif self.info[col]['justify'] == 'c':
                val = self.obs[obs][col].center(self.info[col]['width'])
            elif self.info[col]['justify'] == 'r':
                val = self.obs[obs][col].rjust(self.info[col]['width'])
            this_line += f"{val.replace(' ', '_')}\t"
        return this_line.rstrip()


obstab = ObsTable()
obstab.get_table_info()
obstab.make_header_lines()

with open('satpos.obs', 'w') as fp:
    print(obstab.header_label, file=fp)
    print(obstab.header_unit, file=fp)
    for this_obs in obstab.include:
        row = obstab.make_row(this_obs)
        print(row, file=fp)
