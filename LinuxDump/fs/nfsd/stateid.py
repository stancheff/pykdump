#!/usr/bin/env/python
from __future__ import print_function

__author__ = "Scott Mayhew"
__version__ = "0.1"

from pykdump.API import *
from crccheck.crc import CrcX25
import struct
import sys

class stateid():
    def __init__(self, s):
        self._stateid = readSU("stateid_t", s)
        self._generation = self._stateid.si_generation
        self._opaque = struct.pack('III', self._stateid.si_opaque.so_clid.cl_boot,
                                  self._stateid.si_opaque.so_clid.cl_id,
                                  self._stateid.si_opaque.so_id)
        self._data = struct.pack('!I12s', self._generation, self._opaque)
        self.addr = Deref(self._stateid)
        self.value = ":".join(["%02x" % c for c in self._data])
        self.hash = CrcX25.calc(self._data)

    def __str__(self):
        return("(struct nfs4_stateid *) {self.addr:#x} value = {self.value} "
               "hash = {self.hash:#06x}").format(self=self)

if __name__ == '__main__':
    print(str(stateid(int(sys.argv[1], 0))))
