Contents of **pykdump/** directory
===================================

Program developers import everything as::

  from pykdump.API import *

This document describes the submodules included in *pykdump* package,
in particular logical separation of functionality between submodules

Directory Structure
-------------------

.. code-block:: text

   pykdump/
           __init__.py         - check versions of Python code and C-module
           API.py              - main module
           datatypes.py        - mapping C types to Python types
           dlkmload.py         - loading DLKM debuginfo
           Generic.py          - generic useful subroutines/classes
           highlevel.py        - high-level readers for data
           logging.py          - log messages to be printed as summary
           lowlevel.py         - low-level readers for data
           memocaches.py       - memoization of types and data
           Misc.py             - ASCII-art for tree-like structures
           tparser.py*         - parse pieces of text in C syntax
           vmcorearch.py       - get vmcore arch specific info


Modules Interdependecy
......................

In general, it is a bad idea for two modules to import each other as
this can lead to circular import. Search in Google for 'python
circular imports' to find many articles describing what could go
wrong. The best approach is to combine two such modules into a single
one. But this is not always desirable:

* the resulting file will be bigger, more difficult to read and understand

* it is not a good programming practice to put completely unrelated
  classes/subroutines into a single sourcefile - this makes
  maintenance difficult. If two developers work on logically different
  things but sourcecode is in one file, this is not convenient for
  commits/merges

It is OK to have some interdependencies if they are limited and
implemented properly.

API.py
------

This is a main module to be used by program developers. It does
several things:

* imports all needed subroutines/classes/variables from other modules
  so that there is no need to do this manually

* parses *global* options (such as timeout value for crash-builtins)
  and processes them as needed. These options are stripped from
  argument list passed to programs

* re-initializes logging before each program run and prints summary of
  logged messages when program exits

__init__.py
-----------

This module contains version number of Python API and specifies a
minimal version of C-module needed for this API to work.

If you added a new subroutine to C-module and this subroutine is
used in your updated Python code, you cannot use an old C-module.

This is unimportant for end-users - those who rely on binary
mpykdump.so module. But developers might pull new commits and try to
run Python code without rebuilding C-module - and this can create
problems.

To check for such problems, we compare C-module version (specififed in
C-sources) and Python-API version (specified in __init__.py).

datatypes.py
------------

This module defines classes used to represent information about types, structs,
enumerations etc. to be used by high-level subroutines

We extract symbolic data using Python bindings to GDB internals
(implemented in ``crash`` module, written in C) and then we need to
convert this information to objects suitable for Python.

This modules mainly defines classes and some auxiliary subroutines;
conversion from GDB data to instances of these classes is implemented
in lowelevel.py


dlkmload.py
-----------

To access kernel symbols/structs defined in DLKMs, we need to load
debuginfo as needed.

Depending on your distribution, these files can have different suffixes:

* .ko.debug

* .o.debug

* .ko

* .o

and they can be located in different directories. In addition, loading
DLKM debuginfo might invalidate PyKdump caches (e.g. if struct with
the same name is present both in DLKM and kernel).

This module provides a number of helper subroutines to load/unload
this debuginfos for DLKMs

Generic.py
----------

Useful subroutines not directly related to vmcore analysis: lazy evaluation,
containers, registering handlers for module-level debugging

highlevel.py
------------

File highlevel.py contains code that will be used by developers of
programs. It is imported by API.py.

There are several logical groups of subroutines:

* read data at a specific address (both virtual and physical)

* read a specific global symbol

* subroutines to work with lists

* obtaining information about structs (e.g. member offsets)

* executing built-in GDB and crash commands

logging.py
----------

If your program produces lots of output, it is difficult to quickly
find the important things. It usually makes sense to display a summary
of all "important" findings (such as critical errors) after the end of
normal output, when program exits.

*logging.py* implements PyLog class. It is a singleton, so doing::

  pylog = PyLog()

in any of your own modules will use the same underlying data. Logging
is reinitialized every time when you start a program and on program exit
summary is displayed.


lowlevel.py
-----------

This module contains code to construct instances of classes defined in
*datatypes.py*. This module is rather low-level, used internally by
framework but not developers of programs. The contents of this module
is used byt *highlevel.py*.

So *highlevel.py* imports from *lowlevel.py* but not vice versa.

For objects representing the contents of struct/union we need to
implement struct field access/dereference.

struct/union fields can be of different type, so to implement such
access we need to analyze the type of each field and use an
appropriate subroutine. In PyKdump sources such subroutines are called
*readers*. During analysis of specific struct/union type, we create
and store readers for each field, so that they will be used for all
structs of this type (results of analysis are cached).

Readers are implemented as closures, to preserve information about
extra specifiers of field type. For example, for arrays the reader
needs to take into account array dimensions. Factory functions for
readers at this moment are:

* ptrReader - reading pointers

* suReader - reading structs/unions

* ti_boolReader - reading booleans

* ti_enumReader - reading enumerations

* ti_intReader - reading all integer types



memocaches.py
-------------

Memoization classes and decorators, subroutines for caches maintenance

Some operations are quite CPU-expensive - for example, obtaining and
analyzing symbolic info about structs/unions.

To improve the performance, it makes sense to cache the results, so
that we would not repeat the expensive computations again and again.

Another group of CPU-intensive operations is related to executing
build-in crash commands (e.g. ``kmem -s``). Once again, it makes sense
to cache the results.

Caching depends on whether we are running a live session or using
vmcore (if we are using a live kernel, some things change with time).

Loading DLKM debuginfo might change structs definitions, so some
caches should be invalidated after such operations.

Misc.py
-------

ASCII-art for displaying tree-like structures. Should be really renamed to
something like AArt.py

tparser.py
----------

In some cases, we cannot extract the needed information from
debuginfo. This module implements simple parsers for C-text, so that we
can copy definition from kernel sources (C) and convert it to
format used by PyKdump. In particular, we can copy a block of
``#define`` statements and convert it to a dictionary.


vmcorearch.py
-------------

C-language definitions for integers are rather ambiguous - the size of
*long int* can be either 4 bytes or 8 bytes. This depends on hardware
used to run Linux, and we need this information to be able to read
integers (and pointers) properly.

This module extracts from vmcore basic data needed to do the analysis:

* arch-specific data (integers sizes etc.)

* HZ, PAGESIZE, PAGE_CACHE_SHIFT, CPUS

* kernel revision and directory of the vmcore

* standard directories used for DLKM debuginfo search

* checks whether this is vmcore or we are running on a live kernel


