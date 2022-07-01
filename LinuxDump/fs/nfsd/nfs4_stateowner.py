#!/usr/bin/env/python
from __future__ import print_function

__author__ = "Scott Mayhew"
__version__ = "0.1"

from pykdump.API import *
from LinuxDump.fs.nfsd.nfs4_stid import nfs4_stid

class nfs4_stateowner():
    def __init__(self, s, verbose=False):
        self._stateowner = readSU("struct nfs4_stateowner", s)
        self.addr = Deref(self._stateowner)
        self.stateids = []
        if verbose:
            for stp in readSUListFromHead(self._stateowner.so_stateids, "st_perstateowner",
                                          "struct nfs4_ol_stateid"):
                self.stateids.append(nfs4_stid(Addr(stp.st_stid)))
            self.num_stateids = len(self.stateids)
        else:
            self.num_stateids = getListSize(self._stateowner.so_stateids, 0, 100000)

    def __str__(self):
        return "(struct nfs4_stateowner *) {self.addr:#x} stateids = {self.num_stateids}".format(self=self)

    def print_verbose(self):
        print(str(self))
        if self.stateids:
            print ('{:-^40}'.format('stateids'))
            for stateid in self.stateids:
                print("- {}".format(stateid))

def auto_int(x):
    return int(x, 0)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("s", metavar="STATEOWNER", type=auto_int,
                        help="address of struct nfs4_stateowner")
    parser.add_argument("-v", "--verbose", default = 0,
                        action="store_true",
                        help="verbose output (include stateids)")
    args = parser.parse_args()
    s = nfs4_stateowner(args.s, args.verbose)
    print(str(s))
