blsky contains modules to investigate technosignature observing.  This primarily relates to rfi and drift of narrow-band signals.

satpos  implements the sgp4 orbital tracking code (http://www.astrodynamicstandards.com/sgp4/) and some other code to prep the data.

The TLE files are maintained in the /tle subdirectory and may be updated using the script 'updatetle.py' while in that directory.  There is a branch of this repo called tle\_archive, so please update

Note that when updated should git commit -am 'TLE update on YY-MM-DD' so that old ones may be found via git log.  There is a special branch in the repo where

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
