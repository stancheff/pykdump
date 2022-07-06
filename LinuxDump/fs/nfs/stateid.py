#!/usr/bin/env/python
from __future__ import print_function

__author__ = "Scott Mayhew"
__version__ = "0.1"

from pykdump.API import *
from crccheck.crc import CrcX25
import sys

# enum from include/linux/nfs4.h
__NFS_DELEGATION_TYPE='''
enum {
	NFS4_INVALID_STATEID_TYPE = 0,
	NFS4_SPECIAL_STATEID_TYPE,
	NFS4_OPEN_STATEID_TYPE,
	NFS4_LOCK_STATEID_TYPE,
	NFS4_DELEGATION_STATEID_TYPE,
	NFS4_LAYOUT_STATEID_TYPE,
	NFS4_PNFS_DS_STATEID_TYPE,
	NFS4_REVOKED_STATEID_TYPE
};
'''
NFS_DELEGATION_TYPE=CEnum(__NFS_DELEGATION_TYPE)

class nfs4_stateid():
    def __init__(self, s):
        # pykdump doesn't like the anonymous union in nfs4_stateid
        # so we have to retrieve the struct member fields manually
        _info = getStructInfo("nfs4_stateid")
        _data_off = _info["data"].offset
        _data_size = _info["data"].size
        # the 'type' field was added in commit 93b717fd81bf ("NFSv4: Label stateids with the type")
        try:
            _type_off = _info["type"].offset
            _has_type = True
        except KeyError:
            _has_type = False
        self._stateid = readSU("nfs4_stateid", s)
        if _has_type:
            self._type = readU32(Addr(self._stateid) + _type_off)
        else:
            self._type = sys.maxsize
        self._data = readmem(Addr(self._stateid) + _data_off, _data_size)
        self.addr = Deref(self._stateid)
        self.type = self._get_type(self._type)
        self.value = ":".join(["%02x" % c for c in self._data])
        self.hash = CrcX25.calc(self._data)

    def _get_type(self, t):
        deleg_type = {
            NFS_DELEGATION_TYPE.NFS4_INVALID_STATEID_TYPE: "NFS4_INVALID_STATEID_TYPE",
            NFS_DELEGATION_TYPE.NFS4_SPECIAL_STATEID_TYPE: "NFS4_SPECIAL_STATEID_TYPE",
            NFS_DELEGATION_TYPE.NFS4_OPEN_STATEID_TYPE: "NFS4_OPEN_STATEID_TYPE",
            NFS_DELEGATION_TYPE.NFS4_LOCK_STATEID_TYPE: "NFS4_LOCK_STATEID_TYPE",
            NFS_DELEGATION_TYPE.NFS4_DELEGATION_STATEID_TYPE: "NFS4_DELEGATION_STATEID_TYPE",
            NFS_DELEGATION_TYPE.NFS4_LAYOUT_STATEID_TYPE: "NFS4_LAYOUT_STATEID_TYPE",
            NFS_DELEGATION_TYPE.NFS4_PNFS_DS_STATEID_TYPE: "NFS4_PNFS_DS_STATEID_TYPE",
            NFS_DELEGATION_TYPE.NFS4_REVOKED_STATEID_TYPE: "NFS4_REVOKED_STATEID_TYPE",
            sys.maxsize: "unknown"
        }
        for type in deleg_type:
            if type == t:
                break
        return deleg_type[type]

    def __str__(self):
        return ("(struct nfs4_stateid *) {self.addr:#x} type = {self.type} "
                "value = {self.value} hash = {self.hash:#06x}").format(self=self)

if __name__ == '__main__':
    print(str(nfs4_stateid(int(sys.argv[1], 0))))
