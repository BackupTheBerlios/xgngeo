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
import os.path
from re import match

class History:
	def __init__(self):
		self.path = os.path.expanduser("~/.xgngeo/history")
		self.list = []

	def refreshList(self,size):
		"""Reading content of the ROM History file to build a list 
		containing tuple with full name, path and file system
		presence for each of the recently loaded ROMs."""	

		self.list = [] #(Re)Create ROM History list from scratch.

		if os.path.isfile(self.path):
			file = open(self.path,"r") #Opening.
			content = file.readlines() #Reading.
			file.close() #And closing. :p

			for line in content[:size]:
				plop = match('"(.*)" (.*)',line)
				if plop: 
					path = plop.group(2)
					self.list.append((plop.group(1),path,os.path.exists(path)))

	def getList(self):
		"""Returning current, up-to-date ROM History list."""
		return self.list

	def updateFile(self):
		"""Updating ROM History file."""
		content = ""
		for line in self.list:
			content += '"%s" %s\n' % (line[0],line[1])

		file = open(self.path,"w") #Opening (creating if doesn't exist)
		file.write(content) #Writing.
		file.close() #And closing. :p

	def addRom(self,name,path,size):
		"""Adding a new Rom to the list, with duplicate entries prevention."""

		#Popping the ROM out of the list if already mentioned (similar path).
		i=0
		for x in self.list[:size]:
			if x[1]==path: self.list.pop(i)
			i+=1

		self.list.insert(0,(name,path,True)) #Prepending it to the recent Rom list (indicating the file exists).
		self.list = self.list[:size] #Removing any extra item.
		self.updateFile() #Writing changes.

	def removeRom(self,position):
		"""Popping the ROM out of the list."""
		self.list.pop(position)
		self.updateFile() #Writing changes.

