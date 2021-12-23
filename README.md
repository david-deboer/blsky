blsky contains modules to investigate technosignature observing.  This primarily relates to rfi and drift of narrow-band signals.

satpos  implements the sgp4 orbital tracking code (http://www.astrodynamicstandards.com/sgp4/) and some other code to prep the data.

The TLE files are maintained in the /tle subdirectory and may be updated using the script 'updatetle.py' while in that directory.  There is a branch of this repo called tle_archive, so please update in that branch as well as the main branch.  Use a commit message of the form `TLE update 2021-12-15 11:50:10`.  The tle_archive branch gets updated weekly on Sunday night.  DO NOT MERGE THE tle_archive BRANCH WITH MAIN!  (I intend to write up modules to pull archived tles out.)

--satpos--
Given TLE (from a file, location set in satpos.cfg) it writes a file:
    'sp{filename}{entry_number_in_file:04d}.out' which contains a track over the period specified in satpos.cfg (which must be in that directory)
e.g. satpos active 123


--sattrack--
from satpos import sattrack
reads in the .out files from above and computes various parameters.

--satcensus--
from satpos import satcensus
random modules using sattrack (or not) to look at satellite data.


How-to
======
1 - make sure TLE files in tle_archive are what you want
2 - run satpos_script.py <filename>.tle to generate a shell script for satpos (<filename>=>active)
    writes:  satpos_<filename>.sh:  script for satpos (chmod u+x)
             sp<filename>.list:  used by find_viewable
3 - ?satcensus.find_viewable?
