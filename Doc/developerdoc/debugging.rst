Debugging Aids
==============

There are many ready-to-use PyKdump programs included in its
distribution. To use them you do not need to know anything about
PyKdump internals - they can be used just like ``crash`` builtins.

This section is mainly of interest to developers, both framework developers and
user-program developers.

Global Options
--------------

There are some options parsed by ``pykdump.API`` itself before
arguments are passed to programs. They change global behavior and
after processing are stripped from argument list. Most important of
them are::

    op.add_option("--timeout", dest="timeout", default=120,
              action="store", type="int",
              help="set default timeout for crash commands")
    op.add_option("--maxel", dest="Maxel", default=10000,
              action="store", type="int",
              help="set maximum number of list elements to traverse")
    op.add_option("--usens", dest="usens",
              action="store", type="int",
              help="use namespace of the specified PID")

    op.add_option("--reload", dest="reload", default=0,
              action="store_true",
              help="reload already imported modules from Linuxdump")

Running Code From Your Source Tree
----------------------------------

By default, all needed framework modules are loaded directly from
*mpykdump.so* file. You can check how modules will be searched using::

  crash64> epython -p
  3.8.3 (default, May 21 2020, 13:02:14)
  [GCC 4.4.7 20120313 (Red Hat 4.4.7-18)]
  ['.', '/usr/local/lib/mpykdump64.so/pylib', '/usr/local/lib/mpykdump64.so', '/usr/local/lib/mpykdump64.so/dist-packages']

Please note that before searching for modules in *mpykdump.so* we will
check the current directory. This makes it possible to quickly write
simple ad-hoc programs, creating a file in your current directory (usually
where vmcore resides).

But if you are participating in PyKdump development using its
GIT-repository, you need to search for code in your local repository
copy before searching for it in *mpykdump.so*.

You rarely need to rebuild *mpykdump.so* - this is only needed if you
want to prepare a new binary file for your organization or if you are
working on PyKdump C-module.

To change the search path used by PyKdump, you set the shell
environment variable *PYKDUMPPATH*, e.g.::

  $ export PYKDUMPPATH=~alexs/tools/pykdump/progs:~alexs/tools/pykdump/experiments

After that, PyKdump will search these locations *before* using the
built-in *mpykdump.so*::

  crash64> epython -p
  3.8.3 (default, May 21 2020, 13:02:14)
  [GCC 4.4.7 20120313 (Red Hat 4.4.7-18)]
  ['.', '/usr/local/lib/mpykdump64.so/pylib', '/home/alexs/tools/pykdump/progs', '/home/alexs/tools/pykdump/experiments', '/usr/local/lib/mpykdump64.so', '/usr/local/lib/mpykdump64.so/dist-packages']

Please note one important exception: we still search
``/usr/local/lib/mpykdump64.so/pylib`` *before* our own path. This section
of binary module contains parts of Python Standard Library - we need
them and do not want to override them (except for some very special cases).


Controlling Debugging
---------------------

A typical program consists of the main program importing several
modules. You can add ``--debug`` option or something similar to your
main program, but how to pass this value to modules? We can always pass
it as a parameter to subroutines/methods, but this is not very
convenient. Assuming that we have modules ``mod1`` and ``mod2``, we
can set ``debug`` variable from the main module using the following
approach::

  import mod1
  mod1.debug = debug

  import mod2
  mod2.debug = debug

This works, but is rather ugly. There is another problem: importing a
module might run some code. So what if we want to display debugging
info at this stage?

PyKdump initializes Python machine only once, when you load the
extension. Before running each program it does some cleanup but
preserves many things, such as already cached symbolic
information. This significantly improves the performance if you
execute the same program multiple times (maybe with different
options/arguments).

This persistance lets us implement per-module debugging controls,
something similar to what Linux kernel does with procfs/sysfs.

In your module, you register an attribute in the following way::

  registerModuleAttr("debugDLKM",
                     default=0, help="Debug DLKM debuginfo subroutines")


This creates in this module a variable ``debugDLKM``,` initializes it
to 0, and registers this option in a session cache. Registration is
done during import of this module. There is programmatic interface to
change the values of such attributes *externally*. You can do it
easily usinge 'pyctl' command, modeled after Linux command ``sysctl``.

While ``pyctl`` command is included in binary *mypkdump.so*, it is not
registered as top-level command (i.e. not visible in ``man`` or
``help``). This is done to avoid confusing normal users. To avoid
prepending it with ``epython`` every time, you can create an alias and
put it into your *.crashrc* file.

Examples::

  crash64> epython pyctl -a
      debugDLKM       - Debug DLKM debuginfo subroutines
               currentvalue=0 default=0
      debugDeref
               currentvalue=0 default=0
      debugMP_KW      - Debug Monkey-Patching of default keywords
               currentvalue=0 default=0
      debugMemoize    - Debug Memoization
               currentvalue=0 default=0
      debugReload     - Debug reloading Python modules
               currentvalue=0 default=0

      crash64> epython pyctl debugMemoize=2

       ** Execution took   0.00s (real)   0.00s (CPU)
      crash64> epython pyctl -v debugMemoize
        debugMemoize    - Debug Memoization
                 currentvalue=2 default=0
            pykdump.Generic  func=__func
            {'pyctlname': None, 'default': 0, 'type': <class 'int'>, 'help': 'Debug Memoization'}

If you try to assign to a non-registered attribute, you will get an
error message::

  crash64> epython pyctl debugNN=2
    Unknown key: <debugNN>, skipping it



Reloading Modules
-----------------

As we do not re-initialize Python machine every time we start a
program (as long as we do not exit ``crash``), this means that
modules imported during previous command execution are staying in
memory and not reimported every time. This is good for performance, but
what if we are working on a module and would like to force its
reimport, to accommodate for changes we did?

To reload our modules, you just add ``--reload`` to you command. To see
what is being reloaded, you need to set ``debugReload``. An example:

.. code-block:: text

   crash64> taskinfo --summ
   Number of Threads That Ran Recently
   -----------------------------------
      last second     114
      last     5s     161
      last    60s     266

    ----- Total Numbers of Threads per State ------
     TASK_INTERRUPTIBLE                         896
     TASK_NONINTERACTIVE                          2
     TASK_RUNNING                                 2
     TASK_STOPPED                                 1
     TASK_TRACED                                  1
     TASK_UNINTERRUPTIBLE                       161


    ** Execution took   0.95s (real)   0.93s (CPU)

   crash64> epython pyctl debugReload=2

    ** Execution took   0.00s (real)   0.01s (CPU)
   crash64> taskinfo --summ --reload
   LinuxDump /home/alexs/tools/pykdump/progs/LinuxDump/__init__.py
   --reloading LinuxDump
   LinuxDump.percpu /home/alexs/tools/pykdump/progs/LinuxDump/percpu.py
   --reloading LinuxDump.percpu
   LinuxDump.inet /home/alexs/tools/pykdump/progs/LinuxDump/inet/__init__.py
   --reloading LinuxDump.inet
   LinuxDump.Time /home/alexs/tools/pykdump/progs/LinuxDump/Time.py
   --reloading LinuxDump.Time
   LinuxDump.inet.proto /home/alexs/tools/pykdump/progs/LinuxDump/inet/proto.py
   --reloading LinuxDump.inet.proto
   LinuxDump.BTstack /home/alexs/tools/pykdump/progs/LinuxDump/BTstack.py
   --reloading LinuxDump.BTstack
   LinuxDump.fs /home/alexs/tools/pykdump/progs/LinuxDump/fs/__init__.py
   --reloading LinuxDump.fs
   LinuxDump.Tasks /home/alexs/tools/pykdump/progs/LinuxDump/Tasks.py
   --reloading LinuxDump.Tasks
   Number of Threads That Ran Recently
   -----------------------------------
      last second     114
      last     5s     161
      last    60s     266

    ----- Total Numbers of Threads per State ------
     TASK_INTERRUPTIBLE                         896
     TASK_NONINTERACTIVE                          2
     TASK_RUNNING                                 2
     TASK_STOPPED                                 1
     TASK_TRACED                                  1
     TASK_UNINTERRUPTIBLE                       161


    ** Execution took   0.39s (real)   0.39s (CPU)


At this moment, we do not reload the modules of framework itself - the
contents of ``pykdump`` directory - as this is difficult to implement
properly (e.g. is it OK to reload the module which is responsible for
reloading - we are running code from it at this moment!).

So this approach works well for developing user programs, but not
framework itself.

Monkey-Patching Default Values for Keywords
-------------------------------------------

This started as a fun project (to better understand Python internals)
but can be really useful in some cases.

If you look at the sources of several list-traversal subroutines,
e.g. :func:`~pykdump.API.readList`, you will see that we can
optionally specify the maximum number of elements to traverse,
otherwise we use a default::

  def readList(start, offset=0, *, maxel = _MAXEL, inchead = True, warn = True):

There are several subroutines of this type in ``pykdump/highlevel.py``
and they all use as a default ``_MAXEL`` global variable set in the
beginning of this file.

The idea is to limit the number of elements in lists to traverse, both
to prevent infinite iteration or just to warn you about something
unexpected. For example, if normally list size for some kernel table
is not greater than 10000, finding more than this number during
iteration probably means memory corruption.

But in most cases we do not specify this keyword argument and expect
that the default value it good enough.

If we reach a limit during traversal, a warning is printed. To
demonstrate this, let us set the default to unreasonably low value::

  crash64> xportshow --summ --maxel=100
  ...
      We have reached the limit while reading a list maxel=100
                  from sk_for_each <- get_AF_UNIX <- TCPIP_Summarize

We print a warning and then the sequence of subroutine calls.

There are 7 subroutines/methods using this, so how can we change the
default externally? First, I used the following approach (this is not
a real subroutine, just used for illustration purposes)::

  def a(a1, maxel = None):
    maxel = maxel if (maxel is not None) else _MAXEL


and in pykdump.API we did::

  import highlevel
  ...
  highlevel._MAXEL = newvalue


Now we do it in the following way::

  def setListMaxel(newval):
      patch_default_kw(getCurrentModule(), 'maxel', newval)

A new subroutine ``patch_default_kw(mod, kname, newval)`` replaces all
default keyword arguments that have name ``kname`` in
functions/methods defined in module ``mod`` with the new value ``newval``.



Interactive Development
-----------------------

The standard Python interpreter can be run as a REPL (Read-Eval Print Loop),
which allows the user to enter Python code and see the result of running it
interactively. PyKdump supports this mode of operation as well, with a built in
program that can be run using ``epython repl``::

    crash> epython repl
    PyKdump Embedded REPL: Python 3.8.3 (default, Jul 17 2020, 16:58:36)
    [GCC 4.8.5 20150623 (Red Hat 4.8.5-39.0.3)]
    Use Ctrl-D to return to crash

    from pykdump.API import *

    >>> from LinuxDump.Tasks import TaskTable
    >>> tt = TaskTable()
    >>> tt.getByPid(332005)
    PID=332005 <struct task_struct 0xffff88341422af70> CMD=awk
    >>>
    Returning to crash

     ** Execution took  32.47s (real)   0.00s (CPU)
    crash>

This allows you to import any Python code included by PyKdump and execute it
interactively.

For the best results, your mpykdump.so should be compiled with a static readline
(as is the default, see the installation instructions). This will allow line
editing and command history. The REPL will still work without readline, but it
is less convenient to use.

When done using the REPL, use Ctrl-D to exit it. If you re-open the REPL (by
running ``epython repl`` again), your variables will be preserved::

    crash> epython repl
    PyKdump Embedded REPL: Python 3.8.3 (default, Jul 17 2020, 16:58:36)
    [GCC 4.8.5 20150623 (Red Hat 4.8.5-39.0.3)]
    Use Ctrl-D to return to crash

    from pykdump.API import *

    >>> x = 5
    >>>
    Returning to crash

     ** Execution took   3.14s (real)   0.00s (CPU)
    crash> epython repl
    PyKdump Embedded REPL: Python 3.8.3 (default, Jul 17 2020, 16:58:36)
    [GCC 4.8.5 20150623 (Red Hat 4.8.5-39.0.3)]
    Use Ctrl-D to return to crash

    from pykdump.API import *

    >>> print(x)
    5
