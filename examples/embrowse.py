#!/usr/bin/env python
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

#
# Author: David Woolford (woolford@bcm.edu)
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston MA 02111-1307 USA
#
#

from .emapplication import EMApp
from .emselector import EMBrowser


from EMAN2 import EMData
	
app = None
def on_done(string_list):
	print("on done")
	if len(string_list) != 0:
		for s in string_list:
			print(s, end=' ')
		print()
	app.quit()

# This is just an example of how to make a browser. You should import the browser module from emselector
def main():
	em_app = EMApp()
	app = em_app
	browser = EMBrowser()
	browser.done.connect(on_done)
	em_app.show()
	em_app.execute()


if __name__ == '__main__':
	main()
