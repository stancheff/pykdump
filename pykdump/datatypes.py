# -*- coding: utf-8 -*-
#
#  Type mapping between C/GDB and Python. In this module we deal with
#  representing symbolic information about C structures and varaiables
#
#  Low-level data access is implemented in another module, 'lowlevel'
#
#
# --------------------------------------------------------------------
# (C) Copyright 2006-2021 Hewlett Packard Enterprise Development LP
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

from functools import reduce
import inspect

from .memocaches import *
from .Generic import LazyEval

import crash

# Add all GDB-registered code types
for n in dir(crash):
    if (n.find('TYPE_CODE') == 0):
        globals()[n] = getattr(crash, n)
TYPE_CODE_SU = (crash.TYPE_CODE_STRUCT, crash.TYPE_CODE_UNION)
globals()['TYPE_CODE_SU'] =  TYPE_CODE_SU


@memoize_typeinfo
def gdb_typeinfo(sname):
    return crash.gdb_typeinfo(sname)

# Length of type, where type can be struct/unions/pointer/arrays etc.
# This returns just the "base type length" not caring whether this is
# array or not

@memoize_typeinfo
def type_length(tname):
    try:
        return gdb_typeinfo(tname)["typelength"]
    except:
        # Can be KeyError or crash.error
        return -1

# INTTYPES = ('char', 'short', 'int', 'long', 'signed', 'unsigned',
#             '__u8', '__u16', '__u32', '__u64',
#              'u8', 'u16', 'u32', 'u64',
#             )
# EXTRASPECS = ('static', 'const', 'volatile')


# TypeInfo objects represent information about type:

# 1. basetype or 'target type' - a symbolic name after removing * and
# arrays. For example, for 'struct test **a[2]' this will be 'struct test'.
#
# 2. type of basetype: integer/float/struct/union/func etc.
#    for integers: signed/unsigned and size
#
# 3. Numbers of stars (ptrlev) or None
#
# 4. Dimensions as a list or None
#
# 5. A special case is needed for anonymous embedded structs/unions.
#    We need to store information about their contents and assign some
#    fake name to them, to be able to retrieve this information later


# The constructor iis usually called with with string (type name). In cases
# when typename is not known yet (e.g. in 'whatis'), we can specify
# output of gdb_typeinfo()
# Possible cases:
# (a) we call this subroutine from whatis(symbol). In that case, we know
#     variable name and get gdb_typeinfo
# (b) function prototypes, recursively from TypeInfo (used for printing)
# (c) update_SUI() - in this case we know embedding struct name

class TypeInfo(object):
    def __init__(self, info):
        if (isinstance(info, str)):
            e = gdb_typeinfo(info)
            stype = info            # Requested typename
        else:
            e = info
            stype = None            # Unknown yet


        # Dummy/default values, real initialization done later
        self.stype = stype      # Will be set to real thing later
        self.size = -1
        self.dims = None        # for arrays
        self.ptrlev = None      # number of * in pointers
        self.typedef = None     # used for typedefs
        # For integer types
        self.integertype = None # used for integers
        self.fake_SU = False    # Does this file refer to a fake SU?

        # Compute values based on gdb_typeinfo

        # These fields are always set
        t_size = e["typelength"]
        self.codetype = e["codetype"]

        # For embedded structs without name, we generate a fake name
        # For typedefs, we change name to real type, e.g. for "ulong"
        # "typedef unsigned long ulong" -> "unsigned long"
        self.stype, fake = e_to_tagname(e)
        self.size = t_size

        if ("dims" in e):
            self.dims = e["dims"]

        if ("stars" in e):
            self.ptrlev = e["stars"]

        if ("uint" in e):
            self.uint = e["uint"]
        else:
            self.uint = None

        if ("typedef" in e):
            self.typedef = e["typedef"]        # The initial type

        if ("ptrbasetype" in e):
            self.ptrbasetype = e["ptrbasetype"] # The base type of pointer

        # This object has 'body' - it is a struct/union
        if ("body" in e):
            # Create SUInfo object for this SU
            tag, fake  = e_to_tagname(e)
            ff = SUInfo(tag, e)
            ff.PYT_fake = fake
            self.fake_SU = fake
        # (b) function prototypes
        elif ("prototype" in e):
            prototype = self.prototype = []
            for ee in e["prototype"]:
                fname = ee["fname"]
                ti = TypeInfo(ee)
                prototype.append(ti)

    def getElements(self):
        if (self.dims):
            elements = reduce(lambda x, y: x*y, self.dims)
        else:
            elements = 1
        return elements

    # Get target info for arrays/pointers - i.e. the same type
    # but without ptrlev or dims
    def getTargetType(self):
        return TypeInfo(self.stype)

    def getTargetCodeType(self):
        return self.getTargetType().codetype

    def fullname(self):
        out = []
        if (self.ptrlev != None):
            out.append('*' * self.ptrlev)

        # Here we will insert the varname
        pref = ''.join(out)

        out = []
        if (self.dims != None):
            for i in self.dims:
                out.append("[%d]" % i)
        suff = ''.join(out)
        return (self.stype, pref,suff)

    # A string without a terminating ';', suitable for function args description
    def typestr(self):
        stype, pref, suff = self.fullname()
        if(pref == '' and suff == ''):
            return stype
        else:
            rc = "{} {}{}".format(stype, pref, suff)
        return rc

    # A full form with embedded structs unstubbed.
    # Terminated by ;, to emulate C-style definition
    def fullstr(self, indent = 0):
        stype, pref, suff = self.fullname()
        rc =  ' ' * indent + "%s %s%s;" % \
            (stype, pref, suff)
        return rc

    # Check whether we need to expand (used for embedded structs/unions)
    # and return either string or None.
    # By default we print a field such as "struct some a" as it is, but for
    # struct without tag we need to expand their definition
    #
    # This is a short version
    def _s_expand(self, indent = 0):
        if (self.fake_SU):
            suinfo = SUInfo(self.stype)
            return suinfo.shortstr(indent=indent)
        else:
            return None
    # And this is the full version
    def _f_expand(self, indent = 0):
        if (self.fake_SU):
            suinfo = SUInfo(self.stype)
            return suinfo.fullstr(indent=indent)
        else:
            return None

    def __repr__(self):
        stype, pref, suff = self.fullname()
        if (stype == "(func)"):
            out = []
            for ati in self.prototype:
                astype, apref, asuff = ati.fullname()
                out.append(("%s %s%s" % (astype, apref, asuff)).strip())
            stype = out[0]
            suff = "(func)(" + ", ".join(out[1:]) + ")"

        out = "TypeInfo <%s %s%s> size=%d" % (stype, pref, suff, self.size)
        return out
    # For debugging purposes
    def dump(self):
        print (" -------Dumping all attrs of TypeInfo %s" % self.stype)
        for na in ('stype', 'size', 'dims', 'ptrlev', 'typedef', 'details'):
            a = getattr(self, na)
            # if (type(a) in (StringType, IntType, NoneType, ListType)):
            #    print ("  fn=%-12s " % n, a)
            print("  {}, {} ".format(na, a))
        print (" -----------------------------------------------")
    elements = LazyEval("elements", getElements)
    tcodetype = LazyEval("tcodetype", getTargetCodeType)


# This is unstubbed struct representation - showing all its fields.
# Each separate field is represented as SFieldInfo and access to fields
# is possible both via attibutes and dictionary
#
# This class is intended for framework internal purposes only.
# Real class that can be used by application developers is SUInfo(), a subclass
# of this one
class _SUInfo(dict):
    def __init__(self, sname):
        self.PYT_fake = False
        #dict.__init__(self, {})

        # These three attributes will not be accessible via dict
        object.__setattr__(self, "PYT_sname", sname)
        # PYT_body is needed for printing mainly. As we can have internal
        # struct/union with empty names and there can be several of them,
        # we cannot rely on name to save info.
        #   As a result, each element is (name, ti)
        object.__setattr__(self, "PYT_body",  []) # For printing only
        #object.__setattr__(self, "PYT_dchains", {}) # Deref chains cache

    def __setitem__(self, name, value):
        dict.__setitem__(self, name, value)
        object.__setattr__(self, name, value)

    # Used by ArtStruct and while processing GDB typeinfo
    def _append(self, name, value):
        # A special case: empty name. We can meet this while
        # adding internal union w/o fname, e.g.
        # union {int a; char *b;}
        self.PYT_body.append((name, value))
        if (name):
            self[name] = value
        else:
            self.__appendAnonymousSU(value)
    # Append an anonymous SU. We add its members to our parent's namespace
    # with appropriate offsets
    def __appendAnonymousSU(self, value):
        ti = value.ti
        #print "name <%s>, value <%s>" % (name, str(value))
        # Anonymous structs/unions can be embedded and multilevel
        if (not ti.codetype in TYPE_CODE_SU):
            raise TypeError("field without a name " + str(value))
        usi = SUInfo(ti.stype)
        #print ti.stype, usi
        if (ti.codetype == TYPE_CODE_UNION):
            for fn, usi_v in usi.PYT_body:
                #print "Adding", fn, usi[fn].ti
                vi = VarInfo(fn)
                vi.ti = usi_v.ti
                vi.addr = 0
                vi.offset = value.offset
                if (fn):
                    self[fn] = vi
                else:
                    self.__appendAnonymousSU(vi)

        elif (ti.codetype == TYPE_CODE_STRUCT):
            for fn, usi_v in usi.PYT_body:
                #print "Adding", fn, usi[fn].ti
                vi = VarInfo(fn)
                vi.ti = usi_v.ti
                vi.addr = 0
                vi.offset = value.offset + usi_v.offset
                if (fn):
                    self[fn] = vi
                else:
                    self.__appendAnonymousSU(vi)

    def shortstr(self, indent = 0):
        inds = ' ' * indent
        out = []
        out.append(inds + self.PYT_sname + " {")
        for fn, vi in self.PYT_body:
            out.append(vi.shortstr(indent=indent+2))
        out.append(inds+ "}")
        return "\n".join(out)
    def fullstr(self, indent = 0):
        inds = ' ' * indent
        out = []
        out.append(inds + self.PYT_sname + " {")
        for fn, vi in self.PYT_body:
            out.append(vi.fullstr(indent+2))
        out.append(inds+ "}")
        return "\n".join(out)

    def __repr__(self):
        return self.fullstr()

    def __str__(self):
        out = ["<SUInfo>"]
        out.append(self.PYT_sname + " {")
        for fn, vi in self.PYT_body:
            out.append(vi.shortstr(indent=2))
        out.append("}")
        return "\n".join(out)
    # Get field names in the same order as present in struct
    def getFnames(self):
        return [e[0] for e in self.PYT_body]

# Instances of this class represent Struct/Union, with memoization
# implemented via metaclass.
# Application developers can use it if they need to inspect struct/union
# definition for a give name. For example, to get information about
# 'struct request' you use SUInfo("struct request").
#
# The 2nd argument is needed for framework itself, normal users should
# not specify it.
class SUInfo(_SUInfo, metaclass = MemoizeSU):
    def __init__(self, sname, gdbinfo = None):
        super().__init__(sname)
        if (not gdbinfo):
            try:
                e = gdb_typeinfo(sname)
            except crash.error:
                raise TypeError("no type " + sname)
            # This can be a typedef to struct
            if (not "body" in e):
                e = gdb_typeinfo(e["basetype"])
        else:
            e = gdbinfo

        f = self
        f.PYT_size = f.size = e["typelength"]
        if (not "body" in e):
            # This is not a struct, bail out
            return
        for idx, ee in enumerate(e["body"]):
            fname = ee["fname"]
            f1 = VarInfo(fname)
            ee['idx'] = idx
            ee['parentname'] = sname
            ti = TypeInfo(ee)
            f1.ti = ti
            f1.bitoffset = ee["bitoffset"]
            f1.offset = f1.bitoffset//8
            if ("bitsize" in ee):
                f1.bitsize = ee["bitsize"]

            f._append(fname, f1)

class ArtStructInfo(SUInfo):
    def __init__(self, sname):
        SUInfo.__init__(self, sname, False)
        self.size = self.PYT_size = 0
    def append(self, ftype, fname):
        vi = VarInfo(fname)
        vi.ti = TypeInfo(ftype)
        vi.offset = self.PYT_size
        vi.bitoffset = vi.offset * 8

        SUInfo._append(self, fname, vi)
        # Adjust the size
        self.PYT_size += vi.size
        self.size = self.PYT_size
    # Inline an already defined SUInfo adding its fields and
    # adjusting their offsets
    def inline(self, si):
        osize = self.PYT_size
        for f, tvi in si.PYT_body:
            vi = copy.copy(tvi)
            vi.offset += osize
            vi.bitoffset += 8 *osize
            SUInfo.append(self, vi.name, vi)

        # Adjust the size
        self.PYT_size += si.PYT_size
        self.size += si.PYT_size

# Representing enums
class EnumInfo(dict):
    def __setitem__(self, name, value):
        dict.__setitem__(self, name, value)
        object.__setattr__(self, name, value)
    def __init__(self, stype):
        dd = {}
        self.stype = stype
        update_EI_fromgdb(self, stype)
    def __str__(self):
        out = []
        for n, v in self._Lst:
            out.append("%s = %d" % (n, v))
        return self.stype + " {" + " ,".join(out) +"}"
    def getnam(self, v1):
        for k,v in self.items():
            if (v == v1):
                return k
        # Unknown value
        return '<{}, bad value {}>'.format(self.stype, v1)


# A global Variable or a struct/union field
# This is TypeInfo plus variable/field name plus addr.
# For SU we add manually two attributes: offset and parent
# Finally, we prepare 'reader' for this variable so reading it will be
# faster

class VarInfo(object):
     def __init__(self,  name = None):
         self.name = name
         self.addr = None
         self.bitsize = None
         self.ti = None
     # A short form for printing inside struct
     def shortstr(self, *, indent = 0, unstub = False):
         stype, pref, suff = self.ti.fullname()
         if (self.bitsize != None):
             suff +=":%d" % self.bitsize
         inds = ' ' * indent
         s_embed = self.ti._s_expand(indent)
         if (s_embed):
             if (self.name):
                 rc = f"{s_embed} {pref}{self.name}{suff};"
             else:
                 rc = f"{s_embed} {pref}{suff};"
         else:
             rc = f"{inds}{stype} {pref}{self.name}{suff};"
         return rc

     # A full form with embedded structs unstubbed
     def fullstr(self, indent = 0):
         stype, pref, suff = self.ti.fullname()
         if (self.bitsize != None):
             suff +=":%d" % self.bitsize

         s_embed = self.ti._f_expand(indent)
         if (s_embed):
             if (self.name):
                 rc = f"{s_embed} {pref}{self.name}{suff};"
             else:
                 rc = f"{s_embed} {pref}{suff};"
         else:
             rc =  ' ' * indent + "%s %s%s%s;" % \
                  (stype, pref, self.name, suff)

         #return rc
         # Add offset etc.
         size = self.ti.size * self.ti.elements
         return rc + ' | off=%d size=%d' % (self.offset, size)

     # Return a dereferencer for this varinfo (PTR type)
     def getDereferencer(self):
         ti = self.ti
         tti = ti.getTargetType()
         nvi = VarInfo()
         nvi.ti = tti
         self.tsize = tti.size
         #print "Creating a dereferencer for", self
         return nvi.getReader()
     # Return a reader for this varinfo
     def getReader(self, ptrlev = None):
         from . import lowlevel as d
         ti = self.ti
         if (self.bitsize != None):
             bitoffset = self.bitoffset - self.offset * 8
         else:
             bitoffset = None

         codetype = ti.codetype
         if (codetype == TYPE_CODE_INT):
             return d.ti_intReader(ti, bitoffset, self.bitsize)
         elif (codetype in TYPE_CODE_SU):
             # Struct/Union
             return d.suReader(self)
         elif (codetype == TYPE_CODE_PTR):
             #print "getReader", id(self), self
             # Pointer
             if (ptrlev == None):
                 ptrlev = ti.ptrlev
             return d.ptrReader(self, ptrlev)
         elif (codetype == TYPE_CODE_ENUM):     # TYPE_CODE_ENUM
             return d.ti_enumReader(ti)
         elif (codetype == TYPE_CODE_BOOL):
             return d.ti_boolReader(ti, bitoffset, self.bitsize)
         else:
             raise TypeError("don't know how to read codetype "+str(codetype))


     def __repr__(self):
         stype, pref, suff = self.ti.fullname()
         if (stype == "(func)"):
             out = []
             for ati in self.ti.prototype:
                 astype, apref, asuff = ati.fullname()
                 out.append(("%s %s%s" % (astype, apref, asuff)).strip())
             stype = out[0]
             suff = "(" + ", ".join(out[1:]) + ")"
         if (self.addr is None):
             # We do not have address until data is read
             addr = ""
         else:
             addr = f" addr={self.addr:#x}"
         out = "{} <{}{} {}{}>{}".format(self.__class__.__name__,
                                         stype, pref,
                                         self.name, suff, addr)
         return out

     def getPtrlev(self):
         return self.ti.ptrlev

     # Backwards compatibility
     def getBaseType(self):
         return self.ti.stype

     def getSize(self):
         return self.ti.size * self.ti.elements

     def getArray(self):
         dims = self.ti.dims
         if (len(dims) == 1):
             return dims[0]
         else:
             return dims

     reader = LazyEval("reader", getReader)
     dereferencer = LazyEval("dereferencer", getDereferencer)

     # Backwards compatibility
     basetype = LazyEval("basetype", getBaseType)
     size = LazyEval("size", getSize)
     array = LazyEval("array", getArray)
     ptrlev = LazyEval("ptrlev", getPtrlev)


# Pseudo-variables - to map pseudo-attrs
class PseudoVarInfo(VarInfo):
    pass


def update_EI_fromgdb(f, sname):
    # If sname does not start from 'enum', we are trying to get
    # a group of unnamed enums using one of its members
    try:
        if (sname.find("enum ") == -1):
            e = crash.gdb_whatis(sname)
            f.stype = "enum"
        else:
            e = gdb_typeinfo(sname)
    except crash.error:
        raise TypeError("cannot find enum <%s>" % sname)
    if (e["codetype"] != TYPE_CODE_ENUM): # TYPE_CODE_ENUM
        raise TypeError("%s is not a enum")
    f._Lst = e["edef"]
    for n, v in f._Lst:
        f[n] = v

# Choose a tag used for caching:
# - if we have typedef, use it
# - otherwise, use the real type
# - if the tag is non-descriptive (e.g. embedded structs), create a fakename
def e_to_tagname(e):
    fake = False
    if ("typedef" in e):
        tag = e["typedef"]        # The initial type
    else:
        tag = e["basetype"]
    # Do we have just one word in basetype? If yes, create a proper tag
    if (tag in {'struct', 'union'}):
        parentname = e.get("parentname")
        fname = e["fname"]
        # anonymous but non-embedded structs do not have bitoffset
        offset =  e.get("bitoffset", 0)//8
        # anonymous structs in a union will have the same offset, so use the
        # index of the element within its parent as well.
        idx = e.get("idx", 0)
        if (fname):
            extra = "{}:{}:{}/{}".format(parentname, offset, idx, fname)
        else:
            extra = "{}:{}:{}".format(parentname, offset, idx)
        tag = "{}->{}".format(extra, tag)
        fake = True

    return tag, fake


# Useful for developers when they add temporarily a debugging print
import pprint
pp = pprint.PrettyPrinter(indent=4)
