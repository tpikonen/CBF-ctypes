# Author: Teemu Ikonen <teemu.ikonen@psi.ch>
# License:
#   This program is free software; you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as
#   published by the Free Software Foundation; either version 2 of
#   (the License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
#   02111-1307  USA

import ctypes
import numpy as np
from ctypes import *

class Headers:
    """Header #defines from cfb.h"""
    PLAIN_HEADERS  = 0x0001  # Use plain ASCII headers
    MIME_HEADERS   = 0x0002  # Use MIME headers
    MSG_NODIGEST   = 0x0004  # Do not check message digests
    MSG_DIGEST     = 0x0008  # Check message digests
    MSG_DIGESTNOW  = 0x0010  # Check message digests immediately
    PAD_1K         = 0x0020  # Pad binaries with 1023 0's
    PAD_2K         = 0x0040  # Pad binaries with 2047 0's
    PAD_4K         = 0x0080  # Pad binaries with 4095 0's

class Errors:
    """Error #defines from cbf.h"""
    CBF_FORMAT          = 0x00000001
    CBF_ALLOC           = 0x00000002
    CBF_ARGUMENT        = 0x00000004
    CBF_ASCII           = 0x00000008
    CBF_BINARY          = 0x00000010
    CBF_BITCOUNT        = 0x00000020
    CBF_ENDOFDATA       = 0x00000040
    CBF_FILECLOSE       = 0x00000080
    CBF_FILEOPEN        = 0x00000100
    CBF_FILEREAD        = 0x00000200
    CBF_FILESEEK        = 0x00000400
    CBF_FILETELL        = 0x00000800
    CBF_FILEWRITE       = 0x00001000
    CBF_IDENTICAL       = 0x00002000
    CBF_NOTFOUND        = 0x00004000
    CBF_OVERFLOW        = 0x00008000
    CBF_UNDEFINED       = 0x00010000
    CBF_NOTIMPLEMENTED  = 0x00020000
    CBF_NOCOMPRESSION   = 0x00040000

# FIXME: The C header has only an ordered enum without values.
# Is there a better way to describe enums without values specified in
# the C header in ctypes?
class Nodetype:
    """Values of enum CBF_NODETYPE from cbf_tree.h"""
    CBF_UNDEFINED   = 0
    CBF_LINK        = 1
    CBF_ROOT        = 2
    CBF_DATABLOCK   = 3
    CBF_SAVEFRAME   = 4
    CBF_CATEGORY    = 5
    CBF_COLUMN      = 6
    CBF_VALUE       = 7


# Interface libc fopen to python
def io_errcheck(res, func, args):
    if not res:
        raise IOError('Error opening file')
    return res

class FILE(Structure): pass
FILE_ptr = POINTER(FILE)
c_fopen = ctypes.pythonapi.fopen
c_fopen.restype = FILE_ptr
c_fopen.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
c_fopen.errcheck = io_errcheck


class HandleStruct(Structure): pass # cbf_handle_struct
Handle = POINTER(HandleStruct) # cbf_handle

lib = cdll.LoadLibrary("libcbf.so.0")
#lib.cbf_get_arrayparameters_wdims.restype = c_int
#lib.cbf_get_arrayparameters_wdims.argtypes = [
#    Handle,
#    POINTER(c_uint),
#    POINTER(c_int),
#    POINTER(c_size_t),
#    POINTER(c_int),
#    POINTER(c_int),
#    POINTER(c_size_t),
#    POINTER(c_int),
#    POINTER(c_int),
#    POINTER(c_int),
#    POINTER(c_char_p),
#    POINTER(c_size_t),
#    POINTER(c_size_t),
#    POINTER(c_size_t),
#    POINTER(c_size_t)
#]

class CBF:
    """Create a CBF instance, optionally opening an existing file.
    """
    def __init__(self, filename=None):
        self.h = Handle()
        self.FILE = None
        ret = lib.cbf_make_handle(byref(self.h))
        if ret != 0:
            raise RuntimeError(ret)
        if filename is not None:
            self.read_file(filename)


    def __del__(self):
        ret = lib.cbf_free_handle(self.h)
        if ret != 0:
            raise RuntimeError(ret)

####
#
#  High level Python API

    def datablocks(self):
        """Return a list containing all the datablocks as dictionaries.

        See `datablock_asdict` for the datablock dictionary definition.
        """
        self.rewind_datablock()
        blocks = []
        while True:
            blocks.append(self.datablock_asdict())
            try:
                self.next_datablock()
            except StopIteration:
                break
        return blocks


    def datablock_asdict(self, key=None):
        """Return datablock as dictionary.

        If the argument `key` is None, the current datablock is returned.
        If `key` is a string, datablock with that name is returned.
        If `key` is an integer, datablock with that index is returned.

        The returned dictionary has these keys:
            "name" : name of the datablock
            "categories" : list of categories in the datablock as dictionaries

        See `category_asdict` for category dictionary definition.
        """
        if key is None:
            pass
        elif isinstance(key, str):
            self.find_datablock(key)
        elif isinstance(key, int):
            self.select_datablock(key)
        else:
            raise TypeError(key)
        bd = {}
        bd["name"] = self.datablock_name()
        cats = []
        self.rewind_category()
        while True:
            cats.append(self.category_asdict())
            try:
                self.next_category()
            except StopIteration:
                break
        bd["categories"] = cats
        return bd


    def category_asdict(self, key=None):
        """Return the current category as dictionary.

        If the argument `key` is None, the current category is returned.
        If `key` is a string, category with that name is returned.
        If `key` is an integer, category with that index is returned.

        The returned dictionary has these keys:
            "name" : name of the category
            "columns" : list containing the names of the columns in the order
                they are in the CBF file
            "columns~type" : list containing the types of the column values
                (assuming they are identical for every row)
            "values" : dictionary with column names as keys containing lists
                of the values contained in rows.

        See `get` for the definition of values.
        """
        if key is None:
            pass
        elif isinstance(key, str):
            self.find_category(key)
        elif isinstance(key, int):
            self.select_category(key)
        else:
            raise TypeError(key)
        cd = {}
        cd["name"] = self.category_name()
        ncols = self.count_columns()
        nrows = self.count_rows()
        self.rewind_row()
        colnames = []
        coltypes = []
        colvals = []
        self.rewind_row()
        for i in range(ncols):
            self.select_column(i)
            colnames.append(self.column_name())
            coltypes.append(self.get_typeofvalue())
            colvals.append([])
        self.rewind_row()
        for r in range(nrows):
            self.select_row(r)
            for c in range(ncols):
                self.select_column(c)
                val, _ = self.get()
                colvals[c].append(val)
        cd["columns"] = colnames
        cd["columns~type"] = coltypes
        values = {}
        for i in range(len(colnames)):
            values[colnames[i]] = colvals[i]
        cd["values"] = values
        return cd


    def get(self):
        """Return the current value as a tuple (value, type).

        `value` is either None, an ASCII representation or in the case
            of a binary value, a Numpy array.

        `type` is a string,
            "null" for a null value,
            "bnry" for a binary value,
            "word" for an unquoted string,
            "dblq" for a double-quoted string,
            "sglq" for a single-quoted string, and
            "text" for a semicolon-quoted text field.

        Calling this function on a field without a value returns (None, '')
        """
        valtype = self.get_typeofvalue()
        if valtype == '':
            return (None, valtype)
        elif valtype == 'bnry':
            arr = self.get_binary()
            return (arr, valtype)
        else:
            val = self.get_value()
            return (val, valtype)


    def get_binary(self):
        """Return a binary value as a Numpy array.

        The type of the current value must be 'bnry'.
        """
        valtype = self.get_typeofvalue()
        if valtype != 'bnry':
            raise ValueError("Not a binary value")
        p = self.get_arrayparameters()
        if p["elunsigned"]:
            arr = self.get_integerarray(p["shape"], elsigned=False)
        elif p["elsigned"]:
            arr = self.get_integerarray(p["shape"], elsigned=True)
        else:
            arr = self.get_realarray(p["shape"])
        return arr


####
#
#   Helper functions for lower level Python API

    def _check(self, f):
        ret = f(self.h)
        if ret != 0:
            raise RuntimeError(ret)

    def _get_str(self, f):
        val = c_char_p()
        ret = f(self.h, byref(val))
        if ret != 0:
            raise RuntimeError(ret)
        if val.value is None:
            return ""
        else:
            return val.value

    def _get_int(self, f):
        val = c_int()
        ret = f(self.h, byref(val))
        if ret != 0:
            raise RuntimeError(ret)
        return val.value

####
#
#   Low level Python API to CBFlib functions


    def read_file(self, filename):
        """Associate an existing file to a CBF instance.
        """
        cfile_ptr = c_fopen(filename, 'rb')
        ret =  lib.cbf_read_file(self.h, cfile_ptr, c_int(Headers.MSG_NODIGEST))
        if ret != 0:
            raise RuntimeError(ret)
        self.filename = filename

# Rewinds

    def rewind_datablock(self):
        self._check(lib.cbf_rewind_datablock)

    def rewind_category(self):
        self._check(lib.cbf_rewind_category)

    def rewind_saveframe(self):
        self._check(lib.cbf_rewind_saveframe)

    def rewind_column(self):
        self._check(lib.cbf_rewind_column)

    def rewind_row(self):
        self._check(lib.cbf_rewind_row)

    def rewind_blockitem(self):
        return self._get_int(lib.cbf_rewind_blockitem)

# Nexts

    def _next(self, f):
        """Calls `f`, potentially raising either StopIteration or RuntimeError.
        """
        ret = f(self.h)
        if ret == Errors.CBF_NOTFOUND:
            raise StopIteration()
        elif ret != 0:
            raise RuntimeError(ret)

    def next_datablock(self):
        self._next(lib.cbf_next_datablock)

    def next_saveframe(self):
        self._next(lib.cbf_next_saveframe)

    def next_category(self):
        self._next(lib.cbf_next_category)

    def next_column(self):
        self._next(lib.cbf_next_column)

    def next_row(self):
        self._next(lib.cbf_next_row)

    def next_blockitem(self):
        val = c_int()
        ret = lib.cbf_next_blockitem(self.h, byref(val))
        if ret == Errors.CBF_NOTFOUND:
            raise StopIteration()
        elif ret != 0:
            raise RuntimeError(ret)
        return val.value

# Finds

    def _find(self, f, name):
        ret = f(self.h, name)
        if ret == Errors.CBF_NOTFOUND:
            raise KeyError()
        elif ret != 0:
            raise RuntimeError(ret)

    def find_datablock(self, name):
        self._find(lib.cbf_find_datablock, name)

    def find_saveframe(self, name):
        self._find(lib.cbf_find_saveframe, name)

    def find_category(self, name):
        self._find(lib.cbf_find_category, name)

    def find_column(self, name):
        self._find(lib.cbf_find_column, name)

    def find_row(self, value):
        self._find(lib.cbf_find_row, name)

# Counts

    def count_datablocks(self):
        return self._get_int(lib.cbf_count_datablocks)

    def count_saveframes(self):
        return self._get_int(lib.cbf_count_saveframes)

    def count_categories(self):
        return self._get_int(lib.cbf_count_categories)

    def count_blockitems(self):
        return self._get_int(lib.cbf_count_blockitems)

    def count_columns(self):
        return self._get_int(lib.cbf_count_columns)

    def count_rows(self):
        return self._get_int(lib.cbf_count_rows)

# Selects

    def _select(self, f, index):
        cind = c_uint(index)
        ret = f(self.h, cind)
        if ret == Errors.CBF_NOTFOUND:
            raise IndexError(index)
        elif ret != 0:
            raise RuntimeError(ret)

    def select_datablock(self, index):
        self._select(lib.cbf_select_datablock, index)

    def select_saveframe(self, index):
        self._select(lib.cbf_select_saveframe, index)

    def select_category(self, index):
        self._select(lib.cbf_select_category, index)

    def select_column(self, index):
        self._select(lib.cbf_select_column, index)

    def select_row(self, index):
        self._select(lib.cbf_select_row, index)

    def select_blockitem(self, index):
        cind = c_uint(index)
        blocktype = c_int()
        ret = f(self.h, cind, byref(blocktype))
        if ret == Errors.CBF_NOTFOUND:
            raise IndexError(index)
        elif ret != 0:
            raise RuntimeError(ret)
        return blocktype.value

# Names

    def datablock_name(self):
        return self._get_str(lib.cbf_datablock_name)

    def saveframe_name(self):
        return self._get_str(lib.cbf_saveframe_name)

    def category_name(self):
        return self._get_str(lib.cbf_category_name)

    def column_name(self):
        return self._get_str(lib.cbf_column_name)

# Gets

    def get_arrayparameters(self):
        """Return a dictionary containing CBF array parameters.

        The dictionary has the following keys:
            "compression" : Compression method used
            "id" : Integer binary identifier
            "elsize" : Size in bytes of each array element
            "elsigned" : Set to 1 if the elements can be read as signed integers
            "elunsigned" : Set to 1 if the elements can be read as unsigned integers
            "nelem" : Number of elements
            "minelem" : Smallest element
            "maxelem" : Largest element
            "realarray" : Set to 1 if the elements can be read as floats
            "byteorder" : Byte order ('little_endian' or 'big_endian')
            "shape" : Tuple containing the shape of the array in from slowest to fastest growing index
            "padding" : Padding size
        """
        compression = c_uint()
        binary_id = c_int()
        elsize = c_size_t()
        elsigned, elunsigned = c_int(), c_int()
        nelem = c_size_t()
        minelem, maxelem, realarray = c_int(), c_int(), c_int()
        byteorder = c_char_p()
        dimfast, dimmid, dimslow = c_size_t(), c_size_t(), c_size_t()
        padding = c_size_t()
        ret = lib.cbf_get_arrayparameters_wdims(self.h, byref(compression),
            byref(binary_id), byref(elsize), byref(elsigned),
            byref(elunsigned), byref(nelem), byref(minelem), byref(maxelem),
            byref(realarray), byref(byteorder), byref(dimfast), byref(dimmid),
            byref(dimslow), byref(padding))
        if ret != 0:
            raise RuntimeError(ret)
        if dimslow.value != 0:
            # Numpy array order
            shape = (dimslow.value, dimmid.value, dimfast.value)
        elif dimmid.value != 0:
            shape = (dimmid.value, dimfast.value)
        elif dimfast.value != 0:
            shape = (dimfast.value,)
        else: # Dimensionless arrays
            shape = (nelem.value,)
        return {
                "compression" : compression.value,
                "id" : binary_id.value,
                "elsize" : elsize.value,
                "elsigned" : elsigned.value,
                "elunsigned" : elunsigned.value,
                "nelem" : nelem.value,
                "minelem" : minelem.value,
                "maxelem" : maxelem.value,
                "realarray" : realarray.value,
                "byteorder" : byteorder.value,
                "shape" : shape,
                "padding" : padding.value,
                }


    def get_integerarray(self, shape, elsigned=1):
        """Return the current integer array as a Numpy array.
        """
        binary_id = c_int()
        elread = c_size_t()
        if elsigned:
            dtype = 'int32'
        else:
            dtype = 'uint32'
        arr = np.zeros(shape, dtype=dtype)
        nelems = np.prod(shape)
        ret = lib.cbf_get_integerarray(self.h, byref(binary_id),
            arr.ctypes.get_as_parameter(),
            4, elsigned, c_size_t(nelems), byref(elread))
        if ret != 0 or elread != nelems:
            raise RuntimeError(ret)
        return arr


    def get_realarray(self, shape):
        """Return the current real array as a Numpy array.
        """
        binary_id = c_int()
        elread = c_size_t()
        arr = np.zeros(shape, dtype=np.float64)
        nelems = np.prod(shape)
        ret = lib.cbf_get_realarray(self.h, byref(binary_id),
            arr.ctypes.get_as_parameter(),
            8, nelems, byref(elread))
        if ret != 0 or elread != nelems:
            raise RuntimeError(ret)
        return arr


    def get_typeofvalue(self):
        """Return a string describing the type of value.

        "null" for a null value,
        "bnry" for a binary value,
        "word" for an unquoted string,
        "dblq" for a double-quoted string,
        "sglq" for a single-quoted string, and
        "text" for a semicolon-quoted text field.
        """
        return self._get_str(lib.cbf_get_typeofvalue)


    def get_value(self):
        """Return the ascii representation the current value.

        The type of the value must not be 'bnry', otherwise a ValueError
        is raised.
        """
        val = c_char_p()
        ret = lib.cbf_get_value(self.h, byref(val))
        if ret == Errors.CBF_BINARY:
            raise ValueError("Expecting a non-binary value")
        elif ret != 0:
            raise RuntimeError(ret)
        return val.value

