#!/usr/bin/env python
from __future__ import print_function
from __future__ import division
#
# Author: John Flanagan (jfflanag@bcm.edu)
# Copyright (c) 2000-2011 Baylor College of Medicine


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
from builtins import range
import os, re
from EMAN2 import *
import numpy as np

def main():
	progname = os.path.basename(sys.argv[0])
	usage = """prog [options] --stackname myfile.hdf <image1> <image2> <image3> ...
	This program will combine many image files into a single output file.

	If the output name has a ".lst" extension:
	the output is a formatted text file, one line per image, describing the file containing the actual
	image data in a searchable form. .lst files can be used as if they conatined actual images in any
	EMAN2 programs.

	If the output is a normal image file (.hdf, .spi, etc.) then the images will be copied into the
	output file sequentially in the order provided on the command-line. Some file formats will not
	support multiple images, or multiple volumes. Appropriate errors will be raised in these cases.
	HDF is the only format supporting full metadata retention for stacks of images or volumes.

	The output file will be emptied and overwritten!
	"""

	parser = EMArgumentParser(usage=usage,version=EMANVERSION)

	parser.add_pos_argument(name="stack_files",help="List of images to be stacked", default="", guitype='filebox', browser="EMParticlesEditTable(withmodal=True,multiselect=True)",  row=0, col=0,rowspan=1, colspan=3, nosharedb=True,mode="default")
	parser.add_pos_argument(name="tilt_images",help="List of images to be stacked", default="", guitype='filebox', browser="EMTiltsTable(withmodal=True,multiselect=True)",  row=0, col=0,rowspan=1, colspan=3, nosharedb=True,mode="tomo")
	parser.add_argument("--output",type=str,help="Name of the output stack to build (including file extension).", default=None, guitype='strbox',row=2, col=0, rowspan=1, colspan=1, mode="default,tomo")
	parser.add_argument("--tilts",action="store_true",default=False,help="Write results to 'tiltseries' directory in current project.", guitype='boolbox',row=4, col=0, rowspan=1, colspan=1,mode="tomo[True]")
	parser.add_argument("--rawtlt",type=str,help="Name of tilt angles text file.\nNote, angles must correspond to stack file names in alphabetical/numerical order.", default="", guitype='filebox', browser="EMBrowserWidget(withmodal=True,multiselect=True)",row=3, col=0, rowspan=1, colspan=1, mode="tomo")
	parser.add_argument("--ppid", type=int, help="Set the PID of the parent process, used for cross platform PPID",default=-1)
	parser.add_argument("--verbose", "-v", dest="verbose", action="store", metavar="n", type=int, help="verbose level [0-9], higner number means higher level of verboseness",default=1)

	(options, args) = parser.parse_args()

	if options.output==None:
		print("--output is required (output file)")
		sys.exit(1)

	if options.tilts:

		stdir = os.path.join(".","tiltseries")
		if not os.access(stdir, os.R_OK):
			os.mkdir(stdir)

		options.output = "{}/{}".format(stdir,options.output)

		if options.output.split(".")[-1] not in [".hdf",".mrc",".mrcs"]:
			options.output = options.output + ".hdf"

		# remove existing output file
		if os.path.exists(options.output) :
			print("The file {} already exists.".format(options.output))
			print("Please move, rename, or remove this file to generate an alternate version with this program.")
			sys.exit(1)

		n=0		# number of images in output file

		if options.rawtlt:

			angles = np.loadtxt(options.angles)

			try:
				angles = np.loadtxt(options.angles)
			except:
				print("Error: Could not read tilt angles from {}".format(options.angles))
				sys.exit(1)
			if len(angles) != len(args):
				print("Error: There are not enough tilt angles in this tilt angles file.")
				sys.exit(1)

		tlt_assoc = {}
		for i,arg in enumerate(args):
			if options.angles:
				tlt_assoc[angles[i]] = arg
			else:
				db=js_open_dict(info_name(arg,nodir=True))
				ang = float(db["tilt_angle"])
				tlt_assoc[ang] = arg
			db.close()

		ordered_angles = sorted([float(a) for a in list(tlt_assoc.keys())])
		sorted_args = [tlt_assoc[a] for a in ordered_angles] # order args according to tilt angle parameter

		for angle,infile in zip(ordered_angles,sorted_args):
			nimg = EMUtil.get_image_count(infile) # number of images in each input file as it is processed

			if options.verbose:
				if nimg==1: print(infile)
				else: print(infile,nimg)

			for i in range(nimg):

				img=EMData(infile,i)
				img["tilt_angle"] = angle

				db=js_open_dict(info_name(infile,nodir=True))
				try: # this data may already be present
					img["SerialEM.tilt_angle"] = db["tilt_angle"]
					img["SerialEM.intensity"] = db["intensity"]
					img["SerialEM.exposure_time"] = db["exposure_time"]
					img["SerialEM.exposure_dose"] = db["exposure_dose"]
					img["SerialEM.sub_frame_count"] = db["sub_frame_count"]
					img["SerialEM.prior_record_dose"] = db["prior_record_dose"]
					img["SerialEM.frames_per_second"] = db["frames_per_second"]
				except: pass
				db.close()

				img.write_image(options.output,n)
				n+=1

if __name__ == "__main__":
	main()
