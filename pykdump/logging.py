# -*- coding: utf-8 -*-
#
#  Logging messages to print a summary at the end
#
#
# --------------------------------------------------------------------
# (C) Copyright 2006-2020 Hewlett Packard Enterprise Development LP
#
# Author: Alex Sidorenko <asid@hpe.com>
#
# --------------------------------------------------------------------
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Pubic License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from collections import defaultdict

debug = False

WARNING = "+++WARNING+++"
ERROR =   "+++ERROR+++"
INFO = "...INFO..."

# Using "Singleton Borg pattern" so that we can call constructor
# from different modules
class PyLog:
    _cache = defaultdict(list)
    _silent = ""
    def __init__(self):
        pass
    def _addtocache(self, name, data):
        if (not data in self._cache[name]):
            self._cache[name].append(data)
    def _printandcache(self, name, data):
        self._addtocache(name, data)
        print(name, end=' ')
        args, kwargs = data
        print(*args, **kwargs)
    def timeout(self, msg):
        print(WARNING, msg)
        self._addtocache("timeout", msg)
    def warning(self, *args, **kwargs):
        # Print traceback if debug is enabled
        if (debug):
            traceback.print_stack()
        name = WARNING
        self._printandcache(name, (args, kwargs))
    # Another flavor of warning - print on exit only
    def warning_onexit(self, *args, **kwargs):
        name = WARNING
        self._addtocache(name, (args, kwargs))
    def info(self, *args, **kwargs):
        name = INFO
        self._addtocache(name, (args, kwargs))
    def error(self, *args, **kwargs):
        name = ERROR
        # Print traceback if debug is enabled
        if (debug):
            traceback.print_stack()

        self._printandcache(name, (args, kwargs))
    def silent(self, msg):
        self._silent = msg
    def getsilent(self):
        msg = self._silent
        self._silent = ""
        return msg
    # Propagate silent error to real error if any, but do not print it
    def silenterror(self, extra):
        msg = self.getsilent()
        if (msg):
            args = (extra, msg)
            kwargs = {}
            self._addtocache(ERROR, (args, kwargs))
    def cleanup(self):
        # Clear the cache
        self._cache.clear()
        self._silent = ""
    def onexit(self):
        # Is there anything to print?
        if (not self._cache):
            return
        self.__print_problems()
        self.__print_info()
    def __print_info(self):
        if (not INFO in self._cache):
            return
        print("")
        print(" Additional Info ".center(78, '~'))
        for args, kwargs in self._cache[INFO]:
            print(end="    ")
            print(*args, **kwargs)
        print('~'*78)
    def __print_problems(self):
        _keys = set(self._cache.keys()) - {INFO}
        if (not _keys):
            return
        print("")
        print('*'*78)
        print(" A Summary Of Problems Found ".center(78, '*'))
        print('*'*78)
        # Are there are timeout messages?
        if (self._cache["timeout"]):
            print(" Some crash built-in commands did not complete "
                  "within timeout ".center(78, '-'))
            for l in self._cache["timeout"]:
                print("   ", l)
            print(" *** You can rerun your command with a different timeout\n"
                  "     by adding --timeout=NNN to your options\n"
                  "     For example, 'crashinfo -v --timeout=1200\n"
                  "     to run with timeout of 1200s")
        # Are there any warnings/errors?
        for name in (WARNING, ERROR):
            if (self._cache[name]):
                print(" A list of all {} messages ".format(name).center(78, '-'))
                for args, kwargs in self._cache[name]:
                    print(end="    ")
                    print(*args, **kwargs)
        print('-'*78)
