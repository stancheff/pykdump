#!/usr/bin/env/python
from __future__ import print_function

__author__ = "Scott Mayhew"
__version__ = "0.1"

from pykdump.API import *
from LinuxDump.fs.nfsd.nfs4_client import nfs4_client

class nfsd_net():
    def __init__(self, nn, verbosity):
        self._nn = readSU("struct nfsd_net", nn)
        self.addr = Deref(self._nn)
        self.clients = []
        if verbosity >= 2:
            for c in readSUListFromHead(self._nn.client_lru, "cl_lru", "struct nfs4_client"):
                self.clients.append(nfs4_client(Addr(c), True, True, True, True, True, True, True))
            self.num_clients = len(self.clients)
        elif verbosity >= 1:
            for c in readSUListFromHead(self._nn.client_lru, "cl_lru", "struct nfs4_client"):
                self.clients.append(nfs4_client(Addr(c)))
            self.num_clients = len(self.clients)
        else:
            self.num_clients = getListSize(self._nn.client_lru, 0, 100000)

    def __str__(self):
        return "(struct nfsd_net *) {self.addr:#x} clients: {self.num_clients}".format(self=self)

    def print_summary(self):
        print(str(self))
        if self.clients:
            print ('{:_^40}'.format('clients'))
            for client in self.clients:
                print(str(client))

    def print_verbose(self):
        print(str(self))
        if self.clients:
            print ('{:_^40}'.format('clients'))
            for client in self.clients:
                client.print_verbose()

def auto_int(x):
    return int(x, 0)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("nn", metavar="NFSD_NET", type=auto_int,
                        help="address of struct nfsd_net")
    parser.add_argument("-v", "--verbosity", default=0, action="count",
                        help="increase verbosity")
    args = parser.parse_args()
    nn = nfsd_net(args.nn, args.verbosity)
    if args.verbosity >= 2:
        nn.print_verbose()
    elif args.verbosity >= 1:
        nn.print_summary()
    else:
        print(str(nn))
