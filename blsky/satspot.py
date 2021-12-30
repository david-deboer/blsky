from astropy.time import Time
from astropy.coordinates import SkyCoord
import astropy.units as u
from . import sattrack
import numpy as np
import matplotlib.pyplot as plt
from argparse import Namespace


class Satspot:
    def __init__(self, ephem_file, time_format='mjd'):
        self.ephem_file = ephem_file
        tmptime = []
        self.az = []
        self.el = []
        self.viewable = None
        with open(ephem_file, 'r') as fp:
            for line in fp:
                data = [float(x) for x in line.split(',')]
                tmptime.append(data[0])
                self.el.append(data[1])
                self.az.append(data[2])
        self.times = Time(tmptime, format=time_format)
        plt.figure("Observations")
        plt.plot(self.times.datetime, self.az, 'o', label='Az')
        plt.plot(self.times.datetime, self.el, 's', label='El')

    def get_viewable(self):
        self.viewable = {}
        with open('viewable.csv', 'r') as fp:
            for line in fp:
                if line[0] == '#':
                    continue
                data = line.split(',')
                self.viewable[data[0]] = {'name': data[1],
                                          'norad': int(data[2]),
                                          'orbit': data[3],
                                          'period': float(data[4])}

    def check_window(self, window=20.0):
        if not self.viewable:
            print("Must get_viewable first.")
            return

        num_found = 0
        for sat, entry in self.viewable.items():
            track = sattrack.Track(sat+'.out')
            point = Namespace(t=[], az=[], el=[])
            for i, this_time in enumerate(self.times):
                if this_time >= track.times[0] and this_time <= track.times[-1]:
                    point.t.append(this_time.jd)
                    point.az.append(self.az[i])
                    point.el.append(self.el[i])
            point.t = np.array(point.t)
            point.az = np.array(point.az) * u.deg
            point.el = np.array(point.el) * u.deg
            c1 = SkyCoord(point.az, point.el)
            az_interp = np.interp(point.t, track.times.jd, track.az) * u.deg
            el_interp = np.interp(point.t, track.times.jd, track.el) * u.deg
            c2 = SkyCoord(az_interp, el_interp)
            sep = c1.separation(c2)
            fnd = np.where(sep.value < window)[0]
            if len(fnd):
                if not num_found:
                    plt.figure(f'Satellites within {window:.0f}deg')
                num_found += 1
                plt_t = 24.0 * 60.0 * (point.t - point.t[0])
                plt.plot(plt_t, sep, label=entry['name'])
                minsep = min(sep.value[fnd])
                print(f"{sat}: {entry['name']:20.20s}  {minsep:.2f}deg     "
                      f"{entry['orbit']:6s}  {entry['period']:8.2f}min")
        if num_found:
            print(f"Found {num_found} within {window}deg.")
            plt.xlabel('Time [min]')
            plt.ylabel('Separation [deg]')
            plt.axis(ymax=90.0)
            plt.plot(plt_t, point.el.value, 'ko')
        else:
            print(f"No satellites found within {window}deg.")
