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
	def __init__(self,cmd,*arg):
		Thread.__init__(self)

		self.command = cmd
		self.gngeoStop = arg[0]

		#Widgets.
		self.statusbar = arg[1]
		self.context_id = arg[2]
		self.loadrom_menu_item = arg[3]
		self.history_menu_item = arg[4]
		self.stopMenu_item = arg[5]
		self.execMenu_item = arg[6]

	def run(self):
		"""This function is embeded in a thread and perform
		some Gngeo post-execution instructions after, of
		course, lauching the emulator."""

		#Lauching Gngeo...
		gtk.threads_enter()
		pipe = os.popen(self.command)
		gtk.threads_leave()
		#End.
		
		output = pipe.read()
		#Check if there was a f*ck then display the default message if none.
		if not match(".{12} [[][\-]{62}[]]",output):
			self.statusbar.push(self.context_id,output)
		else: self.statusbar.push(self.context_id,_("Rom stopped."))

		#Do as the `Stop' button has been clicked...
		self.gngeoStop(kill=0)
