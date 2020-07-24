# -*- coding: utf-8 -*-
#

# High-level API to control PyKdump behaviour and debugging
#
# Something similar to 'sysctl' for Linux kernel
# Usage: 'pyctl opt1=val1 opt2=val2 ...'
#
# 'pyctl -a ' - print all registered keys
# If you add '-v', it prints help strings if they are available
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

# Set global PyKdump options
import sys
import re

from pykdump.API import *
from pykdump.Generic import PyCtl


import argparse
parser =  argparse.ArgumentParser()

parser.add_argument("-a","--all", dest="All", default = 0,
                    action="store_true",
                    help="print all")

parser.add_argument("-v", dest="Verbose", default = 0,
                    action="count",
                    help="verbose output")


o, args = parser.parse_known_args()

#print(o)
#print(args)

info = PyCtl.getDict()

# Decode and print a single key
def printKey(k):
    f, mod, kwargscopy, currentvalue = info[k]
    if (help := kwargscopy.get("help")):
        help = f" - {help}"
    else:
        help = ''
    default = kwargscopy.get("default")
    print(f"  {k:15s}{help}")
    print(f"           {currentvalue=} {default=}")
    if (o.Verbose):
          print(f"      {mod.__name__}  func={f.__name__}")
          print(f"      {kwargscopy}")

# If we see '-a', we should not have any pairs
if (o.All):
    if (args):
        print(f"Unexpected extra args {args}")
        sys.exit(1)
    for k in sorted(info.keys()):
        printKey(k)
    sys.exit(0)

# We expect key=val
pairs = []
for a in args:
    spl = a.split('=')
    key = spl[0]
    if (not key in info):
        print(f"  Unknown key: <{key}>, skipping it")
        continue
    nitems = len(spl)
    if (nitems > 2):
        print(f"  Bad syntax: <{a}>")
        sys.exit(1)
    elif (nitems == 1):
        printKey(key)
        continue
    val = spl[1]
    pairs.append((key, val))

# Process found pairs
for k, v in pairs:
    TypeConv = PyCtl.TypeConv(k)
    PyCtl.runfn(k, TypeConv(v))


