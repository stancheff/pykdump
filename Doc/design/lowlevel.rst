:mod:`pykdump.lowlevel` Low-Level Objects
=========================================

.. module:: pykdump.lowelevel
   :synopsis: low-level readers and objects

.. moduleauthor:: Alex Sidorenko <asid@hpe.com>

-----------

This module implements basic types used for mapping C-objects to
Python-objects.

A general idea is like that:

* we define a number of classes that represent typical C objects, such
  as struct/union, pointer and string

* we create instances of our objects and the initialize them using
  Python-mappings to *crash* and *GDB* c-functions

* we use heuristics to map things that are not well-defined (such as:
  is ``char *ptr`` a string or a just pointer?). The idea is to use
  mappings that are probably

In following discussion, we will mostly use ``struct`` term but in
most cases the same is applicable to ``union``.

Smart Strings
-------------

C does not have real strings. They are usually represented by ``char
*`` pointers, or ``char array[]``, but this is just a convention. We
can never be sure looking at variable definition whether it really is
intended to represent a string, or maybe it is just an array of signed
1-byte integers.

Of course, we would like to convert C-strings to real Python-strings -
but the ambiguity mentioned above forces us to store some extra values
in addition to standard Python string. We analyse type of the variable
and based on it we do the following:

* for ``char *`` we read the first 256 bytes at this address, search
  for NULL byte and convert this chunk of memory to Python string. In
  addition, we store the raw bytes and address (pointer value)

* for ``char arr[n]`` we read ``n`` bytes instead of 256 bytes and
  then fo the same as in previous case

Typed Pointers
--------------

When we read pointers to struct, we need a way to record this info
instead of just returning integer address

``tPtr`` is a subclass of ``int``, so they can be used in the same
context as integers. But in addition to that, we store some extra
information:

* pointer level (1 for `*`, 2 for `*` and so on)

* typeinfo of the object this pointer refers to

* dereferencer subroutine for this pointer (cached based on type and
  pointer level)


StructResult
------------

Objects of this type are used to represent the contents of ``struct``
and/or ``union`` as read from a specific address.

It is not unusual to read many structs of the same type: reading
arrays, iterating a list or some other container. The underlying
symbolic information and methods to access struct members are the same
for all such structs; to improve the performance we use
``subStructResult`` as a metaclass to cache and share such common
data.

Another special case are *anonymous* structs. Assuming that we have
the following definition in C::

  struct A {
    int a;
    struct {
      char c;
      int i;
      void *ptr;
    } embedded;
  }

how do we cache information for embedded struct without a name? As all
StructResult instances for this type share the same data via its
metaclass, we generate a fake name)tag) for this embedded struct and
cached it.

Another unusual feature of implementation is that we do not
differentiate between struct and simple struct pointer (one star),
that is, similar Python objects will for::

  struct A a;
  struct A *ptra;

(the only difference will be in address). This is necessary for
mapping C dereferences (both dor ``.`` and arrow ``->`` operators) to
Python (just dot ``.`` operator).

So instead of ``a->b.c->d`` in C we can use just ``a.b.c.d`` in
Python.  This is more than adequate in 99% of all cases. As
``StructResult`` is implemented as subclass of ``int`` and integer
value represents its address, you can check whether it is NULL (0)
before trying to dereference.

``StructResult`` is a subclass of ``int`` and can be used
in arithmetical context, it implements pointer arithmetic according to
C standard, namely:

* (p+i) points to addr + sizeof(stype)*i
* p[i] is equivalent to (p+i)

where ``stype`` is struct type.








