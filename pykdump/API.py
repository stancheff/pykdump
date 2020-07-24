# -*- coding: utf-8 -*-

# This is the only module from pykdump that should be directly imported
# by applications. We want to hide the details of specific implementation from
# end-user. In particular, this module decides what backends to use
# depending on availability of low-level shared library dlopened from crash
#
# --------------------------------------------------------------------
# (C) Copyright 2006-2020 Hewlett Packard Enterprise Development LP
#
# Author: Alex Sidorenko <asid@hpe.com>
#
# --------------------------------------------------------------------
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.



__doc__ = '''
This is the toplevel API for Python/crash framework. Most programs should
not call low-level functions directly but use this module instead.
'''



debug = 0

import sys, os, os.path
import re, string
import time, select
import stat
import traceback
import atexit
import importlib
from collections import defaultdict
import pprint
pp = pprint.PrettyPrinter(indent=4)


# ================ Checking whether C-module is new enough ========

# It does not make sense to continue if C-module is unavailable
try:
    import crash
except ImportError as e:
    # Traverse frames to find the program
    # <frame object at 0x18ef288>
    # ../progs/pykdump/API.py
    # <frozen importlib._bootstrap>
    # <frozen importlib._bootstrap_external>
    # <frozen importlib._bootstrap>
    # <frozen importlib._bootstrap>
    # <frozen importlib._bootstrap>
    # ../progs/xportshow.py

    import inspect
    cframe = inspect.currentframe()
    for f in inspect.getouterframes(cframe)[1:]:
        if ("/progs/" in f.filename):
            #print(f.filename)
            g = f.frame.f_globals
            break
    vers =" %s: %s" % (g["__name__"], g["__version__"])
    raise ImportError(vers)


import pykdump                          # For version check
require_cmod_version = pykdump.require_cmod_version
require_cmod_version(pykdump.minimal_cmod_version)

# To be able to use legacy (Python-2) based subroutines
long = int


# Here we make some pieces of other modules classes/functions/varibles
# visible to API

from .Generic import (Bunch, DCache, TrueOnce,
                      iterN, dbits2str, print2columns,
                      patch_default_kw
)

from .memocaches import ( memoize_cond, purge_memoize_cache, PY_select_purge,
        CU_LIVE, CU_LOAD, CU_PYMOD, CU_TIMEOUT,
        memoize_typeinfo, purge_typeinfo, PY_select)

from .logging import PyLog, WARNING
crash.WARNING = WARNING                 # To be used from C-code

from .dlkmload import *

# This import computes pointer/integer sizes, gets info about kernel
# and fills-in 'sys_info'
from .vmcorearch import *

# The standard hex() appended L for longints, not needed anymore
hexl = hex

# For binary compatibility with older module
try:
    set_default_timeout = crash.set_default_timeout
except AttributeError:
    def set_default_timeout(timeout):
        return None

from . import highlevel
from .highlevel import *


from .tparser import CEnum, CDefine

# API module globals
API_options = Bunch()

# =================================================================
# =                                                               =
#              Global and Debugging options                       =
# =                                                               =
# =================================================================

registerModuleAttr("debugReload", default=0,
                   help="Debug reloading Python modules")

# Timeout used on a previous run
global __timeout_exec
__timeout_exec = 0

pylog = PyLog()

# Check whether we output to a real file.

def isfileoutput():
    if (sys.stdout.isatty()):
        return False
    mode = os.fstat(sys.stdout.fileno())[stat.ST_MODE]
    return stat.S_ISREG(mode)

# Return the current nsproxy
try:
    __init_proxy = readSymbol("init_nsproxy")
except:
    __init_proxy = None

__proxy = __init_proxy
def get_nsproxy():
    return __proxy

def set_nsproxy(pid = None):
    global __proxy
    if (pid == None):
        __proxy = __init_proxy
    else:
        taskaddr = pid_to_task(pid)
        if (taskaddr):
            task = readSU("struct task_struct", taskaddr)
            __proxy = task.nsproxy
        else:
            print("There is no PID={}".format(pid))
            sys.exit(0)


# Process common (i.e. common for all pykdump scripts) options.
from optparse import OptionParser, Option
def __epythonOptions():
    """Process epython common options and filter them out"""

    op = OptionParser(add_help_option=False, option_class=Option)
    op.add_option("--experimental", dest="experimental", default=0,
              action="store_true",
              help="enable experimental features (for developers only)")

    op.add_option("--debug", dest="debug", default=-1,
              action="store", type="int",
              help="enable debugging output")

    op.add_option("--timeout", dest="timeout", default=120,
              action="store", type="int",
              help="set default timeout for crash commands")
    op.add_option("--maxel", dest="Maxel", default=10000,
              action="store", type="int",
              help="set maximum number of list elements to traverse")
    op.add_option("--usens", dest="usens",
              action="store", type="int",
              help="use namespace of the specified PID")

    op.add_option("--reload", dest="reload", default=0,
              action="store_true",
              help="reload already imported modules from Linuxdump")

    op.add_option("--dumpcache", dest="dumpcache", default=0,
              action="store_true",
              help="dump API caches info")

    op.add_option("--ofile", dest="filename",
                  help="write report to FILE", metavar="FILE")

    op.add_option("--ehelp", default=0, dest="ehelp",
                  action = "store_true",
                  help="Print generic epython options")

    if (len(sys.argv) > 1):
        (aargs, uargs) = __preprocess(sys.argv[1:], op)
    else:
        aargs = uargs = []

    (o, args) = op.parse_args(aargs)
    highlevel.experimental = API_options.experimental = o.experimental
    global debug, __timeout_exec
    if (o.debug != -1):
        debug = o.debug
    API_options.debug = debug

    if (o.ehelp):
        op.print_help()
        print ("Current debug level=%d" % debug)
    # pdir <module 'pdir' from '/tmp/pdir.py'>
    # thisdir <module 'thisdir' from './thisdir.pyc'>
    # subdir.otherdir <module 'subdir.otherdir' from './subdir/otherdir.pyc'>

    # Do not reload from /pykdump/ - this is dangerous
    # Do not reload from mpydump.so - it makes no sense as it is
    # immutable
    # We do not reload __main__
    if (o.reload):
        purge_memoize_cache(CU_PYMOD)
        PY_select_purge()
        for k, m in list(sys.modules.items())[:]:
            if (hasattr(m, '__file__')):
                mod1 = k.split('.')[0]
                fpath = m.__file__
                # Do not reload if there is no such file
                if (not os.path.isfile(fpath)):
                    continue
                # Don't reload pykdump/
                if ( mod1 in ('pykdump', '__main__')):
                    continue
                if (debugReload > 1):
                    print(k, fpath)

                importlib.reload(m)
                if (debugReload):
                    print ("--reloading", k)

    if  (o.timeout):
        set_default_timeout(o.timeout)
        crash.default_timeout = o.timeout
        # Purge the CU_TIMEOUT caches if we _increase_ the timeout
        # This makes sense if some commands did not complete and we
        # re-run with bigger timeout
        if (o.timeout > __timeout_exec):
            purge_memoize_cache(CU_TIMEOUT)
        __timeout_exec = o.timeout
    if (o.Maxel):
        setListMaxel(o.Maxel)

    # Reset nsproxy every time
    set_nsproxy(None)
    if  (o.usens):
        print(" *=*=* Using namespaces of PID {}  *=*=*".format(o.usens))
        set_nsproxy(o.usens)

    if (o.filename):
        sys.stdout = open(o.filename, "w")

    sys.argv[1:] = uargs
    #print ("EPYTHON sys.argv=", sys.argv)

    API_options.dumpcache = o.dumpcache
    del op

# Preprocess options, splitting them into these for API_wide and those
# userscript-specific
def __preprocess(iargv,op):
    """Preprocess options separating these controlling API
    from those passed to program as arguments
    """
    # Split the arguments into API/app

    aargv = []                              # API args
    uargv = []                              # Application args

    #print ("iargv=", iargv)

    while(iargv):
        el = iargv.pop(0)
        if (el and (el[:2] == '--' or el[0] == '-')):
            # Check whether this option is present in optparser's op
            optstr = el.split('=')[0]
            opt =  op.get_option(optstr)
            #print ("el, opt", el, opt)
            if (opt):
                nargs = opt.nargs
                aargv.append(el)
                # If we don't have '=', grab the next element too
                if (el.find('=') == -1 and nargs):
                    aargv.append(iargv.pop(0))
            else:
                uargv.append(el)
        else:
            uargv.append(el)
    #print ("aargv=", aargv)
    #print ("uargv", uargv)
    return (aargv, uargv)

# Format sys.argv in a nice way
def argv2s(argv):
    out = ['']
    for i, o in enumerate(argv):
        if (i == 0):
            o = os.path.basename(o)
        if (' ' in o):
            out.append('"{}"'.format(o))
        else:
            out.append(o)
    out.append('')
    return ' '.join(out)


# This function is called on every 'epython' invocation
# It is called _before_ we  start the real script
# This is done by 'epython' command.
# Here we can print information messages  and initialize statistics

re_apidebug=re.compile(r'^--apidebug=(\d+)$')
def __enter_epython():
    # Purge temp entries in DCache
    DCache.cleartmp()
    global t_start, t_start_children, t_starta, pp
    ost = os.times()
    t_start = ost[0]+ost[1]
    t_start_children = ost[2] + ost[3]
    t_starta = time.time()

    # We might redefine stdout every time we execute a command...
    # We expect stdout supporting utf-8
    sys.stdout.reconfigure(encoding='utf-8')

    pp = pprint.PrettyPrinter(indent=4)

    pylog.cleanup()     # Do cleanup every time
    #print ("Entering Epython")

    # Process hidden '--apidebug=level' and '--reload' options
    # filtering them out from sys.argv. Save the old copy in sys.__oldargv
    sys.__oldargv = sys.argv.copy()
    __epythonOptions()

    # The dumpfile name can optionally have extra info appended, e.g.
    # /Dumps/Linux/test/vmcore-netdump-2.6.9-22.ELsmp  [PARTIAL DUMP]
    dumpfile = sys_info.DUMPFILE.split()[0]
    #cwd = os.getcwd()
    dumpfile = os.path.abspath(dumpfile)
    text = " %s (%s) " % (dumpfile, sys_info.RELEASE)
    lpad = (77-len(text))//2
    # Print vmcore name/path when not on tty
    if (isfileoutput()):
        # Print executed command
        print("\n   {:*^60s}".format(argv2s(sys.__oldargv)))
        print (" {:o^77s}".format(text))

    # Use KVADDR
    set_readmem_task(0)

    # Insert directory of the file to sys.path
    pdir = os.path.dirname(sys.argv[0])
    #print ("pdir=", pdir)
    # We need to remove it in __exit_epython
    sys.path.insert(0, pdir)
    #raise Exception("enter_epython")


# We call this when exiting epython
def __exit_epython():
    # Remove prog directory that we have inserted
    sys.path.pop(0)
    if API_options.dumpcache:
        #BaseStructInfo.printCache()
        #wrapcrash.BaseTypeinfo.printCache()
        pass
    pylog.onexit()
    __cleanup()


def __cleanup():
    set_readmem_task(0)
    try:
        ost = os.times()
        parent_t = ost[0] + ost[1] - t_start
        child_t = ost[2] + ost[3] - t_start_children
        if (abs(child_t) > 0.001):
            child_s = ", Child processes: %6.2fs" % child_t
        else:
            child_s = ""
        print ("\n ** Execution took %6.2fs (real) %6.2fs (CPU)%s" % \
                                        (time.time() - t_starta,
                                         parent_t, child_s))
    except IOError as v:
        print(v, file=sys.stderr)
    try:
        sys.stdout.flush()
    except BrokenPipeError as v:
        print(v, file=sys.stderr)
        pass


# -----------  initializations ----------------

# What happens if we use 'epython' command several times without
# leaving 'crash'? The first time import statements really do imports running
# some code, next time the import statement just sees that the code is already
# imported and it does not execute statements inside modules. So the code
# here is executed only the first time we import API (this might change if we
# purge modules, e.g. for debugging).
#
# But the function enter_python() is called every time - the first time when
# we do import, next times as it is registered as a hook

# A special object to be used instead of readSymbol, e.g.
# readSymbol("xtime") -> PYKD.xtime
# we do not try to workaround Python mangling of attrs starting with
# __, as  presumably using names that begin with double underscores
# in C is "undefined behavior", which is the technical term for
# "don't do it."

class __PYKD_reader(object):
    def __getattr__(self, attrname):
        return readSymbol(attrname)

PYKD = __PYKD_reader()

__enter_epython()

# Hooks used by C-extension
sys.enterepython = __enter_epython
sys.exitepython = __exit_epython

if (API_options.debug):
    print ("-------PyKdump %s-------------" % pykdump.__version__)
