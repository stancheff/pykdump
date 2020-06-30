# -*- coding: utf-8 -*-
#
# Get info about architecture and kernel parameters from vmcore,
# such as integer sizes, HZ etc.
#
#
#
# --------------------------------------------------------------------
# (C) Copyright 2006-2020 Hewlett Packard Enterprise Development LP
#
# Author: Alex Sidorenko <asid@hpe.com>
#
# --------------------------------------------------------------------
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Pubic License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import re
import os.path

import crash
from .Generic import Bunch

sys_info = Bunch()


HZ = crash.HZ
PAGESIZE = crash.PAGESIZE
PAGE_CACHE_SHIFT = crash.PAGE_CACHE_SHIFT

class KernelRev(str):
    def __init__(self, s):
        self.ov = KernelRev.conv(s)

    def __lt__(self, s):
        nv = KernelRev.conv(s)
        return self.ov < nv
    def __le__(self, s):
        nv = KernelRev.conv(s)
        return self.ov <= nv
    def __gt__(self, s):
        nv = KernelRev.conv(s)
        return self.ov > nv
    def __ge__(self, s):
        nv = KernelRev.conv(s)
        return self.ov >= nv

    def conv(s):
        a = [0, 0, 0]
        for i, v in enumerate(s.split('.')):
            a[i] = int(v)
        return a[0] * 100000 + a[1] * 1000 + a[2]
    conv = staticmethod(conv)

# Execute 'sys' command and put its split output into a dictionary
# Some names contain space and should be accessed using a dict method, e.g.
# sys_info["LOAD AVERAGE"]
#
# A special case:
   #DUMPFILES: vmcore1 [PARTIAL DUMP]
              #vmcore2 [PARTIAL DUMP]
              #vmcore3 [PARTIAL DUMP]
              #vmcore4 [PARTIAL DUMP]
def _doSys():
    """Execute 'sys' commands inside crash and return the parsed results"""
    key = 'UNKNOWN'
    for il in crash.exec_crash_command("sys").splitlines():
        spl = il.split(':', 1)
        if (len(spl) == 2):
            key = spl[0].strip()
            sys_info[key] = spl[1].strip()
        else:
            sys_info[key] += '|' + il.strip()
    # If there are DUMPFILES, fill-in DUMPFILE for printing
    dfiles = sys_info.get('DUMPFILES', None)
    if (dfiles is None):
        return
    out = []
    for v in dfiles.split('|'):
        out.append(v.split()[0].strip())
    sys_info['DUMPFILE'] = ','.join(out)

_doSys()


# Check whether this is a live dump
if (sys_info.DUMPFILE.find("/dev/") == 0):
    sys_info.livedump = True
else:
    sys_info.livedump = False


# Check the kernel version and set HZ
kernel = re.search(r'^(\d+\.\d+\.\d+)', sys_info.RELEASE).group(1)
sys_info.kernel = KernelRev(kernel)
sys_info.HZ = HZ

# Convert CPUS to integer. Usually we just have an integer, but sometimes
# CPUS: 64 [OFFLINE: 32]
sys_info.CPUS = int(sys_info.CPUS.split()[0])

# Extract hardware from MACHINE
sys_info.machine = sys_info["MACHINE"].split()[0]

# This is where debug kernel resides
try:
    sys_info.DebugDir = os.path.dirname(sys_info["DEBUG KERNEL"])
except KeyError:
    sys_info.DebugDir = os.path.dirname(sys_info["KERNEL"])

# A list of top directories where we will search for debuginfo
kname = sys_info.RELEASE
RHDIR = "/usr/lib/debug/lib/modules/" + kname
CGDIR = "/usr/lib/kernel-image-%s-dbg/lib/modules/%s/" %(kname, kname)
debuginfo = [RHDIR, CGDIR]

if (sys_info.DebugDir == ""):
    sys_info.DebugDir ="."
if (not  sys_info.livedump):
    # Append the directory of where the dump is located
    debuginfo.append(sys_info.DebugDir)
else:
    # Append the current directory (useful for development)
    debuginfo.insert(0, '.')
# Finally, there's always a chance that this kernel is compiled
# with debuginfo
debuginfo.append("/lib/modules/" + kname)
sys_info.debuginfo = debuginfo
