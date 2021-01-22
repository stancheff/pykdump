# -*- coding: utf-8 -*-
#
# High-level subroutines intended for developers of applications
# You do not need ti import this module yourself - all needed objects
# are imported via pykdump.API
#
#  Logical categories are grouped by headers using ~~~~~~ symbols
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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Specify what is imported when we do 'from highlevel *'  - it is easier
# to do this here than in pykdump.API
#
# To avoid typing each name in quotes, we parse a multiline string
# converting it to the needed form
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all = '''
     TypeInfo, SUInfo, ArtStructInfo, EnumInfo,
     type_length,

     pointersize, PTR_SIZE,
     INT_MASK, INT_SIZE, BITS_PER_INT, INT_MAX, uInt,
     LONG_MASK, LONG_SIZE, BITS_PER_LONG, LONG_MAX, uLong,
     ALIGN,

     readU8, readU16, readU32, readS32,
     readU64, readS64, readInt, readPtr,
     readInt, readUInt, readLong, readULong,
     readSymbol, readSU,

     sLong, le32_to_cpu, cpu_to_le32, le16_to_cpu,
     unsigned16, unsigned32, unsigned64,

     setListMaxel,

     readList, readBadList, getListSize, readListByHead,  list_for_each_entry,
     ListHead, LH_isempty, hlist_for_each_entry,
     readSUArray, readSUListFromHead, readStructNext,
     getStructInfo, getFullBuckets, getFullBucketsH, FD_ISSET,
     struct_exists, symbol_exists,
     Addr, Deref, tPtr, SmartString, StructResult,
     sym2addr, addr2sym, sym2alladdr, addr2mod,
     get_pathname, is_task_active, pid_to_task, task_to_pid,
     readmem, uvtop, phys_to_page, readProcessMem, set_readmem_task,
     struct_size, union_size, member_offset, member_size, enumerator_value,
     getSizeOf, container_of, whatis, funcargs, printObject,
     exec_gdb_command, exec_crash_command, exec_crash_command_bg,
     exec_crash_command_bg2, exec_command,
     structSetAttr, structSetProcAttr, AttrSetter,
     getCurrentModule, registerObjAttrHandler, registerModuleAttr,

     atomic_t, SuppressCrashErrors
'''

__all__ = [o.strip(',') for o in __all.split()]

import sys, select, os, time, inspect

from .Generic import (Bunch, patch_default_kw)
from .lowlevel import *
from .vmcorearch import sys_info
from .logging import PyLog

pylog = PyLog()

# =============================================================
#
#           ======= defaults =======
#
# =============================================================

# the default max number of elements returned from list traversal
_MAXEL = 10000

import crash
crash.default_timeout=120

# =============================================================
#   Values specific for this vmcore arch, such as integer sizes
# =============================================================
pointersize = type_length("void *")
__intsize = type_length("int")
__longsize = type_length("long int")

sys_info.pointersize = pointersize
sys_info.pointermask = 2**(pointersize*8)-1

# As we cannnot analyze 32-bit dump with a 32-bit crash, Python
# is built for the same arch. So on Python 2, 'int matches' C-int size
if (pointersize == 4):
    PTR_SIZE = 4
elif (pointersize == 8):
    PTR_SIZE = 8
else:
    raise TypeError("Cannot find pointer size on this arch")


def ALIGN(addr, align):
    return (int(addr) + align-1)&(~(align-1))

# Generic conversions
def unsigned16(l):
    return l & 0xffff

def unsigned32(l):
    return l & 0xffffffff

def unsigned64(l):
    return l & 0xffffffffffffffff



# =============================================================
#
#           ======= read functions =======
#
# =============================================================
#
# ~~~~~~~~~ integer readers ~~~~~~~~~~
def readU8(addr):
    s = readmem(addr, 1)
    return mem2long(s)


def readU16(addr):
    s = readmem(addr, 2)
    return mem2long(s)

def readU32(addr):
    s = readmem(addr, 4)
    return mem2long(s)

def readS32(addr):
    s = readmem(addr, 4)
    return mem2long(s, signed = True)

def readU64(addr):
    s = readmem(addr, 8)
    return mem2long(s)

def readS64(addr):
    s = readmem(addr, 8)
    return mem2long(s, signed = True)

if (__intsize == 4):
    readInt = readS32
    readUInt = readU32
    uInt =  unsigned32
    INT_MASK = 0xffffffff
    INT_SIZE = 4
    BITS_PER_INT = 32
elif (__intsize == 8):
    readInt = readS64
    readUInt = readU64
    uInt =  unsigned64
    INT_MASK = 0xffffffffffffffff
    INT_SIZE = 8
    BITS_PER_INT = 64
else:
    raise TypeError("Cannot find int size on this arch")

if (__longsize == 4):
    readLong = readS32
    readULong = readU32
    uLong = unsigned32
    LONG_MASK = 0xffffffff
    LONG_SIZE = 4
    BITS_PER_LONG = 32
elif (__longsize == 8):
    readLong = readS64
    readULong = readU64
    uLong = unsigned64
    LONG_MASK = 0xffffffffffffffff
    LONG_SIZE = 8
    BITS_PER_LONG = 64
else:
    raise TypeError("Cannot find long size on this arch")

INT_MAX = ~0&(INT_MASK)>>1
LONG_MAX = ~0&(LONG_MASK)>>1

# ~~~~~~~~~~ Subroutine to change default value of 'maxel' ~~~~~~~~~~

def setListMaxel(newval):
    patch_default_kw(getCurrentModule(), 'maxel', newval)

def warn_maxel(maxel):
    funclist = [fr.function for fr in inspect.stack()[2:] if
                fr.function != '<module>'  ]
    funcstr = " <- ".join(funclist)
    pylog.warning(f"We have reached the limit while reading a list"
                  f" {maxel=}\n\t\tfrom {funcstr}")


# ~~~~~~~~~~ SU readers ~~~~~~~~~~

# addr should be numeric here
def readSU(symbol, addr):
    return StructResult(symbol, addr)

#     ======= return a Generator to iterate through SU array
def __SUArray(sname, addr, *, maxel = _MAXEL):
    size = getSizeOf(sname)
    addr -= size
    while (maxel):
        addr += size
        yield readSU(sname, addr)
        maxel -= 1
    return

# Read an array of structs/unions given the structname, start and dimension
def readSUArray(suname, startaddr, dim=0):
    # If dim==0, return a Generator
    if (dim == 0):
        return __SUArray(suname, startaddr)
    sz = struct_size(suname)
    # Now create an array of StructResult.
    out = []
    for i in range(0,dim):
        out.append(StructResult(suname, startaddr+i*sz))
    return out


# ~~~~~~~~ physical memory readers ~~~~~~~~~~

#          ======== read a chunk of physical memory ===
def readProcessMem(taskaddr, uvaddr, size):
    # We cannot read through the page boundary
    out = []
    while (size > 0):
        paddr = uvtop(taskaddr, uvaddr)

        cnt = crash.PAGESIZE - crash.PAGEOFFSET(uvaddr)
        if (cnt > size):
            cnt = size

        out.append(readmem(paddr, cnt, crash.PHYSADDR))
        uvaddr += cnt
        size -= cnt
    return b''.join(out)

# ~~~~~~~~~~~~~~ list readers ~~~~~~~~~~~

# Emulate list_for_each + list_entry
# We assume that 'struct mystruct' contains a field with
# the name 'listfieldname'
# Finally, by default we do not include the address f the head itself
#
# If we pass a string as 'headaddr', this is the symbol pointing
# to structure itself, not its listhead member
def readSUListFromHead(headaddr, listfieldname, mystruct, *,
                       maxel = _MAXEL,
                       inchead = False, warn = True):
    msi = getStructInfo(mystruct)
    offset = msi[listfieldname].offset
    if (type(headaddr) == type("")):
        headaddr = sym2addr(headaddr) + offset
    out = []
    for p in readList(headaddr, 0, maxel=maxel+1, inchead=inchead,
                      warn=warn):
        out.append(readSU(mystruct, p - offset))
    if (len(out) > maxel):
        del out[-1]
        if (warn):
            warn_maxel(maxel)

    return out

# Read a list of structures connected via direct next pointer, not
# an embedded listhead. 'shead' is either a structure or tPtr pointer
# to structure

def readStructNext(shead, nextname, *, maxel=_MAXEL, inchead = True):
    if (not isinstance(shead, StructResult)):
        # This should be tPtr
        if (shead == 0):
            return []
        shead = Deref(shead)
    stype = shead.PYT_symbol
    offset = shead.PYT_sinfo[nextname].offset
    out = []
    for p in readList(Addr(shead), offset, maxel=maxel, inchead=inchead):
        out.append(readSU(stype, p))
    return out

# Walk list_Head and return the full list (or till maxel)
#
# Note: By default we do not include the 'start' address.
# This emulates the behavior of list_for_each_entry kernel macro.
# In most cases the head is standalone and other list_heads are embedded
# in parent structures.

def readListByHead(start, offset=0, *, maxel = _MAXEL, warn = True):
    return readList(start, offset, maxel=maxel, inchead=False, warn=warn)

# An alias
list_for_each_entry = readListByHead

# Another attempt to make working with listheads easily.
# We assume that listhead here is declared outside any specific structure,
# e.g.
# struct list_head modules;
#
# We can do the following:
# ListHead(addr) - will return a list of all list_head objects, excluding
# the head itself.
#
# ListHead(addr, "struct module").list - will return a list of
# "struct module" results, linked by the embedded struct list_head list;
#

class ListHead(list):
    def __new__(cls, lhaddr, sname = None, *, maxel = _MAXEL, warn = True):
        return list.__new__(cls)
    def __init__(self, lhaddr, sname = None, *,  maxel = _MAXEL, warn = True):
        self.sname = sname
        self.warn = warn
        count = 0
        next = lhaddr
        while (count < maxel+1):
            next = readPtr(next)
            if (next == 0 or next == lhaddr):
                break
            if (sname):
                self.append(next)
            else:
                # A special case - return list_head object, not just address
                self.append(readSU("struct list_head", next))
            count += 1
        if (count > maxel):
            del self[-1]
            if (self.warn):
                warn_maxel(maxel)

    def __getattr__(self, fname):
        off = member_offset(self.sname, fname)
        if (off == -1):
            raise KeyError("<%s> does not have a field <%s>" % \
                  (self.sname, fname))
        return [readSU(self.sname, a-off) for a in self]

# Check whether LH is empty - either NULL pointer or no elements
def LH_isempty(lh):
    return (lh and Addr(lh) == lh.next)


# readList returns the addresses of all linked structures, including
# the start address. If the start address is 0, it returns an empty list

# For list declared using LIST_HEAD, the empty list is when both next and prev
# of LIST_HEAD point to its own address

def readList(start, offset=0, *, maxel = _MAXEL, inchead = True, warn = True):
    start = int(start)     # equivalent to (void *) cast
    if (start == 0):
        return []
    if (inchead):
        count = 1
        out = [start]
    else:
        out = []
        count = 0
    next = start
    # Detect list corruption when next refers to one of previous elements
    known = set()
    while (count < maxel+1):
        # If we get an error while reading lists, report it but return what we
        # have already collected anyway
        try:
            next = readPtr(next + offset)
        except crash.error as val:
            print (val)
            break
        if (next == 0 or next == start):
            break
        if (next in known):
            pylog.error("Circular dependency in list")
            break
        known.add(next)
        out.append(next)
        count += 1
    if (count > maxel):
        del out[-1]
        if (warn):
            warn_maxel(maxel)

    return out

# The same as readList, but in case we are interested
# in partial lists even when there are low-level errors
# Returns (partiallist, error/None)
def readBadList(start, offset=0, *, maxel = _MAXEL, inchead = True):
    start = int(start)     # equivalent to (void *) cast
    # A dictionary used to detect duplicates
    ha = {}
    if (start == 0):
        return []
    if (inchead):
        count = 1
        out = [start]
        ha[start] = 1
    else:
        out = []
        count = 0
    next = start
    while (count < maxel):
        try:
            next = readPtr(next + offset)
        except crash.error as err:
            return (out, err)
        if (next == 0 or next == start):
            break
        elif (next in ha):
            err = "Duplicate entry"
            return (out, err)
        ha[next] = 1
        out.append(next)
        count += 1
    if (count == maxel):
        warn_maxel(maxel)

    return (out, None)

#     ======= get list size for LIST_HEAD =====
def getListSize(addr, offset, maxel):
    if (addr == 0):
        return 0


    count = 0                           # We don't include list_head

    next = addr
    while (count < maxel):
        next = readPtr(next + offset)
        if (next == 0 or next == addr):
            break
        count += 1
    return count

#  ~~~~~~~~ hash-arrays ~~~~~~~~~~~~~

# Get a list of non-empty bucket addrs (ppointers) from a hashtable.
# A hashtable here is is an array of buckets, each one is a structure
# with a pointer to next structure. On 2.6 'struct hlist_head' is used
# but we don't depend on that, we just need to know the offset of the
# 'chain' (a.k.a. 'next') in our structure
#
# start - address of the 1st hlist_head
# bsize - the size of a structure embedding hlist_head
# items - a dimension of hash-array
# chain_off - an offset of 'hlist_head' in a bucket
def getFullBuckets(start, bsize, items, chain_off=0):
    chain_sz = pointersize
    m = readmem(start, bsize * items)
    buckets = []
    for i in xrange(0, items):
       chain_s = i*bsize + chain_off
       s = m[chain_s:chain_s+chain_sz]
       bucket = mem2long(s)
       #bucket = mem2long(m, chain_sz, chain_s, False)
       if (bucket != 0):
           #print i
           buckets.append(bucket)
    del m
    return buckets

# Traverse hlist_node hash-lists. E.g.
# hlist_for_each_entry("struct xfrm_policy", table, "bydst")

def hlist_for_each_entry(emtype, head, member):
    pos = head.first                    # struct hlist_node *first
    si = SUInfo(emtype)
    offset = si[member].offset
    while (pos):
        yield readSU(emtype, int(pos) - offset)
        pos = pos.next

    return


# ~~~~~~~~~~~~ Executing Commands ~~~~~~~~~~~~~~~

# Exec either a standard crash command, or a epython command
def exec_command(cmdline):
    argv = cmdline.split()
    #print "argv", argv, "cmds=",  crash.get_epython_cmds()
    if (argv[0] in crash.get_epython_cmds()):
        # This is a epython command. In principle, we should parse using
        # shell-like syntax (i.e. using shlex), but this is probably an overkill
        crash.exec_epython_command(*argv)
    else:
        print(crash.exec_crash_command(cmdline))


# Exec in the background - use this for reliable timeouts
import signal
def exec_crash_command_bg(cmd, timeout = None):
    if (not timeout):
        timeout = crash.default_timeout
    #print("Timeout=", timeout)
    # Flush stdout before exec in background
    sys.stdout.flush()
    #print("-> {}".format(cmd))
    fileno, pid = exec_crash_command_bg2(cmd)
    #signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
    out = []
    endtime = time.time() + timeout
    timeleft = timeout
    # Read until timeout
    timeouted = False
    selerror = False
    while(True):
        try:
            rl, wl, xl = select.select([fileno], [], [], timeleft)
        except select.error as val:
            selerror = val
            break
        timeleft = endtime - time.time()
        if (not rl or timeleft <= 0):
            timeouted = True
            break
        s = os.read(fileno, 82)    # Line-oriented
        if (not s):
            break
        out.append(s.decode("utf-8"))

    os.close(fileno)
    os.kill(pid, 9)
    cpid, status = os.wait()
    # Unblock SIGINT handler
    #signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGINT})
    #print("  {} <-- ".format(cmd))
    if (timeouted):
        badmsg = "<{}> failed to complete within the timeout period of {}s".\
            format(cmd, timeout)
    elif (selerror):
         badmsg = "<{}> interrupted after {}s {}".format(cmd, timeout, selerror)
    elif (status):
        if (os.WIFEXITED(status)):
            ecode = os.WEXITSTATUS(status)
            if (ecode):
                smsg = ("ExitCode=%d" % ecode)
        elif (os.WIFSIGNALED(status)):
            if (os.WCOREDUMP(status)):
                smsg = "Core Dumped"
            else:
                smsg = "Signal {}".format(os.WTERMSIG(status))
        badmsg = "<{}> exited abnormally, {}".format(cmd, smsg)
    else:
        badmsg = ""
    if (timeouted):
        pylog.timeout(badmsg)
    elif (badmsg):
        pylog.warning(badmsg)
    return("".join(out))

# ~~~~~~~~~~ getting info about struct sizes, offsets etc. ~~~~
#   The same functions can be used for unions

#
#
#  -- emulating low-level functions that can be later replaced by
#  Python extension to crash
#
#
# {"symbol_exists",  py_crash_symbol_exists, METH_VARARGS},
# {"struct_size",  py_crash_struct_size, METH_VARARGS},
# {"union_size",  py_crash_union_size, METH_VARARGS},
# {"member_offset",  py_crash_member_offset, METH_VARARGS},
# {"member_size",  py_crash_member_size, METH_VARARGS},
# {"get_symbol_type",  py_crash_get_symbol_type, METH_VARARGS},


# Return -1 if the struct is unknown. At this moment this function
# works for any type, not just for structs
# We cache the results (even negative ones). The cache should be invalidated

@memoize_typeinfo
def struct_size(sname):
    try:
        si = TypeInfo(sname)
        sz = si.size
    except:
        sz = -1
    return sz

def struct_exists(sname):
    if (struct_size(sname) == -1):
        return False
    else:
        return True

@memoize_typeinfo
def member_size(sname, fname):
    #print "++member_size", sname, fname
    sz = -1
    try:
        ti = getStructInfo(sname)[fname].ti
        sz = ti.size * ti.elements
    except KeyError:
        pass
    return sz


# Find a member offset. If field name contains a dot, we do our
# best trying to find its offset checking intermediate structures as
# needed

@memoize_typeinfo
def member_offset(sname, fname):
    try:
        si = getStructInfo(sname)
        chain = fname.split('.')
        lc = len(chain)
        if (lc == 1):
            return si[fname].offset
        else:
            # We have dots in field name, we can handle this as long
            # as the chain consists of union/structs, only the last field can
            # be of different type
            #print "\t", chain
            offset = 0
            for i, f in enumerate(chain):
                vi = si[f]
                ti = vi.ti
                offset += vi.offset
                #print f, ti.codetype, ti.stype, vi.offset
                # If this is the last element, there is no need to continue
                if (i == lc-1):
                    break
                if (not ti.codetype in TYPE_CODE_SU):
                    return -1
                si = getStructInfo(ti.stype)
            return offset                   # Not done yet
    except:
        return -1


# A cached version
__cache_symbolexists = {}
def symbol_exists(sym):
    try:
        return  __cache_symbolexists[sym]
    except:
        rc = noncached_symbol_exists(sym)
        __cache_symbolexists[sym] = rc
        return rc


# Aliases
union_size = struct_size

# ~~~~~~~~~~ Convenience functions ~~~~~~~~~~~~
#     ======= read from global according to its type  =========
def readSymbol(symbol):
    vi = whatis(symbol)
    return vi.reader(vi.addr)


# Get sizeof(type)
def getSizeOf(vtype):
    return struct_size(vtype)

# Similar to C-macro in kernel sources - container of a field
def container_of(ptr, ctype, member):
    offset = member_offset(ctype, member)
    return readSU(ctype, int(ptr) - offset)

@memoize_typeinfo
def getStructInfo(stype):
    si = SUInfo(stype)
    return si


__whatis_cache = {}

def whatis(symbol):
    try:
        return __whatis_cache[symbol]
    except KeyError:
        pass
    try:
        e = crash.gdb_whatis(symbol)
    except crash.error:
        raise TypeError("There's no symbol <%s>" % symbol)

    # Return Varinfo
    vi = VarInfo(e["fname"])
    ti = TypeInfo(e)
    vi.ti = ti
    vi.addr = sym2addr(symbol)

    # This is for backwards compatibility only, will be obsoleted
    vi.ctype = ti.stype
    __whatis_cache[symbol] = vi
    return vi

# get types of function arguments (as an list of strings)
# If there is no data or if this is not a function, return None
def funcargs(symbol):
    try:
        ti = whatis(symbol).ti
    except TypeError:
        return None
    if (ti.stype != '(func)'):
        return None
    return [a.typestr() for a in ti.prototype[1:]]

# Some kernels use a simple integer and some use atomic_t wrapper
# This subroutine returns a.counter if argument is atomic_t or
# just argument without any changes otherwise
def atomic_t(o):
    try:
        return o.counter
    except AttributeError:
        return o

# ---------- A context manager to disable crash/gdb error messages -----

class SuppressCrashErrors():
    def __init__(self, outfile = "/dev/null"):
        self.newf = outfile
    def __enter__(self):
        self.oldf = crash.crash_set_error(self.newf)
        return self.oldf
    def __exit__(self, exc_type, exc_value, traceback):
        if (self.oldf != self.newf):
            crash.crash_set_error(self.oldf)


# Replacing Python versions by bindings to C-subroutines
from crash import sym2addr, addr2sym, sym2alladdr, addr2mod
from crash import  mem2long, FD_ISSET
from crash import enumerator_value
from crash import get_pathname, is_task_active, pid_to_task, task_to_pid
def exec_gdb_command(cmd):
    return crash.get_GDB_output(cmd).replace('\r', '')

noncached_symbol_exists = crash.symbol_exists
exec_crash_command = crash.exec_crash_command
exec_crash_command_bg2 = crash.exec_crash_command_bg2
exec_gdb_command = crash.get_GDB_output
getFullBuckets = crash.getFullBuckets
getFullBucketsH = crash.getFullBucketsH
readPtr = crash.readPtr
readIntN = crash.readInt
sLong = crash.sLong
le32_to_cpu = crash.le32_to_cpu
le16_to_cpu = crash.le16_to_cpu
cpu_to_le32 = crash.cpu_to_le32
uvtop = crash.uvtop
phys_to_page = crash.phys_to_page
getListSize = crash.getListSize
# For some reason the next line runs slower than GDB version
#GDB_sizeof = crash.struct_size
readmem = crash.readmem
set_readmem_task = crash.set_readmem_task
nc_member_offset = crash.member_offset
