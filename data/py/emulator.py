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
import command
import os
from re import match

class Emulator:
	def __init__(self,*paths):
		self.paths = {
			"gngeo" : paths[0].replace("'","\'"),
			"romrc" : paths[1].replace("'","\'")
			}
		self.cmd = None
		self.romFullToMame = {}
		self.romMameToFull = {}

	def setPath(self,param,value):
		"""Changing important path values."""
		self.paths[param] = value

	def getGngeoVersion(self,path=None):
		"""Returning Gngeo version number as tuple and string (or None)."""
		pipe = os.popen("'%s' --version" % (path or self.paths['gngeo']),"r")
		version = match("Gngeo (\S*)",pipe.readline())
		pipe.close()
		if version:
			list = []
			for num in version.group(1).split("."):
				try: list.append(int(num))
				except: list.append(num)
			return tuple(list), version.group(1) #Returning value as a tuple and a string.

		return None #Returning nothing.

	def getAllSupportedRom(self):
		"""Returning list of all the Rom supported by the driver file, according
		to Gngeo output (launched with the `--listgame' argument)."""
		self.romMameNames = []
		self.romFullNames = []
		self.romFullToMame = {}
		self.romMameToFull = {}

		pipe = os.popen("'%s' --listgame" % self.paths['gngeo'])
		for line in pipe.readlines():
			plop = match("(\S*) : (.*)",line)
			if plop:
				#Appending ROM information to the lists & dicts.
				self.romMameNames.append(plop.group(1))
				self.romFullNames.append(plop.group(2))
				self.romMameToFull[plop.group(1)] = plop.group(2)
				self.romFullToMame[plop.group(2)] = plop.group(1)
		pipe.close()

		#Storing lists.
		self.romMameNames.sort(key=str.lower)
		self.romFullNames.sort(key=str.lower)

	def getRomMameToFull(self):	return self.romMameToFull
	def getRomFullToMame(self): return self.romFullToMame
	def getRomMameNames(self): return self.romMameNames
	def getRomFullNames(self): return self.romFullNames

	def archiveRecognition(self,archive_path):
		"""Using Gngeo directory scanning to check whether a mentioned archive
		is a supported ROM, and returning some infos (its MAME and full names)
		if it's the case."""
		dir = os.path.dirname(archive_path)
		filename = os.path.basename(archive_path)

		#Getting Gngeo directory scan results.
		pipe = os.popen("'%s' --scandir='%s'" % (self.paths['gngeo'],dir.replace("'","\'")),"r")
		results = pipe.readlines()[1:]
		pipe.close()

		#Looking for potential details regarding the archive to check in the scan results...
		for line in results:
			plop = match("\s*(\S*):(.*):(\S*)",line)
			if plop:
				if plop.group(3)==filename: #Archive was effectively recognized as a ROM!
					return plop.group(1),plop.group(2) #Returning the infos. :-)

		return None #Arhive wasn't detected as a ROM, returning nothing... :-(

	def scanRomInDirectory(self,dir,filesel_dialog=False):
		"""Generating and returning a dictionary containing the MAME name then the actual
		file name (and optionaly full name) of all the ROMs available in a mentioned directory,
		according to the scan results given by Gngeo (launched with the `--scandir=[dir]'
		argument)."""
		dict = {}
		pipe = os.popen("'%s' --scandir='%s'" % (self.paths['gngeo'],dir.replace("'","\'")),"r")

		if not filesel_dialog:
			#Normal dict formating: MAME name => file name.
			for line in pipe.readlines()[1:]:
				plop = match("\s*(\S*):.*:(\S*)",line)
				if plop:	dict[plop.group(1)] = plop.group(2) #Appending ROM information to the dict.
		else:
			#Including ROM full names in the returned dict, whom keys will
			#be file names (to use for the file selection dialog preview).
			for line in pipe.readlines()[1:]:
				plop = match("\s*(\S*):(.*):(\S*)",line)
				if plop:	 dict[plop.group(3)] = (plop.group(1),plop.group(2)) #Appending ROM information to the dict.

		pipe.close()
		return dict

	def romLaunching(self,rom_path):
		"""Starting the Gngeo (failsafe :p) thread."""
		self.cmd = command.ThreadedCmd("'%s' -d '%s' '%s'" % (self.paths['gngeo'],self.paths['romrc'],rom_path))
		self.cmd.start()

	def romWaitingForHangingUp(self):
		"""Waiting for Gngeo to hang up..."""
		return self.cmd.join()

	def romGetProcessOutput(self):
		"""Returning the raw Gngeo output of its ROM lauching process."""
		return self.cmd.getOutput()
	
	def romRunningState(self):
		"""Telling if Gngeo is either currently running a Rom, or not. :p"""
		if self.cmd: return self.cmd.isAlive()
		else: return False
