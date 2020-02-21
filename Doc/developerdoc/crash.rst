:mod:`crash` C-module 
=======================================

.. module:: crash
   :synopsis: provides crash/GDB bindings

.. moduleauthor:: Alex Sidorenko <asid@hpe.com>

--------------

This module implements Python bindings to ``crash`` and ``GDB``
internal commanda and structures

.. function:: symbol_exits(symname)

   Tests whether symbol *symname* exists in this kernel (as listed by
   ``crash`` builtin ``sym`` command)

   Returns value that evaluates to `True` if it does and `False` if it
   does not

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

.. function:: get_GDB_output(cmd)

   Execute ``GDB`` command and return it soutput as a string

.. function:: exec_crash_command(cmd, no_stdout = 0)

   Executes a vuilt-in ``crash`` command and returns output as a
   string. There is no timeout mechanism for this subroutine

.. function:: exec_crash_command_bg2(cmd, no_stdout = 0)

   This command opens and writes to FIFO so we expect someone to read
   it. Execution is done in the background - we fork() a child process
   that does executing with output redirected to a pipe.

   This function is used in high-level subroutine
   ``exec_crash_command_bg(cmd,  timeout = None)``

   :return: a tuple of (fileno, pid) where *fileno* is OS filedescriptor and
            *pid* is PID of the child process

.. function:: exec_epython_command

.. function:: get_epython_cmds()

   Get a list of registered ``epython`` commands. Used internally in
   higher-level PyKdump API

   :return: a list of strings

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

.. function:: mem2long(bytestr, signed, array)

   This is a swiss-army knife subroutine to convert a byte string into
   integers or a list of integers. In C, we have integers of different
   sizes, signed/unsigned and arrays of integers (this subroutine can
   hadnle 1-dimensional arrays only). After we read a chunk of memory,
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

.. function:: uvtop(taskaddr, vaddr)

   Interface to ``crash`` builtin ``uvtop(tskaddr, vaddr)`` - converts
   a virtual address to physicall address in the context of specified
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

.. function:: readmem(addr, size [, mtype])

   Interface to ``crash`` bulitin ``readmem()``.

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

.. function:: sLong(i)

   In C, the same bits sequnce can represent either *signed* or
   *unsigned* integer. In Python, there is no native *unsigned*
   integer. This subroutine lets you convert a Python integer to
   *unsigned* assuming that integer size is that for *long* type of
   this architecture.

   :param i: Python integer of any size/value
   :return: interpret ``sizeof(long)`` lower bits of provide integer
            as C ``unsigned long`` and return this value

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
   subroutine is significantly faste thatn trying to do the same in
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

.. function:: gdb_whatis(varname)

   Interface to ``gdb_whatis`` GDB internal subroutine

   :param varname: a string that will be passed to ``gdb_whatis``

   :return: a dictionary describing this object

.. function:: gdb_typeinfo(typename)

   :param typename: a strin with data type, e.g. ``struct task_struct``
   :return: a dictionary describing this type

.. function:: set_readmem_task(taskaddr)

   :param taskaddr: task address or zero

   * if taskaddr=0, reset readmem operations to use KVADDR
   * if taskaddr is a valid task address, set readmem operations to UVADDR
     and set the current context to this task

   :return: nothing

.. function:: get_NR_syscalls(void)

   :return: number of sysstem calls registered in *sys_call_table*

.. function:: register_epython_prog

.. function:: set_default_timeout(timeout)

   Set default timeout for execution of ``crash`` built-in commands as
   done via :func:`exec_crash_command_bg2`

   :param timeout: default timeout in seconds

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

Module-level Variables and Constants
------------------------------------

.. data:: error

.. data:: version

.. data:: KVADDR

.. data:: UVADDR

.. data:: PHYSADDR

.. data:: XENMACHADDR

.. data:: FILEADDR

.. data:: AMBIGUOUS

.. data:: PAGESIZE

.. data:: PAGE_CACHE_SHIFT

.. data:: HZ

.. data:: WARNING

.. data:: Crash_run

.. data:: Crash_build

