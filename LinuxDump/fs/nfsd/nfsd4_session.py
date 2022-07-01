#!/usr/bin/env/python
from __future__ import print_function

__author__ = "Scott Mayhew"
__version__ = "0.1"

from pykdump.API import *

class nfsd4_session():
    def __init__(self, s, verbose=False):
        self._s = readSU("struct nfsd4_session", s)
        self._sessionid = readmem(Addr(self._s.se_sessionid), 16)
        self.addr = Deref(self._s)
        self.sessionid = ":".join(["%02x" % c for c in self._sessionid])

    def __str__(self):
        return("(struct nfsd4_session *) {self.addr:#x} sessionid = "
               "{self.sessionid}".format(self=self))

def auto_int(x):
    return int(x, 0)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("s", metavar="SESSION", type=auto_int,
                        help="address of struct nfsd4_session")
    parser.add_argument("-v", "--verbose", default = 0,
                        action="store_true",
                        help="verbose output (currently unused)")
    args = parser.parse_args()
    s = nfsd4_session(args.s, args.verbose)
    print(str(s))
