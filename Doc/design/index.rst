Design Considerations
=====================

There are three logical groups of sourcefiles:

* Framework itself - not related to any specific kernel subsystem. It
  consists of two parts:

  * C-module - implements Python bindings to ``crash`` and ``GDB``
    internals. The sources are in ``Extension/`` subdirectory

  * Python API implemented on top of C-module. The sources are in
    ``pykdump/`` subdirectory

* A library of subroutines implementing access to different Linux
  kernel tables/structures, e.g. *inet* or *storage*. It consists of
  several modules residing in ``LinuxDump/`` subdirectory

* Top-level programs - those that can be used for vmcore analysis
  without doing any programming. They reside in ``progs/`` subdirectory


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   cfiles
   pfiles

   lowlevel

