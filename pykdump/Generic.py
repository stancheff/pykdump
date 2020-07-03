# -*- coding: utf-8 -*-
#
#  Generic classes and subroutines - not using any other PyKdump
#  subroutines/classes
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

import sys
import copy
import inspect
from collections import defaultdict
from itertools import zip_longest

# A helper class to implement lazy attibute computation. It calls the needed
# function only once and adds the result as an attribute so that next time
# we will not try to compute it again

class LazyEval(object):
    def __init__(self, name, meth):
        self.name = name
        self.meth = meth
    def __get__(self, obj, objtype):
        # Switch
        #print " ~~lazy~~ ", self.name
        val = self.meth(obj)
        setattr(obj, self.name, val)
        #obj.__setattr__(self.name, val)
        return val

# A dict-like container
class Bunch(dict):
    def __init__(self, d = {}):
        dict.__init__(self, d)
        self.__dict__.update(d)
    def __setattr__(self, name, value):
        dict.__setitem__(self, name, value)
        object.__setattr__(self, name, value)
    def __setitem__(self, name, value):
        dict.__setitem__(self, name, value)
        object.__setattr__(self, name, value)
    def copy(self):
        return Bunch(dict.copy(self))
    def __str__(self):
        out = []
        keys = sorted(self.keys())
        for k in keys:
            out.append("   {:<12s} {}".format(k, self[k]))
        return "\n".join(out)


# A special subclass of Bunch to be used for 'DataCache' class
# In particular, we can register handlerk subroutines that will
# be called when we change iterm value
class _Bunch(Bunch):
    def __init__(self, d = {}):
        super().__init__(d)
        # Used for regiestered handlers
        object.__setattr__(self, '_registered', defaultdict(list))
    def clear(self):
        for name in self.keys():
            object.__delattr__(self, name)
        dict.clear(self)
    def __setitem__(self, name, value):
        super().__setitem__(name,value)
        if (name in self._registered):
            for func, o, ownermod in self._registered[name]:
                func(value)
                if (_debugDCache):
                    print(" Setting {}={} for {}".format(name, value, o))
    def __getattr__(self, name):
        return None
    def _register(self, pyctlname, func, o, ownermod):
        self._registered[pyctlname].append((func, o, ownermod))
        if (_debugDCache):
            print(" <{}> {} option registered".format(pyctlname, o))

    # Delete all entries related to a specific module - this is needed
    # during reload
    def _delmodentries(self, mod):
        _reg = self._registered
        for k in _reg:
            # _reg[k][2] is ownermoddule
            lst = _reg[k]
            lst[:] = [e for e in lst if e[2] is not mod]
            _reg[k] = lst
    def Dump(self):
        _reg = self._registered
        out = []
        if (_reg):
            out.append(" -- Listing registered options --")
            for k in _reg:
                v = self[k]
                for func, o, ownermod in _reg[k]:
                    if (inspect.ismodule(o)):
                        descr = " in {}".format(o.__name__)
                    else:
                        nowner = ownermod.__name__
                        descr = "{} in {}".format(type(o).__name__, nowner)
                    out.append("     <{}={}>  {}".\
                               format(k, v, descr))
            s = "\n".join(out)
            print(s)

class DataCache(object):
    def __init__(self):
        self._tmp = _Bunch()
        self._perm = _Bunch()
    @property
    def tmp(self):
        return self._tmp
    @property
    def perm(self):
        return self._perm
    def cleartmp(self):
        # Clear both attrs and dict
        self._tmp.clear()
    def clearperm(self):
        # Clear both attrs and dict
        self._perm.clear()
    def __str__(self):
        return "{} in tmp, {} in perm".format(len(self._tmp), len(self._perm))
    def dump(self):
        if (len(self.tmp)):
            print("   ** DCache.tmp **")
            print(self.tmp)
        if (len(self.perm)):
            print("   ** DCache.perm **")
            print(self.perm)

DCache = DataCache()

# Get module object from whete we call this subroutine

def getCurrentModule(depth = 1):
    cframe = inspect.currentframe()
    m = inspect.getmodule(cframe)
    f = inspect.getouterframes(cframe)[depth]

    # The following does not work when called from ZIP (Why?)
    #m = inspect.getmodule(f.frame)
    #return m

    # An alternative approach:
    mname = f.frame.f_globals["__name__"]
    return sys.modules[mname]

# Register object handler to change its attribute externally
def registerObjAttrHandler(o, attrname, pyctlname=None, default=None):
    __D = DCache.perm
    if (pyctlname is None):
        pyctlname = attrname
    def __func(value):
        setattr(o, attrname, value)
        return value
    # If it is not set yet, set it to default
    if (default is None and hasattr(o, attrname)):
        default = getattr(o, attrname)

    if (not pyctlname in __D):
        __D[pyctlname] = default
    __func(default)             # Create it if needed
    __D._register(pyctlname, __func, o, getCurrentModule(2))

# Register a handler for a module attribute, where module is the one
# where we call this subroutine from
def registerModuleAttr(attrname, pyctlname=None, default=None):
    cmod = getCurrentModule(2)
    registerObjAttrHandler(cmod, attrname, pyctlname, default)

# We need the next line as it is used in registerObjAttrHandler
_debugDCache = 0
registerModuleAttr('_debugDCache', 'debugDCache')

# Produce an object that will return True a predefined number of times.
# For example:
# twice = TrueOnce(2)
# for in in range(5):
#    if(twice): print("OK")

class TrueOnce():
    def __init__(self, v = 1):
        self.v = v
    def __bool__(self):
        if (self.v > 0):
            self.v -= 1
            return True
        else:
            return False


#
# ------------------------------------------------------------------
#
# Limit a potentially infinite sequence so that while iterating
# it we'll stop not later than after N elements

def iterN(seq, N):
    it = iter(seq)
    for i in range(N):
        yield next(it)
    return




# If 'flags' integer variable has some bits set and we assume their
# names/values are in a dict-like object, return a string. For example,
# decoding interface flags we will print "UP|BROADCAST|RUNNING|MULTICAST"
#
# Do not consider dictionary keys that have several bits set

def dbits2str(flags, d, offset = 0):
    # Return True if there is 1-bit only
    def bit1(f):
        nb = 0
        while (f):
            if (f & 1):
                nb += 1
            if (nb > 1):
                return False
            f >>= 1
        return nb == 1

    out = ""
    for name, val in d.items():
        if (bit1(val) and (flags & val)):
            if (out == ""):
                out = name[offset:]
            else:
                out += "|" + name[offset:]
    return out


# Join left and right panels, both as multiline strings
def print2columns(left,right):
    left = left.split("\n")
    right = right.split("\n")
    for l, r in zip_longest(left, right, fillvalue= ''):
        print (l.ljust(38), r)



# The following function is used to do some black magic - adding methods
# to classes dynamically after dump is open.
# E.g. we cannot obtain struct size before we have access to dump

def funcToMethod(func,clas,method_name=None):
    """This function adds a method dynamically"""
    import new
    method = new.instancemethod(func,None,clas)
    if not method_name: method_name=func.__name__
    setattr(clas, method_name, method)

