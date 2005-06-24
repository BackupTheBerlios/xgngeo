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
from re import match

class Romrc:
	def parsing(self,path):
		"""Parse the Rom driver file (`romrc') to generate a Rom
		dictionary connecting the Rom MAME name to their full name
		and a second dictionary doing the contrary."""

		self.romFullToMame = {}
		self.romMameToFull = {}

		file = open(path,"r")
		for line in file.readlines():
			plop = match("game (\S*) \S* \"(.*)\"",line)
			if plop:
				#Append Rom information to the dicts.
				self.romMameToFull[plop.group(1)] = plop.group(2)
				self.romFullToMame[plop.group(2)] = plop.group(1)
		file.close()

	def getRomMameToFull(self): return self.romMameToFull

	def getRomFullToMame(self): return self.romFullToMame
	
	def getRomFullNames(self):
		list = self.romFullToMame.keys()
		list.sort()
		return list
