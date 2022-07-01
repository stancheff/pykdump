#!/usr/bin/env/python
from __future__ import print_function

__author__ = "Scott Mayhew"
__version__ = "0.1"

from pykdump.API import *
from LinuxDump.fs.nfsd.nfs4_stid import nfs4_stid

__PNFS_LAYOUTTYPE='''
enum pnfs_layouttype {
        LAYOUT_NFSV4_1_FILES  = 1,
        LAYOUT_OSD2_OBJECTS = 2,
        LAYOUT_BLOCK_VOLUME = 3,
        LAYOUT_FLEX_FILES = 4,
        LAYOUT_SCSI = 5,
        LAYOUT_TYPE_MAX
};
'''
PNFS_LAYOUTTYPE=CEnum(__PNFS_LAYOUTTYPE)

# TODO: add file and layout segments
class nfs4_layout_stateid():
    def __init__(self, ls, verbose=False):
        self._ls = readSU("struct nfs4_layout_stateid", ls)
        self._type = self._ls.ls_layout_type
        self.addr = Deref(self._ls)
        self.type = self._get_type(self._type)
        self.stid = None
        if verbose:
            self.stid = nfs4_stid(self._ls.ls_stid)

    def _get_type(self, t):
        layout_types = {
            PNFS_LAYOUTTYPE.LAYOUT_NFSV4_1_FILES: "LAYOUT_NFSV4_1_FILES",
            PNFS_LAYOUTTYPE.LAYOUT_OSD2_OBJECTS: "LAYOUT_OSD2_OBJECTS",
            PNFS_LAYOUTTYPE.LAYOUT_BLOCK_VOLUME: "LAYOUT_BLOCK_VOLUME",
            PNFS_LAYOUTTYPE.LAYOUT_FLEX_FILES: "LAYOUT_FLEX_FILES",
            PNFS_LAYOUTTYPE.LAYOUT_SCSI: "LAYOUT_SCSI",
            PNFS_LAYOUTTYPE.LAYOUT_TYPE_MAX: "unknown"
        }
        return layout_types[t]

    def __str__(self):
        s = "(struct nfs4_layout_stateid *) {self.addr:#x} type = {self.type}".format(self=self)
        if self.stid:
            s += "\n- {}".format(self.stid)
        return s

def auto_int(x):
    return int(x, 0)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("ls", metavar="LAYOUT_STATEID", type=auto_int,
                        help="address of struct nfs4_layout_stateid")
    parser.add_argument("-v", "--verbose", default = 0,
                        action="store_true",
                        help="verbose output (include stateids)")
    args = parser.parse_args()
    ls = nfs4_layout_stateid(args.ls, args.verbose)
    print(str(ls))
