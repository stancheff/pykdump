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


Dependency on Python and Crash Versions
---------------------------------------

Usually there is no need to change anything when a new *minor* version
of ``crash`` or ``Python`` is released. But when there is a new
*major* release of either ``crash`` or ``Python``, it is quite
possible that C-module will need some changes.

Dependency on ``crash`` Version
...............................

There are three types of changes in ``crash`` per se that might need changes
in C-module (in addition, we depend on ``GDB`` emebedded in ``crash``)

Internal subroutines/variables/macros
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

C-module depends on several internal ``crash`` subroutines, variables
and macros, providing wrappers (usually called *Python bindings*) for
them so that these subroutines can be accessed from Python. Examples of such
subroutines/macros:

* symbol_exists(symbol)

* MEMBER_SIZE(name, member)

Some constants:

* KVADDR/UVADDR/PHYSADDR

* PAGESIZE/PAGE_CACHE_SHIFT

When a new version of ``crash`` is released, it is possible that some
of these subroutines change or become unavailable (happened at least once)

Signal Handlers and Executing ``crash`` Commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``crash`` has its own signal handlers for several signals,
e.g. SIGINT. When we execute Python code, Python has its own signal
handlers. To make everything work properly, we need to store/restore
signal handlers when executing Python.

PyKdump provides several commands to execute ``crash`` built-in and
return result as a string. The logic is rather complicated:

* we need to feed a string as a command-line for ``crash`` to execute,
  modify file descriptors to get output and after command completion
  do some cleanup

* while executing ``crash`` builtin, we need to use its own signal
  handler and after that install Python signal handler again


Dependency on GDB
~~~~~~~~~~~~~~~~~

``crash`` is built on top of ``GDB`` and to access symbolic
information (such as struct/union definitions) we need to execute
internal ``GDB`` subroutines. New *major* releases of ``crash`` are
usually rebased on newer *major* ``GDB`` version.

As a result, some enumeration definitions (used by ``GDB``) can change
(happened twice), subroutine signature can change, and ``GDB``
cleanup/error processing can change.

So in case PyKdump built on top of a new major ``crash`` does not work
properly, be ready to look not only on ``crash`` sources but ``GDB``
sources as well (provided with patches in ``crash`` tarfile).

Dependency on Python Version
............................

When there is a new major release of Python, three things might need
change:

* The contents of Setup.local used to build Python from sources

* The list of Python Standard Library subroutines to be included

* the way to initalize the Python environment and execute Python code

Setup.local and minpylib-3.N.lst
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These two files are often updated together. If you decide to include
another module from Python Standard Library, this often (but not
always) needs linking statically another C-module included in Python
sources distribution. This has nothing to do with Python *major*
version change.

But it is not unusual that a new major release of Python rearranges
library, so that you will need to change the contents of
minpylib-3.N.lst to make things work. This happened e.g. while
migrating from Python-3.6 to Python-3.7.

Python Initalization and Code Execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python environment is initialized only once, while loading the
extension. Initialization subroutines - part of Python C-API - are
regularly improved and older ones are somtimes obsoleted. This means
that we might need to modify the login of _init_python() subroutine
(defined in epython.c).

There are two sources of PyKdump Python code to execute:

* from real files (either user-developed programs or local GIT-repo)

* from ZIP-file - part of binary *mpykdump.so* module

Once again, new major releases of Python regularly improve the
existing C-API subroutines and some old ones are being obsoleted.




