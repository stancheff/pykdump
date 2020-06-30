# -*- coding: utf-8 -*-
#

# Caching and memoizing data

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

# For _getframe
import sys

debugMemoize = 0

# These options can be reset from API.py
debug = 0
livedump = False


# Memoize methods with one simple arg
class MemoizeTI(type):
    __cache = {}
    def __call__(cls, *args):
        sname = args[0]
        try:
            return MemoizeTI.__cache[sname]
        except KeyError:
            rc =  super(MemoizeTI, cls).__call__(*args)
            MemoizeTI.__cache[sname] = rc
            return rc

class MemoizeSU(type):
    def __call__(cls, *args):
        key = (args[0], MemoizeSU)
        try:
            return _typeinfo_cache[key]
        except KeyError:
            rc =  super(MemoizeSU, cls).__call__(*args)
            _typeinfo_cache[key] = rc
            return rc
    @staticmethod
    def purgecache(sn = None):
        purge_typeinfo(sn)



# A cache for anything typeinfo-related. The key to memoize on is
# (sn, function) -and we assume that 'sn' is always the first argument
# (sn, arg1, ...) where 'sn' is struct/type name. The idea is that when we need
# to change structure definition on the fly (e.g. multiple definitons)
# we want to do just purge_type_info(sn) and it will purge all related caches

_typeinfo_cache = {}
def memoize_typeinfo(fn):
    def newfunc(*args, **keyargs):
        key = (args[0], fn.__name__) + args[1:]
        try:
            return _typeinfo_cache[key]
        except KeyError:
            #print ("Memoizing", key)
            val =  fn(*args)
            _typeinfo_cache[key] = val
            return val
    return newfunc

def purge_typeinfo(sn = None):
    if (sn is None):
        _typeinfo_cache.clear()
        return
    for k in list(_typeinfo_cache.keys()):
        if (k[0] == sn):
            del _typeinfo_cache[k]


# Memoize cache. Is mainly used for expensive exec_crash_command

__memoize_cache = {}

CU_LIVE = 1                             # Update on live
CU_LOAD = 2                             # Update on crash 'mod' load
CU_PYMOD = 4                            # Update on Python modules reload
CU_TIMEOUT = 8                          # Update on timeout change

# CU_PYMOD is needed if we are reloading Python modules (by deleting it)
# In this case we need to invalidate cache entries containing references
# to classes defined in the deleted modules


def memoize_cond(condition):
    def deco(fn):
        def newfunc(*args, **keyargs):
            memoize = keyargs.get("MEMOIZE", True)
            #print('fn=',fn, "memoize=", memoize)
            newfunc.__memoize = memoize
            if (not memoize):
                return fn(*args)
            key = (condition, fn.__name__) + args
            # If CU_LIVE is set and we are on live kernel, do not
            # memoize
            if (condition & CU_LIVE and livedump):
                if (debugMemoize > 2):
                    print ("do not memoize: live kernel", key)
                return fn(*args)
            try:
                return __memoize_cache[key]
            except KeyError:
                if (debugMemoize > 1):
                    print ("Memoizing", key)
                val =  fn(*args)
                __memoize_cache[key] = val
                return val
        return newfunc
    return deco

def print_memoize_cache():
    #keys = sorted(__memoize_cache.keys())
    keys = list(__memoize_cache.keys())
    for k in keys:
        v = __memoize_cache[k]
        try:
            print (k, v)
        except Exception as val:
            print ("\n\t", val, 'key=', k)

# Purge those cache entries that have at least one of the specified
# flags set
def purge_memoize_cache(flags):
    #keys = sorted(__memoize_cache.keys())
    keys = list(__memoize_cache.keys())
    for k in keys:
        ce_flags = k[0]
        if (ce_flags & flags):
            if (debugMemoize > 1):
                print ("Purging cache entry", k)
            del __memoize_cache[k]

#  select and retirn the value of one expression only

__PY_select_cache = {}
def PY_select(*expr):
    f =  sys._getframe(1)
    outlocals = f.f_locals
    outglobals = f.f_globals
    cid = __fid(2)
    key = (cid, expr)
    if (key in __PY_select_cache):
        #print("from cache")
        return eval(__PY_select_cache[key][0], outglobals, outlocals)
    for  e in expr:
        try:
            #print("Evaluating", e)
            ee = eval(e, outglobals, outlocals)
            break
        except (KeyError, NameError, TypeError, AttributeError):
            #print(e, "is bad")
            pass
    else:
        return None
    code = compile(e, '<string>', 'eval')
    __PY_select_cache[key] = (code, e)
    return ee

def PY_select_stats():
    kv = [(k[0], v) for k, v in __PY_select_cache.items()]
    for k, v in sorted(kv) :
        print("{} -> {}".format(k, v[1]))

def __fid(depth=1):
    f = sys._getframe(depth)
    cid = (f.f_code.co_filename, f.f_lineno)
    #print(cid)
    return cid

# Purge PY_select cache
def PY_select_purge():
    __PY_select_cache.clear()
