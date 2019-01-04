from __future__ import print_function
from __future__ import division

import numpy
import copy
import math
import EMAN2_cppwrap as e2cpp

import unittest
import copy
import os
import cPickle as pickle
ABSOLUTE_PATH = os.path.dirname(os.path.realpath(__file__))

from ..libpy import sparx_alignment as fu
from .sparx_lib import sparx_alignment as oldfu
from ..libpy import sparx_utilities as ut


def get_data(num,dim = 10):
    data_list = []
    for i in range(num):
        a = e2cpp.EMData(dim, dim)
        data_a = a.get_3dview()
        data_a[...] = numpy.arange(dim * dim, dtype=numpy.float32).reshape(dim, dim) + i
        data_list.append(a)
    return data_list


def get_data_3d(num, dim=10):
    data_list = []
    for i in range(num):
        a = e2cpp.EMData(dim, dim,dim)
        data_a = a.get_3dview()
        data_a[...] = numpy.arange(dim * dim * dim, dtype=numpy.float32).reshape(dim, dim, dim) + i
        data_list.append(a)

    return data_list




class Test_lib_compare(unittest.TestCase):
    """"
    # data = list of images
    # numr = tuple or list precalcualte rings
    # wr = list of weights of numr
    # cs =  cs = [0.0]*2
    # tavg = blanck image
    # cnx = center value x
    # cny = cnx
    # xrng =  list of possible shifts
    # yrng =  list of possible shifts
    # step = stepsize of the shift
    """
    def test_ali2d_single_iter_true_should_return_equal_objects(self):
        filepath = os.path.join(ABSOLUTE_PATH, "files/picklefiles/alignment.ali2d_single_iter")
        with open(filepath, 'rb') as rb:
            argum = pickle.load(rb)
            print(argum[0])
        (dataa, numr, wr, cs, tavg, cnx, cny, xrng, yrng, step) = argum[0]
        (datab, numr, wr, cs, tavg, cnx, cny, xrng, yrng, step) = argum[0]

        dataa = copy.deepcopy(argum[0][0])
        datab = copy.deepcopy(argum[0][0])

        return_new = fu.ali2d_single_iter(dataa, numr, wr, cs, tavg, cnx, cny, xrng, yrng, step)
        return_old = fu.ali2d_single_iter(datab, numr, wr, cs, tavg, cnx, cny, xrng, yrng, step)
        self.assertEqual(return_new,return_old)


    def test_ang_n_true_should_return_equal_object(self):
        return_new = fu.ang_n(2 , 'f' , 3)
        return_old = oldfu.ang_n(2, 'f' , 3)

        self.assertEqual(return_new, return_old)

    def test_log2_true_should_return_equal_object(self):
        return_new = fu.log2(10)
        return_old = oldfu.log2(10)

        self.assertEqual(return_new,return_old)

    def test_Numrinit_true_should_return_equal_object(self):
        return_new = fu.Numrinit(2 , 5)
        return_old = oldfu.Numrinit(2, 5)

        self.assertEqual(return_new, return_old)

    def test_ringwe_true_should_return_equal_object(self):
        filepath = os.path.join(ABSOLUTE_PATH, "files/picklefiles/alignment.ringwe")
        with open(filepath, 'rb') as rb:
            argum = pickle.load(rb)
            (numr) = argum[0][0]

        return_new = fu.ringwe(numr)
        return_old = oldfu.ringwe(numr)

        self.assertEqual(return_new, return_old)

    def test_ornq_true_should_return_equal_object(self):

        filepath = os.path.join(ABSOLUTE_PATH, "files/picklefiles/alignment.ornq")
        with open(filepath, 'rb') as rb:
            (image, crefim, xrng, yrng, step, mode, numr, cnx, cny, deltapsi) = pickle.load(rb)

        return_new = fu.ornq(image,crefim,xrng,yrng,step,mode,numr,cnx,cny,deltapsi)
        return_old = fu.ornq(image,crefim,xrng,yrng,step,mode,numr,cnx,cny,deltapsi)
        self.assertEqual(return_new, return_old)

    def test_ormq_true_should_return_equal_object(self):
        filepath = os.path.join(ABSOLUTE_PATH, "files/picklefiles/alignment.ornq")
        with open(filepath, 'rb') as rb:
            (image, crefim, xrng, yrng, step, mode, numr, cnx, cny, deltapsi) = pickle.load(rb)

        return_new = fu.ormq(image,crefim,xrng,yrng,step,mode,numr,cnx,cny,deltapsi)
        return_old = fu.ormq(image,crefim,xrng,yrng,step,mode,numr,cnx,cny,deltapsi)

        self.assertEqual(return_new, return_old)

    # def test_ormq_fast_true_should_return_equal_object(self):
    #
    #     filepath = os.path.join(ABSOLUTE_PATH, "files/picklefiles/alignment.ornq")
    #     with open(filepath, 'rb') as rb:
    #         (image, crefim, xrng, yrng, step, mode, numr, cnx, cny, deltapsi) = pickle.load(rb)
    #
    #     print(numpy.shape(image.get_3dview()[0]))
    #     print(image, crefim, xrng, yrng, step, mode, numr, cnx, cny, deltapsi)
    #     return_new = fu.ormq_fast(image, crefim, xrng[0], yrng[0], step, numr, mode)
    #     return_old = fu.ormq_fast(image, crefim, xrng[0], yrng[0], step, numr, mode)
    #
    #     self.assertTrue(return_new, return_old)


    # def test_prepref_true_should_return_equal_object(self):
    # dont know what should be maskfile
    #     a,b,c = get_data(3)
    #     data = [a,b,c]
    #     maskfile = b
    #     mode   = 'f'
    #     numr = [int(entry) for entry in numpy.arange(0, 20).tolist()]
    #     cnx  = 2
    #     cny  = 2
    #     maxrangex = 5
    #     maxrangey = 5
    #     step = 3
    #
    #
    #     return_new = fu.prepref(data,maskfile,cnx,cny,numr,mode,maxrangex,maxrangey,step)
    #     return_old = fu.prepref(data,maskfile,cnx,cny,numr,mode,maxrangex,maxrangey,step)
    #
    #     self.assertEqual(return_new, return_old)


    # def test_prepare_refrings_true_should_return_equal_object(self):
    #     filepath = os.path.join(ABSOLUTE_PATH, "files/picklefiles/alignment.prepare_refrings")
    #
    #     if os.path.getsize(filepath) > 0:
    #         print(os.path.getsize(filepath))
    #         print('locationisok')
    #     with open(filepath, 'rb') as rb:
    #         unpickler = pickle.Unpickler(rb)
    #         print(unpickler.load())
    #
    #         # (volft,kb) = pickle.load(rb)
    #
    #     return_new = fu.prepare_refrings(volft,kb)
    #     # return_old = oldfu.prepare_refrings(volft,kb)
    #     #
    #     # self.assertEqual(return_old,return_new)

    def test_align2d_true_should_return_equal_object(self):
        filepath = os.path.join(ABSOLUTE_PATH, "files/picklefiles/alignment.align2d_scf")
        with open(filepath, 'rb') as rb:
            argum = pickle.load(rb)
            (image,refim, xrng, yrng) = argum[0]
            (ou) = argum[1]['ou']

        return_new = fu.align2d(image,refim)
        return_old = oldfu.align2d(image,refim)

        self.assertEqual(return_old, return_new)


    def test_align2d_scf_true_should_return_equal_object(self):
        filepath = os.path.join(ABSOLUTE_PATH, "files/picklefiles/alignment.align2d_scf")
        with open(filepath, 'rb') as rb:
            argum = pickle.load(rb)
            (image,refim, xrng, yrng) = argum[0]
            (ou) = argum[1]['ou']

        return_new = fu.align2d_scf(image,refim,xrng,yrng, ou)
        return_old = oldfu.align2d_scf(image,refim,xrng,yrng, ou)

        self.assertEqual(return_old, return_new)


    def test_parabl_true_should_return_equal_object(self):
        filepath = os.path.join(ABSOLUTE_PATH, "files/picklefiles/alignment.parabl")
        with open(filepath, 'rb') as rb:
            (Z) = pickle.load(rb)
            print(Z[0][0])

        return_new = fu.parabl(Z[0][0])
        return_old = oldfu.parabl(Z[0][0])

        self.assertEqual(return_old, return_new)

    # def test_shc_true_should_return_equal_object(self):
    #     filepath = os.path.join(ABSOLUTE_PATH, "files/picklefiles/alignment.shc")
    #     with open(filepath, 'rb') as rb:
    #         argum = pickle.load(rb)
    #         print(argum)
    #         (data, refrings, list_of_ref_ang, numr, xrng, yrng, step) = argum
    #     return_new = fu.shc(data,refrings,list_of_ref_ang, numr, xrng,yrng,step)
    #     return_old = oldfu.shc(data,refrings,list_of_ref_ang, numr, xrng,yrng,step)
    #
    #     self.assertEqual(return_old, return_new)

    def test_search_range_true_should_return_equal_object(self):
        filepath = os.path.join(ABSOLUTE_PATH, "files/picklefiles/alignment.search_range")
        with open(filepath, 'rb') as rb:
            argum = pickle.load(rb)
            print(argum[0])
            (n, radius, shift, range) = argum[0]

        return_new = fu.search_range(n, radius, shift, range)
        return_old = oldfu.search_range(n, radius, shift, range)

        self.assertEqual(return_old, return_new)



