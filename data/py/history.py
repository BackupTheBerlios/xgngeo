"""
XGngeo: a frontend for Gngeo in GTK ^^.
Copyleft 2003 Choplair-network

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
import os, re

class History:
	def __init__(self,path):
		self.path = path
		self.list = []

	def getList(self,size):
		if os.path.isfile(self.path):
			file = open(self.path,"r") #Open
			content = file.readlines() #Read
			file.close() #And close

			for line in content[:int(size)]:
				match = re.match('"(.*)" (.*)',line)
				if match: self.list.append((match.group(1),match.group(2)))
		
		return self.list

	def add(self,name,location,size):
		content = ""
		#Prepend to the recents' list
		self.list.insert(0,(name,location))

		for line in self.list[:int(size)]:
			content += '"%s" %s\n' % (line[0],line[1])
		
		file = open(self.path,"w") #Open (create if doesn't exist)
		file.write(content) #Write
		file.close() #And close :p
