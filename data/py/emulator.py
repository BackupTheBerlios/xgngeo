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
from os import popen
from re import match

class Emulator:
	def __init__(self,*paths):
		self.path = {
			"gngeo" : paths[0].replace("'","\'"),
			"romrc" : paths[1].replace("'","\'")
			}
		self.cmd = None

	def setPath(self,param,value):
		"""Changing important path values."""
		self.path[param] = value

	def getGngeoVersion(self,path=None):
		"""Returning Gngeo version number as tuple and string (or None)."""
		pipe = popen("'%s' --version" % (path or self.path['gngeo']),"r")
		version = match("Gngeo (\S*)",pipe.readline())
		pipe.close()
		if not version: return None #Returning nothing.
		else:
				list = []
				for num in version.group(1).split("."):
					try: list.append(int(num))
					except: list.append(num)

		return tuple(list), version.group(1) #Returning as tuple and string.

	def getAllSupportedRom(self):
		"""Returning list of all the Rom supported by the driver file,
		according to Gngeo output with the `--listgame' argument."""
		pipe = popen("'%s' --listgame" % (self.path['gngeo'],dir.replace(" ","\ ")),"r")
		for line in pipe.readlines():
			plop = match("(\S*) : (.*)",line)
			if plop:
				pass
		pipe.close()

	def scanRomInDirectory(self,dir):
		"""Generating two ROM dictionaries connecting their MAME name to their full name
		(the contrary for the second) for all the Rom available in a mentioned directory,
		according to the scan result given by Gngeo with the `--scandir=[dir]' argument."""
		self.romFullToMame = {}
		self.romMameToFull = {}
		pipe = popen("'%s' --scandir=%s" % (self.path['gngeo'],dir.replace(" ","\ ")),"r")
		for line in pipe.readlines()[1:]:
			print line
			plop = match("\s*(\S*):(.*):\S*",line)
			if plop:
				#Append Rom information to the dicts.
				self.romMameToFull[plop.group(1)] = plop.group(2)
				self.romFullToMame[plop.group(2)] = plop.group(1)
		pipe.close()

	def getRomMameToFull(self):	return self.romMameToFull
	def getRomFullToMame(self): return self.romFullToMame
	def getRomFullNames(self):
		list = self.romFullToMame.keys()
		list.sort(key=str.lower)
		return list

	def romLaunching(self,rom_path):
		"""Starting the Gngeo (failsafe :p) thread."""
		self.cmd = command.ThreadedCmd("'%s' -d '%s' '%s'" % (self.path['gngeo'],self.path['romrc'],rom_path))
		self.cmd.start()

	def romWaitingForHangingUp(self):
		"""Waiting for Gngeo to hang up..."""
		return self.cmd.join()

	def romGetProcessOutput(self):
		"""Returning raw Gngeo output of its ROM lauching process."""
		return self.cmd.getOutput()
	
	def romRunningState(self):
		"""Telling if Gngeo is either currently running a Rom, or not. :p"""
		if self.cmd: return self.cmd.isAlive()
		else: return False
