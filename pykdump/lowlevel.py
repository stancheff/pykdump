# -*- coding: utf-8 -*-
#
# Reading data from C-structures and variables. This module mainly implements
# internal subroutines of the framework.
#
# Subroutines intended for developers of applications are mostly in
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


import sys
import string, re
import struct
import os, select, time

import types

import pprint
pp = pprint.PrettyPrinter(indent=4)

experimental = False
experimental = True

debug = False

from .tparser import parseSUDef
from . import Generic as Gen
from .vmcorearch import sys_info

long = int

from . import datatypes as Dat

from .datatypes import \
    (TypeInfo,VarInfo, PseudoVarInfo,
     _SUInfo, SUInfo, ArtStructInfo, EnumInfo,
     TYPE_CODE_PTR, TYPE_CODE_SU, TYPE_CODE_FUNC, TYPE_CODE_INT,
     TYPE_CODE_ENUM,
     type_length
)

from .Generic import (Bunch,
             DCache,
             getCurrentModule, registerObjAttrHandler, registerModuleAttr)

from .memocaches import ( memoize_cond, purge_memoize_cache, PY_select_purge,
        CU_LIVE, CU_LOAD, CU_PYMOD, CU_TIMEOUT,
        memoize_typeinfo, purge_typeinfo, PY_select)



# GLobals used my this module

# Deref debugging
registerModuleAttr("debugDeref", default=0)

pointersize = type_length("void *")


# --------- Auxiliary subroutines for data conversions ---------------

# Create a multi-dim list based on index list,
# e.g. [2,3,4] =>  a[2][3][4] filled with None
def multilist(mdim):
    d1 = mdim[0]
    if (len(mdim) > 1):
        a = []
        for i in range(d1):
            a.append(multilist(mdim[1:]))
    else:
        a =  [None for i in range(d1)]
    return a

def _arr1toM(dims, arr1):
    # We do this for 2- and 3-dim only
    out = multilist(dims)
    if (len(dims) == 2):
        I = dims[0]
        J = dims[1]
        for i in range(I):
            for j in range(J):
                out[i][j] = arr1[i*J+j]

    elif (len(dims) == 3):
        I = dims[0]
        J = dims[1]
        K = dims[2]
        for i in range(I):
            for j in range(J):
                for k in range(K):
                    out[i][j] = arr1[i*J*K+j*K +k]
    else:
        raise TypeError("Array with dim >3")
    return out




class subStructResult(type):
    __cache = {}
    def __call__(cls, *args):
        sname = args[0]
        try:
            ncls = subStructResult.__cache[sname]
        except KeyError:
            supername = cls.__name__
            classname = '%s_%s' % (supername, sname)
            # Class names cannot contain spaces or -
            classname = classname.replace(' ', '_').replace('-', '_')
            #execstr = 'class %s(%s): pass' % (classname, supername)
            #print '===', execstr
            #exec(execstr)
            #ncls = locals()[classname]
            ncls = type(classname, (StructResult,), {})
            ncls.PYT_symbol = sname
            ncls.PYT_sinfo = SUInfo(sname)
            ncls.PYT_size = ncls.PYT_sinfo.PYT_size
            ncls.PYT_attrcache = {}

        #print("ncls=", ncls)
        rc =  ncls.__new__(ncls, *args)
        rc.__init__(*args)
        subStructResult.__cache[sname] = ncls
        return rc

# ------------Pseudoattributes------------------------------------------------


# Pseudoattributes.
class PseudoAttr(object):
    def __init__(self, fi, chain):
        self.fi = fi
        self.chain = chain
    def __get__(self, obj, objtype):
        if (self.chain == None):
            return obj
        val = pseudoAttrEvaluator(long(obj),  self.fi, self.chain)
        return val

# Procedural
class PseudoAttrProc(object):
    def __init__(self, proc):
        self.proc = proc
    def __get__(self, obj, objtype):
        return self.proc(obj)


# Test the chain to see whether there were no pointers. In case
# the chain is equivalent to a simple offset, add this field
# to SUinfo for this type

def _test_chain(sname, aname, fi, chain):
    if (not chain):
        return None
    totoffset = 0
    for ptr, off in chain:
        if (ptr):
            return None
        totoffset += off
    # Create a PseudoVarinfo and add it
    vi = PseudoVarInfo(aname)
    vi.ti = fi.ti
    vi.addr = 0
    vi.offset = totoffset
    return vi

def structSetAttr(sname, aname, estrings, sextra = []):
    if (type(estrings) == type("")):
        estrings = [estrings]

    try:
        cls = StructResult(sname).__class__
    except TypeError:
        # This struct does not exist - return False
        return False
    #print sname, cls
    for s in estrings:
        # A special case - an empty string means "return ourself"
        if (s == ""):
            rc =  [None, None]
        else:
            rc = parseDerefString(sname, s)
        if (rc):
            fi, chain = rc
            pa = PseudoAttr(fi, chain)
            setattr(cls,  aname, pa)
            vi = _test_chain(sname, aname, fi, chain)
            if (vi):
                #print sname, vi, vi.offset
                cls.PYT_sinfo[aname] = vi
            for extra in sextra:
                ecls = StructResult(extra).__class__
                setattr(ecls,  aname, pa)
                if (vi):
                    ecls.PYT_sinfo[aname] = vi
            return True
    return False

# Set a general procedural attr
def structSetProcAttr(sname, aname, meth):
    try:
        cls = StructResult(sname).__class__
    except TypeError:
        # This struct does not exist - return False
        return False

    setattr(cls, aname, PseudoAttrProc(meth))
    return True

# A replacement of structSetAttr
# A class to facilitate setting pseudoattributes.
# A very special case: as many sock structures rely on 'struct sock_common',
# we add a special syntax: "SKC.a" means we cast to 'struct sock_common' and
# use its 'a' field after that
class AttrSetter(object):
    specattr = "SKC."
    speclen = len(specattr)
    specstruct = "struct sock_common"
    def __init__(self, *args):
        object.__setattr__(self, "_ArgList_",  args)
        #print("++Structs:", args)
    def __setattr__(self, aname, rhs):
        #print("  --name={}".format(aname))
        if (not (type(rhs) in (list, tuple))):
            rhs = [rhs]
        try:
            basename = self._ArgList_[0]
            cls = StructResult(basename).__class__
        except TypeError:
            # This struct does not exist - set attr to False
            object.__setattr__(self, aname, False)
            return

        # Analyze possible attribute chains
        for s in rhs:
            if (isinstance(s, types.FunctionType)):
                # A programmatic attribute
                for extra in self._ArgList_:
                    try:
                        ecls = StructResult(extra).__class__
                    except TypeError:
                        continue
                    setattr(ecls, aname, PseudoAttrProc(s))
                return
            elif (s == ""):
                # use our base struct as it is
                rc = [None, None]
            elif (s.startswith(self.specattr)):
                rc = parseDerefString(self.specstruct, s[self.speclen:])
            else:
                rc = parseDerefString(basename, s)
            if (not rc):
                # We could not follow this chain, try next
                continue
            fi, chain = rc
            pa = PseudoAttr(fi, chain)
            vi = _test_chain(basename, aname, fi, chain)
            # Set this attribute for all classes
            for extra in self._ArgList_:
                try:
                    ecls = StructResult(extra).__class__
                    setattr(ecls,  aname, pa)
                    ecls.PYT_sinfo[aname] = vi
                except TypeError:
                    pass
            object.__setattr__(self, aname, True)
            return
        object.__setattr__(self, aname, False)



# Parse the derefence string
def parseDerefString(sname, teststring):
    si = SUInfo(sname)
    out =[]
    codetype = -1
    if (debugDeref):
        print ('-------sname=%s, test=%s' % (sname, teststring))
    for f in teststring.split('.'):
        f = f.strip()
        if (si and f in si):
            fi = si[f]
            offset = fi.offset
            if (debugDeref):
                print (f, "offset=%d" % offset)
            ti = fi.ti
            codetype = ti.codetype
            isptr= False
            if (codetype == TYPE_CODE_PTR):
                # Pointer
                if (ti.stype == "(func)"):
                    tcodetype = -1      # Bogus
                    isptr = True
                else:
                    tti = ti.getTargetType()
                    tcodetype = ti.getTargetCodeType()
                if (tcodetype in TYPE_CODE_SU):
                    si = SUInfo(tti.stype)
                    if (debugDeref):
                        print("   pointer:", tti.stype)
                    isptr = True
            elif (codetype in TYPE_CODE_SU):
                # Struct/Union
                if (debugDeref):
                    print ("    SU:", ti.stype)
                si = SUInfo(ti.stype)
            else:
                si = None
                if (debugDeref):
                    print ("    codetype=%d" % codetype)
            out.append((isptr, offset))
        else:
            if (debugDeref):
                print ("Cannot continue f=<%s>, codetype=%d" % (f, codetype))
            return False

    # If we reached this place, we have been able to dereference
    # everything. If the last field is of integer type, check for
    # bitsize/bitoffset
    # If the last field is of pointer type, we do not need to mark it
    # as such - the reader knows better what to do
    out[-1] = (False, out[-1][1])
    return (fi, out)

def pseudoAttrEvaluator(addr, vi, chain):
    addr = long(addr)
    for ptr, offset in chain:
        if (ptr):
            addr = readPtr(addr+offset)
        else:
            addr += offset
    # Now read the variable as defined by fi from address addr
    return vi.reader(addr)

# ----------------------------------------------------------------------------


_testcache = {}

#class StructResult(long, metaclass = subStructResult):
class StructResult(long):
    __metaclass__ = subStructResult
    def __new__(cls, sname, addr = 0):
        return long.__new__(cls, addr)

    def X__init__(self, sname, addr = 0):
        # Create a new class and change our instance to point to it
        try:
            ncls = _testcache[sname]
        except:
            supername = "StructResult"
            classname = '%s_%s' % (supername, sname)
            # Class names cannot contain spaces or -
            classname = classname.replace(' ', '_').replace('-', '_')
            d = {}
            d["PYT_symbol"] = sname
            d["PYT_sinfo"] = SUInfo(sname)
            d["PYT_size"] = d["PYT_sinfo"].PYT_size

            ncls = type(classname, (StructResult,), {})
            setattr(ncls, "PYT_symbol", sname)
            si = SUInfo(sname)
            setattr(ncls, "PYT_sinfo", si)
            setattr(ncls, "PYT_size", si.PYT_size)
            _testcache[sname] = ncls
        self.__class__ = ncls



    # The next two methods implement pointer arithmetic, i.e.
    # stype *p
    # (p+i) points to addr + sizeof(stype)*i
    # p[i] is equivalent to (p+i)

    def __getitem__(self, i):
        if (type(i) == type("")):
            return self.PYT_sinfo[i]

        sz1 = self.PYT_size
        return StructResult(self.PYT_symbol, long(self) + i * sz1)

    # The __add__ method can break badly-written programs easily - if
    # we forget to cast the pointer to (void *)
    def __add__(self, i):
        #raise TypeError, "!!!"
        return self[i]

    def X__getattr__(self, name):
        try:
            fi = self.PYT_sinfo[name]
        except KeyError:
            # Due to Python 'private' class variables mangling,
            # if we use a.__var inside 'class AAA', it will be
            # converted to a._AAA__var. This creates prob;ems for
            # emulating C to access attributes.
            # The approach I use below is ugly - but I have not found
            # a better way yet
            ind = name.find('__')
            if (ind > 0):
                name = name[ind:]
            try:
                fi = self.PYT_sinfo[name]
            except KeyError:
                msg = "<%s> does not have a field <%s>" % \
                      (self.PYT_symbol, name)
                raise KeyError(msg)

        #print( fi, fi.offset, fi.reader)
        #print("addr to read: 0x%x" % (long(self) + fi.offset), type(fi.offset))
        return fi.reader(long(self) + fi.offset)

    # A faster version of __getattr__
    def __getattr__(self, name):
        try:
            return self.PYT_attrcache[name](long(self))
        except KeyError:
            pass
        if (name in self.PYT_sinfo):
            fi = self.PYT_sinfo[name]
        else:
            # Due to Python 'private' class variables mangling,
            # if we use a.__var inside 'class AAA', it will be
            # converted to a._AAA__var. This creates problems for
            # emulating C to access attributes.
            # The approach we use below is ugly - but I have not found
            # a better way yet
            ind = name.find('__')
            if (ind > 0):
                name = name[ind:]
            if (name in self.PYT_sinfo):
                fi = self.PYT_sinfo[name]
            else:
                msg = "<%s> does not have a field <%s>" % \
                      (self.PYT_symbol, name)
                raise KeyError(msg)

        #print( fi, fi.offset, fi.reader)
        #print("addr to read: 0x%x" % (long(self) + fi.offset), type(fi.offset))
        reader = lambda addr: fi.reader(addr + fi.offset)
        self.PYT_attrcache[name] = reader
        #print("+++", self.PYT_symbol, name)
        return reader(long(self))

    def __eq__(self, cmp):
        return (long(self) == cmp)
    # In Python 3, object with __eq__ but without explicit __hash__ method
    # are unhashable!
    def __hash__(self):
        return (long(self))
    def __str__(self):
        return "<%s 0x%x>" % \
               (self.PYT_symbol, long(self))

    def __repr__(self):
        return "StructResult <%s 0x%x> \tsize=%d" % \
               (self.PYT_symbol, long(self), self.PYT_size)
    # Short string (without struct/union word), useful when line space is tight
    def shortStr(self):
        sn = self.PYT_symbol.split()[-1]
        return "<%s 0x%x>" % (sn, long(self))

    # Print all fields (without diving into structs/unions)
    def Dump(self, indent = 0):
        sindent = ' ' * indent
        for fn,fi in self.PYT_sinfo.PYT_body:
            # For big arrays, print just 4 first elements
            elements = fi.ti.elements
            try:
                val = self.__getattr__(fn)
                if (not isinstance(val, SmartString) and elements > 3):
                    val = str(val[:4])[:-1] + ", ..."
                print (sindent, "    %18s " % fn, val)
            except TypeError as err:
                print (sindent, "    %18s  unknown type" % fn)



    # Backwards compatibility
    #def __nonzero__(self):
    #    return (self.PYT_addr != 0)

    def __len__(self):
        return self.PYT_size

    def hasField(self, fname):
        return fname in self.PYT_sinfo

    def isNamed(self, sname):
        return sname == self.PYT_symbol

    def fieldOffset(self, fname):
        return self.PYT_sinfo[fname].offset

    def getDeref(self):
        return self

    def Eval(self, estr):
        cls = self.__class__
        try:
            (fi, chain) = cls.__cache[estr]
            #print "Got from Eval cache", estr, cls
            return pseudoAttrEvaluator(long(self), fi, chain)
        except AttributeError:
            #print "Creating a Eval cache for", cls
            cls.__cache = {}
        except KeyError:
            pass
        (fi, chain) = parseDerefString(self.PYT_symbol, estr)
        cls.__cache[estr] = (fi, chain)
        return pseudoAttrEvaluator(long(self), fi, chain)

    # Cast to another type. Here we assume that that one struct resides
    # as the first member of another one, this is met frequently in kernel
    # sources
    def castTo(self, sname):
        return StructResult(sname, long(self))

    Deref = property(getDeref)


# This adds a metaclass
StructResult = subStructResult('StructResult', (StructResult,), {})

# A factory function for Enum readers. If understand correctly,
# in C we cannot have enums in bitfields (but we can in C++!)
# GCC-5 let me compile C-program with enum bitfields
# At this moment we do a spcial processing for scalar (not array)
# only. for array we fall back to normal int reader
def ti_enumReader(ti):
    #print("ti_enumReader")
    def signedReader(addr):
        #s = readmem(addr, size)
        #return mem2long(s, signed = True)
        return tEnum(readIntN(addr, size, True), einfo)
    einfo = EnumInfo(ti.stype)
    size = ti.size
    if (ti.dims is not None):
        return ti_intReader(ti)
    return signedReader

# A reader for 'bool' type. The size of a bool is the same size as an int.
def ti_boolReader(ti, bitoffset = None, bitsize = None):
    def boolReader(addr):
        val = readIntN(addr, size)
        return True if val else False
    def boolArrayReader(addr):
        s = readmem(addr, totsize)
        val = mem2long(s, signed = False, array = elements)
        #convert integer array to boolean array
        val = [True if e else False for e in val]
        if (len(dims) > 1):
            val = _arr1toM(dims, bval)
        return val
    def boolBfReader(addr):
        val = readIntN(addr, size)
        val = (val>>bitoffset) & mask
        return True if val else False
    size = ti.size
    dims = ti.dims
    elements = ti.elements
    totsize = size * elements
    if (dims is not None):
        # There are no bitfield arrays in C!
        return boolArrayReader
    if (bitsize is None):
        return boolReader
    else:
        mask = (~(~0<<bitsize))
        return boolBfReader

# A factory function for integer readers
def ti_intReader(ti, bitoffset = None, bitsize = None):
    def signedReader(addr):
        #s = readmem(addr, size)
        #return mem2long(s, signed = True)
        return readIntN(addr, size, True)
    def unsignedReader(addr):
        #s = readmem(addr, size)
        #return mem2long(s)
        return readIntN(addr, size)
    def signedBFReader(addr):
        #s = readmem(addr, size)
        #val = mem2long(s)
        val = readIntN(addr, size)
        val = (val >> bitoffset) & mask
        sign = val >> (bitsize - 1)
        if (sign):
            return val - mask -1
        else:
            return val
    def unsignedBFReader(addr):
        #s = readmem(addr, size)
        #val = mem2long(s)
        val = readIntN(addr, size)
        val = (val>>bitoffset) & mask
        return val

    def charArray(addr):
        s = readmem(addr, dim1)
        val = SmartString(s, addr, None)
        return val

    # Arrays
    def signedArrayReader(addr):
        s = readmem(addr, totsize)
        val = mem2long(s, signed = True, array = elements)
        if (len(dims) > 1):
            val = _arr1toM(dims, val)
        return val

    def unsignedArrayReader(addr):
        s = readmem(addr, totsize)
        val =  mem2long(s, array = elements)
        # A subtle problem: for array=1 mem2long returns and
        # integer, not a list. This is bad for declarations like
        # in bits[1]
        if (len(dims) > 1):
            val = _arr1toM(dims, val)
        elif (elements == 1):
            val = [val]
        return val

    # A special case like unsigned char tb_data[0];
    # Return intDimensionlessArray
    def zeroArrayReader(addr):
        return intDimensionlessArray(addr, size, not unsigned)

    size = ti.size
    uint = ti.uint
    unsigned = (uint == None or uint)
    dims = ti.dims
    elements = ti.elements
    totsize = size * elements
    if (debug):
        print ("Creating an intReader size=%d" % size, \
              "uint=", uint, \
              "bitsize=", bitsize, "bitoffset=", bitoffset)

    #print "dims=", dims
    if (dims != None and len(dims) == 1 and ti.stype == 'char'):
        # CharArray
        dim1 = dims[0]
        # If dimension is zero, return the address. Some structs
        # have this at the end, e.g.
        # struct Qdisc {
        # ...
        #     char data[0];
        # };
        if (dim1 == 0):
            return zeroArrayReader
        else:
            return charArray
    elif (dims != None and  len(dims) == 1 and dims[0] == 0):
        return zeroArrayReader
    elif (unsigned):
        if (bitsize == None):
            if (dims == None):
                return unsignedReader
            else:
                return unsignedArrayReader
        else:
            mask = (~(~0<<bitsize))
            return unsignedBFReader
    else:
        if (bitsize == None):
            if (dims == None):
                return signedReader
            else:
                return signedArrayReader
        else:
            mask = (~(~0<<bitsize))
            return signedBFReader



# A factory function for struct/union readers
def suReader(vi):
    def reader1(addr):
        return StructResult(stype, addr)

    def readerarr(addr ):
        out = []
        for i in range(elements):
            sr = StructResult(stype, addr + i * size)
            out.append(sr)
        if (len(dims) > 1):
            out = _arr1toM(dims, out)
        return out

    # A special case, e.g. struct sockaddr_un name[0]
    def zeroArrayReader(addr):
        return StructResult(stype, addr)

    ti = vi.ti
    dims = ti.dims
    elements = ti.elements
    size = ti.size
    stype = ti.stype

    if (elements == 1):
        return reader1
    elif (elements == 0):
        return zeroArrayReader
    else:
        return readerarr


# A factory function for pointer readers
def ptrReader(vi, ptrlev):
    # Struct/Union reader
    def ptrSU(addr):
        #print("ptrSU: 0x%x" % addr, type(addr))
        ptr = readPtr(addr)
        return StructResult(stype, ptr)
    # Smart String reader
    def strPtr(ptraddr):
        ptr = readPtr(ptraddr)
        # If ptr = NULL, return None, needed for backwards compatibility
        if (ptr == 0):
            return None
        # Usually a string pointer points to a NULL-terminates string
        # But it can be used for crah/byte-array as well
        # So we do not really know how many bytes to read. I expected that
        # 256 is a reasonable number but small strings at the end of pages
        # trigger "Cannot access memory" in some rare cases
        try:
            s = readmem(ptr, 256)
        except crash.error:
            bytes = (((ptr>>8) +1)<<8) - ptr
            s = readmem(ptr, bytes)
        return SmartString(s, ptr, ptraddr)
    # Generic pointer
    def genPtr(addr):
        return tPtr(readPtr(addr), ti)

    # Function pointer
    def funcPtr(addr):
        ptr = readPtr(addr)
        if (ptr and sys_info.machine == "ia64"):
            ptr = readPtr(ptr)
        return ptr

    ti = vi.ti
    dims = ti.dims
    elements = ti.elements
    size = ti.size
    stype = ti.stype

    # If we have ptrlev=1, we try to return appropriate types
    # instead of generic pointers
    if (ptrlev == 1):
        if(stype == 'char'):
            # Smart string
            basereader = strPtr
        elif (ti.ptrbasetype in TYPE_CODE_SU):
            #  return StructResult instead of pointer
            basereader = ptrSU
        elif (ti.ptrbasetype == TYPE_CODE_FUNC):      # A pointer to function
            basereader = funcPtr
        else:
            # Is this OK for all types?
            basereader = genPtr
        # Now check whether we have arrays
        if (dims == None):
            # No need to do anything else
            return basereader
        # We have an array
        if (len(dims) == 1 and elements <= 1):
            # Zero-dimensioned array
            class Array0(object):
                def __init__(self, addr):
                    self.addr = addr
                def __getitem__(self, i):
                    return basereader(self.addr + i*size)
                def __long__(self):
                    return self.addr
            return lambda addr: Array0(addr)
        else:
            # A reader for 1-dimensional arrays
            class Array1(list):
                def __init__(self, addr):
                    self.addr = addr
                def __getitem__(self, i):
                    return basereader(self.addr + i*size)
                def __len__(self):
                    return elements
                def __iter__(self):
                    for i in range(elements):
                        yield self[i]
            reader1 = lambda addr: Array1(addr)
            if (len(dims) == 1):
                return reader1
            else:
                # Multi-dim
                def ArrayMulti(addr):
                    return _arr1toM(dims, reader1(addr))
                return ArrayMulti
    else:
       # ptrlev > 1
       return genPtr


    # Error - print debugging info
    raise TypeError("Cannot find a suitable reader for {} ptrbasetype={} dims={}".format(ti, ti.ptrbasetype,dims))
    return None

# With Python3 readmem() returns 'bytes'
# We always have the address where data is located as 'addr'
# If this is created from a struct field, we have another address available,
# that of the variable in struct. That is:
# struct {
#    char *var;
# } s;
#  s.var - addr
# &s.var - ptraddr
#
# We can create this object either providing a bytestring and addr
# (optionally ptraddr) or tPtr

class SmartString(str):
    def __new__(cls, s, addr = None, ptr = None):
        #if (isinstance(s, tPtr) and s.ptrlev == 1):
        ptrlev = getattr(s, "ptrlev", None)
        if (ptrlev == 1):
            addr = long(s)
            s = readmem(s, 256)
        elif (not isinstance(s, bytes)):
            raise TypeError("Cannot convert type {} to SmartString".format(
                type(s)))
        ss = b2str(s)
        sobj = str.__new__(cls, ss.split('\0')[0])
        sobj.ByteArray = s
        sobj.addr = addr
        sobj.ptr = ptr
        sobj.__fullstr = b2str(s)
        return sobj
    def __init__(self, s, addr = None, ptr = None):
        pass
    def __long__(self):
        return self.ptr
    def __getslice__(  self, i, j):
        return self.__fullstr.__getslice__(i, j)
    def __getitem__(self, key):
        return self.__fullstr.__getitem__(key)

def b2str(s):
    return  str(s, 'ascii', errors='backslashreplace')

# Wrapper functions to return attributes of StructResult

def Addr(obj, extra = None):
    if (isinstance(obj, StructResult)):
        # If we have extra set, we want to know the address of this field
        if (extra == None):
            return long(obj)
        else:
            off = obj.PYT_sinfo[extra].offset
            return long(obj) + off
    elif (isinstance(obj, SmartString) or isinstance(obj, SmartList)):
          return obj.addr
    else:
        raise TypeError(type(obj))

# Dereference a tPtr object - at this moment 1-dim pointers to SU only
def Deref(obj):
    if (isinstance(obj, tPtr)):
        return obj.Deref
    if (isinstance(obj, StructResult)):
        # This is needed for backwards compatibility only!
        return obj
    else:
        raise TypeError("Trying to dereference a non-pointer " + str(obj))


# When we do readSymbol and have pointers to struct, we need a way
# to record this info instead of just returning integer address

# To make dereferences faster, we store the basetype and ptrlev


class tPtr(long):
    def __new__(cls, l, ti):
        return long.__new__(cls, l)
    def __init__(self, l, ti):
        self.ti = ti
        self.ptrlev = self.ti.ptrlev
        self.dereferencer = newDereferencer(self.ti)
        #print('++', vi, self.ptrlev)
        #self.ptrlev = vi.ptrlev
    # For pointers, index access is equivalent to pointer arithmetic
    def __getitem__(self, i):
        return self.getArrDeref(i)
    def getArrDeref(self, i):
        addr = long(self)
        ptrlev = self.ptrlev
        if (addr == 0):
            msg = "\nNULL pointer %s" % repr(self)
            raise IndexError(msg)

        if (ptrlev == 1):
            # We need to step by base type
            addr += i * self.dereferencer.basesize
            return  self.dereferencer(addr)
        else:
            # We step by pointersize
            newaddr = readPtr(addr + i * pointersize)
            # Optimization for pointers to SU
            if (self.ti.tcodetype in TYPE_CODE_SU):
                return self.dereferencer(newaddr)
            else:
                ntptr = tPtr(newaddr, self.ti)
                ntptr.ptrlev = ptrlev - 1
                return ntptr
    def getDeref(self, i = None):
        addr = long(self)
        if (addr == 0):
            msg = "\nNULL pointer %s" % repr(self)
            raise IndexError(msg)
        if (self.ptrlev == 1):
            return self.dereferencer(addr)
        else:
            ntptr = tPtr(readPtr(addr), self.ti)
            ntptr.ptrlev = self.ptrlev - 1
            return ntptr
    def __repr__(self):
        stars = '*' * self.ptrlev
        return "<tPtr addr=0x%x ctype='%s %s'>" % \
               (self, self.ti.stype, stars)
    Deref = property(getDeref)

    # Backwards compatibility
    def getPtype(self):
        return self.ti
    ptype = property(getPtype)

# A wrapper for tPtr dimensionless arrays
class tPtrZeroArray(tPtr):
    #pass
    def __getitem__(self, i):
        return tPtr(readPtr(long(self) + i * self.ti.size), self.ti)

# Dimensionless array of pointers to SU, e.g.
# struct rt_trie_node *child[];
class tPtrZeroArraySU(tPtr):
    # pass
    def __getitem__(self, i):
        return readSU(self.ti.stype, readPtr(long(self) + i * self.ti.size))



# An experimental dereferencer. We assume that there can be no pointer bitfields!
@memoize_cond(CU_PYMOD)
def newDereferencer(ti):
    # Target ti
    try:
        tti = ti.getTargetType()
    except:
        return None
    #print('+++ti', ti, ti.size, ti.elements, ti.codetype)
    #print('+++ti', ti, ti.size, tti.size, tti.elements, tti.codetype)
    codetype = tti.codetype
    reader = None
    if (codetype == TYPE_CODE_INT):
        reader = ti_intReader(tti)
    elif (codetype in TYPE_CODE_SU):
        # Struct/Union
        def suReader(addr):
            return StructResult(ti.stype, addr)
        reader = suReader
    #elif (codetype == TYPE_CODE_PTR):
        ##print "getReader", id(self), self
        ## Pointer
        #if (ptrlev == None):
            #ptrlev = tti.ptrlev
        #return ptrReader(self, ptrlev)
    elif (codetype == TYPE_CODE_ENUM):     # TYPE_CODE_ENUM
        reader = ti_enumReader(ti)
    else:
        return None
        raise TypeError("don't know how to read codetype "+str(codetype))

    # Attache basetype size to the reader
    reader.basesize = tti.size
    return reader

# Enums representation - integers plus some data
class tEnum(long):
    def __new__(cls, l, einfo):
        return long.__new__(cls, l)
    def __init__(self, l, einfo):
        self.einfo = einfo
    def __repr__(self):
        return self.einfo.getnam(self)




class SmartList(list):
    def __new__(cls, l = [], addr = None):
        return list.__new__(cls, l)
    def __init__(self, l = [], addr = None):
        list.__init__(self, l)
        self.addr = addr



# Print the object delegating all work to GDB. At this moment can do this
# for StructResult only

def printObject(obj):
    if (isinstance(obj, StructResult)):
        cmd = "p *(%s *)0x%x" %(obj.PYT_symbol, long(obj))
        print (cmd)
        s = exec_gdb_command(cmd)
        # replace the 1st line with something moe useful
        first, rest = s.split("\n", 1)
        print ("%s 0x%x {" %(obj.PYT_symbol, long(obj)))
        print (rest)
    else:
        raise TypeError





#    ======= Arrays Without Dimension =============
#
#  In some cases we have declarations like
#  struct AAA *ptr[];
#
# unsigned long __per_cpu_offset[0];

class intDimensionlessArray(long):
    def __new__(cls, addr, isize, signed):
        return long.__new__(cls, addr)
    def __init__(self, addr, isize, signed):
        self.isize = isize
        self.signed = signed
    def __getitem__(self, i):
        addr = long(self) + i * self.isize
        return readIntN(addr, self.isize, self.signed)
    def __repr__(self):
        return "<intDimensionlessArray addr=0x%x, sz=%d, signed=%d>" %\
            (long(self), self.isize, self.signed)


class tPtrDimensionlessArray(object):
    def __init__(self, ptype, addr):
        self.ptype = ptype
        self.addr = addr
        self.size = pointersize
    def __getitem__(self, key):
        addr = readPtr(self.addr + pointersize * key)
        return tPtr(addr, self.ptype)




# We cannot subclass from ArtStructInfo as signature is different

def sdef2ArtSU(sdef):
    sname, finfo = parseSUDef(sdef)
    uas = ArtStructInfo(sname)
    uas.__init__(sname)
    for ftype, fn in finfo:
        #print ftype, fn
        try:
            ti = TypeInfo(ftype)
        except crash.error:
            #print "  Cannot get typeinfo for %s" % ftype
            sp = ftype.find('*')
            if (sp != -1):
                btype = ftype[:sp].strip()
                #print "    btype=<%s>" % btype
                # Check whether StructInfo exists for btype
                #si = getStructInfo(btype)
                #print si
                # Yes, replace the name with something existing and try again
                newftype = ftype.replace(btype, "struct list_head", 1)
                #print "     new ftype=<%s>" % newftype
                ti = TypeInfo(newftype)
                # Force the evaluation of lazy eval attributes
                ti.tcodetype
                ti.elements
                ti.stype = btype
                #ti.dump()

        vi = VarInfo(fn)
        vi.ti = ti
        vi.offset = uas.PYT_size
        vi.bitoffset = vi.offset * 8

        SUInfo.append(uas, fn, vi)
        # Adjust the size
        uas.PYT_size += vi.size
        uas.size = uas.PYT_size
    return uas


#exec_crash_command = new_exec_crash_command
import crash
from crash import  mem2long, FD_ISSET, readPtr, readmem
readIntN = crash.readInt

