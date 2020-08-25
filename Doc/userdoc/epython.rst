Executing custom PyKdump programs using epython
===============================================

The PyKdump framework allows execution of newly written Python programs
without recompiling the whole extension.  If there is any custom python
program written under PyKdump framework, then it can be executed directly
using 'epython' command as shown below::

    crash> epython  <path-to-PyKdump-python-program>

For example: To run 'hello.py' PyKdump program from below location::

    $ cat hello.py
    # This is a basic PyKdump program
    from pykdump.API import*
    print("Hello PyKdump")

    crash> epython  /usr/lib64/crash/extensions/PyKdump/hello.py
    Hello PyKdump

Printing information about PyKdump environment
----------------------------------------------

After loading the extension, you can check several thinsg executing
``epython`` with some special options without any command, namely:

.. code-block:: text

  crash64> epython -h
  Usage:
    epython [epythonoptions] [progname [--ehelp] [progoptions] [progargs]]
      epythonoptions:
      ---------------
        [-h|--help]
        [-v|--version]  - report versions
        [-d|--debug n]  - set debugging level
        [-p|--path]     - show Python version and syspath
        [--ehelp]       - show extra options, common for all programs

  crash64> epython -v
   ***  C-module Information ***
    C-module version=3.2.1
    crash used for build: 7.2.8

   --- Using /home/alexs/tools/pykdump/Extension/mpykdump.so ---

   === Information About This Archive ===
      Created on Tue Aug 25 14:52:15 2020
      GLIBC: 2.27
      Python: 3.8.5
      The build is based on crash-7.2.8 X86_64
      C-bindings version 3.2.1

     --- PyKdump API Version: 3.2.1 ----

     --- Programs Included ------
      xportshow: 1.0.0
      crashinfo: 1.3.7
      taskinfo: 0.7
      nfsshow: 1.1.2
      hanginfo: 0.4.1
      scsi: 1.0.1
      fregs: 1.11
      tslog: 1.0.0
      scsishow: 0.0.2
      dmshow: 0.0.2

  crash64> epython -p
  3.8.5 (default, Aug  7 2020, 08:15:44)
  [GCC 7.5.0]
  ['.', '/home/alexs/tools/pykdump/Extension/mpykdump.so/pylib', '/home/alexs/tools/pykdump/progs', '/home/alexs/tools/pykdump/experiments', '/home/alexs/tools/pykdump/Extension/mpykdump.so', '/home/alexs/tools/pykdump/Extension/mpykdump.so/dist-packages']

  crash64> epython --ehelp
  Usage: epython <commonoptions> command ...

  Options:
    --experimental     enable experimental features (for developers only)
    --debug=DEBUG      enable debugging output
    --timeout=TIMEOUT  set default timeout for crash commands
    --maxel=MAXEL      set maximum number of list elements to traverse
    --usens=USENS      use namespace of the specified PID
    --reload           reload already imported modules from Linuxdump
    --dumpcache        dump API caches info
    --ofile=FILE       write report to FILE

You can use these *common* options for any program, they are processed
and removed before passing arguments to your programs. As a result,
these options cannot be processed in normal programs - they are
processed by framework itself

Environment variables
---------------------

PYKDUMPPATH

The 'PYKDUMPPATH' environment variable is similar to the PATH variable in
Linux.  It can be used to specify the path for Python programs written under
this framework.  After setting this variable, users can directly execute the
python program from crash environment without specifying full path:

e.g. following directory contains couple of Python programs::

    $ ls /cores/crashext/epython/storage
    dm.py  dmshow.py  rqlist.py  scsishow.py

Set the $PYKDUMPPATH variable with above path::

    $ export PYKDUMPPATH=/cores/crashext/epython/storage
    $ echo $PYKDUMPPATH
    /cores/crashext/epython/storage

The epython command provided by 'mpykdump.so' can now directly access the above
programs::

    crash> extend /usr/lib64/crash/extensions/PyKdump/mpykdump.so
    crash> epython -p
    3.7.3 (default, Oct  7 2019, 11:22:29)
         [GCC 4.4.7 20120313 (Red Hat 4.4.7-18)]
         ['.', '/cores/crashext/scsishow.so/pylib',
                        '/cores/crashext/epython/storage',
                        '/cores/crashext/scsishow.so',
                        '/cores/crashext/scsishow.so/dist-packages']

    crash> ls /cores/crashext/epython/storage
    dm.py  dmshow.py  rqlist.py  scsishow.py

    crash> epython dmshow.py
    NUMBER  NAME                 MAPPED_DEVICE    FLAGS
    dm-0    vg00-root       0xffff93d725733800    flags: 0x43      [Device suspended]
    dm-1    vg00-swap       0xffff93ee12bac000    flags: 0x43      [Device suspended]
    [...]

Changes to 'PYKDUMPPATH' variable can be made persistent by adding an entry for
it in '~/.bash_profile' file::

    e.g.
    $ cat ~/.bash_profile
    export PYKDUMPPATH="$PYKDUMPPATH:/cores/crashext/epython/storage"
