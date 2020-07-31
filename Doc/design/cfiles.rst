Framework - **Extension/** directory
====================================

This directory contains sources (C) to implement Python bindings to
internal subroutines of ``crash`` and ``GDB``.

In addition, its Makefile is used to build the binary distribution of
*PyKdump* - a single self-sufficient file *mpykdump.so* that can
loaded as an extension in ``crash`` environment.

Directory Structure
-------------------

.. code-block:: text

  configure         - configuration script to generate extra Makefiles
  epython.c         - initilization and invoking programs
  functions.c       - generic functions and bindings to crash internals
  gdbspec.c         - bindings to GDB internals
  Makefile          - main Makefile
  makestdlib.py     - create and package a subset of Python Standard Library
  minpylib-3.8.lst  - list of files from Python Standard Library to include
  pyconf.py         - getting info about Python used for builds
  pykdump.h         - main header
  pyparsing.py      - 3rd party Python module to implement parsers
  Setup.local-3.8   - used when you build Python from sources
  testmod/          - a test DLKM, used for framework testing
  writeREADME.py    - generates README with the contents of mpykdump.so


