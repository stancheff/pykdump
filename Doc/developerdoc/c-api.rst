epython command implementation
=======================================


.. highlight:: c

This module implements Python bindings to ``crash`` and ``GDB``
internal commanda and structures

.. c:function:: void cmd_epython(void)

   Run ``epython`` command as specified on ``crash`` command-line

.. c:function:: void epython_execute_prog(int argc, char *argv[], int quiet)
