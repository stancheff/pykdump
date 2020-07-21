Building from GIT
=================

This document describes building mpykdump extension from sources,
Python3.8.x base. At this moment it is in dev branch but soon will be
merged with master.

* `Compiling Python`_
* `Compiling crash`_
* `Install zip command`_
* `Details of the Build Process`_

You can retrieve the sources with GIT::

    $ git clone git://git.code.sf.net/p/pykdump/code pykdump

Even though all popular Linux distributions have Python already packaged, you
need to build Python yourself, from sources. The reasoning for that is as
follows.

It is possible to package everything (C-module, Python interpreter, pure
Python code) into a single file. In this case, the dependencies are minimal -
the created file depends just on glibc and its related libraries (such
as libm). If we build on a host with specific GLIBC version, the extension
should be usable on any GLIBC-compatible host (the same or newer version of
GLIBC).

For example, if we build on RHEL5, the built extension should be usable not
only on RHEL5 but on RHEL6-8, Ubuntu, SLES10-12 and so on. There will
be no need to install any additional packages on the target system - just copy
'crash' and the extension file from your build host to target host and start
using them (that is, no need for Python to be installed on the target host).
All the new development happens on Python 3 only. So, the old code based on
Python-2.7 is now moved to python2 branch and it is no longer used.

Before building the extension itself, we need to build Python and Crash.

Compiling Python
----------------

There are two major versions of Python - 2.x and 3.x. Python version 3 is not
totally backwards compatible with Python version 2. Since all the new PyKdump
development is done using *Python-3.8.x*, this document describes build process
for Python 3.

* Obtain Python sources from `python <http://www.python.org>`_. At this moment
  the latest 3.8.x release is 3.8.1

* Unpack the sources and go to the top Python source directory (we use 3.8.x)::

    $ tar -xvf Python-3.8.1.tar.xz
    $ cd Python-3.8.1

* We need an archive library, not '.so' - but with position-independent code,
  so use the following command::

    $ ./configure CFLAGS=-fPIC --disable-shared

* Obtain the customized modules configuration file Setup.local. It is available
  in 'Extension/' subdirectory of PyKdump source tree.

  You can get the whole tree using GIT, or download the needed file using
  `GIT WEB-Browser <https://sourceforge.net/p/pykdump/code>`_. Go to the
  tree matching the needed branch and then to 'Extension' directory. There can
  be multiple versions of Setup.local file for different Python revisions,
  you need *Setup.local-3.8*. Copy the needed version to 'Modules'
  subdirectory of the Python source tree, for example::

    $ mv /tmp/Setup.local-3.8 Modules/Setup.local

  Please make sure to rename it to just Setup.local as demonstrated
  above.

* The default Setup.local file configures Python to include a static copy of the
  readline module. To support this, you should install the ``readline-static``
  package. Alternatively, if you do not wish to include readline support
  (which provides line-editing for ``input()`` and for Python REPLs), you may
  remove the line in ``Modules/Setup.local`` which refers to readline.

* Compile Python::

    $ make

  By default, Python C-code is compiled with `-g` flag (debugging). If you
  want to decrease the size of the built extension, strip the library from
  debugging symbols::

    $ ls -l libpython3.8.a
    -rw-r--r--. 1 mpg debuginfo 25M Feb  6 12:01 libpython3.8.a

  To strip the debug symbols from above library::

    $ strip --strip-debug libpython3.8.a

  The size of *libpython3.8.a* is reduced after removing debug symbols::

    $ ls -lh libpython3.8.a
    -rw-r--r--. 1 mpg debuginfo 7.5M Feb  6 12:01 libpython3.8.a

Compiling crash
---------------

Extensions built for different major versions of crash are not compatible.
We recommend to use crash-7.X

* Obtain the sources of crash from
  `upstream page <http://people.redhat.com/anderson/>`_. Unpack the sources and
  run make::

    $ make

Install `zip` command
---------------------

* To build the extension you need ZIP utility. Most distributions include
  ``zip`` by default, otherwise please install the needed package.

Build the extension
-------------------

* Obtain the sources of Pykdump from GIT::

    $ git clone git://git.code.sf.net/p/pykdump/code pykdump

* Change to the top directory of pykdump source tree, then change to
  Extension subdirectory::

    $ cd pykdump/Extension

* Configure Makefiles specifying the location of Python and Crash you
  have compiled from sources. The configuration script requires full pathnames
  (those starting from `/`). For example::

    $ ./configure -p /src/Python/Python-3.8.1 -c /src/kerntools/crash-7.2.0

  If everything worked normally, there should be 2 files created: crash.mk,
  and slocal.mk:

* Run make::

    $ make

  If make completes successfully, the file *mpykdump.so* should be created.
  This file is both a dynamically-loadable library and ZIP::

    $ ldd mpykdump.so
        linux-vdso.so.1 =>  (0x00007fff0219d000)
        libcrypt.so.1 => /lib64/libcrypt.so.1 (0x00007f513a08c000)
        libpthread.so.0 => /lib64/libpthread.so.0 (0x00007f5139e6f000)
        libdl.so.2 => /lib64/libdl.so.2 (0x00007f5139c6a000)
        libutil.so.1 => /lib64/libutil.so.1 (0x00007f5139a67000)
        librt.so.1 => /lib64/librt.so.1 (0x00007f513985f000)
        libm.so.6 => /lib64/libm.so.6 (0x00007f51395da000)
        libc.so.6 => /lib64/libc.so.6 (0x00007f5139246000)
        libfreebl3.so => /lib64/libfreebl3.so (0x00007f5139043000)
        /lib64/ld-linux-x86-64.so.2 (0x00000034f3600000)

    $ zipinfo mpykdump.so
    Archive:  mpykdump.so
    Zip file size: 6582022 bytes, number of entries: 179
    drwxr-xr-x  3.0 unx        0 bx stor 20-Feb-06 12:02 pylib/
    drwxr-xr-x  3.0 unx        0 bx stor 20-Feb-06 12:02 pylib/importlib/
    -rw-r--r--  3.0 unx     9303 bx defN 20-Feb-06 12:02 pylib/importlib/util.pyc
    -rw-r--r--  3.0 unx    13584 bx defN 20-Feb-06 12:02 pylib/importlib/abc.pyc
    -rw-r--r--  3.0 unx      973 bx defN 20-Feb-06 12:02 pylib/importlib/machinery.pyc
    -rw-r--r--  3.0 unx     3769 bx defN 20-Feb-06 12:02 pylib/importlib/__init__.pyc
    [...]
    drwxrwxr-x  3.0 unx        0 bx stor 19-Jun-27 09:21 dist-packages/
    drwxrwxr-x  3.0 unx        0 bx stor 20-Feb-06 12:02 dist-packages/crccheck/
    -rw-r--r--  3.0 unx     7296 bx defN 20-Feb-06 12:02 dist-packages/crccheck/checksum.pyc
    -rw-r--r--  3.0 unx    21009 bx defN 20-Feb-06 12:02 dist-packages/crccheck/crc.pyc
    -rw-r--r--  3.0 unx     3650 bx defN 20-Feb-06 12:02 dist-packages/crccheck/__init__.pyc
    -rw-r--r--  3.0 unx     8666 bx defN 20-Feb-06 12:02 dist-packages/crccheck/base.pyc
    -rwxrwxr-x  3.0 unx    54585 tx defN 20-Jan-06 14:30 progs/crashinfo.py
    -rwxrwxr-x  3.0 unx    39055 tx defN 19-Jun-27 09:21 progs/xportshow.py
    -rwxrwxr-x  3.0 unx    15653 tx defN 20-Jan-06 14:30 progs/taskinfo.py
    -rwxrwxr-x  3.0 unx    53017 tx defN 20-Jan-06 14:30 progs/nfsshow.py
    -rwxrwxr-x  3.0 unx    22093 tx defN 20-Jan-06 14:30 progs/hanginfo.py
    -rw-rw-r--  3.0 unx    10596 tx defN 18-Feb-06 16:36 progs/fregs.py
    -rwxrwxr-x  3.0 unx     6864 tx defN 17-Oct-11 12:12 progs/server.py
    -rw-rw-r--  3.0 unx     1099 tx defN 17-Oct-11 12:12 progs/tslog.py
    -rw-rw-r--  3.0 unx     7355 tx defN 17-Oct-11 12:12 progs/scsi.py
    -rw-rw-r--  3.0 unx    35826 tx defN 20-Jan-06 14:30 progs/scsishow.py
    -rw-rw-r--  3.0 unx    26758 tx defN 20-Feb-05 17:01 progs/dmshow.py
    -rwxr-xr-x  3.0 unx    30759 tx defN 20-Jan-29 16:28 progs/rqlist.py
    -rwxrwxr-x  3.0 unx     3577 tx defN 19-Jun-27 09:21 progs/pyctl.py
    -rw-rw-r--  3.0 unx    12798 tx defN 19-Jun-27 09:21 progs/modinfo.py
    -rwxrwxr-x  3.0 unx    28104 tx defN 19-Jun-27 09:21 progs/mountshow.py
    -rw-rw-r--  3.0 unx     7176 tx defN 19-Jun-27 09:21 progs/pstree.py
    -rw-rw-r--  3.0 unx     5250 tx defN 20-Jan-29 16:32 PyKdumpInit.py
    179 files, 2329239 bytes uncompressed, 948678 bytes compressed:  59.3%

  You can then copy this extension to the system used for vmcore analysis and
  start using this file by loading it using
  ``crash> extend <path-to-mpykdump.so>`` command in crash environment::

    crash> extend /test/mpykdump.so
    Setting scroll off while initializing PyKdump
    /test/mpykdump.so: shared object loaded

    crash> extend
    SHARED OBJECT        COMMANDS
    /test/mpykdump.so    epython xportshow crashinfo taskinfo nfsshow hanginfo
                         fregs tslog scsi scsishow dmshow pstree modinfo

Details of the Build Process
----------------------------

*This section is mainly of interest for developers.*

**Pykdump logically consists of three parts**:

  An extension written in 'C' which is linked against Python library and
  crash to create a DLL - a file that can be loaded by ``extend``
  command from crash. The compilation stage needs headers from crash
  (including gdb-headers distributed with crash) and Python headers (from
  the source tree).

  The extension is created by compiling C-sources specific to PyKdump and
  linking with Python C-library (e.g. libpython3.8.a). As we want to build a
  dynamically loadable extension, all C-code (including libpython3.8.a) needs
  to be compiled as position-independent code, with ``gcc`` this is either
  -fpic or -fPIC flag.

  Python runtime environment, in particular the Python Standard Library,
  consists of many subdirectories and contains many hundreds files. Not all of
  them are needed for our purposes - e.g. we don't need to work with XML or
  produce sounds Most of them are in Python, but there are some modules that
  are usually DLLs. If we do not want to distribute them with pykdump
  extension, we need to build Python with these modules compiled statically
  (in this case their PIC code is present in libpython3.8.a). This is why a
  custom  Setup.local file is needed (it lists modules to be built statically).

  In addition to these modules we need to copy parts of the Python Standard
  Library that we need (e.g. regular expressions) that are written in Python.
  The list of these files is Python version specific and there are several
  versions in the Extension directory, e.g. minpylib-3.8.lst lists these
  files for Python-3.6.

  Python programs build on top of this - e.g. ``xportshow``. They use more
  Python files implementing various things for different kernel subsystems::

    $ wc {LinuxDump,pykdump}/*.py
       390   1484  13951 LinuxDump/Analysis.py
       679   2420  21570 LinuxDump/BTstack.py
        66    251   2089 LinuxDump/CpuFreq.py
       274    623   6085 LinuxDump/crashcolor.py
        87    314   3033 LinuxDump/crashhelper.py
      1044   3417  32858 LinuxDump/Dev.py
        35    176   1333 LinuxDump/dlkm.py
        74    307   2584 LinuxDump/Files.py
        69    203   1846 LinuxDump/flock.py
       755   3030  29039 LinuxDump/fregsapi.py
       130    452   3885 LinuxDump/idr.py
        13     38    269 LinuxDump/__init__.py
    ...
       360   1296  11426 pykdump/Misc.py
       331   1169  10062 pykdump/tparser.py
      1816   6520  55698 pykdump/wrapcrash.py
     12241  42964 388495 total

  So how do we combine all this into a single file? The idea (borrowed from
  'cx_Freeze' Python packager) is based on two facts:

  1. Python libraries can be packed into a ZIP-file instead of using real
     directories and Python has API that lets us use these ZIP-files.
  2. ZIP-archive can be prepended by a stub (usually for Self-Extracting
     archives).

  So we ZIP all needed Python libraries (both pieces of standard library and
  pykdump/LinuxDump stuff) and append them to the end of our shared library.
  The resulting file, mpykdump.so, is both a DLL and ZIP-archive!::

    $ ldd mpykdump.so
        linux-vdso.so.1 =>  (0x00007fff0219d000)
        libcrypt.so.1 => /lib64/libcrypt.so.1 (0x00007f513a08c000)
        libpthread.so.0 => /lib64/libpthread.so.0 (0x00007f5139e6f000)
        libdl.so.2 => /lib64/libdl.so.2 (0x00007f5139c6a000)
        libutil.so.1 => /lib64/libutil.so.1 (0x00007f5139a67000)
        librt.so.1 => /lib64/librt.so.1 (0x00007f513985f000)
        libm.so.6 => /lib64/libm.so.6 (0x00007f51395da000)
        libc.so.6 => /lib64/libc.so.6 (0x00007f5139246000)
        libfreebl3.so => /lib64/libfreebl3.so (0x00007f5139043000)
        /lib64/ld-linux-x86-64.so.2 (0x00000034f3600000)

    $ zipinfo mpykdump.so
    Archive:  mpykdump.so
    Zip file size: 6582022 bytes, number of entries: 179
    drwxr-xr-x  3.0 unx        0 bx stor 20-Feb-06 12:02 pylib/
    drwxr-xr-x  3.0 unx        0 bx stor 20-Feb-06 12:02 pylib/importlib/
    -rw-r--r--  3.0 unx     9303 bx defN 20-Feb-06 12:02 pylib/importlib/util.pyc
    -rw-r--r--  3.0 unx    13584 bx defN 20-Feb-06 12:02 pylib/importlib/abc.pyc
    -rw-r--r--  3.0 unx      973 bx defN 20-Feb-06 12:02 pylib/importlib/machinery.pyc
    -rw-r--r--  3.0 unx     3769 bx defN 20-Feb-06 12:02 pylib/importlib/__init__.pyc
    [...]
    drwxrwxr-x  3.0 unx        0 bx stor 19-Jun-27 09:21 dist-packages/
    drwxrwxr-x  3.0 unx        0 bx stor 20-Feb-06 12:02 dist-packages/crccheck/
    -rw-r--r--  3.0 unx     7296 bx defN 20-Feb-06 12:02 dist-packages/crccheck/checksum.pyc
    -rw-r--r--  3.0 unx    21009 bx defN 20-Feb-06 12:02 dist-packages/crccheck/crc.pyc
    -rw-r--r--  3.0 unx     3650 bx defN 20-Feb-06 12:02 dist-packages/crccheck/__init__.pyc
    -rw-r--r--  3.0 unx     8666 bx defN 20-Feb-06 12:02 dist-packages/crccheck/base.pyc
    -rwxrwxr-x  3.0 unx    54585 tx defN 20-Jan-06 14:30 progs/crashinfo.py
    -rwxrwxr-x  3.0 unx    39055 tx defN 19-Jun-27 09:21 progs/xportshow.py
    -rwxrwxr-x  3.0 unx    15653 tx defN 20-Jan-06 14:30 progs/taskinfo.py
    -rwxrwxr-x  3.0 unx    53017 tx defN 20-Jan-06 14:30 progs/nfsshow.py
    -rwxrwxr-x  3.0 unx    22093 tx defN 20-Jan-06 14:30 progs/hanginfo.py
    -rw-rw-r--  3.0 unx    10596 tx defN 18-Feb-06 16:36 progs/fregs.py
    -rwxrwxr-x  3.0 unx     6864 tx defN 17-Oct-11 12:12 progs/server.py
    -rw-rw-r--  3.0 unx     1099 tx defN 17-Oct-11 12:12 progs/tslog.py
    -rw-rw-r--  3.0 unx     7355 tx defN 17-Oct-11 12:12 progs/scsi.py
    -rw-rw-r--  3.0 unx    35826 tx defN 20-Jan-06 14:30 progs/scsishow.py
    -rw-rw-r--  3.0 unx    26758 tx defN 20-Feb-05 17:01 progs/dmshow.py
    -rwxr-xr-x  3.0 unx    30759 tx defN 20-Jan-29 16:28 progs/rqlist.py
    -rwxrwxr-x  3.0 unx     3577 tx defN 19-Jun-27 09:21 progs/pyctl.py
    -rw-rw-r--  3.0 unx    12798 tx defN 19-Jun-27 09:21 progs/modinfo.py
    -rwxrwxr-x  3.0 unx    28104 tx defN 19-Jun-27 09:21 progs/mountshow.py
    -rw-rw-r--  3.0 unx     7176 tx defN 19-Jun-27 09:21 progs/pstree.py
    -rw-rw-r--  3.0 unx     5250 tx defN 20-Jan-29 16:32 PyKdumpInit.py
    179 files, 2329239 bytes uncompressed, 948678 bytes compressed:  59.3%
