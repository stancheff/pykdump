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
