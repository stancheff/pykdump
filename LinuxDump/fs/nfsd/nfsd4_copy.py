#!/usr/bin/env/python
from __future__ import print_function

__author__ = "Scott Mayhew"
__version__ = "0.1"

from pykdump.API import *

# TODO: add stuff
class nfsd4_copy():
    def __init__(self, c, verbose=False):
        self._c = readSU("struct nfsd4_copy", d)
        self.addr = Deref(self._c)

    def __str__(self):
        return("(struct nfsd4_copy *) {self.addr:#x}".format(self=self))

def auto_int(x):
    return int(x, 0)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("c", metavar="COPY", type=auto_int,
                        help="address of struct nfsd4_copy")
    parser.add_argument("-v", "--verbose", default = 0,
                        action="store_true",
                        help="verbose output (currently unused)")
    args = parser.parse_args()
    c = nfsd4_copy(args.c, args.verbose)
    print(str(c))
