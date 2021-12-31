import subprocess


def _get_lno(s):
    try:
        lno = int(s)
    except ValueError:
        lno = 0
    if lno not in [0, 1, 2]:
        lno = 0
    return lno


def read_tle_file(filename):
    lno = ['0', '0', '0']
    sc = {}
    with open(filename, 'r') as ttfp:
        for line in ttfp:
            data = line.split()
            if len(data) < 2:
                continue
            this_lno = _get_lno(data[0])
            lno[this_lno] = line.strip()
            if this_lno == 1:
                this_epoch = int(float(data[3]) * 100.0)
            elif this_lno == 2:
                this_sc = int(data[1])
                if this_sc in sc:
                    sc[this_sc][this_epoch] = [lno[0], lno[1], lno[2]]
                    sc[this_sc]['epochs'].append(this_epoch)
                else:
                    sc[this_sc] = {this_epoch: [lno[0], lno[1], lno[2]]}
                    sc[this_sc]['epochs'] = [this_epoch]
                    lno = ['0', '0', '0']
    return sc


def agg_tle(tlefiles, epoch, outfile='agg.tle', cull_to=None):
    """
    Aggregates a set of tle files, collapsing multiple epochs to nearest supplied value.

    parameters
    ==========
    tlefiles : list
      List of tle filenames to aggregate.
    epoch : float, int
      Epoch to match nearest.
    outfile : str
      Name of output file.
    cull_to : list or None
      If not null, will only include satellites with these norad cat ids
    """
    if '*' in tlefiles:
        from glob import glob
        tlefiles = glob(tlefiles)
    sc = {}
    for this_file in tlefiles:
        print(this_file)
        sc.update(read_tle_file(this_file))
    sc_tot = len(sc.keys())
    print(f"{sc_tot} satellites")
    import numpy as np
    print(f"Matching for epoch {epoch}")
    culled = 0
    with open(outfile, 'w') as fp:
        for norad, ep in sc.items():
            if cull_to is not None and norad not in cull_to:
                culled += 1
                continue
            minep = np.abs(np.array(ep['epochs']) - epoch).argmin()
            usepoch = ep['epochs'][minep]
            for i in range(3):
                print(ep[usepoch][i], file=fp)
    print(f"Writing {sc_tot-culled} to {outfile}")


def match_epoch(mepoch, dtime=None):
    """
    Return a epoch float to match (used in agg_tle above.)

    mepoch is expressed as (yyddd.ddd * 100.0)

    Parameters
    ==========
    mepoch : *
      Input match_epoch value.  If floatable, returns that else computes via dtime
    dtime : None or datetime
      Match_epoch in datetime (if mepoch is not floatable)
    """
    try:
        return float(mepoch)
    except ValueError:
        if dtime is None:
            print("Need to include a datetime to calculate.")
    mes = f"{dtime.strftime('%y')}{dtime.strftime('%j')}"
    try:
        frac = (dtime.hour + dtime.minute / 60.0) / 24.0
    except AttributeError:
        frac = 0.0
    return (float(mes) + frac) * 100.0


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
