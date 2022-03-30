:mod:`pykdump.API` Main Package
=======================================

.. module:: pykdump.API
   :synopsis: main module for PyKdump programming

.. moduleauthor:: Alex Sidorenko <asid@hpe.com>

--------------

This module provides everything necessary to write PyKdump
programs. It imports other modules as needed

.. _conversion_integers:

Conversion of Integers
----------------------

Python integers are always signed and have arbitrary precision. As a
result, they do not behave in the same way as in "C" - e.g. they do not
overflow. So to emulate C behavior we need to use special functions

.. function:: cpu_to_le32(uint)

   Similar to :func:`le32_to_cpu` but invoked C macro ``__cpu_to_le32``

.. function:: le32_to_cpu(ulong)

   Interface to ``__le32_to_cpu`` C macro

   :param ulong: unsigned integer
   :return: converts Python integer to C ``ulong`` val, applies
            ``__le32_to_cpu(val)`` and returns a Python integer

.. function:: le16_to_cpu(uint)

   Similar to :func:`le32_to_cpu` but invoked C macro ``__le16_to_cpu``

.. function:: sLong(i)

   In C, the same bits sequnce can represent either *signed* or
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

.. function:: unsigned16(i)

   :param i: a Python integer
   :return: i & 0xffff

.. function:: unsigned32(i)

   :param i: a Python integer
   :return: i & 0xffffffff

.. function:: unsigned64(i)

   :param i: a Python integer
   :return: i & 0xffffffffffffffff

Reading Memory
--------------

There are different types of memory. See documentation
:ref:`reading_memory` for details about possible memory types. In
case you need to use these types, you should import them from
:mod:`crash` module explicitly.

Several low-level subroutines are automatically imported from
:mod:`crash` module (implemented in *C*), you do not
need to import them yourself. They are documented in the description
of :mod:`crash` module.

.. function:: mem2long(bytestr, signed, array)

   see :func:`crash.mem2long`

.. function:: readmem(addr, size [, mtype])

   see :func:`crash.readmem`

Reading Integers
................

.. function:: readInt(addr, size [, signedvar [, mtype]])

   Given an address, read an integer of given *size*

   See :func:`crash.readInt`


.. function:: readPtr(addr [, mtype])

   Assuming that *addr* contains a pointer, read pointer value.

   See :func:`crash.readPtr`


.. function:: readS32(addr)

   :param addr: address to read from
   :return: read 4 bytes, intepret it as signed

.. function:: readS64(addr)

   :param addr: address to read from
   :return: read 8 bytes, intepret it as signed

.. function:: readU8(addr)

   :param addr: address to read from
   :return: read 1 byte, intepret it as unsigned

.. function:: readU16(addr)

   :param addr: address to read from
   :return: read 2 byte, intepret it as unsigned

.. function:: readU32(addr)

   :param addr: address to read from
   :return: read 4 bytes, intepret it as unsigned

.. function:: readU64(addr)

   :param addr: address to read from
   :return: read 8 bytes, intepret it as unsigned

Working with Lists
------------------

There are several standard ways in Linux kernel to define lists:

* using 'struct list_head' and embedding it into another structure

* using ``next`` and/or ``prev`` pointers embedded directly in
  structure, without any ``list_head``

.. function:: LH_isempty(lh)

   :param lh: ``list head`` address or :class:`StructResult` object
              for ``list_head``

   :return: in boolean context, evaluates to *True* (when list head is
            empty) or *False*

.. function:: list_for_each_entry(start, offset = 0, maxel = None, warn = True)

   Another name for :func:`readListByHead`

.. class:: ListHead(lh, sname = None, maxel = None, warn = True)

   To read a list of structures with ``list_head`` embedded, we can
   create an instance of this class and then use it for iterations

   *lh* is address of ``list_head``

   If *sname* is specified, this is a string with structure name
   embedding our ``list_head``

   *maxel*  is the maximal number of elements to traverse

   *warn* specifies whether we would like to see warnings if we reach
    the *maxel* limit while iterating

   An object created can be used in two ways:

   * if *sname* was not specified, we should use as an iterator the
     object itself, and iterations return return a list of
     ``list_head`` results

   * if *sname* is specified, we should use as an iterator not the
     object itself, but rather ``obj.fieldname`` where *fieldname* is
     the name of structure field containing ``list_head``. In this
     case, we retirn the list of structures of *sname* type

   For example, in *C* we have

   .. code-block:: C

      static LIST_HEAD(cache_list);

      struct cache_detail {
              struct module *         owner;
              int                     hash_size;
              struct cache_head **    hash_table;
              ...
              struct list_head        others;

   Traversing this list in Python::

     cache_list = ListHead(sym2addr("cache_list"), "struct cache_detail")

     for c in cache_list.others:
         if (c.name == cname):
             details = c
             break



.. function:: readBadList(start, offset=0, maxel = _MAXEL, inchead = True)

   Similar to :func:`readList` but in case we are interested # in
   partial lists even when there are low-level errors

   :return: a tuple (partiallist, error/None)

.. function:: readList((start, offset=0, maxel = None, inchead = True, warn = True)

   :param start: address of first structure
   :param offset: offset of the pointer to the next structure in the list
   :param maxel: maximum number of elements to follow (to limit the
                 number of found elements). If not defined, uses the
                 default value (can be changed)
   :param inchead: whether to include list head itself in the output or not
   :param warn: if *True*, print a warning when maximum number of
                elements is reached

.. function:: readListByHead(start, offset = 0, maxel = None, warn = True)

   :param start: address of first structure
   :param offset: offset of the pointer to the next structure in the list
   :param maxel: maximum number of elements to follow (to limit the
                 number of found elements). If not defined,continues
                 indefinitely
   :param warn: if *True*, print a warning when maximum number of
                elements is reached

Working with Hash-Lists
-----------------------

.. function:: hlist_for_each_entry(emtype, head, member)

   Traverse hlist_node hash-lists. E.g. ``hlist_for_each_entry("struct
   xfrm_policy", table, "bydst")`` for

   .. code-block:: C

              struct xfrm_policy {
                    possible_net_t          xp_net;
                    struct hlist_node       bydst;
                    struct hlist_node       byidx;
                    ...

   :param emtype: a string with struct name
   :param head: a :class:`StructResult` object for ``struct hlist_node``
   :param member: a string with the field name embedded in out main struct

.. function:: getFullBuckets(start, bsize, items, chain_off=0)

   See :func:`crash.getFullBuckets`


Struct Lists and Arrays
-----------------------

.. function:: readSUArray(suname, startaddr, dim=0)

    Read an array of structs/unions given the structname, start and
    dimension

    Normally a list with *dim* elements is returned, but iIf dimension
    specified is zero, return a :term:`generator` instead

    :param suname: a string with struct/union name
    :param startaddr: address of the forst element
    :param dim: an integer, either number of elements to read or 0

.. function:: readSUListFromHead(headaddr, listfieldname, mystruct, maxel=None, inchead = False, warn = True)

.. function:: readStructNext(shead, nextname, maxel=None, inchead = True)

Suppressing Internal Crash/GDB Messages
---------------------------------------

When you execute crash/GDB commands, they might display errors. For
example, you try to execute an invalid command, or page is missing in
vmcore. Sometimes you want to suppress displaying this errors. This
can be dome using the following context manager:

.. class:: SuppressCrashErrors(outfile="/dev/null")

   A context manager to redirect or suppress internal crash/GDB errors
   display

   An example::

     with SuppressCrashErrors():
        try:
            print("test", exec_crash_command("set scope st_create"))
        except:
            print("Exception caught")

