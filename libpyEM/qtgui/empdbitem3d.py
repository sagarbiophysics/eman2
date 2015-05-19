#!/usr/bin/env python
#
# Author: James Michael Bell, 2016 (jmbell@bcm.edu)
# Copyright (c) 2011- Baylor College of Medicine
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

from EMAN2 import *
from emglobjects import get_default_gl_colors
from emitem3d import EMItem3D, EMItem3DInspector
from libpyGLUtils2 import GLUtil
import os
import sys

from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui

import numpy as np

class EMPDBItem3D(EMItem3D):
	
	name = "PDB Model"
	nodetype = "ItemChild"
	
	@staticmethod
	def getNodeDialogWidget(attribdict):
		"""Get PDB Model Widget"""
		structurewidget = QtGui.QWidget()
		grid = QtGui.QGridLayout()
		node_name_data_label = QtGui.QLabel("Model Label")
		attribdict["node_name"] = QtGui.QLineEdit()
		data_path_label = QtGui.QLabel("Model Path")
		attribdict["data_path"] = QtGui.QLineEdit()
		browse_button = QtGui.QPushButton("Browse")
		grid.addWidget(node_name_data_label, 0, 0, 1, 2)
		grid.addWidget(attribdict["node_name"], 0, 2, 1, 2)
		grid.addWidget(data_path_label, 1, 0, 1, 2)
		grid.addWidget(attribdict["data_path"], 1, 2, 1, 2)
		grid.addWidget(browse_button, 2, 0, 1, 4)
		EMItem3D.get_transformlayout(grid, 4, attribdict)
		structurewidget.setLayout(grid)
		EMStructureItem3D.attribdict = attribdict
		QtCore.QObject.connect(browse_button, QtCore.SIGNAL('clicked()'), EMPDBItem3D._on_browse)
		return structurewidget
	
	@staticmethod
	def _on_browse():
		filename = QtGui.QFileDialog.getOpenFileName(None, 'Get file', os.getcwd())
		if filename:
			EMStructureItem3D.attribdict["data_path"].setText(str(filename))
			name = os.path.basename(str(filename)).split('/')[-1].split('.')[0]
			EMStructureItem3D.attribdict["node_name"].setText(str(name))
	
	@staticmethod
	def getNodeForDialog(attribdict):
		"""Create a new node using a attribdict"""
		return EMStructureItem3D(str(attribdict["data_path"].text()), transform=EMItem3D.getTransformFromDict(attribdict))
	
	def __init__(self, parent=None,transform=None,pdb_file=None):
		EMItem3D.__init__(self, parent=parent, children=set(), transform=transform)
		if pdb_file == None:
			self.fName = str(self.attribdict['data_path'].text())
			self.name = str(self.attribdict['node_name'].text())
		else:
			self.fName = pdb_file
			self.name = pdb_file.split('/')[-1].split('.')[0]
			self.attribdict = {}
			self.attribdict['data_path'] = self.fName
			self.attribdict['node_name'] = self.name
		self.diffuse = [0.5,0.5,0.5,1.0]
		self.specular = [1.0,1.0,1.0,1.0]
		self.ambient = [1.0, 1.0, 1.0, 1.0]
		self.shininess = 25.0
		self.renderBoundingBox = False
		self.first_render_flag = True # this is used to catch the first call to the render function - so you can do an GL context sensitive initialization when you know there is a valid context
		self.gq = None # will be a glu quadric
		self.dl = None
		self.cylinderdl = 0 # will be a cylinder with no caps
		self.diskdl = 0 # this will be a flat disk
		self.spheredl = 0 # this will be a low resolution sphere
		self.highresspheredl = 0 # high resolution sphere
		self.cappedcylinderdl = 0 # a capped cylinder
		self.radius = 100
		self.colors = get_default_gl_colors()
		amino_acids_list = ["ALA","ARG","ASN","ASP","CYS","GLU","GLN","GLY","HIS","ILE","LEU","LYS","MET","PHE","PRO","SER","THR","TYR","TRP","VAL"]
		self.side_chains = {aa:[] for aa in amino_acids_list}
	
	def setAmbientColor(self, red, green, blue, alpha=1.0):
		self.ambient = [red, green, blue, alpha]

	def setDiffuseColor(self, red, green, blue, alpha=1.0):
		self.diffuse = [red, green, blue, alpha]
		
	def setSpecularColor(self, red, green, blue, alpha=1.0):
		self.specular = [red, green, blue, alpha]
	
	def setShininess(self, shininess):
		self.shininess = shininess
	
	def getItemDictionary(self):
		"""
		Return a dictionary of item parameters (used for restoring sessions
		"""
		dictionary = super(EMStructureItem3D, self).getItemDictionary()
		dictionary.update({"COLOR":[self.ambient, self.diffuse, self.specular, self.shininess]})
		return dictionary

	def setUsingDictionary(self, dictionary):
		"""Set item attributes using a dictionary, used in session restoration"""
		super(EMStructureItem3D, self).setUsingDictionary(dictionary)
		self.setAmbientColor(dictionary["COLOR"][0][0], dictionary["COLOR"][0][1], dictionary["COLOR"][0][2], dictionary["COLOR"][0][3])
		self.setDiffuseColor(dictionary["COLOR"][1][0], dictionary["COLOR"][1][1], dictionary["COLOR"][1][2], dictionary["COLOR"][1][3])
		self.setSpecularColor(dictionary["COLOR"][2][0], dictionary["COLOR"][2][1], dictionary["COLOR"][2][2], dictionary["COLOR"][2][3])
	
	def renderNode(self):
		if self.is_selected and glGetIntegerv(GL_RENDER_MODE) == GL_RENDER and not self.isSelectionHidded(): # No need to draw outline in selection mode
			#if glGetIntegerv(GL_RENDER_MODE) == GL_RENDER: print "X"
			glPushAttrib( GL_ALL_ATTRIB_BITS )
			# First render the cylinder, writing the outline to the stencil buffer
			glClearStencil(0)
			glClear( GL_STENCIL_BUFFER_BIT )
			glEnable( GL_STENCIL_TEST )
			glStencilFunc( GL_ALWAYS, 1, 0xFFFF )		# Write to stencil buffer
			glStencilOp( GL_KEEP, GL_KEEP, GL_REPLACE )	# Only pixels that pass the depth test are written to the stencil buffer
			glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )	
			self.renderShape()
			# Then render the outline
			glStencilFunc( GL_NOTEQUAL, 1, 0xFFFF )		# The object itself is stenciled out
			glStencilOp( GL_KEEP, GL_KEEP, GL_REPLACE )
			glLineWidth( 4.0 )				# By increasing the line width only the outline is drawn
			glPolygonMode( GL_FRONT_AND_BACK, GL_LINE )
			glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 1.0, 0.0, 1.0])
			self.renderShape()
			glPopAttrib()	
		else:
			glPushAttrib( GL_ALL_ATTRIB_BITS )
			self.renderShape()
			glPopAttrib()
	
	def getEvalString(self):
		return "EMStructureItem3D(%s)"%self.name
	
	def getItemInspector(self):
		"""Return a Qt widget that controls the scene item"""
		if not self.item_inspector: self.item_inspector = EMStructureInspector("EMStructureItem3D", self)
		return self.item_inspector
	
	def buildResList(self): # calls PDBReader to read the given pdb file and create a list (self.allResidues) of lists (x,y,z,atom name, residue name) of lists (all the values for that residue)
		self.allResidues = []
		try:
			f = open(self.fName)
			f.close()
		except IOError:
			print "Sorry, the file name \"" + str(self.fName) + "\" does not exist"
			sys.exit()
		self.a = PDBReader()
		self.a.read_from_pdb(self.fName)
		point_x = self.a.get_x()
		point_y = self.a.get_y()
		point_z = self.a.get_z()
		point_x = point_x - np.mean(point_x)
		point_y = point_y - np.mean(point_y)
		point_z = point_z - np.mean(point_z)
		point_atomName = self.a.get_atomName()
		point_resName = self.a.get_resName()
		point_resNum = self.a.get_resNum()
		x =[]
		y =[]
		z =[]
		atomName =[]
		resName = []
		amino = []
		currentRes = point_resNum[0]
		for i in range(len(point_x)):
			if (point_resNum[i]==currentRes):
				x.append(point_x[i])
				y.append(point_y[i])
				z.append(point_z[i])
				temp = point_atomName[i]
				temp2 = temp.strip()
				atomName.append(temp2)
				resName.append(point_resName[i])
			else:
				currentRes = point_resNum[i]
				amino.append(x[:])
				amino.append(y[:])
				amino.append(z[:])
				amino.append(atomName[:])
				amino.append(resName[:])
				self.allResidues.append(amino[:])
				del amino[:]
				del x[:]
				del y[:]
				del z[:]
				del atomName[:]
				del resName[:]
				x.append(point_x[i])
				y.append(point_y[i])
				z.append(point_z[i])
				temp = point_atomName[i]
				temp2 = temp.strip()
				atomName.append(temp2)
				resName.append(point_resName[i])
				if (i == (len(point_x)-1)): 
					amino.append(x[:])
					amino.append(y[:])
					amino.append(z[:])
					amino.append(atomName[:])
					amino.append(resName[:])
					self.allResidues.append(amino[:])
					break
	
	def load_gl_color(self,name):
		color = self.colors[name]
		glColor(color["ambient"])
		glMaterial(GL_FRONT,GL_AMBIENT,color["ambient"])
		glMaterial(GL_FRONT,GL_DIFFUSE,color["diffuse"])
		glMaterial(GL_FRONT,GL_SPECULAR,color["specular"])
		glMaterial(GL_FRONT,GL_EMISSION,color["emission"])
		glMaterial(GL_FRONT,GL_SHININESS,color["shininess"])
	
	def createDefault(self):
		return	#display a default pdb here, currently not done
	
	def current_text(self): 
		return self.text
	
	def getRenderBoundingBox(self):
		return self.renderBoundingBox

	def setRenderBoundingBox(self, state):
		self.renderBoundingBox = state
	
	def draw_objects(self):
		self.init_basic_shapes() # only does something the first time you call it
		if self.dl == None: #self.dl is the display list, every time a new file is added, this is changed back to None
			self.dl=glGenLists(1)
			glNewList(self.dl,GL_COMPILE)
			self.buildResList()
			for res in self.allResidues: #goes through self.allResidues and displays a sphere for every atom in the pdb
				for i in range(len(res[0])):
					glPushMatrix()
					glTranslate(res[0][i], res[1][i], res[2][i])
					glScale(1,1,1)
					if (str(res[3][i])[0] == 'C'): self.load_gl_color("white")
					elif (str(res[3][i])[0] == 'N'): self.load_gl_color("green")
					elif (str(res[3][i])[0] == 'O'): self.load_gl_color("blue")
					elif (str(res[3][i])[0] == 'S'): self.load_gl_color("red")
					else: self.load_gl_color("silver")
					glCallList(self.highresspheredl)
					glPopMatrix()
			for k in range(len(self.allResidues)):
				res = self.allResidues[k]
				key =  res[4][0]
				if self.side_chains.has_key(key):
					self.renderResidues(res,self)
					continue
				if k !=0: #connects residues together from the nitrogen of one residue to the O of the next residue
					nt = [0,0,0]
					pt = [0,0,0]
					nt[0] = res[0][0]
					nt[1] = res[1][0]
					nt[2] = res[2][0]
					pt[0] = self.allResidues[k-1][0][2]
					pt[1] = self.allResidues[k-1][1][2]
					pt[2] = self.allResidues[k-1][2][2]
					self.cylinder_to_from(nt, pt, 0.2)
			glEndList()
		try:
			glCallList(self.dl)
		except:
			print "call list failed",self.dl
			glDeleteLists(self.dl,1)
			self.dl = None
	
	def init_basic_shapes(self):
		if self.gq == None:
			self.gq=gluNewQuadric() # a quadric for general use
			gluQuadricDrawStyle(self.gq,GLU_FILL)
			gluQuadricNormals(self.gq,GLU_SMOOTH)
			gluQuadricOrientation(self.gq,GLU_OUTSIDE)
			gluQuadricTexture(self.gq,GL_FALSE)
		if self.cylinderdl == 0:
			self.cylinderdl=glGenLists(1)
			glNewList(self.cylinderdl,GL_COMPILE)
			glPushMatrix()
			gluCylinder(self.gq,1.0,1.0,1.0,12,2)
			glPopMatrix()
			glEndList()
		if self.diskdl == 0:
			self.diskdl=glGenLists(1)
			glNewList(self.diskdl,GL_COMPILE)
			gluDisk(self.gq,0,1,12,2)
			glEndList()
		if self.spheredl == 0:
			self.spheredl=glGenLists(1)
			glNewList(self.spheredl,GL_COMPILE)
			gluSphere(self.gq,.5,4,2)
			glEndList()
		if self.highresspheredl == 0:
			self.highresspheredl=glGenLists(1)
			glNewList(self.highresspheredl,GL_COMPILE)
			gluSphere(self.gq,.5,16,16)
			glEndList()
		if self.cappedcylinderdl == 0:
			self.cappedcylinderdl=glGenLists(1)
			glNewList(self.cappedcylinderdl,GL_COMPILE)
			glCallList(self.cylinderdl)
			glPushMatrix()
			glTranslate(0,0,1)
			glCallList(self.diskdl)
			glPopMatrix()
			glPushMatrix()
			glRotate(180,0,1,0)
			glCallList(self.diskdl)
			glPopMatrix()
			glEndList()
	
	def makeStick(self, res, index1, index2): #draws a cylinder between two atoms once the index for start and stop is given
		n = [0,0,0]
		p = [0,0,0]
		p[0] = res[0][index1]
		p[1] = res[1][index1]
		p[2] = res[2][index1]
		n[0] = res[0][index2]
		n[1] = res[1][index2]
		n[2] = res[2][index2]
		self.cylinder_to_from(n, p, 0.2)
	
	def cylinder_to_from(self,next,prev,scale=0.5):
		dx = next[0] - prev[0]
		dy = next[1] - prev[1]
		dz = next[2] - prev[2]
		try: length = np.sqrt(dx**2 + dy**2 + dz**2)
		except: return
		if length == 0: return
		alt = np.arccos(dz/length)*180.0/np.pi
		phi = np.arctan2(dy,dx)*180.0/np.pi
		glPushMatrix()
		glTranslatef(prev[0], prev[1], prev[2] )
		glRotatef(90.0+phi,0,0,1)
		glRotatef(alt,1,0,0)
		glScalef(scale,scale,length)
		self.load_gl_color("silver")
		glCallList(self.cylinderdl)
		glPopMatrix()
	
	def renderShape(self):
		glDisable(GL_COLOR_MATERIAL)
		glMaterialfv(GL_FRONT, GL_DIFFUSE, self.diffuse)
		glMaterialfv(GL_FRONT, GL_SPECULAR, self.specular)
		glMaterialf(GL_FRONT, GL_SHININESS, self.shininess)
		glMaterialfv(GL_FRONT, GL_AMBIENT, self.ambient)
		if self.first_render_flag: 
			self.first_render_flag = False
		glPushMatrix()
		self.draw_objects()
		glPopMatrix()
	
	@staticmethod
	def renderResidues(res,target):
		aa = res[4][0]
		if aa == "ALA":
			try: t1 = res[3].index('CB')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass	
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
		elif aa == "ARG":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG')
			except: pass
			try: t3 = res[3].index('CD')
			except: pass
			try: t4 = res[3].index('NE')
			except: pass
			try: t5 = res[3].index('CZ')
			except: pass
			try: t6 = res[3].index('NH1')
			except: pass
			try: t7 = res[3].index('NH2')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t2, t3)
			except: pass
			try: target.makeStick(res, t3, t4)
			except: pass
			try: target.makeStick(res, t4, t5)
			except: pass
			try: target.makeStick(res, t5, t6)
			except: pass
			try: target.makeStick(res, t5, t7)
			except: pass
		elif aa == "ASP":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG')
			except: pass
			try: t3 = res[3].index('OD1')
			except: pass
			try: t4 = res[3].index('OD2')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t2, t3)
			except: pass
			try: target.makeStick(res, t2, t4)
			except: pass
		elif aa == "ASN":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG')
			except: pass
			try: t3 = res[3].index('OD1')
			except: pass
			try: t4 = res[3].index('ND2')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t2, t3)
			except: pass
			try: target.makeStick(res, t2, t4)
			except: pass
		elif aa == "CYS":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('SG')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
		elif aa == "GLY":
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
		elif aa == "GLN":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG')
			except: pass
			try: t3 = res[3].index('CD')
			except: pass
			try: t4 = res[3].index('OE1')
			except: pass
			try: t5 = res[3].index('NE2')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t2, t3)
			except: pass
			try: target.makeStick(res, t3, t4)
			except: pass
			try: target.makeStick(res, t3, t5)
			except: pass
		elif aa == "GLU":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG')
			except: pass
			try: t3 = res[3].index('CD')
			except: pass
			try: t4 = res[3].index('OE1')
			except: pass
			try: t5 = res[3].index('OE2')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t2, t3)
			except: pass
			try: target.makeStick(res, t3, t4)
			except: pass
			try: target.makeStick(res, t3, t5)
			except: pass
		elif aa == "HIS":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG')
			except: pass
			try: t3 = res[3].index('CD2')
			except: pass
			try: t4 = res[3].index('ND1')
			except: pass
			try: t5 = res[3].index('NE2')
			except: pass
			try: t6 = res[3].index('CE1')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t2, t3)
			except: pass
			try: target.makeStick(res, t2, t4)
			except: pass
			try: target.makeStick(res, t3, t5)
			except: pass
			try: target.makeStick(res, t5, t6)
			except: pass
			try: target.makeStick(res, t4, t6)
			except: pass
		elif aa == "ILE":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG1')
			except: pass
			try: t3 = res[3].index('CG2')
			except: pass
			try: t4 = res[3].index('CD1')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t1, t3)
			except: pass
			try: target.makeStick(res, t2, t4)
			except: pass
		elif aa == "LEU":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG')
			except: pass
			try: t3 = res[3].index('CD1')
			except: pass
			try: t4 = res[3].index('CD2')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t2, t3)
			except: pass
			try: target.makeStick(res, t2, t4)
			except: pass
		elif aa == "LYS":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG')
			except: pass
			try: t3 = res[3].index('CD')
			except: pass
			try: t4 = res[3].index('CE')
			except: pass
			try: t5 = res[3].index('NZ')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t2, t3)
			except: pass
			try: target.makeStick(res, t3, t4)
			except: pass
			try: target.makeStick(res, t4, t5)
			except: pass
		elif aa == "MET":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG')
			except: pass
			try: t3 = res[3].index('SD')
			except: pass
			try: t4 = res[3].index('CE')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t2, t3)
			except: pass
			try: target.makeStick(res, t3, t4)
			except: pass
		elif aa == "PHE":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG')
			except: pass
			try: t3 = res[3].index('CD1')
			except: pass
			try: t4 = res[3].index('CD2')
			except: pass
			try: t5 = res[3].index('CE1')
			except: pass
			try: t6 = res[3].index('CE2')
			except: pass
			try: t7 = res[3].index('CZ')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t2, t3)
			except: pass
			try: target.makeStick(res, t2, t4)
			except: pass
			try: target.makeStick(res, t3, t5)
			except: pass
			try: target.makeStick(res, t4, t6)
			except: pass
			try: target.makeStick(res, t5, t7)
			except: pass
			try: target.makeStick(res, t6, t7)
			except: pass
		elif aa == "PRO":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG')
			except: pass
			try: t3 = res[3].index('CD')
			except: pass
			try: t4 = res[3].index('N')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t2, t3)
			except: pass
			try: target.makeStick(res, t3, t4)
			except: pass
		elif aa == "SER":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('OG')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
		elif aa == "THR":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG2')
			except: pass
			try: t3 = res[3].index('OG1')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t1, t3)
			except: pass
		elif aa == "TRP":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG')
			except: pass
			try: t3 = res[3].index('CD1')
			except: pass
			try: t4 = res[3].index('CD2')
			except: pass
			try: t5 = res[3].index('NE1')
			except: pass
			try: t6 = res[3].index('CE2')
			except: pass
			try: t7 = res[3].index('CE3')
			except: pass
			try: t8 = res[3].index('CZ3')
			except: pass
			try: t9 = res[3].index('CH2')
			except: pass
			try: t10 = res[3].index('CZ2')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t2, t3)
			except: pass
			try: target.makeStick(res, t2, t4)
			except: pass
			try: target.makeStick(res, t3, t5)
			except: pass
			try: target.makeStick(res, t5, t6)
			except: pass
			try: target.makeStick(res, t4, t6)
			except: pass
			try: target.makeStick(res, t4, t7)
			except: pass
			try: target.makeStick(res, t7, t8)
			except: pass
			try: target.makeStick(res, t8, t9)
			except: pass
			try: target.makeStick(res, t10, t9)
			except: pass
		elif aa == "VAL":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG2')
			except: pass
			try: t3 = res[3].index('CG1')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t1, t3)
			except: pass
		elif aa == "TYR":
			try: t1 = res[3].index('CB')
			except: pass
			try: t2 = res[3].index('CG')
			except: pass
			try: t3 = res[3].index('CD1')
			except: pass
			try: t4 = res[3].index('CD2')
			except: pass
			try: t5 = res[3].index('CE1')
			except: pass
			try: t6 = res[3].index('CE2')
			except: pass
			try: t7 = res[3].index('CZ')
			except: pass
			try: t8 = res[3].index('OH')
			except: pass
			try: target.makeStick(res, 0, 1)
			except: pass
			try: target.makeStick(res, 1, 2)
			except: pass
			try: target.makeStick(res, 2, 3)
			except: pass
			try: target.makeStick(res, 1, t1)
			except: pass
			try: target.makeStick(res, t1, t2)
			except: pass
			try: target.makeStick(res, t2, t3)
			except: pass
			try: target.makeStick(res, t2, t4)
			except: pass
			try: target.makeStick(res, t3, t5)
			except: pass
			try: target.makeStick(res, t4, t6)
			except: pass
			try: target.makeStick(res, t5, t7)
			except: pass
			try: target.makeStick(res, t6, t7)
			except: pass
			try: target.makeStick(res, t7, t8)
			except: pass

class EMPDBInspector(EMItem3DInspector):
	
	def __init__(self, name, item3d):
		EMItem3DInspector.__init__(self, name, item3d)


class EMSliceItem3D(EMItem3D):
	
	"""
	This displays a slice of the volume that can be oriented any direction.
	Its parent in the tree data structure that forms the scene graph must be an EMDataItem3D instance.
	"""
	name = "Slice"
	nodetype = "DataChild"

	@staticmethod
	def getNodeDialogWidget(attribdict):
		"""
		Get Slice Widget
		"""
		slicewidget = QtGui.QWidget()
		grid = QtGui.QGridLayout()
		node_name_slice_label = QtGui.QLabel("Slice Name")
		attribdict["node_name"] = QtGui.QLineEdit(str(EMSliceItem3D.name))
		grid.addWidget(node_name_slice_label, 0, 0, 1, 2)
		grid.addWidget(attribdict["node_name"], 0, 2, 1, 2)
		EMItem3D.get_transformlayout(grid, 2, attribdict)
		slicewidget.setLayout(grid)

		return slicewidget

	@staticmethod
	def getNodeForDialog(attribdict):
		"""
		Create a new node using a attribdict
		"""
		return EMSliceItem3D(attribdict["parent"], transform=EMItem3D.getTransformFromDict(attribdict))

	def __init__(self, parent=None, children = set(), transform=None):
		"""
		@param parent: should be an EMDataItem3D instance for proper functionality.
		"""
		if not transform: transform = Transform()	# Object initialization should not be put in the constructor. Causes issues
		EMItem3D.__init__(self, parent, children, transform=transform)
		self.texture2d_name = 0
		self.texture3d_name = 0
		self.use_3d_texture = False
		self.force_texture_update = True

		self.colors = get_default_gl_colors()
		self.isocolor = "bluewhite"

		# color Needed for inspector to work John Flanagan
		self.diffuse = self.colors[self.isocolor]["diffuse"]
		self.specular = self.colors[self.isocolor]["specular"]
		self.ambient = self.colors[self.isocolor]["ambient"]
		self.shininess = self.colors[self.isocolor]["shininess"]

		if parent: self.dataChanged()

	# I have added these methods so the inspector can set the color John Flanagan
	def setAmbientColor(self, red, green, blue, alpha=1.0):
		self.ambient = [red, green, blue, alpha]

	def setDiffuseColor(self, red, green, blue, alpha=1.0):
		self.diffuse = [red, green, blue, alpha]

	def setSpecularColor(self, red, green, blue, alpha=1.0):
		self.specular = [red, green, blue, alpha]

	def setShininess(self, shininess):
		self.shininess = shininess

	def useDefaultBrightnessContrast(self):
		"""
		This applies default settings for brightness and contrast.
		"""

		data = self.getParent().getData()
		min = data.get_attr("minimum")
		max = data.get_attr("maximum")
		self.brightness = -min
		if max != min:
			self.contrast = 1.0/(max-min)
		else:
			self.contrast = 1

	def gen3DTexture(self):
		"""
		If no 3D texture exists, this creates one. It always returns the number that identifies the current 3D texture.
		"""
		if self.texture3d_name == 0:
			data_copy = self.getParent().getData().copy()
			data_copy.add(self.brightness)
			data_copy.mult(self.contrast)

			if True: #MUCH faster than generating texture in Python
				self.texture3d_name = GLUtil.gen_gl_texture(data_copy, GL.GL_LUMINANCE)
			else:
				self.texture3d_name = GL.glGenTextures(1)
				GL.glBindTexture(GL.GL_TEXTURE_3D, self.texture3d_name)
				GL.glTexImage3D(GL.GL_TEXTURE_3D,0,GL.GL_LUMINANCE, data_copy["nx"], data_copy["ny"], data_copy["nz"],0, GL.GL_ALPHA, GL.GL_FLOAT, data_copy.get_data_as_vector())

			#print "Slice Node's 3D texture == ", self.texture3d_name
		return self.texture3d_name

	def dataChanged(self):
		"""
		When the EMData changes for EMDataItem3D parent node, this method is called. It is responsible for updating the state of the slice node.
		"""
		if self.texture2d_name != 0:
			GL.glDeleteTextures(self.texture2d_name)
			self.texture2d_name = 0
		if self.texture3d_name != 0:
			GL.glDeleteTextures(self.texture3d_name)
			self.texture3d_name = 0

		self.useDefaultBrightnessContrast()

	def getEvalString(self):
		return "EMSliceItem3D()"

	def getItemInspector(self):
		if not self.item_inspector:
			self.item_inspector = EMSliceInspector("SLICE", self)
		return self.item_inspector

	def getItemDictionary(self):
		"""
		Return a dictionary of item parameters (used for restoring sessions
		"""
		dictionary = super(EMSliceItem3D, self).getItemDictionary()
		dictionary.update({"COLOR":[self.ambient, self.diffuse, self.specular, self.shininess]})
		return dictionary

	def setUsingDictionary(self, dictionary):
		"""
		Set item attributes using a dictionary, used in session restoration
		"""
		super(EMSliceItem3D, self).setUsingDictionary(dictionary)
		self.setAmbientColor(dictionary["COLOR"][0][0], dictionary["COLOR"][0][1], dictionary["COLOR"][0][2], dictionary["COLOR"][0][3])
		self.setDiffuseColor(dictionary["COLOR"][1][0], dictionary["COLOR"][1][1], dictionary["COLOR"][1][2], dictionary["COLOR"][1][3])
		self.setSpecularColor(dictionary["COLOR"][2][0], dictionary["COLOR"][2][1], dictionary["COLOR"][2][2], dictionary["COLOR"][2][3])

	def renderNode(self):
		data = self.getParent().getData()

		nx = data["nx"]
		ny = data["ny"]
		nz = data["nz"]
		interior_diagonal = math.sqrt(nx**2+ny**2+nz**2) #A square with sides this big could hold any slice from the volume
		#The interior diagonal is usually too big, and OpenGL textures work best with powers of 2 so let's get the next smaller power of 2
		diag = 2**(int(math.floor( math.log(interior_diagonal)/math.log(2) ))) #next smaller power of 2
		diag2 = diag/2

		glPushAttrib( GL_ALL_ATTRIB_BITS )
		GL.glDisable(GL.GL_LIGHTING)
		GL.glColor3f(1.0,1.0,1.0)

		if not self.use_3d_texture: #Use 2D texture

			# Any time self.transform changes, a new 2D texture is REQUIRED.
			# It is easiest to create a new 2D texture every time this is called, and seems fast enough.
			# Thus, a new 2D texture is created whether it is needed or not.

			temp_data = EMData(diag, diag)
			temp_data.cut_slice(data, self.transform)
			temp_data.add(self.brightness)
			temp_data.mult(self.contrast)

			if self.texture2d_name != 0:
				GL.glDeleteTextures(self.texture2d_name)

			self.texture2d_name = GLUtil.gen_gl_texture(temp_data, GL.GL_LUMINANCE)


			#For debugging purposes, draw an outline
			GL.glBegin(GL.GL_LINE_LOOP)
			GL.glVertex3f(-diag2, -diag2, 0)
			GL.glVertex3f(-diag2, diag2, 0)
			GL.glVertex3f(diag2, diag2, 0)
			GL.glVertex3f(diag2, -diag2, 0)
			GL.glEnd()


			#Now draw the texture on another quad

			GL.glEnable(GL.GL_TEXTURE_2D)
			GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture2d_name)
			GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP)
			GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP)
			GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)#GL.GL_NEAREST)
			GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)#GL.GL_NEAREST)

			GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_REPLACE)

			GL.glBegin(GL.GL_QUADS)
			GL.glTexCoord2f(0, 0)
			GL.glVertex3f(-diag2, -diag2, 0)
			GL.glTexCoord2f(0, 1)
			GL.glVertex3f(-diag2, diag2, 0)
			GL.glTexCoord2f(1, 1)
			GL.glVertex3f(diag2, diag2, 0)
			GL.glTexCoord2f(1, 0)
			GL.glVertex3f(diag2, -diag2, 0)
			glEnd()

			GL.glDisable(GL.GL_TEXTURE_2D)

		else: #Using a 3D texture

			# Generating a new 3D texture is slower than a new 2D texture.
			# Creating a new texture is needed if brightness or contrast change or if the EMData in self.getParent().getData() has changed.

			if self.force_texture_update:
				GL.glDeleteTextures(self.texture3d_name)
				self.texture3d_name = 0
			self.gen3DTexture()

			quad_points = [(-diag2, -diag2, 0), (-diag2, diag2, 0), (diag2, diag2, 0), (diag2, -diag2, 0)]

			#For debugging purposes, draw an outline
			GL.glMatrixMode(GL.GL_MODELVIEW)
			GL.glBegin(GL.GL_LINE_LOOP)
			for i in range(4):
				GL.glVertex3f(*quad_points[i])
			GL.glEnd()

			#Now draw the texture on another quad

			GL.glEnable(GL.GL_TEXTURE_3D)
			GL.glBindTexture(GL.GL_TEXTURE_3D, self.texture3d_name)
			GL.glTexParameterf(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_BORDER)
			GL.glTexParameterf(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_BORDER)
			GL.glTexParameterf(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_R, GL.GL_CLAMP_TO_BORDER)
			GL.glTexParameterf(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)#GL.GL_NEAREST)
			GL.glTexParameterf(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)#GL.GL_NEAREST)
	#		GL.glTexParameterfv(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_BORDER_COLOR, (0.0, 0.0,1.0,1.0,1.0))

			GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_REPLACE)
			GL.glMatrixMode(GL.GL_TEXTURE)
			GL.glLoadIdentity()
			GL.glTranslatef(0.5, 0.5, 0.5) #Put the origin at the center of the 3D texture
			GL.glScalef(1.0/nx, 1.0/ny, 1.0/nz) #Scale to make the texture coords the same as data coords
			GLUtil.glMultMatrix(self.transform) #Make texture coords the same as EMSliceItem3D coords
			GL.glMatrixMode(GL.GL_MODELVIEW)

			GL.glBegin(GL.GL_QUADS)
			for i in range(4):
				GL.glTexCoord3f(*quad_points[i])
				GL.glVertex3f(*quad_points[i])
			glEnd()

			GL.glMatrixMode(GL.GL_TEXTURE)
			GL.glLoadIdentity()
			GL.glMatrixMode(GL.GL_MODELVIEW)

			GL.glDisable(GL.GL_TEXTURE_3D)

		GL.glEnable(GL.GL_LIGHTING)
		glPopAttrib()

class EMSliceInspector(EMInspectorControlShape):
	def __init__(self, name, item3d):
		EMInspectorControlShape.__init__(self, name, item3d)

		self.constrained_plane_combobox.currentIndexChanged.connect(self.onConstrainedOrientationChanged)
		self.use_3d_texture_checkbox.clicked.connect(self.on3DTextureCheckbox)
		QtCore.QObject.connect(self.constrained_slider, QtCore.SIGNAL("valueChanged"), self.onConstraintSlider)
		QtCore.QObject.connect(self.brightness_slider, QtCore.SIGNAL("valueChanged"), self.onBrightnessSlider)
		QtCore.QObject.connect(self.contrast_slider, QtCore.SIGNAL("valueChanged"), self.onContrastSlider)

		self.updateItemControls()

	def updateItemControls(self):
		""" Updates this item inspector. Function is called by the item it observes"""
		super(EMSliceInspector, self).updateItemControls()
		# Anything that needs to be updated when the scene is rendered goes here.....
		self.use_3d_texture_checkbox.setChecked(self.item3d().use_3d_texture)
		data = self.item3d().getParent().getData()
		min = data["minimum"]
		max = data["maximum"]
		mean = data["mean"]
		std_dev = data["sigma"]

		self.brightness_slider.setValue(self.item3d().brightness)
		self.brightness_slider.setRange(-max, -min)

		self.contrast_slider.setValue(self.item3d().contrast)
		self.contrast_slider.setRange(0.001, 1.0)

	def addTabs(self):
		""" Add a tab for each 'column' """
		tabwidget = QtGui.QWidget()
		gridbox = QtGui.QGridLayout()
		tabwidget.setLayout(gridbox)
		self.addTab(tabwidget, "slices")
		# add slices tab first then basic tab
		super(EMSliceInspector, self).addTabs()
		EMSliceInspector.addControls(self, gridbox)

	def addControls(self, gridbox):
		""" Construct all the widgets in this Item Inspector """
		sliceframe = QtGui.QFrame()
		sliceframe.setFrameShape(QtGui.QFrame.StyledPanel)
		slice_grid_layout = QtGui.QGridLayout()

		self.constrained_group_box = QtGui.QGroupBox("Constrained Slices")
		self.constrained_group_box.setCheckable(True)
		self.constrained_group_box.setChecked(False)

		self.constrained_plane_combobox = QtGui.QComboBox()
		self.constrained_plane_combobox.addItems(["XY", "YZ", "ZX"])
		self.constrained_slider = ValSlider(label="Trans:")

		constrained_layout = QtGui.QVBoxLayout()
		constrained_layout.addWidget(self.constrained_plane_combobox)
		constrained_layout.addWidget(self.constrained_slider)
		constrained_layout.addStretch()
		self.constrained_group_box.setLayout(constrained_layout)

		self.use_3d_texture_checkbox = QtGui.QCheckBox("Use 3D Texture")
		self.use_3d_texture_checkbox.setChecked(self.item3d().use_3d_texture)

		self.brightness_slider = ValSlider(label="Bright:")
		self.contrast_slider = ValSlider(label="Contr:")

		slice_grid_layout.addWidget(self.constrained_group_box, 0, 1, 2, 1)
		slice_grid_layout.addWidget(self.use_3d_texture_checkbox, 2, 1, 1, 1)
		slice_grid_layout.addWidget(self.brightness_slider, 3, 1, 1, 1)
		slice_grid_layout.addWidget(self.contrast_slider, 4, 1, 1, 1)
		slice_grid_layout.setRowStretch(5,1)
		sliceframe.setLayout(slice_grid_layout)
		gridbox.addWidget(sliceframe, 2, 0, 2, 1)

	def on3DTextureCheckbox(self):
		self.item3d().use_3d_texture = self.use_3d_texture_checkbox.isChecked()
		if self.inspector:
			self.inspector().updateSceneGraph()

	def onConstrainedOrientationChanged(self):
		self.constrained_slider.setValue(0)
		(nx, ny, nz) = self.item3d().getParent().getBoundingBoxDimensions()
		range = (0, nx)
		plane = str(self.constrained_plane_combobox.currentText())
		if plane == "XY": range = (-nz/2.0, nz/2.0)
		elif plane == "YZ": range = (-nx/2.0, nx/2.0)
		elif plane == "ZX": range = (-ny/2.0, ny/2.0)
		self.constrained_slider.setRange(*range)
		self.onConstraintSlider()

	def onConstraintSlider(self):
		value = self.constrained_slider.getValue()
		transform = self.item3d().getTransform()
		plane = str(self.constrained_plane_combobox.currentText())
		if plane == "XY":
			transform.set_rotation((0,0,1))
			transform.set_trans(0,0,value)
		elif plane == "YZ":
			transform.set_rotation((1,0,0))
			transform.set_trans(value, 0, 0)
		elif plane == "ZX":
			transform.set_rotation((0,1,0))
			transform.set_trans(0,value,0)

		if self.inspector:
			self.inspector().updateSceneGraph()

	def onBrightnessSlider(self):
		self.item3d().brightness = self.brightness_slider.getValue()
		self.item3d().force_texture_update = True
		if self.inspector:
			self.inspector().updateSceneGraph()

	def onContrastSlider(self):
		self.item3d().contrast = self.contrast_slider.getValue()
		self.item3d().force_texture_update = True
		if self.inspector:
			self.inspector().updateSceneGraph()