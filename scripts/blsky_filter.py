#! /usr/bin/env python
from blsky import satcensus
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('satfile', help="Name of sat list file to use (satpos_X.sh for viewable).",
                nargs='?', default='default')
ap.add_argument('-q', '--quiet', help="Flag to stop progress print.",
                action='store_true')
ap.add_argument('-v', '--viewable', help='Flag to run viewable filter.',
                action='store_true')
ap.add_argument('-d', '--drift', help='Flag to run drift filter.',
                action='store_true')
ap.add_argument('-f', '--frequency', help='For drift, freq in Hz', default=1e9, type=float)
ap.add_argument('-r', '--range', help='For drift, range in Hz/s (r1,r2)', default='-0.5,0.5')
ap.add_argument('-a', '--absvalue', help='For drift, use absolute value.',
                action='store_true')
ap.add_argument()
args = ap.parse_args()

if args.viewable:
    if args.satfile == 'default':
        args.satfile = 'satpos_active.sh'
    satcensus.find_viewable(args.satfile,
                            rewrite_file=True,
                            verbose=not args.quiet)

if args.drift:
    if args.satfile == 'default':
        args.satfile = 'viewable.csv'
    args.range = [float(x) for x in args.range.split(',')]
    satcensus.filter_on_drift(f=args.frequency,
                              rng=args.range,
                              absvalue=args.absvalue,
                              trackfilelist=args.satfile,
                              verbose=not args.quiet)
