"""Miscellaneous collection of modules to count satellite/etc"""
from argparse import Namespace
from . import sattrack
import os.path as op
from os import chmod
import yaml


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


def filter_drift(f=982e6, rng=[0.025, 0.05], absvalue=True,
                 trackfilelist='viewable.csv', path='output', addtag='out'):
    """
    Uses the satellites written in find_viewable below and
    filters on drift range from the .out files.

    Writes outsats.csv with the list and returns a dict of the relevant portion
    of track.
    """
    outsats = open('outsats.csv', 'w')
    drifts = {}
    with open(trackfilelist, 'r') as satslist:
        loc = satslist.readline().strip()
        print("Location: ", loc)
        for line in satslist:
            data = line.strip().split(',')
            if data[0] == 'file':
                continue
            fname = data[0]
            if addtag is not None:
                fname = f"{fname}.{addtag}"
            fname = op.join(path, fname)
            s = sattrack.Track(fname)
            s.view(loc)
            s.rates(f)
            for i, drift in enumerate(s.vis(s.drift)):
                chkdrift = drift
                if absvalue:
                    chkdrift = abs(drift)
                if s.el[i] > 0.0 and chkdrift > rng[0] and chkdrift < rng[1]:
                    drifts.setdefault(s.satnum, Namespace(t=[], drift=[], el=[], period=[]))
                    drifts[s.satnum].t.append(s.dtime[i])
                    drifts[s.satnum].drift.append(drift)
                    drifts[s.satnum].el.append(s.el[i])
                    drifts[s.satnum].period.append(s.period)
                    print(f"{fname},{s.satnum},{s.since[i]},{drift},{s.x[i]},{s.y[i]},{s.z[i]},"
                          f"{s.el[i]},{s.period}", file=outsats)
    outsats.close()
    return drifts


def showdist():
    """
    Reads in viewable.csv and notviewable.csv
    """
    import numpy as np
    view = Namespace(num=[], period=[], elmin=[], elmax=[])
    notv = Namespace(num=[], period=[], elmin=[], elmax=[])
    with open('viewable.csv', 'r') as fp:
        loc = fp.readline().strip('#').strip()
        print("Location ", loc)
        for line in fp:
            if line.startswith('#'):
                continue
            data = line.split(',')
            view.num.append(int(data[2]))
            view.period.append(float(data[4]))
            view.elmin.append(float(data[-2]))
            view.elmax.append(float(data[-1]))
    view.period = np.array(view.period)
    view.elmin = np.array(view.elmin)
    view.elmax = np.array(view.elmax)

    with open('notviewable.csv', 'r') as fp:
        for line in fp:
            if line.startswith('#'):
                continue
            data = line.split(',')
            notv.num.append(int(data[2]))
            notv.period.append(float(data[4]))
            notv.elmin.append(float(data[-2]))
            notv.elmax.append(float(data[-1]))
    notv.period = np.array(notv.period)
    notv.elmin = np.array(notv.elmin)
    notv.elmax = np.array(notv.elmax)

    return view, notv


def check_location(previous_loc, fullfname):
    with open(fullfname, 'r') as fp:
        for line in fp:
            if line.startswith('#observer:'):
                return previous_loc, line.split(':')[-1].strip()


def find_viewable(satlist='satpos_active.sh', path='',
                  rewrite_file=False, verbose=False):
    """
    This writes viewable.csv and notviewable.csv of those tracks for loc.
    """
    viewable = open('viewable.csv', 'w')
    notviewable = open('notviewable.csv', 'w')
    hdrstr = "file,scname,satnum,orbit,period,sublon,elmin,elmax"
    count = Namespace(leo=0, meo=0, geo=0, deep=0, other=0, viewable=0, notviewable=0)
    loc = None
    with open(satlist, 'r') as fp:
        i = 0
        for line in fp:
            data = line.split()
            if len(data) != 3 or data[0] != 'satpos':
                continue
            fname = f"sp_{data[1]}{int(data[2]):07d}.out"
            fullfname = op.join(path, fname)
            previous_loc, loc = check_location(loc, fullfname)
            if previous_loc is None:
                print(f"#{loc}\n#{hdrstr}", file=viewable)
                print(f"#{loc}\n#{hdrstr}", file=notviewable)
            elif previous_loc != loc:
                raise RuntimeError(f"Locations don't agree:  {previous_loc} vs {loc}")
            if verbose:
                print(f"\rReading {fullfname}", end='')
            try:
                s = sattrack.Track(fullfname)
                s.view(loc)
            except:  # noqa
                print(" Warning - Track error.")
                continue
            if rewrite_file:
                s.rewrite_file(overwrite=True)
            if s.period > 1500.0:
                count.deep += 1
                orbit = 'deep'
            elif s.period < 1450.0 and s.period > 1420.0:
                count.geo += 1
                orbit = 'geo'
            elif s.period < 1000.0 and s.period > 500.0:
                count.meo += 1
                orbit = 'meo'
            elif s.period < 200.0:
                count.leo += 1
                orbit = 'leo'
            else:
                count.other += 1
                orbit = 'other'
            try:
                elmin = s.el.min().value
                elmax = s.el.max().value
            except (ValueError, AttributeError):
                elmin = '!'
                elmax = '!'
            fnp = fname.split('.')[0]
            pline = f"{fnp},{s.scname},{s.satnum},{orbit},{s.period},{s.sublon},{elmin},{elmax}"
            if s.viewable:
                print(pline, file=viewable)
                count.viewable += 1
            else:
                print(pline, file=notviewable)
                count.notviewable += 1
            i += 1
    viewable.close()
    notviewable.close()

    print(f"\nLEO: {count.leo}")
    print(f"MEO: {count.meo}")
    print(f"GEO: {count.geo}")
    print(f"DEEP: {count.deep}")
    print(f"OTHER: {count.other}")
    print(f"VIEWABLE: {count.viewable}")
    print(f"NOTVIEWABLE: {count.notviewable}")

    print("Wrote viewable.csv, notviewable.csv")


def satpos_script(tlefile, cfgfile=None):
    """
    Write a bash script to check entry numbers within a tle file repetitiously via satpos.
    """
    scfg = {}
    if not tlefile.endswith('.tle'):
        tlefile = f"{tlefile}.tle"

    if cfgfile is not None:
        with open(cfgfile, 'r') as fp:
            scfg = yaml.load(fp, Loader=yaml.Loader)['config']
        tlefile = op.join(scfg['path_to_tle_files'], tlefile)

    tprename = op.splitext(op.basename(tlefile))[0]
    tot = 0
    with open(tlefile, 'r') as fp:
        for line in fp:
            tot += 1
    tot = tot // 3
    outfile = f'satpos_{tprename}.sh'
    print(f"Using {tlefile}")
    print(f"Writing {tot} entries to {outfile}")
    with open(outfile, 'w') as fp:
        for i in range(tot):
            print(f"satpos {tprename} {i+1}", file=fp)
    chmod(outfile, 0o755)


def generate_complete_set(epoch=None, path='tle', fmname='master.dat'):
    """
    Goes through all tle files to find unique satellites and produce a completeset.
    [N.B. should use most recent epoch -- currently doesn't check that.]
    """
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
