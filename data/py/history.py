"""
XGngeo: a frontend for Gngeo in GTK ^^.
Copyleft 2003, 2004, 2005 Choplair-network

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

			for line in content[:size]:
				match = re.match('"(.*)" (.*)',line)
				if match: self.list.append((match.group(1),match.group(2)))

		return self.list

	def add(self,name,location,size):
		already = False
		i,j = 0,0

		print self.list

		#Check if the game is already on the list.
		for x in self.list[:size]:
			if x[0]==name: already=True; j=i; break
			i+=1

		if already:
			#Pull off the others and move it to the first place.
			da_item = self.list[j]

			i=1
			for val in self.list[:j]:
				self.list[i] = val
				i+=1

			self.list[0] = da_item
		else:	#Prepend to the recent rom list.
			self.list.insert(0,(name,location))

		#Remove any extra item.
		print self.list
		self.list = self.list[:size]

		#Updating file.
		content = ""
		for line in self.list:
			content += '"%s" %s\n' % (line[0],line[1])

		file = open(self.path,"w") #Open (create if doesn't exist)
		file.write(content) #Write
		file.close() #And close.

		return self.list
