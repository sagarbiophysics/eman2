#! /usr/bin/env python
from __future__ import print_function
#
# Do not run this script directly. You could run this as 
# ipython --gui=qt -i e2_real.py
# otherwise it is normally run via the e2.py script
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

import EMAN2
import IPython.lib.inputhook
import eman2_gui.emapplication as emapplication
import eman2_gui.emimage as emimage
import global_def
import os
import sparx
pass#IMPORTIMPORTIMPORT import EMAN2
pass#IMPORTIMPORTIMPORT import IPython.lib.inputhook
pass#IMPORTIMPORTIMPORT import eman2_gui.emapplication as emapplication
pass#IMPORTIMPORTIMPORT import eman2_gui.emimage as emimage
pass#IMPORTIMPORTIMPORT import global_def
pass#IMPORTIMPORTIMPORT import os
pass#IMPORTIMPORTIMPORT import sparx
pass#IMPORTIMPORTIMPORT import EMAN2
pass#IMPORTIMPORTIMPORT import IPython.lib.inputhook
pass#IMPORTIMPORTIMPORT import eman2_gui.emapplication as emapplication
pass#IMPORTIMPORTIMPORT import eman2_gui.emimage as emimage
pass#IMPORTIMPORTIMPORT import global_def
pass#IMPORTIMPORTIMPORT import os
pass#IMPORTIMPORTIMPORT import sparx
pass#IMPORTIMPORTIMPORT import EMAN2
pass#IMPORTIMPORTIMPORT import IPython.lib.inputhook
pass#IMPORTIMPORTIMPORT import eman2_gui.emapplication as emapplication
pass#IMPORTIMPORTIMPORT import eman2_gui.emimage as emimage
pass#IMPORTIMPORTIMPORT import global_def
pass#IMPORTIMPORTIMPORT import os
pass#IMPORTIMPORTIMPORT import sparx
pass#IMPORTIMPORTIMPORT import EMAN2
pass#IMPORTIMPORTIMPORT pass#IMPORTIMPORTIMPORT pass#IMPORTIMPORTIMPORT pass#IMPORTIMPORTIMPORT from EMAN2 import *



GUIUSE=True
try:
	if EMAN2.get_platform()=="Linux" and os.os.getenv("DISPLAY")==None: raise Exception

	from PyQt4 import QtCore, QtGui, QtOpenGL
	pass#IMPORTIMPORTIMPORT pass#IMPORTIMPORTIMPORT pass#IMPORTIMPORTIMPORT pass#IMPORTIMPORTIMPORT from eman2_gui.emapplication import EMApp
	pass#IMPORTIMPORTIMPORT import IPython.lib.inputhook


	app=emapplication.EMApp()
	IPython.lib.inputhook.enable_qt4(app)

	pass#IMPORTIMPORTIMPORT pass#IMPORTIMPORTIMPORT pass#IMPORTIMPORTIMPORT pass#IMPORTIMPORTIMPORT from eman2_gui.emimage import image_update

	def ipy_on_timer():
		emimage.image_update()

	ipytimer = QtCore.QTimer()
	ipytimer.timeout.connect(ipy_on_timer)
	ipytimer.start(200)
	
	EMAN2.GUIMode=True
	EMAN2.app=app
except:
	GUIUSE=False

pass#IMPORTIMPORTIMPORT pass#IMPORTIMPORTIMPORT pass#IMPORTIMPORTIMPORT pass#IMPORTIMPORTIMPORT from sparx import *
pass#IMPORTIMPORTIMPORT import global_def
if GUIUSE:
	print("Welcome to the interactive SPARX-GUI Python interface, provided by ipython")
else:
	print("Welcome to the interactive SPARX-NoGUI Python interface, provided by ipython")
print("  ",global_def.SPARXVERSION)
