"""
XGngeo: a frontend for Gngeo in GTK ^^.
Copyleft 2003, 2004, 2005 Choplair-network
$id: $

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""
<<<<<<< configfile.py
from re import match
=======
from string import split
from re import match
>>>>>>> 1.6
import os.path

class Configfile:
<<<<<<< configfile.py
	"""XGngeo manages two main configuration files:
- Gngeo's configuration file (`gngeorc') to modify emulator
parameters (graphic, path, keys, etc.);
- his own configuration file (`xgngeo.conf') to customize some
frontend features (history, preview images, etc.).
XGngeo's configuration file uses the same syntax than Gngeo's.

In the same time, this class allow creation of Rom-specific
configuration files, which may define the same kind of option
as the `gngeorc'."""

	def __init__(self):
		self.xgngeoconfPath = "data/xgngeo.conf" #Path to XGngeo config file.
		self.gngeoDir = os.path.expanduser("~/.gngeo") #Gngeo local configuration directory.
		self.gngeorcPath = os.path.join(self.gngeoDir,"gngeorc") #Path to Gngeo config file.

	def getDefaultParams(self):
		"""Returns default options for the `gngeorc'/Rom-specific
		and XGngeo configuration files."""
		return { #Gngeo default.
			#Path
			"libglpath":"/usr/lib/libGL.so",
			"rompath": os.path.join(os.getenv("HOME"),"..."),
			"romrc":"/usr/local/share/gngeo/romrc",
			#Graphic
			"blitter":"soft",
			"effect":"none",
			"fullscreen":"false",
			"interpolation":"false",
			"showfps":"false",
			"autoframeskip":"true",
			"scale":1,
			"screen320":"true",
			"raster":"false",
			#Audio / Joystick
			"sound":"true",
			"samplerate":"44100",
			"joystick":"true",
			"p1joydev":0,
			"p2joydev":1,
			#Keyboard
			"p1key":"119,120,113,115,38,34,273,274,276,275",
			"p2key":"108,109,111,112,233,39,264,261,260,262",
			#System
			"system":"arcade",
			"country":"europe",
			},{ #XGngeo default.
			"autoexecrom":"false",
			"gngeopath":"/usr/local/bin/gngeo",
			"historysize":5,
			"previewimagedir":"data/previewimages/",
			"rominfoxml":"data/rominfos.xml",
			"showavailableromsonly":"true"
			}

=======
	"""XGngeo manages two configuration files:
- Gngeo's configuration file (`gngeorc') to modify emulator paramas (graphic, path, keys, etc.);
- his own configuration file (`xgngeo.conf') to customize some features (history, preview images, etc.).
XGngeo's configuration file uses the same syntax than Gngeo's."""

	def __init__(self,gngeorc,xgngeo,gngeodir):
		self.gngeorcPath = gngeorc #Path to Gngeo config file.
		self.xgngeoPath = xgngeo #Path to XGngeo config file.
		self.gngeoDir = gngeodir #Gngeo local configuration directory.

>>>>>>> 1.6
	def exists(self):
<<<<<<< configfile.py
		return os.path.isfile(self.gngeorcPath),os.path.isfile(self.xgngeoconfPath)
=======
		return os.path.isfile(self.gngeorcPath),os.path.isfile(self.xgngeoPath)
>>>>>>> 1.6

<<<<<<< configfile.py
	def getParams(self,mamename=None):
		"""Try to get the params of the global or a Rom-specific configuration file.
If the file doesn't exist, there is no error but the param dict stays empty."""
		if not mamename:
			#Parsing default main configuration files.
			dict = [{},{}]
			i=0
			for path in self.gngeorcPath,self.xgngeoconfPath:
				if self.exists()[i]:
					file = open(path,"r") #Open
					content = file.readlines() #Read
					file.close() #And close :p
					for line in content:
						line.strip()
						if line[0]!="#" and line!="\n":
							plop = match("(\S*) (.*)",line)
							dict[i][plop.group(1).strip()] = plop.group(2).strip()
				i+=1
		else:
			#Parsing specific rom configuration file.
			dict = {}
			path = os.path.join(self.gngeoDir,"%s.cf" % mamename)
			if os.path.isfile(path):
				file = open(path,"r") #Open
				content = file.readlines() #Read
				file.close() #And close :p
				for line in content:
					line.strip()
					if line[0]!="#" and line!="\n":
						plop = match("(\S*) (.*)",line)
						dict[plop.group(1).strip()] = plop.group(2).strip()
=======
	def getParams(self,mamename=None):
		if not mamename:
			#Parsing default configuration files.
			dict = [{},{}]
			i=0
			for path in self.gngeorcPath,self.xgngeoPath:
				if self.exists()[i]:
					file = open(path,"r") #Open
					content = file.readlines() #Read
					file.close() #And close :p
					for line in content:
						plop = match("(\S*) (.*)",line)
						if plop: #Append Rom information to the dicts.
							dict[i][plop.group(1)] = plop.group(2)
				i+=1
		else:
			#Parsing specific rom configuration file.
			dict = {}
			path = os.path.join(self.gngeoDir,"%s.cf" % mamename)
			if os.path.isfile(path):
				file = open(path,"r") #Open
				content = file.readlines() #Read
				file.close() #And close :p
				for line in content:
					plop = match("(\S*) (.*)",line)
					if plop: #Append Rom information to the dicts.
						dict[plop.group(1)] = plop.group(2)
>>>>>>> 1.6

		return dict

<<<<<<< configfile.py
	def writeGlobalConfig(self,gngeoDict,xgngeoDict,version):
		#Top comments. :p
		gngeoContent = "# Gngeo global configuration file.\n\
# Generated by XGngeo version %s (http://www.choplair.org/). ^o^\n\
=======
	def write(self,gngeoDict,xgngeoDict,version):
		#Top comments. :p
		gngeoContent = "# Gngeo configuration file.\n\
# Generated by XGngeo version %s (http://www.choplair.org/). ^o^\n\
>>>>>>> 1.6
\n" % version
		xgngeoContent = "# XGngeo configuration file.\n\
# This file is dedicated to customize XGngeo's own features. ^o^\n\
# It uses same syntax as Gngeo's.\n\
\n"

		#WAGLAMOT (``Write A Gngeorc Like A Maman Ours Technology") version 2 in action!
		i=0
		for dict in gngeoDict,xgngeoDict:
			for key, val in dict.items():
				if i==0: gngeoContent += "%s %s\n" % (key,val)
				else: xgngeoContent += "%s %s\n" % (key,val)
			i+=1

		file = open(self.gngeorcPath,"w") #Open (create if doesn't exist)
		file.write(gngeoContent) #Write
		file.close() #And close

<<<<<<< configfile.py
		file = open(self.xgngeoconfPath,"w") #Open (create if doesn't exist)
		file.write(xgngeoContent) #Write
=======
		file = open(self.gngeorcPath,"w") #Open (create if doesn't exist)
		file.write(gngeoContent) #Write
>>>>>>> 1.6
		file.close() #And close

<<<<<<< configfile.py
	def writeRomConfig(self,dict,mamename,version):
		path = os.path.join(self.gngeoDir,"%s.cf" % mamename)

		#Top comment. :p
		content = "# Specific configuration file for the \"%s\" Rom.\n\
# Generated by XGngeo version %s (http://www.choplair.org/). ^o^\n\
\n" % (mamename,version)
		for key, val in dict.items(): content += "%s %s\n" % (key,val)

		file = open(path,"w") #Open (create if doesn't exist)
		file.write(content) #Write
=======
		file = open(self.xgngeoPath,"w") #Open (create if doesn't exist)
		file.write(xgngeoContent) #Write
		file.close() #And close

	def writeRomConfig(self,dict,mamename,version):
		path = os.path.join(self.gngeoDir,"%s.cf" % mamename)

		#Top comment. :p
		content = "# Specific configuration file for the \"%s\" Rom.\n\
# Generated by XGngeo version %s (http://www.choplair.org/). ^o^\n\
\n" % (mamename,version)
		for key, val in dict.items(): content += "%s %s\n" % (key,val)
		content += "\n" #Add blank line at the end.

		file = open(path,"w") #Open (create if doesn't exist)
		file.write(content) #Write
>>>>>>> 1.6
		file.close() #And close
