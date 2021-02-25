// Used for separating C++ and C code for gdbspec10
#include <Python.h>

#ifdef __cplusplus
extern "C" {
#endif

void basic_test();

PyObject * py_gdb_typeinfo(PyObject *self, PyObject *args);
PyObject * py_gdb_whatis(PyObject *self, PyObject *args);
void py_gdb_register_enums(PyObject *m);

#ifdef __cplusplus
}
#endif



