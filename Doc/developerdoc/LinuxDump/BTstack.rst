:mod:`LinuxDump.BTstack` - Module for working with stacks
=========================================================

.. module:: LinuxDump.BTstack
   :synopsis: module containing tools for analyzing backtrace stacks

.. moduleauthor:: Alex Sidorenko <asid@hpe.com>

--------------

This module contains Python code built on :mod:`pykdump.API` which can help with
loading and analyzing stacks. Currently, it is implemented by running the crash
``bt`` comand and parsing its results. However, this could be replaced with a
more efficient method in the future.

Below are presented some common actions you may want to perform with this
module:

Load the current stack::

    stack = LinuxDump.BTstack.exec_bt('bt', MEMOIZE=False)[0]

Load the stack of a given PID::

    stack = LinuxDump.BTstack.exec_bt('bt PID')[0]

Group and report every stack on the system::

    allstacks = LinuxDump.BTstack.exec_bt('foreach bt')
    tt = LinuxDump.Tasks.TaskTable()
    LinuxDump.BTstack.bt_merge_stacks(allstacks, tt=tt)

List PIDs which may be executing a function::

    finder = LinuxDump.BTstack.fastSubroutineStacks()
    maybe_doing_read = finder.find_pids_byfuncname('sys_read')

Types
-----

.. class:: BTStack

   The :class:`BTStack` represents a single backtrace stack. This class should
   not be constructed manually. Instead, it should be created via the
   :func:`exec_bt()` function.

   .. attribute:: pid
      :type: int

      The PID associated with this stack.

   .. attribute:: addr
      :type: int

      The address of the task struct associated with this stack.

   .. attribute:: cpu
      :type: int

      The index of the CPU associated with this stack.

   .. attribute:: cmd
      :type: str

      The shortened command string associated with this task.

   .. attribute:: frames
      :type: list[BTFrame]

      A list of stack frames (as :class:`BTFrame`) within this stack. The list
      is ordered most recent first.

   .. method:: BTStack.hasfunc(self, func, reverse=False)

      Tells whether this stack contains the given function, and where.

      Returns false when the stack does not contain the function. When the stack
      does contain the function, return a 2-tuple giving information about its
      location. The first element of the tuple is the frame index, and the
      second element is the matched portion of the function name (as ``func`` is
      treated as a regexp). When ``reverse`` is True, find the last stack frame
      rather than the first.

      .. note::
         Note that when using ``reverse=True``, the frame index returned from
         this function is also reversed. That is, the last frame of the stack
         would have index 0.

      :param func: A precompiled regexp, or a string which will be complied as a
        regexp, to search for in the stack.
      :type func: compiled regexp or str
      :param reverse: If True the last occurrence of this function rather than
        the first.
      :type reverse: bool
      :returns: False when not found. When found, returns a tuple of (frame
        index, matched function name)
      :rtype: either False, or (int, str)

   .. method:: BTStack.getSimpleSignature(self)

      Return a string "signature" which identifies which functions are called in
      this stack. The signature does not include offsets, which identify
      /exactly/ where a function was called.

      :returns: A string like: ``function_one/function_two/function_three``
      :rtype: str

   .. method:: BTStack.getFullSignature(self)

      Return a string "signature" which identifies not just the functions that
      are called in this stack, but also offsets, indices, and any data in the
      stack frame.

      :returns: A long string containing the ``repr()`` of every frame
      :rtype: str

   .. method:: BTStack.simplerepr(self)

      Return a simple string representation of the stack which includes only
      function names and indices.

      :rtype: str


.. class:: BTFrame

   This class represents a single frame on the stack. Each attribute of this
   class is populated by the ``bt`` output. When fields are not present, a
   default value of ``-1`` (for integers) or ``''`` (for strings) is stored.

   This class is not typically created by a user, instead it is returned by
   :func:`exec_bt()` or another function of this module.

   .. attribute:: level
      :type: int

      At what index into the stack is this frame? The most recent stack frame
      would have a level of 0.

      .. note::

         This index is reported by crash. (e.g. ``#0 [addr] ...``). For some
         frames (such as exception frames), there is no index, and this remains
         at its default value of -1. Frames occurring after this in the
         backtrace will be offset. If you wish to have a reliable value, use the
         index in the :attr:`BTStack.frames` list.

   .. attribute:: addr
      :type: int

      The return address from this stack frame.

   .. attribute:: frame
      :type: int

      The address of the return address within the stack, which is nearly (but
      not exactly) the frame pointer.

   .. attribute:: func
      :type: str

      The name of the function which this stack frame was executing.

   .. attribute:: via
      :type: str

      Some stack frames include entries like ``error code (via page_fault) at
      ...``. This attribute contains the text of this via field, or a default of
      the empty string if it does not exist.

   .. attribute:: offset
      :type: int

      The offset of the return address within the function being executed. For
      example, the return address of a function might be represented as
      ``sys_mprotect+0x16b``. In this return address, ``sys_mprotect`` is the
      function, and ``0x16b`` is the offset from that function. The actual
      address could be computed via ``sym2addr(frame.func) + frame.addr``.

   .. attribute:: data
      :type: list[str]

      The data field is a list (potentially empty) of any lines of text which
      occur in the backtrace text following the stack frame line. Each line is a
      string within the list, and the strings do not contain trailing newlines.

      One sort of data which may occur in this field is a register dump, from a
      system call or exception. Another sort of data may be the stack contents,
      if this frame came from a ``bt -a``.

   .. method:: simplerepr(self)

      Return a simple string representation of this frame, showing only its
      index and the function name.

      :rtype: str

   .. method:: fullstr(self)

      Return a multi-line string containing full details of every field in this
      class.

      :rtype: str


.. class:: fastSubroutineStacks

   This object can be used to search for stacks which are executing a certain
   function. On creation, this class needs to load a lot of data for the search,
   but once created, the returned object can be used multiple times to identify
   tasks which may be executing a current function::

       finder = fastSubroutineStacks()
       maybe_doing_read = finder.find_pids_byfuncname('sys_read')
       maybe_selecting = finder.find_pids_byfuncname('sys_select')

   .. method:: find_pids_byfuncname(self, funcnames):

      Use this instance's indexed task data to search for stacks which may be
      executing functions.

      :param funcnames: Either a string, or a compiled regular expression. If it
        is a string, then it may be specified like so:
        ``function_one|function_two``. That is, multiple functions may be
        listed, separated by a pipe character. If the argument is a regular
        expression, then we search for stacks executing a function which matches
        that regexp.
      :type funcnames: str or regexp
      :returns: A set of pids. This set simply contains pids which appear to be
        executing this function (because ``bt -t`` reported that symbol on the
        stack). There may be false positives! Use :func:`verifyFastSet()` to
        remove any false positives, by actually parsing the stacks for each PID.
      :rtype: set[int]

Functions
---------

.. function:: exec_bt(crashcmd=None, text=None, bg=False, MEMOIZE=True)

   Create (potentially multiple) :class:`BTStack` instances by running a command
   or parsing text.

   This function either executes the crash command ``crashcmd`` and parses the
   resulting stack descriptions, or it directly parses the text given in
   ``text``. Either ``crashcmd`` or ``text`` must be specified.

   Using this function to retrieve the current task's backtrace::

       stack = exec_bt('bt', MEMOIZE=False)[0]

   Using this function to retrieve backtraces from every CPU::

       stack_list = exec_bt('bt -a')

   :param crashcmd: A crash command to execute which will return a backtrace,
     e.g. ``bt PID`` or ``bt -a``.
   :type crashcmd: str
   :param text: Text which contains a backtrace already.
   :type text: str
   :param bg: Whether we should use :func:`exec_crash_command_bg()` to execute
     ``crashcmd`` in the background. This is mainly useful if the command
     execution will take a long time and may need to be timed out. Commands
     which contain ``foreach`` or ``-a`` are automatically run in the
     background.
   :type bg: bool
   :param MEMOIZE: Should the result of this function be cached? This should be
     set to False when using ``text`` to parse an existing string, since parsing
     is fast and need not waste cache space. This should also be set to False
     when executing a command whose output may change, such as ``bt`` (as the
     output would change if the current PID is updated with ``set``).
   :type MEMOIZE: bool

.. function:: bt_mergestacks(btlist, precise=False, count=1, reverse=False, tt=None, verbose=0)

   Group stacks based on their signature and display counts for each one.

   Given a list of :class:`BTStack`'s, identify and group which ones involve the
   same function calls, and print a report for all grouped stacks.

   Example: group and analyze all stacks of a vmcore::

       from LinuxDump.BTstack import exec_bt, bt_mergestacks
       from LinuxDump.Tasks import TaskTable

       allstacks = exec_bt('foreach bt')
       tt = TaskTable()
       bt_merge_stacks(allstacks, tt=tt)

   This code could produce sample output such as:

   .. code::

        ------- 56 stacks like that: ----------
          #0   __schedule
          #1   schedule
          #2   do_nanosleep
          #3   hrtimer_nanosleep
          #4   sys_nanosleep
          #5   system_call_fastpath
            youngest=0s(pid=1234), oldest=81036s(pid=5678)

           ........................
             command_1                      2 times
             command_2                      1 times
             command_3                      1 times
             command_4                      52 times

   :param btlist: A list of :class:`BTStack` objects
   :type btlist: list[BTStack]
   :param precise: When True, use :meth:`BTStack.getFullSignature()` to compare
     stacks. The default (False) is to use :meth:`BTStack.getSimpleSignature()`.
   :type precise: bool
   :param count: Only report groups which have at least this many members
   :type count: int
   :param reverse: When True, report groups in descending order (by member
     count). The default (False) is to report in ascending order.
   :type reverse: bool
   :param tt: An optional :class:`LinuxDump.Tasks.TaskTable` object which may
     be used to provide additional information about groups (youngest and oldest
     in the sample output above).
   :type tt: LinuxDump.Tasks.TaskTable
   :param verbose: Specify verbose=1 (or True) in order to output a list of PIDs
     for each group.
   :type verbose: int

.. function:: verifyFastSet(dset, func)

   Remove false positives from a set of PIDs which may be executing a function.

   Given a set of PIDs (e.g., returned from
   :meth:`fastSubroutineStacks.find_pids_byfuncname()`), load each stack and
   verify that the PID is actually executing ``func``. If not, removes that pid
   from ``dset``.

   :param dset: A set of PIDs
   :type dset: set[int]
   :param func: A string (or regexp) to test whether it is contained by a stack.
     This parameter is interpreted by :meth:`BTStack.hasfunc()`, see the
     documentation of that method for further details.
   :type func: str or regexp
