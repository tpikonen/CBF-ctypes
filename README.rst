CBF-ctypes
==========

Introduction
------------

CBF-ctypes is a module providing support (currently read-only) for using
Crystallographic Binary Files (CBF_) in Python. It is written with the
Python ctypes module as a binding to the C-language library CBFlib_.

.. _CBF: http://it.iucr.org/Ga/ch1o1v0001/sec1o1o10/
.. _CBFlib: http://www.bernstein-plus-sons.com/software/CBF/

Example usage
-------------

The most straightforward way to read CBF files into the Python interpreter is
to use the datablocks() method which returns a Python list / dictionary /
numpy array -structure with the contents of the file:

 >>> import cbf
 >>> h = cbf.CBF("testdata/agbeh_long.cbf")
 >>> blocks = h.datablocks()
 >>> blocks[0]['name']
 'e12608_1_00016_00000_00000'
 >>> blocks[0]['categories'][0]['name']
 'array_data'
 >>> blocks[0]['categories'][0].keys()
 ['columns~type', 'values', 'name', 'columns']
 >>> blocks[0]['categories'][0]['columns']
 ['header_convention', 'header_contents', 'data']
 >>> blocks[0]['categories'][0]['columns~type']
 ['dblq', 'text', 'bnry']
 >>> blocks[0]['categories'][0]['values']['data'] #doctest: +SKIP
 [array([[0, 0, 0, ..., 0, 2, 1],
      [1, 0, 0, ..., 0, 2, 1],
      [0, 0, 0, ..., 3, 2, 4],
      ...,
      [0, 0, 0, ..., 1, 4, 3],
      [0, 0, 0, ..., 1, 2, 0],
      [0, 0, 0, ..., 1, 4, 4]], dtype=int32)]

API
---

A CBF object (handle) is created with the constructor::

 >>> h = cbf.CBF()

The CBF object contains wrapped methods of most of the low-level CBFlib
functions related to reading values and iterating through the file
These have generally the same name as the corresponding CBFlib
function, like rewind_*, next_*, find_*, select_*, count_*. For example::

 >>> h.read_file("testdata/agbeh_long.cbf")
 >>> h.rewind_datablock()
 >>> h.find_category("array_data")
 >>> h.count_columns()
 3

The next_* methods will raise the StopIteration exception when called
in the last element of their block, find_* methods will raise KeyError
if the given key is not found in the file, and select_* methods will
raise IndexError, if the given index does not exist. RuntimeErrors are
raised on CBFlib errors, and IOErrors with non-existing files etc.

Also, a set of higher level functions which give the CBF-file
data as values inside a Python dictionary are provided:

h.get()
    Return the current value as a tuple (value, type).

h.category_asdict(key=None)
    Return the current category as dictionary.

h.datablock_asdict(key=None)
    Return the current datablock as dictionary.

h.datablocks()
    Return a list containing all the datablocks as dictionaries.

See the code and docstrings for details.

Other similar projects
----------------------

- The CBFlib source contains a Python wrapper ('pycbf') written in SWIG.
- PyCifRW_ is a pure Python CIF (Crystallographic Information File) parser.

.. _PyCifRW: http://anbf2.kek.jp/CIF/

License
-------

CBF-ctypes has a license similar to CBFlib, you can redistribute it and/or
modify it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License, or (at
your option) any later version.

See http://www.gnu.org/licenses/gpl2.html for the license text.

Author
------

CBF-ctypes was written by Teemu Ikonen <tpikonen@gmail.com>.

Copyright
---------
Copyright © 2010 Paul Scherrer Institute (http://www.psi.ch/)
