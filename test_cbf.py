# Author: Teemu Ikonen <teemu.ikonen@psi.ch>
# Copyright: 2010 Paul Scherrer Institute
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

import doctest, cbf


def doctest_readme_test():
    doctest.NORMALIZE_WHITESPACE=True
    doctest.testfile("README.rst", module_relative=False, raise_on_error=True)


def doctest_docstrings_test():
    doctest.testmod(cbf)


def datablocks_test():
    # This caused a segfault at 61bbba43eadc (2010-08-30)
    h = cbf.CBF("testdata/agbeh_long.cbf")
    ll = h.datablocks()


def iteration_test():
    h = cbf.CBF()
    h.read_file("testdata/agbeh_long.cbf")
    h.rewind_datablock()
    h.select_datablock(0)
    h.rewind_category()
    categories = h.count_categories()
    for i in range(categories):
        h.select_category(i)
        rows=h.count_rows()
        cols = h.count_columns()
        h.rewind_column()
        ss = 'Row#'
        for j in range(rows):
            h.select_row(j)
            print "%d:" % j,
            h.rewind_column()
            for k in range(cols):
                h.select_column(k)
                typeofvalue=h.get_typeofvalue()
                if typeofvalue.find("bnry") > -1:
                    print "<binary>"
                    s=h.get_arrayparameters()
                    print(s)
                    d, valtype = h.get()
                    print d.shape
                else:
                    value=h.get_value()
                    print '"%s":%s, ' % (value, typeofvalue),
            print('')
        print
    del(h)
