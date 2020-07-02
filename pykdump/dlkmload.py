# -*- coding: utf-8 -*-
#
#
#  loading/reloading DLKM debuginfo subroutines
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

import os

from .highlevel import *
from .vmcorearch import sys_info
from .memocaches import purge_typeinfo

# Deref debugging
registerModuleAttr("debugDLKM", default=0)

# For fbase specified as 'nfsd' find all files like nfds.o, nfsd.ko,
# nfsd.o.debug and nfsd.ko.debug that are present in a given directory

def possibleModuleNames(topdir, fbase):
    """Find filenames matching a given module name"""
    if (topdir == None):
        return None
    exts = (".ko.debug", ".o.debug", ".ko", ".o")
    lfb = len(fbase)
    #print ("++ searching for", fbase, " at", topdir)

    for d, dummy, files in os.walk(topdir):
        for f in files:
            if (f.find(fbase) != 0):
                continue
            ext = f[lfb:]
            for e in exts:
                if (ext == e):
                    return os.path.join(d, fbase + e)
    return None


# Loading extra modules. Some defauls locations for debuginfo:

# RH /usr/lib/debug/lib/modules/uname/...
# CG /usr/lib/kernel-image-2.6.10-telco-1.27-mckinley-smp-dbg/lib/modules/2.6.10-telco-1.27-mckinley-smp/...

# So we'll try these directories first, then the default /lib/modules/uname,
# then the dump directory

# If we load module successfully, we receive
#  MODULE   NAME          SIZE  OBJECT FILE
# f8a95800  sunrpc      139173  /data/Dumps/test/sunrpc.ko.debug


__loaded_Mods = {}
def loadModule(modname, ofile = None, altname = None):
    """Load module file into crash"""

    # In some cases we load modules renaming them.
    # In this case modname is the original name (used to search for debug)
    # and altname is the name in 'mod' output
    if (not altname):
        altname = modname
    try:
        return __loaded_Mods[modname]
    except KeyError:
        pass

    if (debugDLKM > 1):
        print ("Starting module search", modname)
    if (ofile == None):
        for t in sys_info.debuginfo:
            if (debugDLKM > 1):
                print (t)
            # Some modules use different names in file object and lsmod, e.g.:
            # dm_mod -> dm-mod.ko
            for mn in (modname, modname.replace("_", "-")):
               ofile = possibleModuleNames(t, mn)
               if (ofile):
                   break
            if (ofile):
                break
        if (debugDLKM > 1):
            print ("Loading", ofile)
    if (ofile == None):
        return False
    # If we specify a non-loaded module, exec_crash_command does not return
    if (debugDLKM > 1):
        print ("Checking for altname")
    if (not altname in lsModules()):
        return False
    if (debugDLKM > 1):
        print ("Trying to insert", altname, ofile)
    rc = exec_crash_command("mod -s %s %s" % (altname, ofile))
    success = (rc.find("MODULE") != -1)
    __loaded_Mods[modname] = success
    # Invalidate typeinfo caches
    purge_typeinfo()
    return success

# Unload module


def delModule(modname):
    #print __loaded_Mods
    try:
        del __loaded_Mods[modname]
        exec_crash_command("mod -d %s" % modname)
        if (debugDLKM):
            print ("Unloading", modname)
    except KeyError:
        pass

# get modules list. We need it mainly to find
__mod_list = []
def lsModules():
    if (len(__mod_list) > 1):
        return __mod_list

    try:
        # On older kernels, we have module_list
        kernel_module = sym2addr("kernel_module")
        if (kernel_module):
            module_list = readSymbol("module_list")
            for m in readStructNext(module_list, "next", inchead = False):
                if (long(m) != kernel_module):
                    __mod_list.append(m.name)
        else:
            # On new kernels, we have a listhead
            lh = ListHead(sym2addr("modules"), "struct module")
            for m in lh.list:
               __mod_list.append(m.name)
    except:
        # If anything went wrong, return a partial list
        pass
    return __mod_list
