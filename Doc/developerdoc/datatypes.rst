Mapping between C and Python Data
=================================

*C* and *Python* languages are quite different. The purpose of this
document is to explain how different *C* types are represented in
*PyKdump* framework and how to emulate *C* operators such as
dereference.

Integers and Pointers
---------------------

There are many integer types in *C* and only one integer type in
*Python*. See :ref:`typesnumeric` for details about Python

While emulating C-code in Python, we should take into account that
Python integers never overflow. As a result, after doing operations on
integers, we might need to mask bits and/or do other conversions
manually, taking into account size of integers in C-code. See
:ref:`conversion_integers` for some examples

Pointer is essentially an integer. But to be able to represent
pointers to structures ot some other typed data, *PyKdump* subclasses
:class:`int` adding to it some additional data.

.. class:: tPtr(addr, ti)

   Create a typed pointer with address *addr* and TypeInfo
   *ti*. Normally you do not create these objects yourself but rather
   rely on framework API to return objects of this type when needed

   Index access for pointers is implemented as in *C*, so that you can
   do something like::

     tptr[i]

   There are two attributes implemented as properties

   .. attribute:: ptype

      returns typeinfo of thhis object

   .. attribute:: Deref

      returns a dereference for this pointer (with appropriate type)

.. class:: StructResult

   This is an object representing *struct* or *union*. In *C*, you can
   access struct members in two ways::

     // 1
     s.field;
     // 2
     s->fieldptr;

   As Python does not have ``->`` operator, both struct pointers and
   structs themselves are represented similarly, with an object that
   has address, type information, and access methods to its
   fields. Normally you do not use this class constructor yourself but
   rather rly on framework subroutines to create these objects when
   calling functions

