/* Python extension to interact with CRASH - GDB-specific subroutines

   This is C++-code, intended to be used with crash based on GDB10
   and later


// --------------------------------------------------------------------
// (C) Copyright 2021 Hewlett-Packard Enterprise Development LP
//
// Author: Alex Sidorenko <asid@hpe.com>
//
// --------------------------------------------------------------------

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
*/

#define __CONFIG_H__ 1
#include "defs.h"
#include "gdbtypes.h"
#include "expression.h"
#include "value.h"

// For debugging. We cannot include "defs.h" from top-level crash directory
// as it conflicts with gdb/defs.h
extern FILE *fp;

#include <Python.h>
#include "gdbspec.h"

// The following macros wre available in gdbtypes.h for older GDB,
// but not for GDB10. We copy them from gdb/symtab.c

#define TYPE_CODE(t)	(t->code ())
#define TYPE_TAG_NAME(t) (TYPE_MAIN_TYPE(t)->name)
#define TYPE_NFIELDS(t) (t->num_fields ())
#define TYPE_NAME(t) (t->name ())
#define TYPE_FIELD_TYPE(t, i) (t->field (i).type ())
#define CHECK_TYPEDEF(TYPE)                     \
  do {                                          \
    (TYPE) = check_typedef (TYPE);              \
  } while (0)

// ------------ for reference pusposes, in case these subroutines ------
//              change again in future releases of GDB
//
// ..... A list of GDB internal subroutines we use: ..................
//
// lookup_symbol(char const*, block const*, domain_enum_tag,
//                            field_of_this_result*)
// check_typedef(type*)
// get_array_bounds(type*, long*, long*)
// parse_expression(char const*, innermost_block_tracker*)
// evaluate_type(expression*)
// value_type(value const*)
//
// ........... Possible exceptions ..................................
// gdb_exception
// gdb_exception_error

extern int debug;
extern PyObject *crashError;

static void do_SU(struct type *type, PyObject *dict);
static void do_func(struct type *type, PyObject *dict);
static void do_enum(struct type *type, PyObject *pitem);
static void do_ftype(struct type *ftype, PyObject *item);

static void
my_error_hook(void)  {
  //printf("Error hook\n");
}

int
myDict_SetCharChar(PyObject *v, const char *key, const char *item) {
	PyObject *iv;
	int err;
	iv = PyUnicode_FromString(item);
	if (iv == NULL)
		return -1;
	err = PyDict_SetItemString(v, key, iv);
	Py_DECREF(iv);
	return err;
}


static void
do_ftype(struct type *ftype, PyObject *item) {
  const char *tagname = TYPE_TAG_NAME(ftype);
  //struct type *range_type;
  struct type *tmptype;

  PyObject *v;

  char buf[256];

  int i;

  int stars = 0;
  int dims[4] = {0,0,0,0};
  int ndim = 0;

  int codetype = TYPE_CODE(ftype);
  const char *_typename = TYPE_NAME(ftype);
  PyObject *fname;
  PyObject *ptr;
  PyObject *pdims;

  if(TYPE_STUB(ftype) && tagname) {
    struct symbol *sym = lookup_symbol(tagname, NULL, STRUCT_DOMAIN,
                                       NULL).symbol;
    if(sym) {
      ftype=sym->type;
    }
  }

  switch (codetype) {
  case TYPE_CODE_STRUCT:
  case TYPE_CODE_UNION:
    v = PyUnicode_FromString("fname");
    fname = PyDict_GetItem(item, v);
    Py_DECREF(v);

    v = PyUnicode_FromString("stars");
    ptr = PyDict_GetItem(item, v);
    Py_DECREF(v);
    /* Expand only if we don't have tagname or fname */
    if (tagname != NULL) {
      if (codetype == TYPE_CODE_STRUCT)
	sprintf(buf, "struct %s", tagname);
      else
	sprintf(buf, "union %s", tagname);
      if (fname == NULL && !ptr)
	do_SU(ftype, item);
    } else {
      // this seems to be an anonymous/embedded struct, that is without
      // a name. We will assign a fake name for it later (to be used for
      // caching) but we need to expand its body right now
      if  (codetype == TYPE_CODE_STRUCT)
	sprintf(buf, "struct");
      else
	sprintf(buf, "union");
      // Expand even if this is a pointer. Before refactoring done last year,
      // logic was different. Do not fully remove the test yet, just disable it
      if (TRUE || !ptr)
	do_SU(ftype, item);
    }
    myDict_SetCharChar(item, "basetype", buf);
    break;
  case TYPE_CODE_ENUM:
    if (tagname != NULL) {
      sprintf(buf, "enum %s", tagname);
      do_enum(ftype, item);
    } else {
      /* Untagged enum */
      sprintf(buf, "enum");
      do_enum(ftype, item);
    }
    myDict_SetCharChar(item, "basetype", buf);
    break;
  case TYPE_CODE_PTR:
    tmptype = ftype;
    do {
      stars++;
      tmptype = TYPE_TARGET_TYPE(tmptype);
    } while (TYPE_CODE(tmptype) == TYPE_CODE_PTR);

    if (TYPE_CODE(tmptype) == TYPE_CODE_TYPEDEF) {
      const char *ttypename = TYPE_NAME(tmptype);
      if (ttypename)
	myDict_SetCharChar(item, "typedef", ttypename);
      CHECK_TYPEDEF(tmptype);
    }

    v =  PyLong_FromLong(stars);
    PyDict_SetItemString(item, "stars", v);
    Py_DECREF(v);

    v = PyLong_FromLong(TYPE_CODE(tmptype));
    PyDict_SetItemString(item, "ptrbasetype", v);
    Py_DECREF(v);

    do_ftype(tmptype, item);
    break;
  case TYPE_CODE_FUNC:
    myDict_SetCharChar(item, "basetype", "(func)");
    do_func(ftype, item);
    break;
  case TYPE_CODE_TYPEDEF:
    /* Add extra tag - typedef name. This is useful
       in struct/union case as we can cache info based on it */
    if (_typename)
      myDict_SetCharChar(item, "typedef", _typename);
    CHECK_TYPEDEF(ftype);
    do_ftype(ftype, item);
    break;
  case TYPE_CODE_INT:
    v= PyLong_FromLong(TYPE_UNSIGNED(ftype));
    PyDict_SetItemString(item, "uint", v);
    Py_DECREF(v);
    myDict_SetCharChar(item, "basetype", TYPE_NAME(ftype));
    break;
  case TYPE_CODE_ARRAY:
    /* Multidimensional C-arrays are visible as arrays of arrays.
       We need to recurse or iterate to obtain all dimensions
    */
    //printf("TYPE_CODE_ARRAY\n");
    do {
      LONGEST low_bound, high_bound;
      int dim;
      if (!get_array_bounds(ftype, &low_bound, &high_bound))
	dim = 0;
      else
	dim = high_bound + 1;

      ftype= TYPE_TARGET_TYPE(ftype);
     /* The following worked with older GDB, but not with 7.3.1
      range_type = TYPE_FIELD_TYPE (ftype, 0);
       dims[ndim++] = TYPE_FIELD_BITPOS(range_type, 1)+1;
      */
      //printf(" ndim=%d l=%ld\n", ndim, high_bound);
      dims[ndim++] = dim;
    } while (TYPE_CODE(ftype) == TYPE_CODE_ARRAY);

    /* Reduce typedefs of the target */
    if (TYPE_CODE(ftype) == TYPE_CODE_TYPEDEF) {
      const char *ttypename = TYPE_NAME(ftype);
      if (ttypename)
	myDict_SetCharChar(item, "typedef", ttypename);
      CHECK_TYPEDEF(ftype);
    }

    do_ftype(ftype, item);
    pdims = PyList_New(0);
    for (i=0; i < ndim; i++) {
      v = PyLong_FromLong(dims[i]);
      PyList_Append(pdims, v);
      Py_DECREF(v);
    }

    PyDict_SetItemString(item, "dims", pdims);
    Py_DECREF(pdims);
    break;
  default:
    myDict_SetCharChar(item, "basetype", TYPE_NAME(ftype));
    //break;
  }
  /* Set CODE_TYPE. For arrays and typedefs it should already be
     reduced (we detect array by dims, and we are not interested
     in typedef. But for pointers we are interested both in
     original CODE_TYPE (pointer) and target type (when all
     stars are removed)
  */
  v = PyLong_FromLong(TYPE_CODE(ftype));
  PyDict_SetItemString(item, "codetype", v);
  Py_DECREF(v);

  v = PyLong_FromLong(TYPE_LENGTH(ftype));
  PyDict_SetItemString(item, "typelength", v);
  Py_DECREF(v);

}

static void
do_SU(struct type *type, PyObject *pitem) {
  int nfields =   TYPE_NFIELDS(type);
  int i;
  PyObject *v;

  PyObject *body = PyList_New(0);
  PyDict_SetItemString(pitem, "body", body);

  for (i=0; i < nfields; i++) {
    PyObject *item = PyDict_New();
    PyList_Append(body, item);
    struct type *ftype = TYPE_FIELD_TYPE(type, i);
    const char *fname = TYPE_FIELD_NAME(type, i);
    int boffset = TYPE_FIELD_BITPOS(type, i);
    int bsize = TYPE_FIELD_BITSIZE(type, i);

    myDict_SetCharChar(item, "fname", fname);
    if (bsize) {
      v = PyLong_FromLong(bsize);
      PyDict_SetItemString(item, "bitsize", v);
      Py_DECREF(v);
    }

    v = PyLong_FromLong(boffset);
    PyDict_SetItemString(item, "bitoffset", v);
    Py_DECREF(v);

    do_ftype(ftype, item);
    Py_DECREF(item);

  }
  Py_DECREF(body);

}


static void
do_enum(struct type *type, PyObject *pitem) {
  int nfields =   TYPE_NFIELDS(type);
  int i;
  PyObject *n, *v;		/* Name, Value */

  PyObject *edef = PyList_New(0);
  PyDict_SetItemString(pitem, "edef", edef);


  for (i=0; i < nfields; i++) {
    PyObject *item = PyList_New(0);
    //struct type *ftype = TYPE_FIELD_TYPE(type, i);
    const char *fname = TYPE_FIELD_NAME(type, i);
    long bp = TYPE_FIELD_BITPOS (type, i);
    n = PyUnicode_FromString(fname);
    v = PyLong_FromLong(bp);
    PyList_Append(item, n);
    PyList_Append(item, v);
    Py_DECREF(n);
    Py_DECREF(v);

    PyList_Append(edef, item);
    Py_DECREF(item);
  }
  Py_DECREF(edef);
}

static void
do_func(struct type *type, PyObject *pitem) {
  int nfields =   TYPE_NFIELDS(type);
  int i;
  char buf[256];

  PyObject *body = PyList_New(0);
  PyDict_SetItemString(pitem, "prototype", body);

  /* Function return type */
  struct type *return_type= TYPE_TARGET_TYPE(type);
  PyObject *item = PyDict_New();
  PyList_Append(body, item);
  myDict_SetCharChar(item, "fname", "returntype");
  do_ftype(return_type, item);
  Py_DECREF(item);

  for (i=0; i < nfields; i++) {
    struct type *ftype = TYPE_FIELD_TYPE(type, i);
    PyObject *item = PyDict_New();
    PyList_Append(body, item);
    sprintf(buf, "arg%d", i);
    myDict_SetCharChar(item, "fname", buf);

    do_ftype(ftype, item);
    Py_DECREF(item);
  }
  Py_DECREF(body);
}

PyObject * py_gdb_typeinfo(PyObject *self, PyObject *args) {
  char *_typename;
  struct type *type;
  expression_up expr;
  struct value *val;

  if (!PyArg_ParseTuple(args, "s", &_typename)) {
    PyErr_SetString(crashError, "invalid parameter type");
    return NULL;
  }
  if (debug > 1)
    printf("gdb_typeinfo(%s)\n", _typename);


  // ----------------------------------------------
  //printf("GDB: %s\n", typename);
  try {
    expr = parse_expression (_typename);
    val = evaluate_type (expr.get());

    type = value_type(val);

    if (type == NULL)
      my_error_hook();

    PyObject *topdict =  PyDict_New();
    do_ftype(type, topdict);
    return topdict;
  } catch (const gdb_exception_error &ex) {
    PyErr_SetString(crashError, "PyKdump/GDB error");
    return NULL;
  }


  // ----------------------------------------------

}

PyObject * py_gdb_whatis(PyObject *self, PyObject *args) {
  char *varname;

  expression_up expr;
  struct value *val;
  struct type *type;

  if (!PyArg_ParseTuple(args, "s", &varname)) {
    //PyErr_SetString(crashError, "invalid parameter type");
    fprintf(fp, "invalid parameter type\n");
    return NULL;
  }

  if (debug > 1)
    printf("gdb_whatis(%s)\n", varname);

  try {

    expr = parse_expression (varname);
    val = evaluate_type (expr.get());

    type = value_type(val);

    //printf("vartype=%d\n", TYPE_CODE(type));

    PyObject *item = PyDict_New();
    myDict_SetCharChar(item, "fname", varname);


    do_ftype(type, item);
    return item;
  } catch (const gdb_exception_error &ex) {
    PyErr_SetString(crashError, "PyKdump/GDB error");
    return NULL;
  }
}

// Register enums needed to be used for type-analysis
#define REGISTER_ENUM(name) PyModule_AddObject(m, #name, PyLong_FromLong(name))

void py_gdb_register_enums(PyObject *m) {
  REGISTER_ENUM(TYPE_CODE_PTR);
  REGISTER_ENUM(TYPE_CODE_ARRAY);
  REGISTER_ENUM(TYPE_CODE_STRUCT);
  REGISTER_ENUM(TYPE_CODE_UNION);
  REGISTER_ENUM(TYPE_CODE_ENUM);
  REGISTER_ENUM(TYPE_CODE_FUNC);
  REGISTER_ENUM(TYPE_CODE_INT);
  REGISTER_ENUM(TYPE_CODE_FLT);
  REGISTER_ENUM(TYPE_CODE_VOID);
  REGISTER_ENUM(TYPE_CODE_BOOL);
}

//
// --------------- Basic testing -------------------------------
//
// This is need on debugging stage only, Python is not used here

extern "C" {
void basic_test() {
  expression_up expr;
  struct value *val;
  struct type *type;
  const char *fname;
  int idx;
  int stars = 0;

  printf("Before parse_expression\n");
  try {
    expr = parse_expression ("struct device");
    //type = expr->elts[1].type;
    val = evaluate_type (expr.get());
    type = value_type(val);
    printf("Numer of fields: %d\n", type->num_fields ());
    for (idx = 0; idx < type->num_fields (); idx++) {
      struct type *ftype = type->field (idx).type ();
      stars = 0;
      if ((ftype->code () == TYPE_CODE_PTR) || TYPE_IS_REFERENCE (ftype)) {
        while (TYPE_CODE(ftype) == TYPE_CODE_PTR) {
          stars++;
          ftype = TYPE_TARGET_TYPE(ftype);
        }
        fname = TYPE_NAME(ftype);
      } else
        fname= TYPE_NAME(ftype);

      fprintf(fp, "  %3d %20s type=%2d %25s ptrlev=%d\n", idx,
              TYPE_FIELD_NAME(type, idx), TYPE_CODE(ftype),
              fname, stars);
    }

  } catch (const gdb_exception_error &ex) {
    printf("Error caught\n");
  }
  printf("test\n");
}
}
