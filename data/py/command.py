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
from threading import Thread
from re import match
import os, gtk

class Command(Thread):
	def __init__(self,cmd):
		Thread.__init__(self)

		self.command = cmd
		self.output = "RAS"

	def run(self):
		gtk.threads_enter()
		pipe = os.popen(self.command)
		gtk.threads_leave()
		self.output = pipe.read()
	
	def getOutput(self): return self.output
