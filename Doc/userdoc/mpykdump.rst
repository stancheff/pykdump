PyKdump - Python crash API (mpykdump)
=====================================

SYNOPSIS
--------
PyKdump crash extension - /usr/lib64/crash/extensions/PyKdump/mpykdump.so

DESCRIPTION
-----------

PyKdump framework provides Python bindings to GDB/crash internals. It can be
used to create Python based programs to automate the vmcore analysis and
quickly process various information from the vmcores. The current version of
PyKdump is standardized on Python 3.

Automating the vmcore analysis requires programatic analysis of various data
structures e.g. linked lists, structures, unions, enums and various global
variables. The PyKdump framework provides extensive set of built-in
API calls which can be used to fetch required structures, symbols and process
them in Python programs.

To allow the kernel data structures to be processed within Python programs, the
‘PyKdump’ framework first maps the C-structures used within Linux kernel to
the Python objects.  For example: PyKdump maps C ‘struct’ and ‘union’ by
creating corresponding Python objects with attributes matching the respective
field names of C struct/union.  Other C data types are mapped to similar
Python types e.g. C ‘int’ is mapped to Python ‘integer’.  Also, most operators
in C are mapped to similar Python operators.

The 'mpykdump.so' extension comprises of:

    | o Embedded Python interpreter
    | o Interface module to crash internals
    | o Subset of Python Standard Library
    | o Standard tools built on top of PyKdump as listed below

The extension file is constructed as a shared library with ZIP-archive
appended.  This extension includes Python3 interpreter (embedded) and
a comprehensive subset of Python3 Standard  Library (strings, sockets, option
parsers, itertools etc.) but not the whole library (as it is huge). This
design makes it completely independent on Python installed on the host where
you do dump analysis.

There are several practical programs already developed using this framework
that can be used immediately:

**xportshow** - Displays information about connections and sockets

**crashinfo** - Shows general information about kernel dump

**scsishow**  - Shows SCSI subsystem information from the dump

**dmshow**    - Shows device-mapper, multipath and lvm information

**taskinfo**  - Prints process/task status information as captured at the time
of crash

**nfsshow**   - Prints NFS client/server information from the dump

**hanginfo**  - Summarizes the information about hung tasks

EXAMPLES
--------
The mpykdump extension can be loaded in crash environment as::

    crash> extend /usr/lib64/crash/extensions/PyKdump/mpykdump.so

To view the ready to use programs::

    crash> extend
    SHARED OBJECT                                    COMMANDS
    /usr/lib64/crash/extensions/PyKdump/mpykdump.so  epython xportshow crashinfo taskinfo
                                                     nfsshow hanginfo fregs tslog scsi
                                                     scsishow dmshow pstree modinfo

As soon as the extension is loaded, any of the above programs can be executed
as normal command in crash environment:

For example, running dmshow program to review lvm information::

    crash>  dmshow --lvs
    LV DM-X DEV   LV NAME      VG NAME           OPEN COUNT       LV SIZE (MB)     PV NAME
    dm-0          lv_root      vg_system                  1           28156.00     sda
    dm-1          lv_swap      vg_system                  1            2048.00     sda
    dm-2          lv_app2      vg_app2                    1           20476.00     sdd
    dm-3          lv_app1      vg_app1                    1          425980.00     sdc
    dm-4          lv_swap2     vg_swap2                   1           14332.00     sdb
    dm-5          lv_var       vg_system                  1           18432.00     sda
    dm-6          lv_tmp       vg_system                  1            2048.00     sda
    
    ** Execution took   1.12s (real)   1.11s (CPU)
    crash>

Running hanginfo::

    crash> hanginfo
    *** UNINTERRUPTIBLE threads, classified ***
    
    ================== Waiting in io_schedule ==================
    ... 7 pids. Youngest,oldest: 2757, 1787  Ran ms ago: 80427, 227483
    sorted by ran_ago, youngest first
    [2757, 1785, 1519, 809, 13462, 17140, 1787]
    
    ********  Non-classified UN Threads ********** 5 in total
    
    ------- 1 stacks like that: ----------
    #0   schedule
    #1   start_this_handle
    #2   jbd2_journal_start
    #3   ext4_journal_start_sb
    #4   ext4_dirty_inode
    #5   __mark_inode_dirty
    #6   file_update_time
    #7   __generic_file_aio_write
    #8   generic_file_aio_write
    #9   ext4_file_write
    #10  do_sync_write
    #11  vfs_write
    #12  sys_write
    #13  sysenter_dispatch
    #14  ia32_sysenter_target
    #15  ia32_sysenter_target
    [...]

The '-h' argument with above programs will provide more information about the
options supported by it.

PyKdump framework also allows execution of newly written Python programs
without recompiling the whole extension.  If there is any custom python
program written under PyKdump framework, then it can be executed directly
using epython command as shown below::

    crash> epython  <path-to-PyKdump-python-program>

For example: To run hello.py PyKdump program from below location::

    $ cat hello.py
    # This is a basic PyKdump program
    from pykdump.API import*
    print("Hello PyKdump")
    
    crash> epython  /usr/lib64/crash/extensions/PyKdump/hello.py
    Hello PyKdump

ENVIRONMENT
-----------

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

The epython command provided by mpykdump.so can now directly access the above
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

Changes to $PYKDUMPPATH variable can be made persistent by adding an entry for
it in ~/.bash_profile file::

    e.g.
    $ cat ~/.bash_profile
    export PYKDUMPPATH="$PYKDUMPPATH:/cores/crashext/epython/storage"

'crashrc' file:

To automatically load the crash extensions at the start of crash session, add
the entry in .crashrc file::

    $ cat ~/.crashrc
    extend /usr/lib64/crash/extensions/PyKdump/mpykdump.so

SEE ALSO
--------
o Upstream project page:
<https://sourceforge.net/projects/pykdump>

o Programmatic Kernel Dump Analysis On Linux:
<https://www.kernel.org/doc/ols/2009/ols2009-pages-251-262.pdf>

o DevConf.CZ talk on PyKdump:
<http://people.redhat.com/mgandhi/presentation_pykdump.pdf>

crash(8), gdb(1)
