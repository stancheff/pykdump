epython command implementation
=======================================


.. highlightlang:: c

This module implements Python bindings to ``crash`` and ``GDB``
internal commanda and structures

.. c:function:: cmd_epython()

   Run ``epython`` command as specified on ``crash`` command-line

.. c:function:: void epython_execute_prog(int argc, char *argv[], int quiet)
