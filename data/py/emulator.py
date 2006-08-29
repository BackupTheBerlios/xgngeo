""" XGngeo: a frontend for Gngeo in GTK ^^.

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

__author__ = "Choplair-network"
__copyright__ = "Copyleft 2003, 2004, 2005, 2006 Choplair-network"
__license__ = "GPL"
__revision__ = "$Revision $"
# $Source  $
__date__ = "$Date $"

import command
import os
from re import match

class Emulator:
	def __init__(self, *paths):
		self.paths = {"gngeo" : paths[0].replace("'","\'")}
		self.cmd = None
		self.romFullToMame = {}
		self.romMameToFull = {}
		self.romMameNames = []
		self.romFullNames = []

	def set_path(self, param, value):
		"""Changing important path values."""
		self.paths[param] = value

	def get_gngeo_version(self, path=None):
		"""Returning Gngeo version number as tuple and string (or None)."""
		pipe = os.popen("'%s' --version" % (path or self.paths['gngeo']),"r")
		version = match("Gngeo (\S*)", pipe.readline())
		pipe.close()

		if version:
			version_list = []
			for num in version.group(1).split("."):
				try:
					version_list.append(int(num))
				except:
					version_list.append(num)
				#Returning value as a tuple and a string.
			return tuple(version_list), version.group(1) 

		return None #Returning nothing.

	def get_all_supported_roms(self):
		"""Returning list of all the Rom supported by the driver file, according
		to Gngeo output (launched with the `--listgame' argument).
		
		"""
		self.romMameNames = []
		self.romFullNames = []
		self.romFullToMame = {}
		self.romMameToFull = {}

		pipe = os.popen("'%s' --listgame" % self.paths['gngeo'])
		for line in pipe.readlines():
			plop = match("(\S*)\s*:\s*(.*)", line)
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

	def get_rom_mame_to_full(self):
		return self.romMameToFull

	def get_rom_full_to_mame(self):
		return self.romFullToMame

	def get_rom_mame_names(self):
		return self.romMameNames

	def get_rom_full_names(self):
		return self.romFullNames

	def archive_recognition(self, archive_path):
		"""Using Gngeo directory scanning to check whether a mentioned archive
		is a supported ROM, and returning some infos (its MAME and full names)
		if it's the case.
		
		"""
		directory = os.path.dirname(archive_path)
		filename = os.path.basename(archive_path)

		#Getting Gngeo directory scan results.
		pipe = os.popen("'%s' --scandir='%s'" %
			(self.paths['gngeo'], directory.replace("'","\'")),
			"r")
		results = pipe.readlines()[1:]
		pipe.close()

		#Looking for potential details regarding the archive to
		#check in the scan results...
		for line in results:
			plop = match("\s*(\S*):(.*):(\S*)", line)
			if plop:
				#Archive was effectively recognized as a ROM!
				if plop.group(3)==filename:
					#Returning the infos. :-)
					return plop.group(1), plop.group(2) 

		return None #Arhive wasn't detected as a ROM, returning nothing... :-(

	def scan_rom_in_directory(self, directory, filesel_dialog=False):
		"""Generating and returning a dictionary containing the MAME name.
		
		Then the actual file name (and optionaly full name) of all the ROMs
		available in a mentioned directory, according to the scan results
		given by Gngeo (launched with the `--scandir=[dir]' argument).
		
		"""
		dictionary = {}
		pipe = os.popen("'%s' --scandir='%s'" % (self.paths['gngeo'],
			directory.replace("'","\'")),
			"r")

		if not filesel_dialog:
			#Normal dict formating: MAME name => file name.
			for line in pipe.readlines()[1:]:
				plop = match("\s*(\S*):.*:(\S*)", line)
				if plop: 
					#Appending ROM information to the dict.
					dictionary[plop.group(1)] = plop.group(2) 
		else:
			#Including ROM full names in the returned dict, whom keys will
			#be file names (to use for the file selection dialog preview).
			for line in pipe.readlines()[1:]:
				plop = match("\s*(\S*):(.*):(\S*)", line)
				if plop:
					#Appending ROM information to the dict.
					dictionary[plop.group(3)] = (plop.group(1), plop.group(2)) 

		pipe.close()
		return dictionary

	def rom_launching(self, rom_path):
		"""Starting the Gngeo (failsafe :p) thread."""
		self.cmd = command.ThreadedCmd("'%s' '%s'" % (self.paths['gngeo'],
			rom_path))
		self.cmd.start()

	def rom_waiting_for_hanging_up(self):
		"""Waiting for Gngeo to hang up..."""
		return self.cmd.join()

	def rom_get_process_output(self):
		"""Returning the raw Gngeo output of its ROM lauching process."""
		return self.cmd.get_output()
	
	def rom_running_state(self):
		"""Telling if Gngeo is either currently running a Rom, or not. :p"""
		if self.cmd:
			return self.cmd.isAlive()
		else: return False

# vim:ai:et:sw=4:ts=4:sts=4:tw=78:fenc=utf-8
