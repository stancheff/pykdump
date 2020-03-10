User Guide
==========

The PyKdump framework provides quite a few ready to use programs to allow
users to quickly extract and process various useful information from vmcore
dump.

These in-built programs can be used to quickly fetch details about SCSI
adapters, disk devices, multipath maps, LVM volumes, TCP/IP sockets, NFS
mounts, processes holding or waiting for mutex locks and much more. Some of
these programs also provide an option to run automated checks and report
potential issues.

These programs can be accessed by loading the extension in crash environment::

    crash> extend /test/mpykdump.so
    Setting scroll off while initializing PyKdump
    /test/mpykdump.so: shared object loaded

Once the extension is loaded, the commands provided by built-in programs can be
viewed as below.
Using '-h' option with these commands will provide more details about what a
specific command does and options provided by it::

    crash> extend
    SHARED OBJECT        COMMANDS
    /test/mpykdump.so    epython xportshow crashinfo taskinfo nfsshow hanginfo
                         fregs tslog scsi scsishow dmshow pstree modinfo

The epython command in above list allows direct execution of any custom python
programs written using this framework, without a need to rebuild the whole
extension.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   epython.rst
   xportshow.rst
   crashinfo.rst
   taskinfo.rst
   nfsshow.rst
   hanginfo.rst
   scsishow.rst
   dmshow.rst
   pstree.rst
   modinfo.rst
