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
from threading import Thread
from gtk import threads_enter, threads_leave
from os import popen

class ThreadedCmd(Thread):
	def __init__(self,cmd):
		Thread.__init__(self)

		print cmd
		
		self.command = cmd
		self.output = ""

	def run(self):
		threads_enter()
		pipe = popen(self.command,"r")
		threads_leave()
		self.output = pipe.read()
	
	def getOutput(self): return self.output
