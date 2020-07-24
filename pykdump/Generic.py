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
from collections import (defaultdict, namedtuple)
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


# Get module object from where we call this subroutine

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

def getFrameLocals(depth = 1):
    cframe = inspect.currentframe()
    m = inspect.getmodule(cframe)
    f = inspect.getouterframes(cframe)[depth]
    return f.frame.f_locals

def getMod_and_kwargs():
    loc2 = getFrameLocals(depth=3)
    return (loc2["mod"], loc2["kwargscopy"])

# Format *args and **kwargs for nice printing
def formatargs(*args, **kwargs):
    out = []
    out.extend([str(s) for s in args])
    out.extend([f"{a!r} = {v}" for a, v in kwargs.items()])
    return ", ".join(out)

# !!!!!!!!!!!!!!!!!!!! Obsoleted code, need to be reworked !!!!!!!!!
# A special subclass of Bunch to be used for 'DataCache' class
# In particular, we can register handlerk subroutines that will
# be called when we change iterm value
class _Bunch(Bunch):
    def __init__(self, d = {}):
        super().__init__(d)
    def clear(self):
        for name in self.keys():
            object.__delattr__(self, name)
        dict.clear(self)
    def __setitem__(self, name, value):
        super().__setitem__(name,value)
    def __getattr__(self, name):
        return None

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

# !!!!!!!!!!!!!!!!!!!!!!!!!!!@!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ---------- Dispatcher - run work for registered callbacks -----
#
# Callbacks are registered per module.
# While registering the callback function, we can optionally provide
# keyword arguments and their shallow copy will be stored for this key
# This copy is attached to our function as _kwargs
#
# This might be useful, for example we can print the contents of 'help'
# or we can store the default value so that we can reset to it
#

class _Pyctl(object):
    def __init__(self):
        self._names = {}
    # Register a callback function for 'name'. If there already is one,
    # replace it
    def regfunc(self, name, f, **kwargs):
        #argscopy = copy.copy(args)
        kwargscopy = copy.copy(kwargs)
        mod = getCurrentModule(depth=2)
        currentvalue = None
        info = self._names[name] = [f, mod, kwargscopy, currentvalue]
    # Execute a registered function by name
    def runfn(self, name, *args, **kwargs):
        f, mod, kwargscopy, currentvalue  = self._names[name]
        fargs = formatargs(*args, **kwargs)
        #print(f"-- Executing {f.__name__}({fargs})")
        retval = f(*args, **kwargs)
        self.setCurentValue(name, retval)
    def Dump(self):
        for name,  (f, mod, kwargs, currentvalue) in self._names.items():
            print(f"{name=} {mod.__name__}\n\tfunc={f.__name__}, "
                  f"{kwargs=}")
    def getDict(self):
        return self._names
    def setCurentValue(self, name, newval):
        self._names[name][3] = newval
    def TypeConv(self, name):
        return self._names[name][2]['type']

PyCtl = _Pyctl()

# Register object handler to change its attribute externally
def registerObjAttrHandler(o, attrname, **kwargs):
    pyctlname = attrname
    def __func(value):
        setattr(o, attrname, value)
        return value
    # If it is not set yet, set it to default
    default = kwargs["default"]
    if (hasattr(o, attrname)):
        curval = getattr(o, attrname)
        if (default is None):
            default = curval
    __curval = __func(default)    # Create it if needed
    PyCtl.regfunc(pyctlname, __func, **kwargs)
    PyCtl.setCurentValue(pyctlname, __curval)

# Register a handler for a module attribute, where module is the one
# where we call this subroutine from
def registerModuleAttr(attrname, pyctlname=None, default=None,
                       help="", type=int):
    cmod = getCurrentModule(2)
    kwargs = {"pyctlname": pyctlname, "default" : default,
              "type": type, "help":help}
    registerObjAttrHandler(cmod, attrname, **kwargs)

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


# Monkey-patching of default keyword argument value.
# Assuming that there are functions/classes in module 'mod' that use default
# value, e.g.
# def func(one, *, two=2, ...)
#
# Calling this functions lets us to change the default value for all
# functions/class methods for this module

registerModuleAttr('debugMP_KW', default=0,
                   help="Debug Monkey-Patching of default keywords")

def patch_default_kw(mod, kname, newval):
    modname = mod.__name__
    def __patch(o, newval):
        o.__kwdefaults__[kname] = newval

    # A generator to iterate through all callables,
    # both functions and class methods
    def __getcallables():
        for o in dir(mod):
            o = getattr(mod, o)
            omod = getattr(o, '__module__', None)
            if (omod != modname):
                continue
            # Check whether this is a function or a class
            if (inspect.isclass(o)):
                # For class, we need to patch all callable methods,
                # including__new__ and __init__
                yield from  (getattr(o, method_name) for method_name in dir(o)
                      if callable(getattr(o, method_name)))

            elif (inspect.isfunction(o)):
                yield o

    for co in __getcallables():
        # Check whether it has default kwargs
        kwd = getattr(co, '__kwdefaults__', None)
        if (kwd is None):
            continue
        if (debugMP_KW):
            print(f"-- patching  {co}  {kname} -> {newval}")
        kwd[kname] = newval
