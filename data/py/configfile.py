"""
XGngeo: a frontend for Gngeo in GTK ^^.
Copyleft 2003, 2004, 2005, 2006 Choplair-network
$Id$

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
from re import match
import os.path
from sys import prefix

class Configfile:
	"""XGngeo manages two main configuration files:
- Gngeo's configuration file (`gngeorc') to modify emulator
parameters (graphic, path, keys, etc.);
- his own configuration file (`xgngeo.conf') to customize some
frontend features (history, preview images, etc.).
XGngeo's configuration file uses the same syntax than Gngeo's.

In the same time, this class allow creation of Rom-specific
configuration files, which may define the same kind of option
as the `gngeorc'."""

	def __init__(self,datarootpath,xgngeoUserDir,gngeoUserDir):
		#Initial attributes.
		self.datarootpath = datarootpath
		self.gngeorc_buffer = None
		self.paths = {
			"xgngeoUserDir" : xgngeoUserDir, #XGngeo local configuration directory.
			"xgngeoConf" : os.path.join(xgngeoUserDir,"xgngeo.conf"), #Path to XGngeo config file.
			"gngeoUserDir" : gngeoUserDir, #Gngeo local configuration directory.
			"gngeorc" : os.path.join(gngeoUserDir,"gngeorc"), #Path to Gngeo config file.
			}
		for dir in (self.paths["xgngeoUserDir"],self.paths["gngeoUserDir"]):
			if not os.path.isdir(dir): os.mkdir(dir)

	def getDefaultParams(self):
		"""Returns default options for the `gngeorc'/Rom-specific
		and XGngeo configuration files."""
		return { #Gngeo default.
			#Important path section.
			"rompath": os.path.expanduser("~/..."),
			"romrc":os.path.join(prefix,"share","gngeo","romrc"),
			#Display section.
			"fullscreen":"false",
			"interpolation":"false",
			"showfps":"false",
			"autoframeskip":"true",
			"raster":"false",
			"hwsurface":"false",
			"scale":1,
			"screen320":"true",
			"blitter":"soft",
			"effect": None,
			"transpack": None,
			#Audio / Joystick section.
			"sound":"true",
			"samplerate":"22050",
			"joystick":"true",
			"p1joydev":0,
			"p2joydev":1,
			#Controller section.
			"p1key":"119,120,113,115,38,34,273,274,276,275,-1,-1,-1,-1",
			"p2key":"108,109,111,112,233,39,264,261,260,262,-1,-1,-1,-1",
			"p1joy" : "2,3,0,1,5,4,0,1,1,1",
			"p2joy" : "1,0,3,2,7,6,0,1,1,1",
			"p1hotkey0": "4,8",
			"p1hotkey1": "2,4",
			"p1hotkey2": "1,2,4",
			"p1hotkey3": None,
			"p2hotkey0": None,
			"p2hotkey1": None,
			"p2hotkey2": None,
			"p2hotkey3": None,
			#System section.
			"system":"arcade",
			"country":"europe",
			"68kclock":0,
			"z80clock":0,
			#Other thing section.
			"libglpath":"/usr/lib/libGL.so",
			"sleepidle":"true",
			"bench":"false",
			},{ #XGngeo default.
			"autoexecrom":"true",
			"gngeopath":"gngeo",
			"historysize":5,
			"previewimages":"false",
			"previewimagedir": os.path.join(self.datarootpath,"img","rom_previews"),
			"rominfos":"true",
			"rominfoxml": os.path.join(self.datarootpath,"rominfos.xml"),
			"showavailableromsonly":"true",
			"centerwindow":"false"
			}

	def exists(self):
		return os.path.isfile(self.paths["gngeorc"]),os.path.isfile(self.paths["xgngeoConf"])

	def getParams(self,mamename=None):
		"""Try to get the params of the global or a Rom-specific configuration file.
		If the file doesn't exist, there is no error but the param dict stays empty."""
		if not mamename:
			#Parsing default main configuration files.
			dict = [{},{}]
			i=0
			for path in self.paths["gngeorc"],self.paths["xgngeoConf"]:
				if self.exists()[i]:
					file = open(path,"r") #Openning.
					content = file.readlines() #Reading.
					if i==0: self.gngeorc_buffer = content
					file.close() #And closing. :p
					for line in content:
						line.strip()
						if line[0]!="#" and line!="\n":
							plop = match("(\S*) (.*)",line)
							dict[i][plop.group(1).strip()] = plop.group(2).strip()
				i+=1
		else:
			#Parsing specific ROM configuration file.
			dict = {}
			path = os.path.join(self.paths["gngeoUserDir"],"%s.cf" % mamename)
			if os.path.isfile(path):
				file = open(path,"r") #Opening.
				content = file.readlines() #Reading.
				file.close() #Then closing. :p
				for line in content:
					line.strip()
					if line[0]!="#" and line!="\n":
						plop = match("(\S*) (.*)",line)
						if plop:
							dict[plop.group(1).strip()] = plop.group(2).strip()

		return dict

	def writeGlobalConfig(self,gngeoDict,xgngeoDict,version):
		#Top comments. :p
		content = []
		content.append("# Gngeo global configuration file.\n\
# Generated by XGngeo version %i (http://www.choplair.org/). ^o^\n\
\n" % version)
		content.append("# XGngeo configuration file.\n\
# This file is dedicated to customize XGngeo's own features. ^o^\n\
# It uses same syntax as Gngeo's.\n\
\n")

		#WAGLAMOT (``Write A Gngeorc Like A Maman Ours Technology") version 3 in action!
		i=0
		for dict in gngeoDict,xgngeoDict:
			#Use a first-pass, formating & comment preservative method (for gngeorc only).
			if i==0:
				yet_passed = []
				preserved_content = ""
				for line in self.gngeorc_buffer:
					if line[0]=="#" or line=="\n":
						preserved_content += line
						if line[0]=="#": yet_passed.append(line[1:].strip())
					else:
						plop = match("(\S*) .*",line)
						if plop:
							key = plop.group(1).strip()
							if dict.has_key(key) and not key in yet_passed:
								preserved_content += "%s %s\n" % (key,dict[key])
								yet_passed.append(key.strip())

				#Removing top XGngeo comment if yet present.
				mark = "(http://www.choplair.org/). ^o^\n\n"
				pos = preserved_content.find(mark)
				if pos>0: preserved_content = preserved_content[pos+len(mark):]

				content[i] += "%s\n" % preserved_content.rstrip()

			#Then follows the classic, destructive method. :p
			for key, val in dict.items():
				if i==0 and key in yet_passed: continue

				if val==None:	#Unset value, simply display the param in a commented line.
					val=""
					content[i] += "#"

				content[i] += "%s %s\n" % (key,val)
			content[i] += "\n" #Final blank line.
			i+=1

		file = open(self.paths["gngeorc"],"w") #Opening (creating if doesn't exist).
		file.write(content[0]) #Writing.
		file.close() #And closing.

		file = open(self.paths["xgngeoConf"],"w") #Opening (creating if doesn't exist).
		file.write(content[1]) #Writing.
		file.close() #And closing.

	def writeRomConfig(self,dict,mamename,version):
		path = os.path.join(self.paths["gngeoUserDir"],"%s.cf" % mamename)

		#Top comment. :p
		content = "# Specific configuration file for the \"%s\" Rom.\n\
# Generated by XGngeo version %s (http://www.choplair.org/). ^o^\n\
\n" % (mamename,version)

		for key, val in dict.items():
			if val in (None,""):	#Unset value, simply display the param in a commented line.
				val=""
				content += "#"

			content += "%s %s\n" % (key,val)
			content += "\n" #Final blank line.

		file = open(path,"w") #Openning (creating if doesn't exist)
		file.write(content) #Writing.
		file.close() #Then closing.
