#!/usr/bin/env/python
from __future__ import print_function

__author__ = "Scott Mayhew"
__version__ = "0.1"

from pykdump.API import *
from LinuxDump.fs.nfsd.nfs4_stateowner import nfs4_stateowner
from LinuxDump.fs.nfsd.nfs4_layout_stateid import nfs4_layout_stateid
from LinuxDump.fs.nfsd.nfs4_delegation import nfs4_delegation
from LinuxDump.fs.nfsd.nfsd4_session import nfsd4_session
from LinuxDump.fs.nfsd.nfsd4_copy import nfsd4_copy
import socket

class nfs4_client():
    def __init__(self, c, openowners=False, layouts=False, delegations=False,
                 sessions=False, copies=False, revoked=False, verbose=False):
        self._client = readSU("struct nfs4_client", c)
        self.addr = Deref(self._client)
        self.name = readmem(self._client.cl_name.data, self._client.cl_name.len).decode()
        self.clientid = (socket.htonl(self._client.cl_clientid.cl_boot) << 32) | socket.htonl(self._client.cl_clientid.cl_id)
        self.cb_waitq_qlen = self._client.cl_cb_waitq.qlen
        self.num_openowners = self.num_layouts = self.num_delegations = self.num_sessions = self.num_copies = self.num_revoked = 0

        self.openowners = []
        if openowners:
            if verbose:
                for openowner in readSUListFromHead(self._client.cl_openowners, "oo_perclient",
                                            "struct nfs4_openowner"):
                    self.openowners.append(nfs4_stateowner(Addr(openowner.oo_owner), verbose))
                self.num_openowners = len(self.openowners)
            else:
                self.num_openowners = getListSize(self._client.cl_openowners, 0, 100000)

        self.layouts = []
        if layouts:
            if verbose:
                for layout in readSUListFromHead(self._client.cl_lo_states, "ls_perclnt",
                                            "struct nfs4_layout_stateid"):
                    self.layouts.append(nfs4_layout_stateid(Addr(layout), verbose))
                self.num_layouts = len(self.layouts)
            else:
                self.num_layouts = getListSize(self._client.cl_lo_states, 0, 100000)

        self.delegations = []
        if delegations:
            if verbose:
                for delegation in readSUListFromHead(self._client.cl_delegations, "dl_perclnt",
                                            "struct nfs4_delegation"):
                    self.delegations.append(nfs4_delegation(Addr(delegation), verbose))
                self.num_delegations = len(self.delegations)
            else:
                self.num_delegations = getListSize(self._client.cl_delegations, 0, 100000)

        self.sessions = []
        if sessions:
            if verbose:
                for session in readSUListFromHead(self._client.cl_sessions, "se_perclnt",
                                            "struct nfsd4_session"):
                    self.sessions.append(nfsd4_session(Addr(session), verbose))
                self.num_sessions = len(self.sessions)
            else:
                self.num_sessions = getListSize(self._client.cl_sessions, 0, 100000)

        self.copies = []
        if copies:
            _info = getStructInfo("struct nfs4_client")
            if "async_copies" in _info.keys():
                if verbose:
                    for copy in readSUListFromHead(self._client.async_copies, "copies",
                                                "struct nfsd4_copy"):
                        self.copies.append(nfsd4_copy(Addr(copy), verbose))
                    self.num_copies = len(self.copies)
                else:
                    self.num_copies = getListSize(self._client.async_copies, 0, 100000)
            else:
                self.num_copies = 0

        self.revoked = []
        if revoked:
            if verbose:
                for delegation in readSUListFromHead(self._client.cl_revoked, "dl_recall_lru",
                                            "struct nfs4_delegation"):
                    self.revoked.append(nfs4_delegation(Addr(delegation), verbose))
                self.num_revoked = len(self.revoked)
            else:
                self.num_revoked = getListSize(self._client.cl_revoked, 0, 100000)

    def __str__(self):
        s = ("(struct nfs4_client *) {self.addr:#x} name = {self.name} clientid = {self.clientid:#x} "
             "cl_cb_waitq qlen = {self.cb_waitq_qlen}").format(self=self)
        if self.num_openowners:
            s += " openowners = {self.num_openowners}".format(self=self)
        if self.num_layouts:
            s += " layouts = {self.num_layouts}".format(self=self)
        if self.num_delegations:
            s += " delegations = {self.num_delegations}".format(self=self)
        if self.num_sessions:
            s += " sessions = {self.num_sessions}".format(self=self)
        if self.num_copies:
            s += " copies = {self.num_copies}".format(self=self)
        if self.num_revoked:
            s += " revoked = {self.num_revoked}".format(self=self)
        return s

    def print_verbose(self):
        print(str(self))
        if self.openowners:
            print ('{:=^40}'.format('openowners'))
            for openowner in self.openowners:
                openowner.print_verbose()
        if self.layouts:
            print ('{:=^40}'.format('layouts'))
            for layout in self.layouts:
                print("- {}".format(layout))
        if self.delegations:
            print ('{:=^40}'.format('delegations'))
            for delegation in self.delegations:
                print("- {}".format(delegation))
        if self.sessions:
            print ('{:=^40}'.format('sessions'))
            for session in self.sessions:
                print("- {}".format(session))
        if self.copies:
            print ('{:=^40}'.format('copies'))
            for copy in self.copies:
                print("- {}".format(copy))
        if self.revoked:
            print ('{:=^40}'.format('revoked delegations'))
            for delegation in self.revoked:
                print("- {}".format(delegation))

def auto_int(x):
    return int(x, 0)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("client", metavar="CLIENT", type=auto_int,
                        help="address of struct nfs4_client")
    parser.add_argument("-a", "--all", default=0, action="store_true",
                        help="print all")
    parser.add_argument("-o", "--openowners", default=0, action="store_true",
                        help="print nfs4_stateowner structures")
    parser.add_argument("-l", "--layouts", default=0, action="store_true",
                        help="print nfs4_layout_stateid structures")
    parser.add_argument("-d", "--delegations", default=0, action="store_true",
                        help="print nfs4_delegation structures")
    parser.add_argument("-s", "--sessions", default=0, action="store_true",
                        help="print nfsd4_session structures")
    parser.add_argument("-c", "--copies", default=0, action="store_true",
                        help="print nfsd4_copy structures")
    parser.add_argument("-r", "--revoked", default=0, action="store_true",
                        help="print revoked delegations")
    parser.add_argument("-v", "--verbose", default=0, action="store_true",
                        help="verbose output (include stateids)")
    args = parser.parse_args()
    if (args.all):
        args.openowners = args.layouts = args.delegations = args.sessions = args.copies = args.revoked = True
    c = nfs4_client(args.client, args.openowners, args.layouts, args.delegations,
                    args.sessions, args.copies, args.revoked, args.verbose)
    if args.verbose:
        c.print_verbose()
    else:
        print(str(c))
