#!/usr/bin/env python

#
# Author: Steven Ludtke, 04/10/2003 (sludtke@bcm.edu)
# Copyright (c) 2000-2006 Baylor College of Medicine
#
# This software is issued under a joint BSD/GNU license. You may use the
# source code in this file under either license. However, note that the
# complete EMAN2 and SPARX software packages have some GPL dependencies,
# so you are responsible for compliance with the licenses of these packages
# if you opt to use BSD licensing. The warranty disclaimer below holds
# in either instance.
#
# This complete copyright notice must be included in any revised version of the
# source code. Additional authorship citations may be added, but existing
# author citations must be preserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  2111-1307 USA
#
#

# $Id$
import	global_def
from	global_def 	import *
from	EMAN2 		import EMUtil, parsemodopt
from    EMAN2jsondb import js_open_dict

def main():
	import sys
	import os.path
	import math
	import random
	import pyemtbx.options
	import time
	from   random   import random, seed, randint
	from   optparse import OptionParser

	progname = os.path.basename(sys.argv[0])
	usage = progname + """ [options] <inputfile> <outputfile>

	Generic 2-D image processing programs.

	Functionality:

	1.  phase flip a stack of images and write output to new file:
	sxprocess.py input_stack.hdf output_stack.hdf --phase_flip
	
	2.  resample (decimate or interpolate up) images (2D or 3D) in a stack to change the pixel size.
	    The window size will change accordingly.
	sxprocess input.hdf output.hdf  --changesize --ratio=0.5

	3.  compute average power spectrum of a stack of 2D images with optional padding (option wn) with zeroes.
	sxprocess.py input_stack.hdf powerspectrum.hdf --pw [--wn=1024]

	4.  Order a 2-D stack of image based on pair-wise similarity (computed as a cross-correlation coefficent).
	sxprocess.py input_stack.hdf output_stack.hdf --order

	5. generate a stack of projections bdb:data and micrographs with prefix mic (i.e., mic0.hdf, mic1.hdf etc) from structure input_structure.hdf, with CTF applied to both projections and micrographs:
	sxprocess.py input_structure.hdf data mic --generate_projections format="bdb":apix=5.2:CTF=True:boxsize=64 	

    6. Retrieve original image numbers in the selected ISAC group (here group 12 from generation 3):
    sxprocess.py  bdb:test3 class_averages_generation_3.hdf  list3_12.txt --isacgroup=12 --params=myid

    . Adjust rotationally averaged power spectrum of an image to that of a reference image or a reference 1D power spectrum stored in an ASCII file.
    	Optionally use a tangent low-pass filter.  Also works for a stack of images, in which case the output is also a stack.
    sxprocess.py  vol.hdf ref.hdf  avol.hf < 0.25 0.2> --adjpw
    sxprocess.py  vol.hdf pw.txt  avol.hf < 0.25 0.2> --adjpw
"""

	parser = OptionParser(usage,version=SPARXVERSION)
	parser.add_option("--order", action="store_true", help="Two arguments are required: name of input stack and desired name of output stack. The output stack is the input stack sorted by similarity in terms of cross-correlation coefficent.", default=False)
	parser.add_option("--changesize", action="store_true", help="resample (decimate or interpolate up) images (2D or 3D) in a stack to change the pixel size.", default=False)
	parser.add_option("--ratio", type="float", default=1.0, help="The ratio of new to old image size (if <1 the pixel size will increase and image size decrease, if>1, the other way round")
	parser.add_option("--pw", action="store_true", help="compute average power spectrum of a stack of 2-D images with optional padding (option wn) with zeroes", default=False)
	parser.add_option("--wn", type="int", default=-1, help="Size of window to use (should be larger/equal than particle box size, default padding to max(nx,ny))")
	parser.add_option("--phase_flip", action="store_true", help="Phase flip the input stack", default=False)
	parser.add_option("--makedb", metavar="param1=value1:param2=value2", type=str,
					action="append",  help="One argument is required: name of key with which the database will be created. Fill in database with parameters specified as follows: --makedb param1=value1:param2=value2, e.g. 'gauss_width'=1.0:'pixel_input'=5.2:'pixel_output'=5.2:'thr_low'=1.0")
	parser.add_option("--generate_projections", metavar="param1=value1:param2=value2", type=str,
					action="append", help="Three arguments are required: name of input structure from which to generate projections, desired name of output projection stack, and desired prefix for micrographs (e.g. if prefix is 'mic', then micrographs mic0.hdf, mic1.hdf etc will be generated). Optional arguments specifying format, apix, box size and whether to add CTF effects can be entered as follows after --generate_projections: format='bdb':apix=5.2:CTF=True:boxsize=100, or format='hdf', etc., where format is bdb or hdf, apix (pixel size) is a float, CTF is True or False, and boxsize denotes the dimension of the box (assumed to be a square). If an optional parameter is not specified, it will default as follows: format='bdb', apix=2.5, CTF=False, boxsize=64.")
	parser.add_option("--isacgroup", type="int", help="Retrieve original image numbers in the selected ISAC group   See ISAC documentaion for details.", default=-1)
	parser.add_option("--params",	   type="string",       default=None,    help="Name of header of parameter, which one depends on specific option")
	parser.add_option("--adjpw", action="store_true", help="Adjust rotationally averaged power spectrum of an image", default=False)
 	(options, args) = parser.parse_args()

	global_def.BATCH = True

	if options.order:
		nargs = len(args)
		if nargs != 2:
			print "must provide name of input and output file!"
			return
		
		from utilities import get_params2D, model_circle
		from fundamentals import rot_shift2D
		from statistics import ccc
		stack = args[0]
		new_stack = args[1]
		
		d = EMData.read_images(stack)
		for i in xrange(len(d)):
			alpha, sx, sy, mirror, scale = get_params2D(d[i])
			d[i] = rot_shift2D(d[i], alpha, sx, sy, mirror)
		m = model_circle(30, 64, 64)

		init = 0
		temp = d[init].copy()
		temp.write_image(new_stack, 0)
		del d[init]
		k = 1
		while len(d) > 1:
			maxcit = -111.
			for i in xrange(len(d)):
					cuc = ccc(d[i], temp, m)
					if cuc > maxcit:
							maxcit = cuc
							qi = i
			#print k, maxcit
			temp = d[qi].copy()
			del d[qi]
			temp.write_image(new_stack, k)
			k += 1

		d[0].write_image(new_stack, k)
			
	if options.phase_flip:
		nargs = len(args)
		if nargs != 2:
			print "must provide name of input and output file!"
			return
		from EMAN2 import Processor
		instack = args[0]
		outstack = args[1]
		nima = EMUtil.get_image_count(instack)
		from filter import filt_ctf
		for i in xrange(nima):
			img = EMData()
			img.read_image(instack, i)
			try:
				ctf = img.get_attr('ctf')
			except:
				print "no ctf information in input stack! Exiting..."
				return
			
			dopad = True
			sign = 1
			binary = 1  # phase flip
				
			assert img.get_ysize() > 1	
			dict = ctf.to_dict()
			dz = dict["defocus"]
			cs = dict["cs"]
			voltage = dict["voltage"]
			pixel_size = dict["apix"]
			b_factor = dict["bfactor"]
			ampcont = dict["ampcont"]
			dza = dict["dfdiff"]
			azz = dict["dfang"]
			
			if dopad and not img.is_complex(): ip = 1
			else:                             ip = 0
	
	
			params = {"filter_type": Processor.fourier_filter_types.CTF_,
	 			"defocus" : dz,
				"Cs": cs,
				"voltage": voltage,
				"Pixel_size": pixel_size,
				"B_factor": b_factor,
				"amp_contrast": ampcont,
				"dopad": ip,
				"binary": binary,
				"sign": sign,
				"dza": dza,
				"azz":azz}
			
			tmp = Processor.EMFourierFilter(img, params)
			tmp.set_attr_dict({"ctf": ctf})
			
			tmp.write_image(outstack, i)

	if options.changesize:
		nargs = len(args)
		if nargs != 2:
			ERROR("must provide name of input and output file!", "change size", 1)
			return
		from utilities import get_im
		instack = args[0]
		outstack = args[1]
		sub_rate = float(options.ratio)
			
		nima = EMUtil.get_image_count(instack)
		from fundamentals import resample
		for i in xrange(nima):
			resample(get_im(instack, i), sub_rate).write_image(outstack, i)

	if options.isacgroup>-1:
		nargs = len(args)
		if nargs != 3:
			ERROR("Three files needed on impurt!", "isacgroup", 1)
			return
		from utilities import get_im
		instack = args[0]
		m=get_im(args[1],int(options.isacgroup)).get_attr("members")
		l = []
		for k in m:
			l.append(int(get_im(args[0],k).get_attr(options.params)))
		from utilities import write_text_file
		write_text_file(l, args[2])

	if options.pw:
		nargs = len(args)
		if nargs != 2:
			ERROR("must provide name of input and output file!", "pw", 1)
			return
		from utilities import get_im
		d = get_im(args[0])
		nx = d.get_xsize()
		ny = d.get_ysize()
		wn = int(options.wn)
		if wn == -1:
			wn = max(nx, ny)
		else:
			if( (wn<nx) or (wn<ny) ):  ERROR("window size cannot be smaller than the image size","pw",1)
		n = EMUtil.get_image_count(args[0])
		from utilities import model_blank, pad
		from EMAN2 import periodogram
		p = model_blank(wn,wn)
		for i in xrange(n):
			d = get_im(args[0], i)
			st = Util.infomask(d, None, True)
			d -= st[0]
			p += periodogram(pad(d, wn, wn, 1, 0.))
		p /= n
		p.write_image(args[1])
		sys.exit()

	if options.adjpw:

		if len(args) < 3:
			ERROR("filt_by_rops input target output fl aa (the last two are optional parameters of a low-pass filter)","adjpw",1)
			return
		img_stack = args[0]
		from math         import sqrt
		from fundamentals import rops_table, fft
		from utilities    import read_text_file, get_im
		from filter       import  filt_tanl, filt_table
		if(  args[1][-3:] == 'txt'):
			rops_dst = read_text_file( args[1] )
		else:
			rops_dst = rops_table(get_im( args[1] ))

		out_stack = args[2]
		if(len(args) >4):
			fl = float(args[3])
			aa = float(args[4])
		else:
			fl = -1.0
			aa = 0.0

		nimage = EMUtil.get_image_count( img_stack )

		for i in xrange(nimage):
			img = fft(get_im(img_stack, i) )
			rops_src = rops_table(img)

			assert len(rops_dst) == len(rops_src)

			table = [0.0]*len(rops_dst)
			for j in xrange( len(rops_dst) ):
				table[j] = sqrt( rops_dst[j]/rops_src[j] )

			if( fl > 0.0):
				img = filt_tanl(img, fl, aa)
			img = fft(filt_table(img, table))
			img.write_image(out_stack, i)


	if options.makedb != None:
		nargs = len(args)
		if nargs != 1:
			print "must provide exactly one argument denoting database key under which the input params will be stored"
			return
		dbkey = args[0]
		print "database key under which params will be stored: ", dbkey
		gbdb = js_open_dict("e2boxercache/gauss_box_DB.json")
				
		parmstr = 'dummy:'+options.makedb[0]
		(processorname, param_dict) = parsemodopt(parmstr)
		dbdict = {}
		for pkey in param_dict:
			if (pkey == 'invert_contrast') or (pkey == 'use_variance'):
				if param_dict[pkey] == 'True':
					dbdict[pkey] = True
				else:
					dbdict[pkey] = False
			else:		
				dbdict[pkey] = param_dict[pkey]
		gbdb[dbkey] = dbdict

	if options.generate_projections:
		nargs = len(args)
		if nargs != 3:
			print "must provide name of input structure from which to generate projections, desired name of output projection stack, and desired prefix for output micrographs. Exiting..."
			return
		inpstr = args[0]
		outstk = args[1]
		micpref = args[2]

		parmstr = 'dummy:'+options.generate_projections[0]
		(processorname, param_dict) = parsemodopt(parmstr)

		parm_CTF = False
		parm_format = 'bdb'
		parm_apix = 2.5

		if 'CTF' in param_dict:
			if param_dict['CTF'] == 'True':
				parm_CTF = True

		if 'format' in param_dict:
			parm_format = param_dict['format']

		if 'apix' in param_dict:
			parm_apix = float(param_dict['apix'])

		boxsize = 64
		if 'boxsize' in param_dict:
			boxsize = int(param_dict['boxsize'])

		print "pixel size: ", parm_apix, " format: ", parm_format, " add CTF: ", parm_CTF, " box size: ", boxsize

		scale_mult = 2500
		sigma_add = 1.5
		sigma_proj = 30.0
		sigma2_proj = 17.5
		sigma_gauss = 0.3
		sigma_mic = 30.0
		sigma2_mic = 17.5
		sigma_gauss_mic = 0.3
		
		if 'scale_mult' in param_dict:
			scale_mult = float(param_dict['scale_mult'])
		if 'sigma_add' in param_dict:
			sigma_add = float(param_dict['sigma_add'])
		if 'sigma_proj' in param_dict:
			sigma_proj = float(param_dict['sigma_proj'])
		if 'sigma2_proj' in param_dict:
			sigma2_proj = float(param_dict['sigma2_proj'])
		if 'sigma_gauss' in param_dict:
			sigma_gauss = float(param_dict['sigma_gauss'])	
		if 'sigma_mic' in param_dict:
			sigma_mic = float(param_dict['sigma_mic'])
		if 'sigma2_mic' in param_dict:
			sigma2_mic = float(param_dict['sigma2_mic'])
		if 'sigma_gauss_mic' in param_dict:
			sigma_gauss_mic = float(param_dict['sigma_gauss_mic'])	
			
		from filter import filt_gaussl, filt_ctf
		from utilities import drop_spider_doc, even_angles, model_gauss, delete_bdb, model_blank,pad,model_gauss_noise,set_params2D, set_params_proj
		from projection import prep_vol,prgs
		seed(14567)
		delta = 29
		angles = even_angles(delta, 0.0, 89.9, 0.0, 359.9, "S")
		nangle = len(angles)
		
		modelvol = EMData()
		#modelvol.read_image("../model_structure.hdf")
		modelvol.read_image(inpstr)
		
		nx = modelvol.get_xsize()
		
		if nx != boxsize:
			print "requested box dimension does not match dimension of the input model....Exiting"
			sys.exit()

		nvol = 10
		volfts = [None]*nvol
		for i in xrange(nvol):
			sigma = sigma_add + random()  # 1.5-2.5
			addon = model_gauss(sigma, boxsize, boxsize, boxsize, sigma, sigma, 38, 38, 40 )
			scale = scale_mult * (0.5+random())
			model = modelvol + scale*addon
			volfts[i], kb = prep_vol(modelvol + scale*addon)
			
		if parm_format == "bdb":
			stack_data = "bdb:"+outstk
			delete_bdb(stack_data)
		else:
			stack_data = outstk + ".hdf"
		Cs      = 2.0
		pixel   = parm_apix
		voltage = 120.0
		ampcont = 10.0
		ibd     = 4096/2-boxsize
		iprj    = 0

		width = 240
		xstart = 8 + boxsize/2
		ystart = 8 + boxsize/2
		rowlen = 17

		params = []
		for idef in xrange(3, 8):

			irow = 0
			icol = 0

			mic = model_blank(4096, 4096)
			defocus = idef * 0.2
			if parm_CTF:
				ctf = EMAN2Ctf()
				ctf.from_dict({"defocus": defocus, "cs": Cs, "voltage": voltage, "apix": pixel, "ampcont": ampcont, "bfactor": 0.0})

			for i in xrange(nangle):
				for k in xrange(12):
					dphi = 8.0*(random()-0.5)
					dtht = 8.0*(random()-0.5)
					psi  = 360.0*random()

					phi = angles[i][0]+dphi
					tht = angles[i][1]+dtht

					s2x = 4.0*(random()-0.5)
					s2y = 4.0*(random()-0.5)

					params.append([phi, tht, psi, s2x, s2y])

					ivol = iprj % nvol
					proj = prgs(volfts[ivol], kb, [phi, tht, psi, -s2x, -s2y])
		
					x = xstart + irow * width
					y = ystart + icol * width

					mic += pad(proj, 4096, 4096, 1, 0.0, x-2048, y-2048, 0)
			
					proj = proj + model_gauss_noise( sigma_proj, nx, nx )
					if parm_CTF:
						proj = filt_ctf(proj, ctf)
						proj.set_attr_dict({"ctf":ctf, "ctf_applied":0})
			
					proj = proj + filt_gaussl(model_gauss_noise(sigma2_proj, nx, nx), sigma_gauss)
					proj.set_attr("active", 1)
					# flags describing the status of the image (1 = true, 0 = false)
					set_params2D(proj, [0.0, 0.0, 0.0, 0, 1.0])
					set_params_proj(proj, [phi, tht, psi, s2x, s2y])

					proj.write_image(stack_data, iprj)
			
					icol += 1
					if icol == rowlen:
						icol = 0
						irow += 1

					iprj += 1

			mic += model_gauss_noise(sigma_mic,4096,4096)
			if parm_CTF:
				#apply CTF
				mic = filt_ctf(mic, ctf)
			mic += filt_gaussl(model_gauss_noise(sigma2_mic, 4096, 4096), sigma_gauss_mic)
	
			mic.write_image(micpref + "%1d.hdf" % (idef-3), 0)
		
		drop_spider_doc("params.txt", params)

if __name__ == "__main__":
	main()
