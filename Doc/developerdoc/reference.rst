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
