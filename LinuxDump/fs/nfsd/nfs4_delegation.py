#!/usr/bin/env/python
from __future__ import print_function

__author__ = "Scott Mayhew"
__version__ = "0.1"

from pykdump.API import *
from LinuxDump.fs.nfsd.nfs4_stid import nfs4_stid

__DELEGATION_TYPE='''
enum open_delegation_type4 {
        NFS4_OPEN_DELEGATE_NONE = 0,
        NFS4_OPEN_DELEGATE_READ = 1,
        NFS4_OPEN_DELEGATE_WRITE = 2,
        NFS4_OPEN_DELEGATE_NONE_EXT = 3
};
'''
DELEGATION_TYPE=CEnum(__DELEGATION_TYPE)

# TODO: add open & delegation state
class nfs4_delegation():
    def __init__(self, d, verbose=False):
        self._d = readSU("struct nfs4_delegation", d)
        self._type = self._d.dl_type
        self.addr = Deref(self._d)
        self.type = self._get_type(self._type)
        self.stid = None
        if verbose:
            self.stid = nfs4_stid(self._d.dl_stid)

    def _get_type(self, t):
        delegation_types = {
            DELEGATION_TYPE.NFS4_OPEN_DELEGATE_NONE: "NFS4_OPEN_DELEGATE_NONE",
            DELEGATION_TYPE.NFS4_OPEN_DELEGATE_READ: "NFS4_OPEN_DELEGATE_READ",
            DELEGATION_TYPE.NFS4_OPEN_DELEGATE_WRITE: "NFS4_OPEN_DELEGATE_WRITE",
            DELEGATION_TYPE.NFS4_OPEN_DELEGATE_NONE_EXT: "NFS4_OPEN_DELEGATE_NONE_EXT"
        }
        return delegation_types[t]

    def __str__(self):
        s = "(struct nfs4_delegation *) {self.addr:#x} type = " "{self.type}".format(self=self)
        if self.stid:
            s += "\n- {}".format(self.stid)
        return s

def auto_int(x):
    return int(x, 0)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("d", metavar="DELEGATION", type=auto_int,
                        help="address of struct nfs4_delegation")
    parser.add_argument("-v", "--verbose", default = 0,
                        action="store_true",
                        help="verbose output (include stateids)")
    args = parser.parse_args()
    d = nfs4_delegation(args.d, args.verbose)
    print(str(d))
