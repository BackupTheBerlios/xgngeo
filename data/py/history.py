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

	def getList(self,size):
		"""Getting content of the Rom History file as a list
		(which also indicates whether each Rom currenlty
		exists on the file system)."""
		
		if os.path.isfile(self.path):
			file = open(self.path,"r") #Opening.
			content = file.readlines() #Reading.
			file.close() #And closing. :p

			for line in content[:size]:
				plop = match('"(.*)" (.*)',line)
				location = plop.group(2)
				if plop: self.list.append((plop.group(1),location,os.path.exists(location)))

		return self.list

	def addRom(self,name,location,size):
		"""Adding a new Rom to the list, with duplicate entries prevention."""
		
		#Popping the Rom out of the list if already mentioned (similar path).
		i=0
		for x in self.list[:size]:
			if x[1]==location: self.list.pop(i)
			i+=1

		#Prepending it to the recent Rom list (indicating the file exists).
		self.list.insert(0,(name,location,True))

		#Removing any extra item.
		self.list = self.list[:size]

		#Updating Rom History file.
		content = ""
		for line in self.list:
			content += '"%s" %s\n' % (line[0],line[1])

		file = open(self.path,"w") #Opening (creating if doesn't exist)
		file.write(content) #Writing.
		file.close() #And closing. :p

		return self.list
