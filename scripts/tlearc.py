#! /usr/bin/env python
# STTest.py (copyright 2019 by Andrew Stokes, original file named differently)
#
# Simple Python app to extract resident space object history data from www.space-track.org into
# spreadsheet (prior to executing, register for a free personal account at
# https://www.space-track.org/auth/createAccount)
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# For full licencing terms, please refer to the GNU General Public License (gpl-3_0.txt)
# distributed with this release, or see http://www.gnu.org/licenses/gpl-3.0.html.

import requests
import time
import sys
from blsky import satcensus


class MyError(Exception):
    def __init___(self, args):
        Exception.__init__(self, "my exception was raised with arguments {0}".format(args))
        self.args = args

# See https://www.space-track.org/documentation for details on REST queries
# "Find Starlinks" query finds all satellites w/ NORAD_CAT_ID > 40000 & OBJECT_NAME matching
# STARLINK*, 1 line per sat;
# the "OMM Starlink" query gets all Orbital Mean-Elements Messages (OMM) for a specific
# NORAD_CAT_ID in JSON format.


uriBase = "https://www.space-track.org"
requestLogin = "/ajaxauth/login"
requestCmdAction = "/basicspacedata/query"
requestBuild = "/class/tle/NORAD_CAT_ID/${NCILO}--${NCIHI}/EPOCH/${EPLO}--${EPHI}/orderby/EPOCH asc/format/3le/emptyresult/show"  # noqa


# Log in to personal account obtained by registering for free at https://www.space-track.org/auth/createAccount  # noqa
# import getpass
# print('\nEnter your personal Space-Track.org username (usually your email address for registration):  ')  # noqa
# configUsr = input()
# print('Username capture complete.\n')
# configPwd = getpass.getpass(prompt='Securely enter your Space-Track.org password (minimum of 15 characters):  ')  # noqa

elo = '2021-05-22'
ehi = '2021-06-02'
match_epoch = 2115230  # (100 * YYDDD.ddd for observations per above)
aggfile = 'agg.tle'
NORAD_CAT_ID_range = range(51001, 1000)

configUsr = 'ddeboer@berkeley.edu'
configPwd = 'blc1-technoSignature'
tleout = 'tle.out'
siteCred = {'identity': configUsr, 'password': configPwd}


def countdown(t, step=1, msg='Sleeping...'):  # in seconds
    pad_str = ' ' * len('%d' % step)
    for i in range(t, 0, -step):
        sys.stdout.write('{} for the next {} seconds {}\r'.format(msg, i, pad_str))
        sys.stdout.flush()
        time.sleep(step)
    print('Done {} for {} seconds!  {}'.format(msg, t, pad_str))

# login = "https://www.space-track.org/ajaxauth/login -d 'identity=<user>&password=<pw>'"


# use requests package to drive the RESTful session with space-track.org
print('Interfacing with SpaceTrack.org to obtain data...')
maxs = 1
afiles = []
with requests.Session() as session:

    # Log in first. NOTE:  we get a 200 to say the web site got the data, not that we are logged in.
    resp = session.post(uriBase + requestLogin, data=siteCred)
    if resp.status_code != 200:
        print(resp)
        raise MyError(resp, "POST fail on login.")

    for ncid in NORAD_CAT_ID_range:
        nlo = f"{ncid:05d}"
        nhi = f"{ncid+999:05d}"
        query = requestBuild.replace('${NCILO}', nlo).replace('${NCIHI}', nhi)\
                            .replace('${EPLO}', elo).replace('${EPHI}', ehi)
        print(query)
        resp = session.get(uriBase + requestCmdAction + query)

        if resp.status_code != 200:
            print(resp)
            raise MyError(resp, "GET fail on request for resident space objects.")
        this_file = f"A{nlo}.tle"
        afiles.append(this_file)
        with open(this_file, 'w') as fp:
            print(resp.text, file=fp)

        maxs += 1
        if maxs > 18:
            print('\nSnoozing for 60 secs for rate limit reasons (max 20/min and 200/hr).')
            countdown(60)
            maxs = 1
    session.close()

print(f'\nCompleted session.  Aggregating to {aggfile}.')
satcensus.agg_tle(afiles, epoch=match_epoch, outfile=aggfile)
