#!/usr/bin/env python
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
import gtk, os, string, gettext, gobject
from sys import path as syspath
from re import match
from threading import Timer

#Change working directory to XGngeo's
os.chdir(os.path.abspath(syspath[0]))

#Add `data/py/' to PATH, then import internal modules
syspath.append("data/py/")
import command, configfile, history, rominfos, romrcfile

VERSION = 15
gngeoPath = os.path.expanduser("~/.gngeo")

#Internationalization.
gettext.install("xgngeo","data/lang")

class XGngeo:
	def welcome(self):
		#Check for Gngeo's home directory
		if not os.path.isdir(gngeoPath): os.mkdir(gngeoPath)

		self.introDialog = gtk.Dialog(_("Welcome! ^_^"))
		self.introDialog.connect("delete_event",self.quit)

		label = gtk.Label(_("The configuration file of Gngeo was not found!\nSo, we have to set some required parameters.\nPress OK to continue..."))
		label.set_padding(5,10)
		self.introDialog.vbox.pack_end(label)

		button = gtk.Button(stock=gtk.STOCK_OK)
		button.connect("clicked",self.destroy,[self.introDialog,2])
		self.introDialog.action_area.pack_end(button)

		self.introDialog.show_all()

	def license(self,widget):
		#Checks if something is not already open...
		if self.busyState!=1:
			self.busy(1)

			self.licenseDialog = gtk.Dialog(_("License"),flags=gtk.DIALOG_NO_SEPARATOR)
			self.licenseDialog.connect("destroy",self.destroy,[self.licenseDialog,1])

			label = gtk.Label(_("XGngeo is released under the GNU GPL license:"))
			label.set_padding(10,4)
			self.licenseDialog.vbox.pack_start(label,False)

			#
			# VIEW LICENSE
			#
			licensePath = "LICENSE.txt"
			textbuffer = gtk.TextBuffer()

			if os.path.isfile(licensePath):
				licenseFile = open(licensePath,"r")
				licenseText = licenseFile.read()
				licenseFile.close()
				textbuffer.set_text(licenseText)
				del licenseText
			else:
				textbuffer.set_text(_("Error: Unable to open the file \"%s\"!\nYou can read the GNU CPL license at:\nhttp://www.gnu.org/licenses/gpl.html") % licensePath)
			
			textview = gtk.TextView(textbuffer)
			textview.set_editable(False)
	
			scrolled_window = gtk.ScrolledWindow()
			scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
			scrolled_window.add(textview)
			scrolled_window.set_size_request(330,220)
			self.licenseDialog.vbox.pack_end(scrolled_window)

			#Button at bottom..
			button = gtk.Button(stock=gtk.STOCK_CLOSE)
			button.connect("clicked",self.destroy,[self.licenseDialog,1])
			self.licenseDialog.action_area.pack_end(button)

			self.licenseDialog.show_all()

	def gngeoGetOutput(self):
		"""This function is embeded in a thread and perform
		some Gngeo post-execution instructions after it
		terminates."""
		print "debug 5"
		#Waiting for Gngeo to hang up...
		self.cmd.join()
		print "debug 6"
		output = self.cmd.getOutput()
		#~ if output!="":
			#~ #Check if there was a f*ck then display the default message if none.
			#~ if not match(".{12} [[][\-]{62}[]]",output):
				#~ self.statusbar.push(self.context_id,string.replace(output,"\n"," "))
			#~ else:
				#~ #The Rom was successfully exectuted, so we can append it to the ``History" menu.
				#~ self.historyAdd(self.romFullName,self.romPath)
				#~ self.statusbar.push(self.context_id,_("Rom stopped."))
		print "debug 7"
		#Perform some modifications on the menu.
		self.loadrom_menu_item.set_sensitive(True)
		self.history_menu_item.set_sensitive(True)
		self.stopMenu_item.set_sensitive(False)
		self.execMenu_item.set_sensitive(True)
		print "debug 8\n"

	def gngeoExec(self,widget=None):
		print "debut 1"
		self.statusbar.push(self.context_id,_("Starting Rom..."))
		self.loadrom_menu_item.set_sensitive(False)
		self.history_menu_item.set_sensitive(False)
		self.stopMenu_item.set_sensitive(True)
		self.execMenu_item.set_sensitive(False)
		print "debug 2"
		#Starting the thread.
		self.cmd = command.Command("%s '%s'" % (self.paramXGngeo['gngeopath'],self.romPath))
		self.cmd.start()
		print "debug 3"
		#Starting another thread which watch out the last one!
		Timer(0,self.gngeoGetOutput).start()
		print "debug 4"

	def gngeoStop(self,widget=None):
		#Kill Gngeo if it is still running.
		if self.cmd.isAlive():
			Timer(0,os.system,("killall -9 '%s'" % self.paramXGngeo['gngeopath'],)).start()

	def romList(self,widget):
		if self.busyState!=1:
			def setRomTemp(widget,data):
				#If the selected rom is available
				if data[0]==1:
					if self.romFromList and self.romFromList!=data[1]:
						self.listButton[self.romFromList].set_active(False) #Desactivate last selected Rom button.
					if widget.get_active():	self.romFromList,self.romFromListName = data[1],data[2]
					else: self.romFromList,self.romFromListName = None,None

				#Update preview image
				if os.path.isfile(os.path.join(self.paramXGngeo["previewimagedir"],data[1]+".png")): self.previewImage.set_from_file(os.path.join(self.paramXGngeo["previewimagedir"],data[1]+".png"))
				elif os.path.isfile(os.path.join(self.paramXGngeo["previewimagedir"],"unavailable.png")): self.previewImage.set_from_file(os.path.join(self.paramXGngeo["previewimagedir"],"unavailable.png"))

				#Update rom infos
				if os.path.isfile(self.paramXGngeo["rominfoxml"]):
					#Check for game informations
					if self.romInfos.has_key(data[1]):
						for x in ("desc","manufacturer","year","genre","players","rating","size"):
							if self.romInfos[data[1]].has_key(x): self.romInfosWidget[x].set_text(self.romInfos[data[1]][x])
							else: self.romInfosWidget[x].set_text("--")
					else:
						for x in ("desc","manufacturer","year","genre","players","rating","size"):
							self.romInfosWidget[x].set_text("--")

			def setRomFromList(widget):
				#Something selected?
				if self.romFromList:
					#Setting important variables.
					self.romPath = os.path.join(self.param['rompath'],"%s.zip" % self.romFromList) #Note that, because of a Gngeo disfuntionment, we indicate the full rom path rather than simply its Mame name. 
					self.romFullName = self.romFromListName

					#Doing post-selection actions.
					self.historyAdd(self.romFullName,self.romPath) #Append it to the list.
					self.statusbar.push(self.context_id,_("Rom: \"%s\" (%s)") % (self.romFromListName,self.romFromList)) #Update Status message
					if self.paramXGngeo["autoexecrom"]=="true": self.gngeoExec() #Auto execute the Rom...
					else: self.execMenu_item.set_sensitive(True) #Activate the "Execute" button

				self.listDialog.destroy()
				self.busyStatus = "off"

			def showAvailable(widget):
				if widget.get_active():
					for x in self.listButtonOther.values(): x.hide()
					self.paramXGngeo["showavailableromsonly"] = "true"
				else: #Show other Roms
					for x in self.listButtonOther.values(): x.show()
					self.paramXGngeo["showavailableromsonly"] = "false"

			self.busy(1)
			self.romFromList = None #Selected Rom

			self.listDialog = gtk.Dialog(_("List of Roms from your \"romrc\" file"))
			self.listDialog.connect("destroy",self.destroy,[self.listDialog,1])

			label = gtk.Label(_("Please select the Rom you want to load from this list ^^\nAvailable Roms are displayed in blue..."))
			label.set_justify(gtk.JUSTIFY_CENTER)
			self.listDialog.vbox.pack_start(label,False,False,2)

			table = gtk.Table(2,2)

			buttonShowAvailable = gtk.CheckButton(_("Show available Roms only."))
			buttonShowAvailable.connect("toggled",showAvailable)
			table.attach(buttonShowAvailable,0,1,0,1,yoptions=gtk.SHRINK)

			scrolled_window = gtk.ScrolledWindow()
			scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
			table.attach(scrolled_window,0,1,1,2)

			#Graphical rom list generation.
			romrc = romrcfile.Romrc()
			romrc.parsing(self.param['romrc'])
			gamelist = romrc.getRomFullToMame()
			gamelistNames = romrc.getRomFullNames()

			self.listButton, self.listButtonOther = {}, {}
			box = gtk.VBox()
			for name in gamelistNames:
				if os.path.isfile(os.path.join(self.param["rompath"],"%s.zip" % gamelist[name])):
					self.listButton[gamelist[name]] = gtk.ToggleButton(name)
					self.listButton[gamelist[name]].modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#69F"))
					self.listButton[gamelist[name]].connect("clicked",setRomTemp,[1,gamelist[name],name])
					box.pack_start(self.listButton[gamelist[name]])
				else:
					self.listButtonOther[gamelist[name]] = gtk.ToggleButton(name)
					self.listButtonOther[gamelist[name]].set_inconsistent(True)
					self.listButtonOther[gamelist[name]].connect("clicked",setRomTemp,[0,gamelist[name]])
					box.pack_start(self.listButtonOther[gamelist[name]])
			del gamelist, gamelistNames

			scrolled_window.set_size_request(-1,180) #Set scrolled window's height.
			scrolled_window.add_with_viewport(box)

			#
			# Preview image/info's
			#
			notebook = gtk.Notebook()
			
			#Preview images
			if(os.path.isdir(self.paramXGngeo["previewimagedir"])):
				self.previewImage = gtk.Image()
				path = os.path.join(self.paramXGngeo["previewimagedir"],"unavailable.png")
				if os.path.isfile(path): self.previewImage.set_from_file(path) #Display the ``unavailable" image by default.
				notebook.append_page(self.previewImage,gtk.Label(_("Preview image")))

			#Rom infos
			if(os.path.isfile(self.paramXGngeo["rominfoxml"])):
				self.romInfos = rominfos.Rominfos(path=self.paramXGngeo["rominfoxml"]).getDict()
				self.romInfosWidget = {}

				box = gtk.VBox()

				#Description
				self.romInfosWidget["desc"] = gtk.TextBuffer()
				self.romInfosWidget["desc"].set_text("--")
				textview = gtk.TextView(self.romInfosWidget["desc"])
				textview.set_editable(0)
				textview.set_wrap_mode(gtk.WRAP_WORD)
				scrolled_window = gtk.ScrolledWindow()
				scrolled_window.set_policy(gtk.POLICY_NEVER,gtk.POLICY_ALWAYS)
				box.set_size_request(220,-1) #Set width
				scrolled_window.add(textview)
				frame = gtk.Frame(_("Description:"))
				frame.add(scrolled_window)
				box.pack_start(frame)

				#Other infos
				table2 = gtk.Table(3,2,True)

				frame = gtk.Frame(_("Manufacturer:"))
				self.romInfosWidget["manufacturer"] = gtk.Entry()
				self.romInfosWidget["manufacturer"].set_text("--")
				self.romInfosWidget["manufacturer"].set_editable(0)
				frame.add(self.romInfosWidget["manufacturer"])
				table2.attach(frame,0,1,0,1)

				frame = gtk.Frame(_("Year:"))
				self.romInfosWidget["year"] = gtk.Entry()
				self.romInfosWidget["year"].set_text("--")
				self.romInfosWidget["year"].set_editable(0)
				frame.add(self.romInfosWidget["year"])
				table2.attach(frame,0,1,1,2)

				frame = gtk.Frame(_("Genre:"))
				self.romInfosWidget["genre"] = gtk.Entry()
				self.romInfosWidget["genre"].set_text("--")
				self.romInfosWidget["genre"].set_editable(0)
				frame.add(self.romInfosWidget["genre"])
				table2.attach(frame,0,1,2,3)

				frame = gtk.Frame(_("Players:"))
				self.romInfosWidget["players"] = gtk.Entry()
				self.romInfosWidget["players"].set_text("--")
				self.romInfosWidget["players"].set_editable(0)
				frame.add(self.romInfosWidget["players"])
				table2.attach(frame,1,2,0,1)

				frame = gtk.Frame(_("Rating:"))
				self.romInfosWidget["rating"] = gtk.Entry()
				self.romInfosWidget["rating"].set_text("--")
				self.romInfosWidget["rating"].set_editable(0)
				frame.add(self.romInfosWidget["rating"])
				table2.attach(frame,1,2,1,2)

				frame = gtk.Frame(_("Size:"))
				self.romInfosWidget["size"] = gtk.Entry()
				self.romInfosWidget["size"].set_text("--")
				self.romInfosWidget["size"].set_editable(0)
				frame.add(self.romInfosWidget["size"])
				table2.attach(frame,1,2,2,3)

				box.pack_start(table2,False)

				notebook.append_page(box,gtk.Label(_("Rom infos")))

			table.attach(notebook,1,2,0,2,gtk.SHRINK)
			self.listDialog.vbox.pack_start(table)

			#Buttons at bottom
			button = gtk.Button(stock=gtk.STOCK_OK)
			button.connect("clicked",setRomFromList)
			self.listDialog.action_area.pack_start(button)

			button = gtk.Button(stock=gtk.STOCK_CANCEL)
			button.connect("clicked",self.destroy,[self.listDialog,1])
			self.listDialog.action_area.pack_start(button)

			self.listDialog.show_all()
			if self.paramXGngeo["showavailableromsonly"]=="true": buttonShowAvailable.set_active(True) #Activate button.

	def optParam(self,widget,data):
		if data[0]=="blitter":
			self.tempparam['blitter'] = data[1] #Updating param
		elif data[0]=="effect":
			self.tempparam['effect'] = data[1]
		elif data[0]=="samplerate":
			self.tempparam['samplerate'] = data[1]

	def fileSelect(self,widget,title,folder,arg,dirselect=0):
		dialog = gtk.FileChooserDialog(title,action=(gtk.FILE_CHOOSER_ACTION_OPEN,gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)[dirselect],buttons=(gtk.STOCK_OPEN, gtk.RESPONSE_OK,gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL))
		dialog.set_current_folder((os.path.dirname(folder),folder)[os.path.isdir(folder)])
		dialog.connect("response",self.setPath,arg)

		if arg=="rom":
			filter = gtk.FileFilter()
			filter.set_name(_("Rom archive"))
			filter.add_pattern("*.zip")
			dialog.add_filter(filter)

		dialog.run()

	def setPathFromRecent(self,widget,fullname,path):
		#Getting a hypothetic Mame name.
		if path[-4:]==".zip": mamename = os.path.basename(path)[:-4]
		else: mamename = os.path.basename(path)
	
		#Setting important variables.
		self.romPath = path
		self.romFullName = fullname
		
		#Doing post-selection actions.
		self.historyAdd(self.romFullName,self.romPath) #Append it to the list.
		self.statusbar.push(self.context_id,(_("Rom: \"%s\" (%s)") % (fullname,mamename))) #Update Status message
		if self.paramXGngeo["autoexecrom"]=="true": self.gngeoExec() #Auto execute the Rom...
		else: self.execMenu_item.set_sensitive(True) #Activate the "Execute" button

	def setPath(self,dialog,response,data):
		"""Get and set path of various things from
		the path of the file chooser."""
		if response==gtk.RESPONSE_OK:
			if data=="rom":
				path = dialog.get_filename()
				#Does it exist?
				if os.path.isfile(path):
					#Getting a hypothetic Mame name.
					if path[-4:]==".zip": mamename = os.path.basename(path)[:-4]
					else: mamename = os.path.basename(path)

					#Tring to resolve Rom full name.
					romrc = romrcfile.Romrc()
					romrc.parsing(self.param['romrc'])
					dict = romrc.getRomMameToFull()
					if mamename in dict.keys(): fullname = dict[mamename]
					else: fullname = "Unknow \"%s\" Rom" % mamename

					#Setting important variables.
					self.romPath = path
					self.romFullName = fullname

					#Doing post-selection actions.
					self.historyAdd(self.romFullName,self.romPath) #Append it to the list.
					self.statusbar.push(self.context_id,_("Rom: \"%s\" (%s)" % (fullname,mamename))) #Update Status message
					if self.paramXGngeo["autoexecrom"]=="true": self.gngeoExec() #Auto execute the Rom...
					else: self.execMenu_item.set_sensitive(True) #Activate the "Execute" button

				else: self.statusbar.push(self.context_id,"Error: file doesn't exist!")
			else:
				path = dialog.get_filename() #Get the path
				self.configwidgets[data].set_text(path)

		dialog.destroy()

	def historyAdd(self,fullname,path):
		#Update history file and get new list...
		list = self.history.add(fullname,path,size=int(self.paramXGngeo["historysize"]))

		#Recreate the history menu.
		for x in self.historyMenu.get_children(): self.historyMenu.remove(x) #Remove old entries.
		for x in list: #Put the new ones.
			menu_item = gtk.MenuItem(x[0])
			menu_item.connect("activate",self.setPathFromRecent,x[0],x[1])
			self.historyMenu.append(menu_item)

		self.historyMenu.show_all()

	def about(self,widget):
		#Checks if something is not already open...
		if self.busyState!=1:
			self.busy(1)

			self.aboutDialog = gtk.Dialog(_("About XGngeo"),flags=gtk.DIALOG_NO_SEPARATOR)
			self.aboutDialog.connect("destroy",self.destroy,[self.aboutDialog,1])

			pipe = os.popen("%s --version" % self.paramXGngeo['gngeopath'])
			line = match("Gngeo (\S*)",pipe.readline())
			pipe.close()
			if line:	gngeoversion = line.group(1)
			else:	gngeoversion = "&lt;=0.5.9a"

			label = gtk.Label("<span color='#008'><b>%s</b>\n%s\n%s\n</span>%s\nCopyleft 2003, 2004, 2005 Choplair-network." % (_("XGngeo: a frontend for Gngeo :p"),_("Version %i.") % VERSION,_("Running Gngeo version %s.") % gngeoversion, _("This program is released under the GNU GPL license.")))
			label.set_justify(gtk.JUSTIFY_CENTER)
			label.set_use_markup(True)
			self.aboutDialog.vbox.pack_start(label)

			frame = gtk.Frame(_("Credits"))
			box = gtk.HBox(spacing=3)
			frame.add(box)

			logo = gtk.Image()
			logo.set_from_file("data/img/chprod.png")
			box.pack_start(logo,False)

			label = gtk.Label(_("Main coder: Choplair.\nAssisted by: Pachilor.")+"\n\nhttp://www.choplair.org/")
			label.set_justify(gtk.JUSTIFY_CENTER)
			box.pack_start(label)

			self.aboutDialog.vbox.pack_start(frame)

			#Button at bottom..
			button = gtk.Button(stock=gtk.STOCK_CLOSE)
			button.connect("clicked",self.destroy,[self.aboutDialog,1])
			self.aboutDialog.action_area.pack_end(button)

			self.aboutDialog.show_all()
	
	def config(self,widget=None,type=0,firstrun=0):
		if self.busyState!=1:
			def setPathIcon(widget,image,dir=0):
				"""We check whether the path written in the text entry
				is an existing file or directory and change the icon
				in consequence."""

				path = widget.get_text()
				if (dir and os.path.isdir(path)) or os.path.isfile(path): 
					stock = gtk.STOCK_YES
				else: stock = gtk.STOCK_NO

				image.set_from_stock(stock,gtk.ICON_SIZE_MENU)

			self.busy(1)
			self.configDialog = gtk.Dialog()
			if type in (0,5): self.configDialog.set_geometry_hints(min_width=350)

			if firstrun==1: self.configDialog.connect("delete_event",self.quit)
			else: self.configDialog.connect("destroy",self.destroy,[self.configDialog,1])

			if type==0:
				#
				# Important path configuration.
				#
				self.configDialog.set_title(_("Important path configuration"))
				box = gtk.VBox(spacing=5) #The box :p
	
				frame = gtk.Frame(_("Roms & Bios directory:"))
				box2 = gtk.HBox()
	
				image = gtk.Image()
				box2.pack_start(image,False,padding=3)
				self.configwidgets['rompath'] = gtk.Entry()
				self.configwidgets['rompath'].connect("changed",setPathIcon,image,1)
				self.configwidgets['rompath'].set_text(self.param["rompath"])
				box2.pack_start(self.configwidgets['rompath'])
				button = gtk.Button()
				image = gtk.Image()
				image.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_MENU)
				button.add(image)
				button.connect("clicked",self.fileSelect,_('Select the Roms & Bios directory.'),self.configwidgets['rompath'].get_text(),"rompath",1)
				box2.pack_end(button,False)
				frame.add(box2)
				box.pack_start(frame)
	
				frame = gtk.Frame(_("Path to romrc:"))
				box2 = gtk.HBox()
	
				image = gtk.Image()
				box2.pack_start(image,False,padding=3)
				self.configwidgets['romrc'] = gtk.Entry()
				self.configwidgets['romrc'].connect("changed",setPathIcon,image)
				self.configwidgets['romrc'].set_text(self.param["romrc"])
				box2.pack_start(self.configwidgets['romrc'])
				button = gtk.Button()
				image = gtk.Image()
				image.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_MENU)
				button.add(image)
				button.connect("clicked",self.fileSelect,_('Select the "%s" file.') % "romrc",self.configwidgets['romrc'].get_text(),"romrc")
				box2.pack_end(button,False)
				frame.add(box2)
				box.pack_start(frame)

				frame = gtk.Frame(_("Path to gngeo executable:"))
				box2 = gtk.HBox()
	
				image = gtk.Image()
				box2.pack_start(image,False,padding=3)
				self.configwidgets['gngeopath'] = gtk.Entry()
				self.configwidgets['gngeopath'].connect("changed",setPathIcon,image)
				self.configwidgets['gngeopath'].set_text(self.paramXGngeo["gngeopath"])
				box2.pack_start(self.configwidgets['gngeopath'])
				button = gtk.Button()
				image = gtk.Image()
				image.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_MENU)
				button.add(image)
				button.connect("clicked",self.fileSelect,_('Select the "%s" file.') % "gngeo",self.configwidgets['gngeopath'].get_text(),"gngeopath")
				box2.pack_end(button,False)
				frame.add(box2)
				box.pack_start(frame)

				self.configDialog.vbox.pack_start(box)

			elif type in (1,2,3,4):
				#
				# Global emulation configuration.
				#
				self.configDialog.set_title(_("Global emulation configuration"))
				notebook = gtk.Notebook()

				#
				# GRAPHIC section
				#
				box = gtk.VBox(spacing=4) #The box :p
				notebook.append_page(box,gtk.Label(_("Graphic")))

				table = gtk.Table(2,3)

				#Fullscreen
				self.configwidgets['fullscreen'] = gtk.CheckButton(_("Fullscreen"))
				if self.param["fullscreen"]=="true": self.configwidgets['fullscreen'].set_active(1)
				table.attach(self.configwidgets['fullscreen'],0,1,0,1)
				#Interpolation
				self.configwidgets['interpolation'] = gtk.CheckButton(_("Interpolation"))
				if self.param["interpolation"]=="true": self.configwidgets['interpolation'].set_active(1)
				table.attach(self.configwidgets['interpolation'],0,1,1,2)
				#Show FPS
				self.configwidgets['showfps'] = gtk.CheckButton(_("Show FPS"))
				if self.param["showfps"]=="true": self.configwidgets['showfps'].set_active(1)
				table.attach(self.configwidgets['showfps'],1,2,0,1)
				#Auto Frameskip
				self.configwidgets['autoframeskip'] = gtk.CheckButton(_("Auto Frameskip"))
				if self.param["autoframeskip"]=="true": self.configwidgets['autoframeskip'].set_active(1)
				table.attach(self.configwidgets['autoframeskip'],1,2,1,2)

				#Scale
				adjustment = gtk.Adjustment(float(self.param["scale"]),1,5,1)

				frame = gtk.Frame(_("Scale:"))
				self.configwidgets['scale'] = gtk.HScale(adjustment)
				self.configwidgets['scale'].set_size_request(60,-1)
				self.configwidgets['scale'].set_digits(0)
				frame.add(self.configwidgets['scale'])
				table.attach(frame,2,3,0,2)
	
				box.pack_start(table)

				#320x224 screen output.
				self.configwidgets['screen320'] = gtk.CheckButton(_("Use a 320x224 screen (instead of 304x224)"))
				if self.param["screen320"]=="true": self.configwidgets['screen320'].set_active(True)
				box.pack_start(self.configwidgets['screen320'])

				# BLITTER
				self.tempparam['blitter'] = self.param["blitter"]
				frame = gtk.Frame(_("Blitter:"))

				#Translation of know blitter fullname.
				i18n_dict = {
					"soft":_("Software blitter"),
					"opengl":_("Opengl blitter"),
					"yuv":_("YUV blitter (YV12)")}

				blitter = os.popen("%s --blitter help" % self.paramXGngeo['gngeopath'])
				lines = blitter.readlines() #Get Gngeo's available blitter
				blitter.close()

				opt = gtk.OptionMenu()
				menu = gtk.Menu()
				i=0
				for line in lines:
					if string.find(line,":")>0:
						splited = string.split(line,":") #Syntax is "REF : FULLNAME"
						ref,fullname = splited[0].strip(),splited[1].strip()

						menu_item = gtk.MenuItem((fullname,i18n_dict[ref])[i18n_dict.has_key(ref)])
						menu_item.connect("activate",self.optParam,["blitter",ref])
						menu.append(menu_item)
						#Set active the last selection
						if ref==self.param["blitter"]: menu.set_active(i)
						i+=1
				opt.set_menu(menu)
				frame.add(opt)
				box.pack_start(frame)

				# EFFECT
				self.tempparam['effect'] = self.param["effect"]
				frame = gtk.Frame(_("Effect:"))

				#Translation of know effect fullname.
				i18n_dict = {
					"none":_("No effect"),
					"scanline":_("Scanline effect"),
					"scanline50":_("Scanline 50% effect"),
					"scale2x":_("Scale2x effect"),
					"scale3x":_("Scale3x effect"),
					"scale4x":_("Scale4x effect"),
					"scale2x50":_("Scale2x effect with 50% scanline"),
					"scale2x75":_("Scale2x effect with 75% scanline"),
					"hq2x":_("HQ2X effect. High quality"),
					"hq3x":_("HQ3X effect. High quality"),
					"lq2x":_("LQ2X effect. Low quality"),
					"lq3x":_("LQ3X effect. Low quality"),
					"doublex":_("Double the x resolution (soft blitter only)"),
					"sai":_("SAI effect"),
					"supersai": _("SuperSAI effect"),
					"eagle":_("Eagle effect")}

				effect = os.popen("%s --effect help" % self.paramXGngeo['gngeopath'])
				lines = effect.readlines() #Get Gngeo's available blitter
				effect.close()

				opt = gtk.OptionMenu()
				menu = gtk.Menu()
				i=0
				for line in lines:
					if string.find(line,":")>0:
						splited = string.split(line,":") #Syntax is "REF : FULLNAME"
						ref,fullname = splited[0].strip(),splited[1].strip()

						menu_item = gtk.MenuItem((fullname,i18n_dict[ref])[i18n_dict.has_key(ref)])
						menu_item.connect("activate",self.optParam,["effect",ref])
						menu.append(menu_item)
						#Set active the last selection
						if ref==self.param["effect"]: menu.set_active(i)
						i+=1
				opt.set_menu(menu)
				frame.add(opt)
				box.pack_start(frame)

				#
				# AUDIO / JOYSTICK section
				#
				box = gtk.VBox(spacing=4) #The Box
				notebook.append_page(box,gtk.Label(_("Audio / Joystick")))

				frame = gtk.Frame(_("Audio"))
				table = gtk.Table(2,2)
		
				self.configwidgets['sound'] = gtk.CheckButton(_("Enable sound"))
				if self.param["sound"]=="true": self.configwidgets['sound'].set_active(1)
				table.attach(self.configwidgets['sound'],0,2,0,1)

				#Sample rate
				self.tempparam['samplerate'] = self.param["samplerate"]
				
				label = gtk.Label(_("Sample rate:"))
				table.attach(label,0,1,1,2)

				opt = gtk.OptionMenu()
				menu = gtk.Menu() 
				i=0
				for val in ["8192","11025","22050","32000","44100","48000"]:
					menu_item = gtk.MenuItem(val)
					menu_item.connect("activate",self.optParam,["samplerate",val])
					menu.append(menu_item)
					#Set active the last selection
					if val==self.param["samplerate"]: menu.set_active(i)
					i+=1
				opt.set_menu(menu)
				table.attach(opt,1,2,1,2)

				frame.add(table)
				box.pack_start(frame)
		
				frame = gtk.Frame(_("Joystick"))
				table = gtk.Table(2,3)
				
				self.configwidgets['joystick'] = gtk.CheckButton("Enable joystick support")
				if self.param['joystick']=="true": self.configwidgets['joystick'].set_active(True)
				table.attach(self.configwidgets['joystick'],0,2,0,1)

				label = gtk.Label(_("Player 1 device:"))
				table.attach(label,0,1,1,2)
				self.configwidgets['p1joydev'] = gtk.OptionMenu()
				menu = gtk.Menu()
				for x in range(4): menu.append(gtk.MenuItem("/dev/js%s" % x))
				self.configwidgets['p1joydev'].set_menu(menu)
				self.configwidgets['p1joydev'].set_history(int(self.param["p1joydev"]))
				table.attach(self.configwidgets['p1joydev'],1,2,1,2)

				label = gtk.Label(_("Player 2 device:"))
				table.attach(label,0,1,2,3)
				self.configwidgets['p2joydev'] = gtk.OptionMenu()
				menu = gtk.Menu()
				for x in range(4): menu.append(gtk.MenuItem("/dev/js%s" % x))
				self.configwidgets['p2joydev'].set_menu(menu)
				self.configwidgets['p2joydev'].set_history(int(self.param["p2joydev"]))
				table.attach(self.configwidgets['p2joydev'],1,2,2,3)

				frame.add(table)
				box.pack_start(frame)

				#
				# KEYBOARD section.
				#
				self.toggled = None

				# Key order : A,B,C,D,START,COIN,UP,DOWN,LEFT,RIGHT
				keys_list = ["A","B","C","D","START","COIN","UP","DOWN","LEFT","RIGHT"]

				# The Gngeo compliant keymap!
				conpliant_KeyMap = {
				"backspace":8, "tab":9, "return":13, "pause":19, "space":32, "exclam":33, "quotedbl":34, "dollar":36, "ampersand":38, "apostrophe":39, "parenleft":40, "parenright":41, "comma":44, "minus":45,
				"colon":58, "semicolon":59,"less":60, "equal":61, "asciicircum":94, "underscore":95, "a":97, "b":98, "c":99, "d":100, "e":101, "f":102, "g":103, "h":104, "i":105, "j":106, "k":107, "l":108,
				"m":109, "n":110, "o":111, "p":112, "q":113, "r":114, "s":115, "t":116, "u":117, "v":118, "w":119, "x":120, "y":121, "z":122, "delete":127, "twosuperio":178, "agrave":224, "ccedilla":231,
				"egrave":232, "eacute":233, "ugrave":249, "kp_0":256, "kp_1":257, "kp_2":258, "kp_3":259, "kp_4":260, "kp_5":261, "kp_6":262, "kp_home":263, "kp_7":263, "kp_up":264, "kp_8":264, "kp_9":265,
				"kp_decimal":266, "kp_divide":267, "kp_multiply":268, "kp_subtract":269, "kp_add":270, "kp_enter":271, "up":273, "down":274, "right":275, "left":276, "insert":277, "home":278, "end":279,
				"page_up":280, "page_down":281, "num_lock":300, "caps_lock":301, "scroll_lock":302, "shift_r":303, "shift_l":304, "control_r":305, "control_l":306, "super_l":311, "super_r":312, "print":316
				}

				def getPressed(widget,event):
					if widget.get_active() and event.keyval: #Only when widget is active
						value = gtk.gdk.keyval_to_lower(event.keyval) #Get the get (lower only)

						# GTK's keys are not same as SDL's used by Gngeo. T_T
						# So, a Gngeo compatible key-value is given according to its GTK's name.
						key_name = gtk.gdk.keyval_name(value).lower()
						key = None

						if key_name in conpliant_KeyMap.keys():
							key = conpliant_KeyMap[key_name]
							widget.set_label("%s" % (key))
							widget.clicked()

				def toggled(widget):
					if self.toggled and self.toggled!=widget:
						if self.toggled.get_active(): self.toggled.set_active(False)
					self.toggled = widget

				def radioToggled(widget,data):
					if data: #Show P2 key and hide P1's
						for x in self.configwidgets['p2key'].values():
							x.show()
						for x in self.configwidgets['p1key'].values():
							x.hide()
					else: #Show P1 key and hide P2's
						for x in self.configwidgets['p1key'].values():
							x.show()
						for x in self.configwidgets['p2key'].values():
							x.hide()

				box = gtk.VBox()
				notebook.append_page(box,gtk.Label(_("Keyboard")))

				label = gtk.Label(_("To modify a key, click the button then push your new key.\nThis configuration is only for keyboard."))
				label.set_justify(gtk.JUSTIFY_CENTER)
				box.pack_start(label)

				table = gtk.Table(4,6,True) #The sweet table O_o;;

				#Player's keyboard selection
				frame = gtk.Frame("Controller:")
				frame.set_border_width(5)
				box2 = gtk.VBox()
				frame.add(box2)
				radio = gtk.RadioButton(None,_("Player 1"))
				radio.connect("toggled",radioToggled,0)
				box2.pack_start(radio)
				radio = gtk.RadioButton(radio,_("Player 2"))
				radio.connect("toggled",radioToggled,1)
				box2.pack_start(radio)
				table.attach(frame,0,2,2,4)

				self.configwidgets['p1key'] = {}; image = {}; i=0
				split = string.split(self.param["p1key"],",")
				for x in keys_list:
					#Generate key's image
					image[x] = gtk.Image()
					image[x].set_from_file("data/img/key_%s.png" % x)

					#Generate P1key's button
					self.configwidgets['p1key'][x] = gtk.ToggleButton(split[i])
					self.configwidgets['p1key'][x].connect("toggled",toggled)
					self.configwidgets['p1key'][x].connect("key_press_event",getPressed)
					self.configwidgets['p1key'][x].set_use_underline(False)

					i+=1 

				self.configwidgets['p2key'] = {}; i=0
				split = string.split(self.param["p2key"],",")
				for x in keys_list:
					#Generate P2key's button
					self.configwidgets['p2key'][x] = gtk.ToggleButton(split[i])
					self.configwidgets['p2key'][x].connect("toggled",toggled)
					self.configwidgets['p2key'][x].connect("key_press_event",getPressed)
					self.configwidgets['p2key'][x].set_use_underline(False)

					box2 = gtk.HBox() #A box...
					box2.pack_start(self.configwidgets['p1key'][x]) #with P1 key...
					box2.pack_start(self.configwidgets['p2key'][x]) #and P2 key :p

					#Put them in table
					if i<6:
						table.attach(image[x],i,i+1,0,1)
						table.attach(box2,i,i+1,1,2)
					else:
						table.attach(image[x],i-4,i-3,2,3)
						table.attach(box2,i-4,i-3,3,4)

					i+=1

				box.pack_start(table)

				#
				# SYSTEM section
				#
				box = gtk.VBox(spacing=4) #The box :p
				notebook.append_page(box,gtk.Label(_("System")))

				#Type
				frame2 = gtk.Frame(_("Neo Geo type:"))
				box2 = gtk.HBox()
				self.configwidgets['type_arcade'] = gtk.RadioButton(None,_("Arcade"))
				if self.param["system"]=="arcade": self.configwidgets['type_arcade'].set_active(1)
				box2.pack_start(self.configwidgets['type_arcade'])
				radio = gtk.RadioButton(self.configwidgets['type_arcade'],_("Home"))
				if self.param["system"]=="home": radio.set_active(1)
				box2.pack_start(radio)
				frame2.add(box2)
				box.pack_start(frame2)

				#Contry
				frame2 = gtk.Frame(_("Country:"))

				table = gtk.Table(3,2)
				self.configwidgets['country_japan'] = gtk.RadioButton(None,_("Japan"))
				if self.param["country"]=="japan": self.configwidgets['country_japan'].set_active(1)
				table.attach(self.configwidgets['country_japan'],0,1,0,1)
				image = gtk.Image()
				image.set_from_file("data/img/japan.png")
				table.attach(image,0,1,1,2)

				self.configwidgets['country_usa'] = gtk.RadioButton(self.configwidgets['country_japan'],_("USA"))
				if self.param["country"]=="usa": self.configwidgets['country_usa'].set_active(1)
				table.attach(self.configwidgets['country_usa'],1,2,0,1)
				image = gtk.Image()
				image.set_from_file("data/img/usa.png")
				table.attach(image,1,2,1,2)

				radio = gtk.RadioButton(self.configwidgets['country_japan'],_("Europe"))
				if self.param["country"]=="europe": radio.set_active(1)
				table.attach(radio,2,3,0,1)
				image = gtk.Image()
				image.set_from_file("data/img/europe.png")
				table.attach(image,2,3,1,2)
				frame2.add(table)
				box.pack_start(frame2)

				self.configDialog.vbox.pack_start(notebook) #Packing the Notebook

			elif type==5:
				#
				# Other thing configuration.
				#
				self.configDialog.set_title(_("Other thing configuration"))
				box = gtk.VBox(spacing=4) #The box :p

				box2 = gtk.HBox()
				self.configwidgets['autoexecrom'] = gtk.CheckButton(_("Auto execute Roms"))
				if self.paramXGngeo["autoexecrom"]=="true": self.configwidgets['autoexecrom'].set_active(1)
				box2.pack_start(self.configwidgets['autoexecrom'])

				#History size
				label = gtk.Label(_("History size:"))
				box2.pack_start(label)

				adjustment = gtk.Adjustment(float(self.paramXGngeo["historysize"]),1,10,1)

				self.configwidgets['historysize'] = gtk.SpinButton(adjustment)
				box2.pack_start(self.configwidgets['historysize'],False)
				box.pack_start(box2)

				frame = gtk.Frame(_("Path to libGL.so (optional):"))
				box2 = gtk.HBox()

				image = gtk.Image()
				box2.pack_start(image,False,padding=3)
				self.configwidgets['libglpath'] = gtk.Entry()
				self.configwidgets['libglpath'].connect("changed",setPathIcon,image)
				self.configwidgets['libglpath'].set_text(self.param["libglpath"])
				box2.pack_start(self.configwidgets['libglpath'])
				setPathIcon(self.configwidgets['libglpath'],image)
				button = gtk.Button()
				image = gtk.Image()
				image.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_MENU)
				button.add(image)
				button.connect("clicked",self.fileSelect,_('Select the "%s" file.') % "libGL.so",self.configwidgets['libglpath'].get_text(),"libglpath")
				box2.pack_end(button,False)
				frame.add(box2)
				box.pack_start(frame)

				frame = gtk.Frame(_("Preview image directory (optional):"))
				box2 = gtk.HBox()

				image = gtk.Image()
				box2.pack_start(image,False,padding=3)
				self.configwidgets['previewimagedir'] = gtk.Entry()
				self.configwidgets['previewimagedir'].connect("changed",setPathIcon,image,1)
				self.configwidgets['previewimagedir'].set_text(self.paramXGngeo["previewimagedir"])
				box2.pack_start(self.configwidgets['previewimagedir'])
				button = gtk.Button()
				image = gtk.Image()
				image.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_MENU)
				button.add(image)
				button.connect("clicked",self.fileSelect,_('Select the preview image directory.'),self.configwidgets['previewimagedir'].get_text(),"previewimagedir",1)
				box2.pack_end(button,False)
				frame.add(box2)
				box.pack_start(frame)

				frame = gtk.Frame(_("XML file containing Rom infos (optional):"))
				box2 = gtk.HBox()

				image = gtk.Image()
				box2.pack_start(image,False,padding=3)
				self.configwidgets['rominfoxml'] = gtk.Entry()
				self.configwidgets['rominfoxml'].connect("changed",setPathIcon,image)
				self.configwidgets['rominfoxml'].set_text(self.paramXGngeo["rominfoxml"])
				box2.pack_start(self.configwidgets['rominfoxml'])
				button = gtk.Button()
				image = gtk.Image()
				image.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_MENU)
				button.add(image)
				button.connect("clicked",self.fileSelect,_('Select the XML file containing Rom infos.'),self.paramXGngeo["rominfoxml"],"rominfoxml")
				box2.pack_end(button,False)
				frame.add(box2)
				box.pack_start(frame)

				self.configDialog.vbox.pack_start(box)

			#"Save" Button
			button = gtk.Button(stock=gtk.STOCK_SAVE)
			button.connect("clicked",self.configWrite,type,firstrun)
			self.configDialog.action_area.pack_start(button)

			if not firstrun:
				#"Cancel" Button (except at the first time configuration).
				button = gtk.Button(stock=gtk.STOCK_CANCEL)
				if firstrun==1:	button.connect("clicked",self.quit)
				else: button.connect("clicked",self.destroy,[self.configDialog,5])
				self.configDialog.action_area.pack_end(button)

			self.configDialog.show_all()
			#Display the right section in global emulation configuration.
			if type in (1,2,3,4):
				notebook.set_current_page(type-1)
				#Hide the keyboard P2 keys.
				for x in self.configwidgets['p2key'].values(): x.hide();

	def configWrite(self,widget,type,firstrun=0):
		letsWrite = 0

		if type==0:
			#Update important path configuration params.
			self.param["rompath"] = self.configwidgets['rompath'].get_text() #rompath
			self.param["romrc"] = self.configwidgets['romrc'].get_text() #romrc
			
			error = ""
			#Looking for errors :p
			if not os.path.exists(self.configwidgets['rompath'].get_text()): error += _("Roms & Bios directory doesn't exist.")+"\n" #rompath
			elif not os.path.isdir(self.configwidgets['rompath'].get_text()): error += _("Roms & Bios directory is not a directory! O_o;")+"\n"
			if not os.path.exists(self.configwidgets['romrc'].get_text()): error += _("Path to \"romrc\" doesn't exist.")+"\n" #romrc
			elif not os.path.isfile(self.configwidgets['romrc'].get_text()): error += _("Path to \"romrc\" is not a file!")+"\n"
			if not os.path.exists(self.configwidgets['gngeopath'].get_text()): error += _("Path to gngeo executable doesn't exist.")+"\n" #gngeopath
			elif not os.path.isfile(self.configwidgets['gngeopath'].get_text()): error += _("Path to gngeo executable is not a file!")+"\n"

			if len(error)>0: #Display the warning dialog...
				self.configDialog.set_sensitive(False) #Busying Configuration window

				dialog = gtk.Dialog(_("Configuration error!"))
				dialog.connect("destroy",self.destroy,[dialog,4])

				box = gtk.HBox()
				image = gtk.Image()
				image.set_from_stock(gtk.STOCK_DIALOG_WARNING,gtk.ICON_SIZE_DIALOG)
				image.set_padding(5,5)
				box.pack_start(image)
				box2 = gtk.VBox(spacing=0)
				label = gtk.Label(_("Sorry, I can't save the configuration because:")+"\n")
				box2.pack_start(label)
				label = gtk.Label(error)
				label.modify_fg(gtk.STATE_NORMAL,label.get_colormap().alloc_color("#b00"))
				box2.pack_start(label)
				label = gtk.Label(_("Please check it up then save again... ^^;"))
				box2.pack_end(label)
				box.pack_end(box2,padding=5)
				dialog.vbox.pack_end(box)

				#Ok button
				button = gtk.Button(stock=gtk.STOCK_OK)
				button.connect("clicked",self.destroy,[dialog,4])
				dialog.action_area.pack_start(button)

				dialog.show_all()

			else: letsWrite = 1 #Let's write!

		elif type in (1,2,3,4):
			#Update global emulation configuration params.
			self.param["fullscreen"] = ("false","true")[self.configwidgets['fullscreen'].get_active()] #fullscreen
			self.param["interpolation"] = ("false","true")[self.configwidgets['interpolation'].get_active()] #interpolation
			self.param["autoframeskip"] = ("false","true")[self.configwidgets['autoframeskip'].get_active()] #showfps
			self.param["showfps"] = ("false","true")[self.configwidgets['showfps'].get_active()] #autoframeskip
			self.param["scale"] = int(self.configwidgets['scale'].get_value()) #scale
			self.param["screen320"] = ("false","true")[self.configwidgets['screen320'].get_active()] #screen320
			self.param["blitter"] = self.tempparam['blitter'] #blitter
			self.param["effect"] = self.tempparam['effect'] #effect
			self.param["sound"] = ("false","true")[self.configwidgets['sound'].get_active()] #sound
			self.param["samplerate"] = self.tempparam['samplerate'] #sample rate
			self.param["joystick"] = ("false","true")[self.configwidgets['joystick'].get_active()] #joystick
			self.param["p1joydev"] = self.configwidgets['p1joydev'].get_history() #p1joydev
			self.param["p2joydev"] = self.configwidgets['p2joydev'].get_history() #p2joydev
			self.param["system"] = ("home","arcade")[self.configwidgets['type_arcade'].get_active()] #system
			if self.configwidgets['country_japan'].get_active(): self.param["country"] = "japan" #country
			elif self.configwidgets['country_usa'].get_active(): self.param["country"] = "usa"
			else: self.param["country"] = "europe"

			# Keyboard.
			# This following list is important! Without it, keys-values are wrongly arranged!
			keys_list = ["A","B","C","D","START","COIN","UP","DOWN","LEFT","RIGHT"]
			#P1KEY
			self.param["p1key"] = "" #Empty the variable
			for x in keys_list: self.param["p1key"] += self.configwidgets['p1key'][x].get_label()+","
			self.param["p1key"] = self.param["p1key"][:-1] #Remove the last ",".
			#P2KEY
			self.param["p2key"] = "" #Empty the variable
			for x in keys_list: self.param["p2key"] += self.configwidgets['p2key'][x].get_label()+","
			self.param["p2key"] = self.param["p2key"][:-1] #Remove the last ",".

			letsWrite = 1 #Let's write!

		elif type==5:
			#Update other thing configuration params.
			self.paramXGngeo["autoexecrom"] = ("false","true")[self.configwidgets['autoexecrom'].get_active()] #autoexecrom
			self.paramXGngeo["historysize"] = int(self.configwidgets['historysize'].get_value()) #historysize
			self.param["libglpath"] = self.configwidgets['libglpath'].get_text() #libglpath
			self.paramXGngeo["previewimagedir"] = self.configwidgets['previewimagedir'].get_text() #previewimagedir
			self.paramXGngeo["rominfoxml"] = self.configwidgets['rominfoxml'].get_text() #rominfoxml

			letsWrite = 1 #Let's write!

		if letsWrite: #We are now Ok to write configuration files...

			self.configfile.write(self.param,self.paramXGngeo,VERSION)

			self.configDialog.destroy()
			self.busy(0)
			if firstrun: self.main() #Program has been configured, so now we can use it!
			else: self.statusbar.push(self.context_id,_("Configuration has been saved.")) #Update Status message

	def busy(self,state=0):
		if state==1: self.window.set_state(gtk.STATE_INSENSITIVE); self.busyState=1
		else: self.window.set_sensitive(True); self.busyState=0

	def destroy(self,widget,data):
		data[0].destroy()
		if data[1]==1: self.busy(0) #Unbusy the main window
		elif data[1]==2: self.config(firstrun=1) #Configure Gngeo for the first time
		elif data[1]==3: self.main() #Display the main window
		elif data[1]==5: self.busy(0); self.statusbar.push(self.context_id,_("Configuration was not saved.")) #If Configuration cancelled
	
	def quit(self,*args):
		if self.cmd and self.cmd.isAlive(): self.gngeoStop() #Stop any running Gngeo.
		gtk.main_quit() #Stop waiting for event...
		return False

	def __init__(self):
		#Default values...
		self.busyState=0
		self.busyStatus = "off"
		self.param = {
			#PATH
			"libglpath":"/usr/lib/libGL.so",
			"rompath": os.path.join(os.getenv("HOME"),"..."),
			"romrc":"/usr/local/share/gngeo/romrc",
			#GRAPHIC
			"blitter":"soft",
			"effect":"none",
			"fullscreen":"false",
			"interpolation":"false",
			"showfps":"false",
			"autoframeskip":"true",
			"scale":1,
			"screen320":"true",
			#AUDIO / JOYSTICK
			"sound":"true",
			"samplerate":"22050",
			"joystick":"true",
			"p1joydev":0,
			"p2joydev":1,
			#SYSTEM
			"system":"arcade",
			"country":"europe",
			#KEYBOARD
			"p1key":"119,120,113,115,38,34,273,274,276,275",
			"p2key":"108,109,111,112,233,39,264,261,260,262",
			}
		self.paramXGngeo = {
			"autoexecrom":"false",
			"gngeopath":"/usr/local/bin/gngeo",
			"historysize":5,
			"previewimagedir":"data/previewimages/",
			"rominfoxml":"data/rominfos.xml",
			"showavailableromsonly":"true"
			}
		self.tempparam = {}
		self.configwidgets = {}
		self.romPath = None
		self.configfile = configfile.Configfile(gngeo=os.path.join(gngeoPath,"gngeorc"),xgngeo="data/xgngeo.conf")
		self.history = history.History(path=os.path.join(gngeoPath,"history"))

		self.cmd = None
		self.execMenu_item = gtk.ImageMenuItem(gtk.STOCK_EXECUTE)
		self.stopMenu_item = gtk.ImageMenuItem(gtk.STOCK_STOP)

		#Window
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)

		#Statusbar
		self.statusbar = gtk.Statusbar()
		self.context_id = self.statusbar.get_context_id("Info")

	def main(self):
		self.window.set_title("XGngeo")
		self.window.connect("delete_event",self.quit)

		box = gtk.VBox(False,0)
		self.window.add(box)
		menu_bar = gtk.MenuBar()

		#
		# FILE Menu
		#
		menu = gtk.Menu()
		self.file_menu_item = gtk.MenuItem(_("_File"))
		self.file_menu_item.set_submenu(menu)
		menu_bar.append(self.file_menu_item )

		menu2 = gtk.Menu()
		self.loadrom_menu_item = gtk.MenuItem(_("_Load Rom"))
		self.loadrom_menu_item.set_submenu(menu2)
		menu.append(self.loadrom_menu_item)

		menu_item = gtk.MenuItem(_("From _list"))
		menu_item.connect("activate",self.romList)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_Manually"))
		menu_item.connect("activate",self.fileSelect,_("Select a Rom"),self.param["rompath"],"rom")
		menu2.append(menu_item)

		self.history_menu_item = gtk.MenuItem(_("_History"))
		self.historyMenu = gtk.Menu()
		self.history_menu_item.set_submenu(self.historyMenu)
		#Generate history menu from history file
		for x in self.history.getList(size=int(self.paramXGngeo["historysize"])):
			menu_item2 = gtk.MenuItem(x[0])
			menu_item2.connect("activate",self.setPathFromRecent,x[0],x[1])
			self.historyMenu.append(menu_item2)
		menu.append(self.history_menu_item)

		menu.append(gtk.SeparatorMenuItem()) #Separator

		#execMenu_item (yet defined)
		self.execMenu_item.connect("activate",self.gngeoExec)
		self.execMenu_item.set_state(gtk.STATE_INSENSITIVE)
		menu.append(self.execMenu_item)

		#stopMenu_item (yet defined)
		self.stopMenu_item.connect("activate",self.gngeoStop)
		self.stopMenu_item.set_state(gtk.STATE_INSENSITIVE)
		menu.append(self.stopMenu_item)

		menu.append(gtk.SeparatorMenuItem()) #Separator

		menu_item = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		menu_item.connect("activate",self.quit)		
		menu.append(menu_item)

		#
		# CONFIG Menu
		#
		menu = gtk.Menu()
		menu_item = gtk.MenuItem(_("_Configuration"))
		menu_item.set_submenu(menu)
		menu_bar.append(menu_item)

		menu_item = gtk.MenuItem(_("_Important paths"))
		menu_item.connect("activate",self.config,0)
		menu.append(menu_item)

		menu2 = gtk.Menu()
		menu_item = gtk.MenuItem(_("_Global emulation"))
		menu_item.set_submenu(menu2)
		menu.append(menu_item)

		menu_item = gtk.MenuItem(_("_Graphic"))
		menu_item.connect("activate",self.config,1)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_Audio / Joystick"))
		menu_item.connect("activate",self.config,2)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_Keyboard"))
		menu_item.connect("activate",self.config,3)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_System"))
		menu_item.connect("activate",self.config,4)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_Other"))
		menu_item.connect("activate",self.config,5)
		menu.append(menu_item)

		#
		# INFO Menu
		#
		menu = gtk.Menu()
		menu_item = gtk.MenuItem(_("_Info"))
		menu_item.set_right_justified(True) #At right
		menu_item.set_submenu(menu)
		menu_bar.append(menu_item)

		menu_item = gtk.MenuItem(_("_About"))
		menu_item.connect("activate",self.about)
		menu.append(menu_item)

		menu_item = gtk.MenuItem(_("_License"))
		menu_item.connect("activate",self.license)
		menu.append(menu_item)

		# Pack MemuBar into the Box
		box.pack_start(menu_bar,False)

		#
		# Logo
		#
		container = gtk.EventBox()
		container.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("white"))
		logo = gtk.Image()
		logo.set_from_file("data/img/xgngeo.png")
		logo.set_padding(20,0)
		container.add(logo)
		box.pack_start(container)

		#
		# Statusbar
		#
		self.statusbar.push(self.context_id,_("Welcome to XGngeo version %i.") % VERSION)
		box.pack_end(self.statusbar,False)

		#Show All
		self.window.show_all()

	def check(self):
		if self.configfile.exists()[0]:
			params = self.configfile.getParams()
			#Replace default params by gngeorc's.
			for key,val in params[0].items():
				self.param[key] = val

			if self.configfile.exists()[1]:
				#Replace default params by xgngeo's.
				for key,val in params[1].items():
					self.paramXGngeo[key] = val

			self.main() #Display the main window
		else: self.welcome()

if __name__ == "__main__":
	gtk.threads_init()
	XGngeo().check()
	gtk.main()
