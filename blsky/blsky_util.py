import subprocess
import yaml
from math import modf, copysign, pow, fabs


def dms(deg, sfrac=2):
    f, d = modf(deg)
    f, m = modf(abs(f) * 60)
    f, s = modf(f * 60)
    sf = str(pow(10, sfrac) * f).split('.')[0]
    if len(sf) < sfrac:
        sf = '0' * (sfrac - len(sf)) + sf
    return f"{int(d)}:{int(m):02d}:{int(s):02d}.{sf}"


def deg(dms):
    if isinstance(dms, str):
        dms = dms.split(':')
    dms = [float(x) for x in dms]
    sum = 0.0
    for i in range(len(dms)):
        sum += fabs(dms[i]) / pow(60.0, i)
    return copysign(1.0, dms[0]) * sum


class Observatories:
    def __init__(self, obsfile='satpos_obs.yaml', sec_precision=2):
        with open(obsfile, 'r') as fp:
            self.obs = yaml.load(fp, Loader=yaml.Loader)
        self.proc_dict()

    def proc_dict(self):
        """
        Strip out meta data and fix lat/lon and lat_dms/lon_dms
        """
        cull_keys = []
        extra_fields = {}
        for obs, entry in self.obs.items():
            if obs.startswith('__'):
                if obs.strip('__') in ['columns', 'include', 'exclude']:
                    entry = entry.split(',')
                setattr(self, obs.strip('__'), entry)
                cull_keys.append(obs)
            else:
                extra_fields[obs] = {}
                for key, val in entry.items():
                    if key in ['lat', 'lon']:
                        if ':' in str(val):
                            self.obs[obs][key] = deg(val)
                        else:
                            self.obs[obs][key] = float(val)
                        extra_fields[obs][key + '_dms'] = dms(self.obs[obs][key])
                    elif key in ['horizon', 'alt', 'tz']:
                        self.obs[obs][key] = float(val)
        for obs in extra_fields:
            self.obs[obs]['lat_dms'] = extra_fields[obs]['lat_dms']
            self.obs[obs]['lon_dms'] = extra_fields[obs]['lon_dms']
        for key in cull_keys:
            del(self.obs[key])
        if self.include[0].lower() == 'all':
            self.include = sorted(self.obs.keys())
        for excl in self.exclude:
            if excl in self.include:
                self.include.remove(excl)

    def table_get_meta(self):
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

    def table_make_header(self):
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

    def table_make_row(self, obs):
        this_line = obs.ljust(6) + '\t'
        for col in self.columns:
            entry = str(self.obs[obs][col]).replace(' ', '_')
            if self.info[col]['justify'] == 'l':
                val = entry.ljust(self.info[col]['width'])
            elif self.info[col]['justify'] == 'c':
                val = entry.center(self.info[col]['width'])
            elif self.info[col]['justify'] == 'r':
                entry = entry + '  '
                val = entry.rjust(self.info[col]['width'])
            this_line += f"{val}\t"
        return this_line.rstrip()


def git_commit_tle(commit_path):
    """
    Not used (see beast_tle_update.sh instead)
    """
    cmd = f"git -C {commit_path} commit -am 'updating csv to repo.'"
    subprocess.call(cmd, shell=True)
    cmd = f"git -C {commit_path} push origin main"
    subprocess.call(cmd, shell=True)


def find_tle_commit(this_date=None):
    tcommit = {}
    for line in subprocess.check_output(['git', 'log']).decode().split('\n'):
        if line.startswith('commit'):
            this_commit = line.split()[1]
            tcommit[this_commit] = {}
        elif line.startswith('    '):
            tcommit[this_commit]['msg'] = line.strip()
        elif len(line):
            key = line.split(':')[0]
            msg = ':'.join(line.split(':')[1:])
            tcommit[this_commit][key] = msg.strip()
    return tcommit
