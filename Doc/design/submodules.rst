Contents of **pykdump/** directory
===================================

Program developers import everything as::

  from pykdump.API import *

This document described the submodules included in *pykdump* package,
in particular logical separation of functionality between subbmodules

Directory Structure
-------------------

.. code-block:: text

   pykdump/
           API.py              - main module
           datatypes.py        - mapping C types to Python types
           dlkmload.py         - loading DLKM debuginfo
           Generic.py          - generic useful subroutines/classes
           highlevel.py        - high-level readers for data
           __init__.py         - check versions of Python code and C-module
           logging.py          - log messages to be printed as summary
           lowlevel.py         - low-level readers for data
           memocaches.py       - memoization of types and data
           Misc.py             - ASCII-art for tree-like structures
           tparser.py*         - parse pieces of text in C syntax
           vmcorearch.py       - get vmcore arch specific info


Modules Interdependecy
----------------------

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

It is OK to have some interdependcies if they are limited and
implemented properly.
