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

    def get_header_info(self):
        self.h_info = {}
        for hdr in self.columns:
            self.h_info[hdr] = {}
            cin = self.label[hdr].split('|')
            self.h_info[hdr]['width'] = int(cin[0])
            self.h_info[hdr]['justify'] = cin[1].lower()
            self.h_info[hdr]['label'] = cin[2]
            try:
                self.h_info[hdr]['unit'] = cin[3]
            except IndexError:
                self.h_info[hdr]['unit'] = ' '

    def make_header_line(self, lna, lb, rb):
        if lna == 'label':
            header = "#Code \t"
            lb, rb = '', ''
        else:
            header = "#     \t"
            lb, rb = '[', ']'
        for hdr in self.columns:
            val = f"{lb}{self.h_info[hdr][lna]}{rb}"
            if lna == 'label':
                col = f"{val.ljust(self.h_info[hdr]['width'])}\t"
            else:
                col = f"{val.center(self.h_info[hdr]['width'])}\t"
            header += col
        return header.rstrip()

    def make_row(self, obs):
        this_line = obs.ljust(6) + '\t'
        for col in self.columns:
            if self.h_info[col]['justify'] == 'l':
                val = self.obs[obs][col].ljust(self.h_info[col]['width'])
            elif self.h_info[col]['justify'] == 'c':
                val = self.obs[obs][col].center(self.h_info[col]['width'])
            elif self.h_info[col]['justify'] == 'r':
                val = self.obs[obs][col].rjust(self.h_info[col]['width'])
            print(col, self.obs[obs][col], val)
            this_line += f"{val}\t"
        return this_line.rstrip()


obstab = ObsTable()
obstab.get_header_info()
header1 = obstab.make_header_line('label')
header2 = obstab.make_header_line('unit')

with open('satpos.obs', 'w') as fp:
    print(header1, file=fp)
    print(header2, file=fp)
    for this_obs in obstab.include:
        row = obstab.make_row(this_obs)
        print(row, file=fp)
