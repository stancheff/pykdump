#!/usr/bin/env/python
from __future__ import print_function

__author__ = "Scott Mayhew"
__version__ = "0.1"

from pykdump.API import *
from LinuxDump.fs.nfsd.nfsd_net import nfsd_net

def print_all_containers(verbosity):
    nfsd_net_id = readSymbol("nfsd_net_id")
    if sys_info.kernel < "4.10.0":
        nfsd_net_id = nfsd_net_id - 1
    ns_list = sym2addr("net_namespace_list")
    print ('{:+^40}'.format('containers'))
    for net in readSUListFromHead(ns_list, "list", "struct net"):
        nn = nfsd_net(net.gen.ptr[nfsd_net_id], verbosity)
        if verbosity >= 2:
            nn.print_verbose()
        elif verbosity >= 1:
            nn.print_summary()
        else:
            print(str(nn))

def auto_int(x):
    return int(x, 0)

def main(args):
    if args.nn:
        nn = nfsd_net(args.nn, args.verbosity)
        if args.verbosity >= 2:
            nn.print_verbose()
        elif args.verbosity >= 1:
            nn.print_summary()
        else:
            print(str(nn))
    else:
        print_all_containers(args.verbosity)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--nfsd-net", metavar="NFSD_NET", dest="nn", type=auto_int,
                        help="address of struct nfsd_net")
    parser.add_argument("-v", "--verbosity", default=0, action="count",
                        help="increase verbosity")
    args = parser.parse_args()
    main(args)
