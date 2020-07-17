:mod:`crash` C-module
=======================================

.. module:: crash
   :synopsis: provides crash/GDB bindings

.. moduleauthor:: Alex Sidorenko <asid@hpe.com>

--------------

This module implements Python bindings to ``crash`` and ``GDB``
internal commands and structures. Some of these subroutines are
intended for framework itself. Those of general interest are available
after ``import pydkump.API``, there is no need to ``import crash`` to
use them.

That is - in most cases, you do not need to import this module in your
own programs.


Basic Info about struct/union/enum
----------------------------------

.. function:: struct_size(structname)

   :param structname: a string with struct name, e.g.
                      *struct task_struct*. While ``crash`` lets you
                      specify simplified names without *struct*,
                      this subroutine needs proper C-syntax
   :return: size as an integer, or -1 if there is no symbolic info for
            this struct

.. function:: union_size(unionname)

   Similar to :func:`struct_size` but for unions instead of structs

.. function:: member_offset(sname, smember)

   :param sname: a string with struct name
   :param smember: a string with member name
   :return: offset as an integer, or -1 if there is no such member

.. function:: member_size(sname, smember)

   :param sname: a string with struct name
   :param smember: a string with member name
   :return: size as an integer, or -1 if there is no such member

.. function:: enumerator_value(ename)

   Interface to ``crash`` internal subroutine
   ``int enumerator_value(char *e, long *value)``

   :param ename: a string with enum name
   :return: an int with numeric value

   Example: ``WORK_CPU_NONE = enumerator_value("WORK_CPU_NONE")``


Symbol/Address Subroutines
--------------------------

.. function:: symbol_exits(symname)

   Tests whether symbol *symname* exists in this kernel (as listed by
   ``crash`` builtin ``sym`` command)

   Returns value that evaluates to `True` if it does and `False` if it
   does not

.. function:: sym2addr(symbolname)

   :param symbolname: a string with symbol name
   :return: address as an integer. 0 means that there is no such
            symbol. If there are multiple variables with this name
            (e.g. in different DLKMs), address of the first one is returned

.. function:: sym2alladdr(symbolname)

   Similar to :func:`sym2addr` but returns a list of addresses. If
   there are no matches at all, returns an empty list. If there is one
   match only, returns a list of one element

.. function:: addr2sym(addr, loose_match = False)

   Tries to find a symbol matching the given address.

   By default, it tries to find an exact match and if found, returns a
   string. If no exact match is found, returns *None*

   If we call this subroutine with ``loose_match= True``, we are
   trying to find an approximate match and return a tuple ``(name, offset)``

   Example: there is a symbol *tcp_shudown* with address 0xffffffff8147e580::

     print(crash.addr2sym(0xffffffff8147e581, True))

     ('tcp_shutdown', 1)

   In case when there is no match for loose matching we return a tuple of
   ``(None, None)``

.. function:: addr2mod(addr)

   :param addr: address as an integer
   :return: a string with module name where this address belongs, or *None*

.. _reading_memory:

Reading Memory
--------------

There are different types of memory, e.g. :data:`KVADDR`. Some of the
following subroutines let you specify the memory type as an extra
argument and some rely on default

.. function:: mem2long(bytestr, signed, array)

   This is a swiss-army knife subroutine to convert a byte string into
   integers or a list of integers. In C, we have integers of different
   sizes, signed/unsigned and arrays of integers (this subroutine can
   handle 1-dimensional arrays only). After we read a chunk of memory,
   it is represented by a byte string. Thus subroutine converts it
   according as specified by arguments. We assume that byte string
   consists of *int* for this architecture. So you cannot use this
   subroutine for dealing e.g. with ``short in a[10]``, only for
   C-objects like ``int a[10]`` or ``signed int[10]``.

   :param bytestr: a byte-string with data
   :param signed: *True/False* to specify whether integers are
                     signed or not, *unsigned* by default
   :param array: if specified, we will return a list of *array*
                 integers instead of one value


.. function:: readmem(addr, size [, mtype])

   Interface to ``crash`` builtin ``readmem()``.

   :param addr: address to read from
   :param size: how many bytes to read
   :param mtype: memory type to read, by default :data:`KVADDR`

   :return: a bytestring with data

.. function:: readPtr(addr [, mtype])

   Assuming that *addr* contains a pointer, read pointer value.

   :param addr: address
   :param mtype: memory type, by default :data:`KVADDR`

.. function:: readInt(addr, size [, signedvar [, mtype]])

   Given an address, read an integer of given *size*

   :param addr: address to read from
   :param size: integer size, according to C
                char/short/int/long/longlong specification for this
                architecture
   :param signedvar: False for ``unsigned``, True for ``signed``. If
                     not specified, we assume ``unsigned``
   :param mtype:  memory type, by default :data:`KVADDR`

.. function:: set_readmem_task(taskaddr)

   :param taskaddr: task address or zero

   * if taskaddr=0, reset readmem operations to use KVADDR
   * if taskaddr is a valid task address, set readmem operations to UVADDR
     and set the current context to this task

   :return: nothing

Conversion between Memory Types
-------------------------------

.. function:: uvtop(taskaddr, vaddr)

   Interface to ``crash`` builtin ``uvtop(tskaddr, vaddr)`` - converts
   a virtual address to physical address in the context of specified
   task

   :param taskaddr: address of ``struct task_struct``
   :param vaddr: virtual address
   :return: physical address as an integer

.. function:: phys_to_page(physaddr)

   Interface to ``crash`` bulitin ``phys_to_page(physaddr_t phys``

   :param physaddr: physical address
   :return: page as an integer

.. function:: PAGEOFFSET(vaddr)

   Interface to ``crash`` bulitin ``PAGEOFFSET(vaddr)``

Miscellaneous
-------------

.. function:: getListSize(addr, offset[, maxel = 1000])

   Assuming that *addr* points to a list head, find a total number of
   elements. The same can be done in Python easily - but C is faster
   for big lists

   :param addr: address of a structure representing a list head
   :param offset: offset or ``next`` pointer in this structure
   :param maxel: maximum number of elements to search for, that is we
                 stop iteration of we reach this limit

   :return: number of list elements found (not counting the list head
            itself)

.. function:: getFullBuckets(start, bsize, items, chain_off)

   Find full buckets in hash-tables. If we have hash-tables consisting
   of many buckets (>100,000) but just a few of them are non-empty, this
   subroutine is significantly faster than trying to do the same in
   pure Python. Useful for networking tables

   :param start: address of the hash-table
   :param bsize: hash-bucket size
   :param items: how many buckets (hash-size)
   :param chain_off: chain offset

   :return: a list of addresses of full buckets

.. function:: getFullBucketsH(start, bsize, items, chain_off)

   Similar to :func:`getFullBuckets` but for different hash-table
   (needs to be further explained ASID)

.. function:: FD_ISSET(i, fileparray)

   Interface to C-macro ``FD_ISSET``

   :param i: an index in ``fileparray``
   :param fileparray: address of ``struct fdtable *fdt`` in ``struct
                      files_struct``


.. function:: get_NR_syscalls(void)

   :return: number of system calls registered in *sys_call_table*


.. function:: get_pathname(dentry, vfsmnt)

   :param dentry:  dentry address
   :param vfsmnt: vfsmnt address

   :return: a string with pathname of this object

.. function:: setprocname(name)

   Changes the name of the currently running process - needed if we
   want to implement daemons or background processes

   :param name: a string with a new name

.. function:: is_task_active(taskaddr)

   Interface to internal ``crash`` subroutine ``is_task_active``

   :param taskaddr: address of a task

   :return: *True* for active tasks, *False* for inactive ones

.. function:: pid_to_task(pid)

   Interface to internal ``crash`` subroutine ``pid_to_task``

   :return: address of the task

.. function:: task_to_pid(taskaddr)

   Interface to internal ``crash`` subroutine ``task_to_pid``

   :return: PID of this task

.. function:: get_uptime()

   Interface to ``crash`` builtin subroutine ``get_uptime(NULL, &jiffies)``

   :return: an integer - seconds since boot

.. function:: get_task_mem_usage

Conversion of Integers
----------------------

Python integers are always signed and have arbitrary precision. As a
result, they do not behave in the same way - e.g. they do not
overflow. So to emulate C behavior we need to use special functions

.. function:: sLong(i)

   In C, the same bits sequence can represent either *signed* or
   *unsigned* integer. In Python, there is no native *unsigned*
   integer. This subroutine lets you convert a Python integer to
   *signed* assuming that integer size is that for *long* type of
   this architecture.

   :param i: Python integer of any size/value
   :return: process ``sizeof(long)`` lower bits of provided integer
            as C ``unsigned long`` and return this value as ``signed long``

   An example::

     l = 0xffffffffffffffff
     print(l, sLong(l))

     # Prints 18446744073709551615 -1


.. function:: le32_to_cpu(ulong)

   Interface to ``__le32_to_cpu`` C macro

   :param ulong: unsigned integer
   :return: converts Python integer to C ``ulong`` val, applies
            ``__le32_to_cpu(val)`` and returns a Python integer

.. function:: le16_to_cpu(uint)

   Similar to :func:`le32_to_cpu` but invoked C macro ``__le16_to_cpu``

.. function:: cpu_to_le32(uint)

   Similar to :func:`le32_to_cpu` but invoked C macro ``__cpu_to_le32``


Executing Commands
------------------

.. function:: exec_crash_command(cmd, no_stdout = 0)

   Execute a built-in ``crash`` command and return output as a
   string. There is no timeout mechanism for this subroutine

   :param cmd: a string with command name and arguments

.. function:: exec_crash_command_bg2(cmd, no_stdout = 0)

   This command opens and writes to FIFO so we expect someone to read
   it. Execution is done in the background - we fork() a child process
   that does executing with output redirected to a pipe.

   This function is used in high-level subroutine
   ``exec_crash_command_bg(cmd,  timeout = None)``

   :param cmd: a string with command name and arguments
   :return: a tuple of (fileno, pid) where *fileno* is OS filedescriptor and
            *pid* is PID of the child process

.. function:: exec_epython_command(cmd)

   :param cmd: a string with command name and arguments
   :return: nothing - at this moment we just execute the command and
            output goes to stdout

.. function:: set_default_timeout(timeout)

   Set default timeout for execution of ``crash`` built-in commands as
   done via :func:`exec_crash_command_bg2`

   :param timeout: default timeout in seconds

Registering Commands
--------------------

Normally you execute your own programs doing ``epython progname``. But
if you develop a program to be included in PyKdump for general
consumption, it makes sense to register it so that you can execute it
in ``crash`` without specifying ``epython`` every time, so that you
would be able to execute it just as ``progname``. For example,
``xportshow`` is implemented in Python but is registered.

.. function:: register_epython_prog(progname, description, shorthelp, longhelp)

   :param progname: a string with program name

   :param description: a string with description

   :param shorthelp: a string with short help

   :param longhelp: a string with detailed help

An example::

  help = '''
  Print information about tasks in more details as the built-in 'ps'
  command
  '''

  register_epython_prog("taskinfo", "Detailed info about tasks",
        "-h   - list available options",
        help)


.. function:: get_epython_cmds()

   Get a list of registered ``epython`` commands. Used internally in
   higher-level PyKdump API

   :return: a list of strings


GDB Interface
-------------

This section describes GDB-specific subroutines, intended primarily
to be used by framework developers, not end-users.

When we use ``whatis`` or ``struct`` command in ``crash``, we really
execute internal ``gdb`` commands *whatis* and *ptype* and they print
information in C-syntax. Programmatically in ``GDB`` we rely on
``struct symbol`` obtained by calling different internal ``GDB``
functions.

Python bindings to ``GDB`` internals return type info as a dictionary
with the following keys:

* basetype - type name, e.g. 'int' or 'struct net_protocol'

* codetype - GDB type, e.g. :data:`TYPE_CODE_INT`

* fname - field or variable name

* typelength - an integer, sizeof() for this type

* dims - for array, a list of integers with dimensions

* stars - for pointers, how many starts in C-syntax

* ptrbasetype - for pointers, base type of object

* uint - 0 for signed, 1 for unsigned

* bitsize - for bitfields, the size in bits. For normal fields, this
  key is not present in dictionary

* bitoffset - for bitfields, offset from the word boundary, in bits

* edef - for enumeration types, a list of pairs (name, value)

For *struct*, we have an extra key - *body* - which is a list of
dictionaries for all fields. These entries have *bitoffset* keys with
values showing what is the offset (in bits) from the beginning of this
*struct*. This is true even for normal fields (when there is no
*bitsize* key).

To make this clearer, here are some examples.

In crash::

  crash64> whatis int
  SIZE: 4

  crash64> whatis struct task_struct
  struct task_struct {
      volatile long state;
      void *stack;
  ...

  crash64> whatis inet_protos
  const struct net_protocol *inet_protos[256];

  crash64> struct list_head
  struct list_head {
      struct list_head *next;
      struct list_head *prev;
  }
  SIZE: 16


Now the same in PyKdump program::

  pp.pprint(crash.gdb_whatis("int"))
  pp.pprint(crash.gdb_whatis("struct task_struct"))
  pp.pprint(crash.gdb_whatis("inet_protos"))
  pp.pprint(crash.gdb_typeinfo("struct list_head"))


This results in output:

.. code-block:: text

   {'basetype': 'int', 'codetype': 8, 'fname': 'int', 'typelength': 4, 'uint': 0}

   {   'basetype': 'struct task_struct',
       'codetype': 3,
       'fname': 'struct task_struct',
       'typelength': 2648}

   {   'basetype': 'struct net_protocol',
       'codetype': 1,
       'dims': [256],
       'fname': 'inet_protos',
       'ptrbasetype': 3,
       'stars': 1,
       'typelength': 8}

   {   'basetype': 'struct list_head',
       'body': [   {   'basetype': 'struct list_head',
                       'bitoffset': 0,
                       'codetype': 1,
                       'fname': 'next',
                       'ptrbasetype': 3,
                       'stars': 1,
                       'typelength': 8},
                   {   'basetype': 'struct list_head',
                       'bitoffset': 64,
                       'codetype': 1,
                       'fname': 'prev',
                       'ptrbasetype': 3,
                       'stars': 1,
                       'typelength': 8}],
       'codetype': 3,
       'typelength': 16}

.. function:: get_GDB_output(cmd)

   Execute ``GDB`` command and return its output as a string

.. function:: gdb_whatis(varname)

   Interface to ``gdb_whatis`` GDB internal subroutine

   :param varname: a string that will be passed to ``gdb_whatis``

   :return: a dictionary describing this object

.. function:: gdb_typeinfo(typename)

   :param typename: a string with data type, e.g. ``struct task_struct``
   :return: a dictionary describing this type

``gdb/gdbtypes.h`` from GDB sources defines

.. code-block:: c

   enum type_code
     {
       TYPE_CODE_BITSTRING = -1,   /* Deprecated  */
       TYPE_CODE_UNDEF = 0,        /* Not used; catches errors */
       TYPE_CODE_PTR,              /* Pointer type */
       ...

Some of these values are accessible as module constants, namely:

.. data:: TYPE_CODE_PTR
.. data:: TYPE_CODE_ARRAY
.. data:: TYPE_CODE_STRUCT
.. data:: TYPE_CODE_UNION
.. data:: TYPE_CODE_ENUM
.. data:: TYPE_CODE_FUNC
.. data:: TYPE_CODE_INT
.. data:: TYPE_CODE_FLT
.. data:: TYPE_CODE_VOID
.. data:: TYPE_CODE_BOOL



Other Module-level Constants
----------------------------

.. data:: error

   Exception raised when we have a problem when executing ``crash``
   internal subroutine, e.g. bad address

.. data:: version

   A string with ``crash`` module version, e.g. "3.2.0"

The following constants are copied from ``crash`` sources, namely from
``defs.h``

  .. data:: KVADDR
  .. data:: UVADDR
  .. data:: PHYSADDR
  .. data:: XENMACHADDR
  .. data:: FILEADDR
  .. data:: AMBIGUOUS
  .. data:: PAGESIZE
  .. data:: PAGE_CACHE_SHIFT

.. data:: HZ

   An integer with the value of HZ for this vmcore

.. data:: WARNING

   A string to be used while printing warnings, at this moment set to
   "++WARNING+++"

When we build PyKdump, we use headers from a specific ``crash``
sources. We do not necessarily need to load the extension using
exactly the same version of `crash``, typically extensions are
compatible with any ``crash`` binary as long as its major version is
the same. So it is OK to build extensions using e.g. crash-7.2.3 and
use them with the binary of crash-7.2.8. But when major version of
``crash`` changes, extensions built with previous major version might
not work.

.. data:: Crash_run

   Version of ``crash`` utility that we are using at this moment

.. data:: Crash_build

   version of ``crash`` used for building the extension
