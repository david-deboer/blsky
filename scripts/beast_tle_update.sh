#!/bin/bash
cd blsky
git add tle
CURRENTDATE=`date +"%Y-%m-%d %T"`
GCOMMSG='git commit -m "TLE update '$CURRENTDATE'"'
eval $GCOMMSG
git push origin tle_archive
