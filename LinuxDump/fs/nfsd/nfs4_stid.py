#!/usr/bin/env/python
from __future__ import print_function

__author__ = "Scott Mayhew"
__version__ = "0.1"

from pykdump.API import *
from LinuxDump.fs.nfsd.stateid import stateid
import sys

__STID_TYPES='''
#define NFS4_OPEN_STID 1
#define NFS4_LOCK_STID 2
#define NFS4_DELEG_STID 4
#define NFS4_CLOSED_STID 8
#define NFS4_REVOKED_DELEG_STID 16
#define NFS4_CLOSED_DELEG_STID 32
#define NFS4_LAYOUT_STID 64
'''
STID_TYPES=CDefine(__STID_TYPES)

class nfs4_stid():
    def __init__(self, s):
        self._stid = readSU("struct nfs4_stid", s)
        self._type = self._stid.sc_type
        self.addr = Deref(self._stid)
        self.type = self._get_type(self._type)
        self.stateid = stateid(self._stid.sc_stateid)

    def _get_type(self, t):
        stid_types = { STID_TYPES.NFS4_OPEN_STID: "NFS4_OPEN_STID",
            STID_TYPES.NFS4_LOCK_STID: "NFS4_LOCK_STID",
            STID_TYPES.NFS4_DELEG_STID: "NFS4_DELEG_STID",
            STID_TYPES.NFS4_CLOSED_STID: "NFS4_CLOSED_STID",
            STID_TYPES.NFS4_REVOKED_DELEG_STID: "NFS4_REVOKED_DELEG_STID",
            STID_TYPES.NFS4_CLOSED_DELEG_STID: "NFS4_CLOSED_DELEG_STID",
            STID_TYPES.NFS4_LAYOUT_STID: "NFS4_LAYOUT_STID"
        }
        return stid_types[t]

    def __str__(self):
        return("(struct nfs4_stid *) {self.addr:#x} type = {self.type} "
               "stateid = {self.stateid}".format(self=self))

if __name__ == '__main__':
    print(str(nfs4_stid(int(sys.argv[1], 0))))
