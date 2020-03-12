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


