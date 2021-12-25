import subprocess
import yaml


class Observatories:
    def __init__(self, obsfile='satpos_obs.yaml'):
        with open('satpos_obs.yaml', 'r') as fp:
            self.obs = yaml.load(fp, Loader=yaml.Loader)

    def table_get_meta(self):
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
            if self.info[col]['justify'] == 'l':
                val = self.obs[obs][col].ljust(self.info[col]['width'])
            elif self.info[col]['justify'] == 'c':
                val = self.obs[obs][col].center(self.info[col]['width'])
            elif self.info[col]['justify'] == 'r':
                val = self.obs[obs][col].rjust(self.info[col]['width'])
            this_line += f"{val.replace(' ', '_')}\t"
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
