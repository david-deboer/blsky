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


def generate_complete_set(epoch=None, path='tle', fmname='master.dat'):
    """
    Goes through all tle files to find unique satellites and produce a completeset.
    [N.B. should use most recent epoch -- currently doesn't check that.]
    """
    import os.path as op
    satellites = {}
    sats_by_file = {}
    total_count = 0
    flistname = op.join(path, fmname)
    with open(flistname, 'r') as fp:
        for line in fp:
            fname = op.join(path, f"{line.strip().split(':')[0]}")
            sats_by_file[fname] = []
            with open(fname, 'r') as fptle:
                for tleline in fptle:
                    data = tleline.split()
                    if not len(data):
                        continue
                    if data[0] not in ['1', '2']:
                        scname = tleline.strip()
                        line0 = tleline.strip('\n')
                    elif data[0] == '1':
                        line1 = tleline.strip('\n')
                        this_epoch = float(line1[3])
                    elif data[0] == '2':
                        line2 = tleline.strip('\n')
                        key = data[1]
                        total_count += 1
                        satellites.setdefault(key, {'scname': scname, 'files': [], 'epoch': epoch})
                        if abs(this_epoch-epoch) <= abs(this_epoch-satellites[key]['epoch']):
                            satellites[key]['line0'] = line0
                            satellites[key]['line1'] = line1
                            satellites[key]['line2'] = line2
                            satellites[key]['epoch'] = this_epoch
                        satellites[key]['files'].append(fname)
    satlist = list(satellites.keys())

    print("Total satellites listed: {}".format(total_count))
    print("Total unique satellites:  {}".format(len(satlist)))

    # Still do, even though aren't using
    for i in range(len(satlist)):
        this_sat = satlist.pop()
        for fname in sats_by_file.keys():
            if fname in satellites[this_sat]['files']:
                satdes = '{}:{}'.format(this_sat, satellites[this_sat]['scname'])
                sats_by_file[fname].append(satdes)
                break
    with open('completeset.tle', 'w') as fp:
        for this_sat in satellites.keys():
            print(satellites[this_sat]['line0'], file=fp)
            print(satellites[this_sat]['line1'], file=fp)
            print(satellites[this_sat]['line2'], file=fp)
