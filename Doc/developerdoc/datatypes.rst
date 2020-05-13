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
pointers to structures or other typed data, *PyKdump* subclasses
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

      returns typeinfo of this object

   .. attribute:: Deref

      returns a dereference for this pointer (with appropriate type)


As Python does not have ``->`` operator, both struct pointers and
structs themselves are represented similarly, with an object that has
address, type information, and access methods to its fields. Normally
you do not use this class constructor yourself but rather rely on
framework subroutines to create these objects when calling
functions. We will describe different methods of this class in the
next section.

Working with Structs and Unions
-------------------------------

In the following discussion we will mainly talk about *struct*, but in
most cases the same methods are applicable to *union* objects as
well. PyKdump uses the same class to represent both of them.

As has been mentioned in previous section, there is no difference in
representing between a *struct* and a pointer to a *struct*. In *C*
they both have address and only acess to their fields is
different. For example:

.. code-block:: c

  struct A {
     int ifield;
     ...
  };

  struct A a;
  struct A *ap;

  a.ifield;   // field value
  &a;         // struct address

  ap;         // a pointer with struct address
  ap->ifield; // field value

In Python, we will get a :class:`StructResult` object in both
cases.

Dereference Chains
..................

Assuming that in *C* we have the following:

.. code-block:: c

  result = a->f1.f2.f3->f4;  // result variable should be of appropriate type

we will use the following in Python::

  result = a.f1.f2.f3.f4

PyKdump analyzes intermediate fields type and intepretes them as
structs or pointer to structs as needed, so that we ultimately reach
*f4* value. Please note that this works for simple pointers only, not
to pointer to a pointer like ``struct B **dp;``. The type of *result*
object will be as needed, according to its C-definition.

Useful Methods and Fields of  :class:`StructResult`
...................................................

.. class:: StructResult

   This is an object representing *struct* or *union*. It is created
   by framework as needed, as a result of calling subroutines to read
   structs or as a result of dereference.

   .. note::

      In most cases, we obtain instances of subclasses of this class,
      one per *C*-struct. This is an optimization as this lets us
      analyze symbolic info obtained from GDB once only and cache it
      as subclass class methods

.. method:: __len__()

   :return: an integer with struct size

.. method:: __str__()

   :return: q string suitable for printing, e.g.::

     <struct nfs_client 0xffff88042e947000>

.. method:: castTo(sname)

   Analog of type-casting in *C*

   :param sname: a string with struct name
   :return: an object of a new type

   Example::

     skbhead = sd.input_pkt_queue.castTo("struct sk_buff")

.. method:: Dump(indent = 0)

   Dump object contents for debugging purposes, with indentation if needed

.. method:: Eval(estr)

   This method is useful if we have a :class:`StructResult` object
   and want to do a complex dereference. For example, our object is
   ``S``, it has a field ``a`` which is another struct and we want to do
   something like::

     S.a.b.c


   :param estr: a string describing a dereference chain, possibly with
                multiple dereferences, such as "a.b.c" for example
                above

   :return: result of dereference

   This mainly is useful for performance reasons. When we do::

     S.a.b.c

   this does dereferencing sequentially. But if we do::

     S.Eval("a.b.c")

   this creates an optimized dereferencer for "a.b.c" chain, caches it
   and next time reuses it


.. method:: fieldOffset(fname)

   :param name: a string with field name
   :return: an integer with offset of this field

.. method:: hasField(fname)

   :param fname: a string with filed name
   :return: whether a filed with this name exist in this *struct*

   Example::

     if t.hasField("rlim"):
         ...

.. method:: isNamed(sname)

   :param sname: a string with struct name
   :return: whether this instance represents *struct* with such name

   Example::

     o.isNamed("struct sock")

.. method:: shortStr()

   when we want to display struct name and address in our programs, we
   usually rely on str() subroutine. This method is useful when we
   want to save space (e.g. to fit output into 80-char string). So we
   do not display *struct/union* like __str__ does, e.g.::

     <nfs_client 0xffff88042e947000>
