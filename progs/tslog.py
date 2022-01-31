#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Reformat 'log' command output to print date/time
#

# --------------------------------------------------------------------
# (C) Copyright 2017 Hewlett Packard Enterprise Development LP
#
# Author: Alex Sidorenko <asid@hpe.com>
#
# --------------------------------------------------------------------

__version__ = "1.0.0"


import sys
import re

from pykdump.API import *
#from LinuxDump.Time import get_uptime_from_crash

def get_uptime_fromcrash():
    return crash.get_uptime()/HZ


import datetime

def get_xtime():
    return PY_select(
        "PYKD.timekeeper.xtime.tv_sec",
        "PYKD.timekeeper.xtime_sec",
        "PYKD.shadow_timekeeper.xtime_sec",
        "PYKD.xtime.tv_sec"
        )

uptime = get_uptime_fromcrash()
#print ("Uptime from crash: {}",uptime)

re_ts = re.compile(r'\s*\[\s*(\d+)\.\d+\]')
sec = get_xtime()

loglines = exec_crash_command("log").splitlines()

last_line = loglines[-1]
m = re_ts.search(last_line)
if (not m):
    print("No timestamps")
    sys.exit(0)

print(m.group(1))

#base = sec - int(m.group(1))
base = sec - int(uptime)

# Log buffer timestamps use local_clock() which is not adjusted for NTP, so it drifts over time.  Our old method to
# calculate wall-clock times was accurate close to boot time but less so going back toward boot time.  Crash's log -T
# is the opposite: it's accurate close to boot time and gets less so as time increases.
#
# New method: compromise by scaling logbuf timestamps so they are linear across the entire uptime.  This will be accurate
# close to boot time and crash time, but may be less so in the middle (but probably still better than no adjustment).

#print ("Base time = {}".format(datetime.datetime.fromtimestamp(base)))
ratio = uptime / float(m.group(1))
#print ("Time ratio = {}",ratio)

for l in loglines:
    m = re_ts.search(l)
    if (m):
        ts = int(float(m.group(1)) * ratio)
        print("{} {}".format(datetime.datetime.fromtimestamp(base+ts),l))
    else:
        print(l)
