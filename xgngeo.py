#!/usr/bin/env python
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
import gtk, os, string, re, gettext, gobject
from sys import path as syspath

#Change working directory to XGngeo's
os.chdir(os.path.abspath(syspath[0]))

#Add `data/py/' to PATH, then import internal modules
syspath.append("data/py/")
import command, configfile, history, rominfos

VERSION = 14
gngeoPath = os.path.expanduser("~/.gngeo")

#Internationalization
gettext.install("xgngeo","data/lang")

class XGngeo:
	def keysConfig(self,widget):
		if self.busyState!=1:
			self.busy(1)
			self.toggled = None
	
			# Keyboard - Order : A,B,C,D,START,COIN,UP,DOWN,LEFT,RIGHT
			keys_list = ["A","B","C","D","START","COIN","UP","DOWN","LEFT","RIGHT"]
	
			# The Gngeo's compliant keymap!
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
					# So, a Gngeo's compatible key-value is given according to its GTK's name.
					key_name = gtk.gdk.keyval_name(value).lower()
					key = None

					#~ print key_name

					if key_name in conpliant_KeyMap.keys():
						key = conpliant_KeyMap[key_name]
						widget.set_label("%s" % (key))
						widget.clicked()

			def toggled(widget):
				if self.toggled and self.toggled!=widget:
					if self.toggled.get_active(): self.toggled.set_active(gtk.FALSE)
				self.toggled = widget

			def radioToggled(widget,data):
				i=0
				if data: #Show P2 key and hide P1's
					for x in self.p2keysButt.values():
						x.show()
					for x in self.p1keysButt.values():
						x.hide()
				else: #Show P1 key and hide P2's
					for x in self.p1keysButt.values():
						x.show()
					for x in self.p2keysButt.values():
						x.hide()
					

			self.keysDialog = gtk.Dialog(_("Keys configuration"))
			self.keysDialog.connect("destroy",self.destroy,[self.keysDialog,1])	

			label = gtk.Label(_("To modify a key, click the button then push your new key.\nThis configuration is only for keyboard."))
			label.set_justify(gtk.JUSTIFY_CENTER)
			label.set_padding(5,5)
			self.keysDialog.vbox.pack_start(label)

			#Player's keyboard selection
			box = gtk.HBox()
			radio = gtk.RadioButton(None,_("Player 1"))
			radio.connect("toggled",radioToggled,0)
			box.pack_start(radio)
			radio = gtk.RadioButton(radio,_("Player 2"))
			radio.connect("toggled",radioToggled,1)
			box.pack_start(radio)
			self.keysDialog.vbox.pack_start(box,padding=2)

			table = gtk.Table(4,6,gtk.TRUE) #The sweet table O_o;;

			self.p1keysButt = {}; image = {}; i=0
			split = string.split(self.param["p1key"],",")
			for x in keys_list:
				#Generate key's image
				image[x] = gtk.Image()
				image[x].set_from_file("data/img/key_%s.png" % x)

				#Generate P1key's button
				self.p1keysButt[x] = gtk.ToggleButton(split[i])
				self.p1keysButt[x].connect("toggled",toggled)
				self.p1keysButt[x].connect("key_press_event",getPressed)
				self.p1keysButt[x].set_use_underline(gtk.FALSE)
				
				i+=1 

			self.p2keysButt = {}; i=0
			split = string.split(self.param["p2key"],",")
			for x in keys_list:
				#Generate P2key's button
				self.p2keysButt[x] = gtk.ToggleButton(split[i])
				self.p2keysButt[x].connect("toggled",toggled)
				self.p2keysButt[x].connect("key_press_event",getPressed)
				self.p2keysButt[x].set_use_underline(gtk.FALSE)

				box = gtk.HBox() #A box...
				box.pack_start(self.p1keysButt[x]) #with P1 key...
				box.pack_start(self.p2keysButt[x]) #and P2 key :p

				#Put them in table
				if i<6:
					table.attach(image[x],i,i+1,0,1)
					table.attach(box,i,i+1,1,2)
				else:
					table.attach(image[x],i-5,i-4,2,3)
					table.attach(box,i-5,i-4,3,4)
	
				i+=1

			self.keysDialog.vbox.pack_start(table,padding=5)

			#"Save" Button
			button = gtk.Button(stock=gtk.STOCK_SAVE)
			button.connect("clicked",self.configWrite,"keysConfig")
			self.keysDialog.action_area.pack_start(button)

			#"Cancel" Button
			button = gtk.Button(stock=gtk.STOCK_CANCEL)
			button.connect("clicked",self.destroy,[self.keysDialog,5])
			self.keysDialog.action_area.pack_end(button)

			self.keysDialog.show_all()

			#Hide the P2keys
			for x in self.p2keysButt.values():
				x.hide()

	def welcome(self):
		#Check for Gngeo's home directory
		if not os.path.isdir(gngeoPath): os.mkdir(gngeoPath)

		self.introDialog = gtk.Dialog(_("Welcome! ^_^"))
		self.introDialog.connect("delete_event",self.quit)

		label = gtk.Label(_("The configuration file of Gngeo was not found!\nWe have to create one. Press OK to continue...") % self.configfile.get_path()[0])
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

			label = gtk.Label(_("XGngeo is released under the GNU GPL:"))
			label.set_padding(10,4)
			self.licenseDialog.vbox.pack_start(label,gtk.FALSE)

			#
			# VIEW LICENSE
			#
			licensePath = "LICENSE.txt"
			textbuffer = gtk.TextBuffer()

			if os.path.isfile(licensePath):
				licenceFile = open(licensePath,"r")
				licenceText = licenceFile.read()
				licenceFile.close()
				textbuffer.set_text(licenceText)
				del licenceText
			else:
				textbuffer.set_text(_("Error: Unable to open the file \"%s\"!\nYou can read the GNU CPL license at:\nhttp://www.gnu.org/licenses/gpl.html") % licensePath)
			
			textview = gtk.TextView(textbuffer)
			textview.set_editable(gtk.FALSE)
	
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

	def gngeoExec(self,widget=None):
		self.cmd = command.Command("gngeo '%s'" % self.romPath)
		self.loadfromfile_menu_item.set_sensitive(gtk.FALSE)
		self.loadfromlist_menu_item.set_sensitive(gtk.FALSE)
		self.history_menu_item.set_sensitive(gtk.FALSE)
		self.stopMenu_item.set_sensitive(gtk.TRUE)
		self.execMenu_item.set_sensitive(gtk.FALSE)
		self.cmd.start() #Let's start!
		
		# Check if the thread still alive every time `File' menu is opened :p
		self.checkexechandler = self.file_menu_item.connect("activate",self.gngeoCheckExec)

	def gngeoCheckExec(self,widget):
		if self.cmd.isAlive(): pass
		else: 
			self.gngeoStop(kill=0) #Do as `Stop' has been clicked...
			self.file_menu_item.disconnect(self.checkexechandler) #Stop checking

	def gngeoStop(self,widget=None,kill=1):
		if kill: command.Command("killall -9 gngeo").start()
		self.loadfromfile_menu_item.set_sensitive(gtk.TRUE)
		self.loadfromlist_menu_item.set_sensitive(gtk.TRUE)
		self.history_menu_item.set_sensitive(gtk.TRUE)
		self.stopMenu_item.set_sensitive(gtk.FALSE)
		self.execMenu_item.set_sensitive(gtk.TRUE)

	def romList(self,widget):
		self.rominfos = rominfos.Rominfos(path=self.paramXGngeo["rominfosxml"])
		
		def setRomTemp(widget,data):
			#If the selected rom is available
			if data[0]==1:
				if self.romFromList and self.romFromList!=data[1]:
					self.listButton[self.romFromList].set_active(gtk.FALSE) #Desactivate last selected Rom's button.
				if widget.get_active():	self.romFromList,self.romFromListName = data[1],data[2]
				else: self.romFromList,self.romFromListName = None,None

			#Update preview image
			if os.path.isfile(os.path.join(self.paramXGngeo["previewimagesdir"],data[1]+".png")): self.previewImage.set_from_file(os.path.join(self.paramXGngeo["previewimagesdir"],data[1]+".png"))
			elif os.path.isfile(os.path.join(self.paramXGngeo["previewimagesdir"],"unavailable.png")): self.previewImage.set_from_file(os.path.join(self.paramXGngeo["previewimagesdir"],"unavailable.png"))
				
			#Update rom infos
			if os.path.isfile(self.paramXGngeo["rominfosxml"]):
				#Check for game informations
				if self.romInfos.has_key(data[1]):
					for x in ("desc","manufacturer","year","genre","players","rating","size"):
						if self.romInfos[data[1]].has_key(x): self.romInfosWidget[x].set_text(self.romInfos[data[1]][x])
						else: self.romInfosWidget[x].set_text("--")
				else:
					for x in ("desc","manufacturer","year","genre","players","rating","size"):
						self.romInfosWidget[x].set_text("--")

		def showAvailable(widget):
			if widget.get_active():
				for x in self.listButtonOther.values(): x.hide()
				self.paramXGngeo["showavailableromsonly"] = "true"
			else: #Show other Roms
				for x in self.listButtonOther.values(): x.show()
				self.paramXGngeo["showavailableromsonly"] = "false"

		if self.busyState!=1:
			self.busy(1)
			self.romFromList = None #Selected Rom

			self.listDialog = gtk.Dialog(_("List of Roms from your \"romrc\" file"))
			self.listDialog.connect("destroy",self.destroy,[self.listDialog,1])

			label = gtk.Label(_("Please select the Rom you want to load from this list ^^\nAvailable Roms are showed in blue..."))
			label.set_justify(gtk.JUSTIFY_CENTER)
			self.listDialog.vbox.pack_start(label,gtk.FALSE,gtk.FALSE,2)

			table = gtk.Table(2,2)

			buttonShowAvailable = gtk.CheckButton(_("Show available Roms only."))
			buttonShowAvailable.connect("toggled",showAvailable)
			table.attach(buttonShowAvailable,0,1,0,1,yoptions=gtk.SHRINK)

			scrolled_window = gtk.ScrolledWindow()
			scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
			table.attach(scrolled_window,0,1,1,2)
	
			file = open(self.param["romrc"],"r")
			gamelist = {} #NAME:REF
			gamelistNames = [] #NAME only (can be sorted)
			for line in file.readlines():
				match = re.match("game (\S*) \S* \"(.*)\"",line)
				if match!=None:
					#Check if the game isn't added yet
					if match.group(1) not in gamelist.values():
						gamelist[match.group(2)] = match.group(1)
						gamelistNames.append(match.group(2))
			file.close()
			gamelistNames.sort() #Sort the Name list
			self.listButton, self.listButtonOther = {}, {}

			box = gtk.VBox()
			for name in gamelistNames:
				if os.path.isfile(os.path.join(self.param["rompath"],gamelist[name]+".zip")):
					self.listButton[gamelist[name]] = gtk.ToggleButton(name)
					self.listButton[gamelist[name]].modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#69F"))
					self.listButton[gamelist[name]].connect("clicked",setRomTemp,[1,gamelist[name],name])
					box.pack_start(self.listButton[gamelist[name]])
				else:
					self.listButtonOther[gamelist[name]] = gtk.ToggleButton(name)
					self.listButtonOther[gamelist[name]].set_inconsistent(gtk.TRUE)
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
			if(os.path.isdir(self.paramXGngeo["previewimagesdir"])):
				self.previewImage = gtk.Image()
				path = os.path.join(self.paramXGngeo["previewimagesdir"],"unavailable.png")
				if os.path.isfile(path): self.previewImage.set_from_file(path) #Display the ``unavailable" image by default.
				notebook.append_page(self.previewImage,gtk.Label(_("Preview image")))

			#Rom infos
			if(os.path.isfile(self.paramXGngeo["rominfosxml"])):
				self.romInfos = rominfos.Rominfos(path=self.paramXGngeo["rominfosxml"]).getDict()
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
				table2 = gtk.Table(3,2,gtk.TRUE)

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

				box.pack_start(table2,gtk.FALSE)

				notebook.append_page(box,gtk.Label(_("Rom infos")))

			table.attach(notebook,1,2,0,2,gtk.SHRINK)
			self.listDialog.vbox.pack_start(table)

			#Buttons at bottom
			button = gtk.Button(stock=gtk.STOCK_OK)
			button.connect("clicked",self.setRomFromList)
			self.listDialog.action_area.pack_start(button)

			button = gtk.Button(stock=gtk.STOCK_CANCEL)
			button.connect("clicked",self.destroy,[self.listDialog,1])
			self.listDialog.action_area.pack_start(button)

			self.listDialog.show_all()
			if self.paramXGngeo["showavailableromsonly"]=="true": buttonShowAvailable.set_active(gtk.TRUE) #Activate button.
	
	def optParam(self,widget,data):
		if data[0]=="blitter":
			self.blitter = data[1] #Updating param
		elif data[0]=="effect":
			self.effect = data[1]
		elif data[0]=="samplerate":
			self.samplerate = data[1]

	def fileSelect(self,widget,data):
		if self.busyState!=1: self.busy(1) #Busy the main window if not yet
		destroyInt = 1 #Value for the destroy command...

		if data[1][1] in ("romrc","libglpath","rominfosxml"):
			self.configDialog.set_sensitive(gtk.FALSE) #Busy the Configuration window
			destroyInt = 4

		self.fileSel = gtk.FileSelection(data[0][0])
		self.fileSel.button_area.hide() #Hide the ``fileops" area.
		self.fileSel.set_filename(os.path.dirname(data[0][1])+"/")
		self.fileSel.connect("destroy",self.destroy,[self.fileSel,destroyInt]);
		self.fileSel.ok_button.connect("clicked",data[1][0],data[1][1])
		self.fileSel.cancel_button.connect("clicked",self.destroy,[self.fileSel,destroyInt])
		self.fileSel.show()

	def setPathFromRecent(self,widget,data):
		formatedPath = os.path.basename(data[1])
		self.romPath = data[1]
		self.statusbar.push(self.context_id,_("Rom:")+" \"%s\" (%s)" % (data[0],formatedPath)) #Update Status message
		if self.paramXGngeo["autoexecrom"]=="true": self.gngeoExec() #Auto execute the Rom...
		else: self.execMenu_item.set_sensitive(gtk.TRUE) #Activate the "Execute" button

	def setPath(self,widget,data):
		if data=="rom":
			formatedPath = os.path.basename(self.fileSel.get_filename())
			#Something is selected?
			if formatedPath:
				#Does it exist?
				if os.path.isfile(self.fileSel.get_filename()):
					self.romPath = self.fileSel.get_filename()
					self.statusbar.push(self.context_id,_("Rom:")+" %s" % formatedPath) #Update Status message
					if self.paramXGngeo["autoexecrom"]=="true": self.gngeoExec() #Auto execute the Rom...
					else: self.execMenu_item.set_sensitive(gtk.TRUE) #Activate the "Execute" button
					self.historyAdd(formatedPath,self.fileSel.get_filename()) #Put in the history menu
				else: self.statusbar.push(self.context_id,"Error: File doesn't exist!")
		elif data in ("romrc","libglpath","rominfosxml"):
			path = self.fileSel.get_filename() #Get the path
			if data=="romrc": self.romrc.set_text(path)
			elif data=="libglpath": self.libglpath.set_text(path)
			elif data=="rominfosxml": self.rominfosxml.set_text(path)
			self.configDialog.set_sensitive(gtk.TRUE) #Unbusy the Configuration window

		self.fileSel.destroy()
		self.busyStatus = "off"

	def setRomFromList(self,widget):
		#Something selected?
		if self.romFromList!=None:
			self.romPath = self.romFromList
			self.statusbar.push(self.context_id,_("Rom:")+" \"%s\" (%s)" % (self.romFromListName,self.romFromList)) #Update Status message
			if self.paramXGngeo["autoexecrom"]=="true": self.gngeoExec() #Auto execute the Rom...
			else: self.execMenu_item.set_sensitive(gtk.TRUE) #Activate the "Execute" button
			self.historyAdd(self.romFromListName,self.romFromList) #Put in the history menu

		self.listDialog.destroy()
		self.busyStatus = "off"

	def historyAdd(self,name,location):
		#Update history file...
		self.history.add(name,location,size=self.paramXGngeo["historysize"])

		#Add entry to history menu
		menu_item = gtk.MenuItem(name)
		menu_item.connect("activate",self.setPathFromRecent,[name,location])
		self.historyMenu.prepend(menu_item)
		
		#Remove the oldest entries if too much...
		for menu_item in self.historyMenu.get_children()[int(self.paramXGngeo["historysize"]):]:
			self.historyMenu.remove(menu_item)

		self.historyMenu.show_all()

	def about(self,widget):
		#Checks if something is not already open...
		if self.busyState!=1:
			self.busy(1)

			self.aboutDialog = gtk.Dialog(_("About XGngeo"),flags=gtk.DIALOG_NO_SEPARATOR)
			self.aboutDialog.connect("destroy",self.destroy,[self.aboutDialog,1])

			pipe = os.popen("gngeo --version")
			line = re.match("Gngeo (\S*)",pipe.readline())
			pipe.close()
			if line:	gngeoversion = line.group(1)
			else:	gngeoversion = "&lt;=0.5.9a"

			label = gtk.Label(_("<span color='#008'><b>XGngeo: a frontend for Gngeo :p</b>\nVersion %i.\nRunning Gngeo version %s.\nXGngeo's license is the GNU GPL.</span>") % (VERSION,gngeoversion))
			label.set_justify(gtk.JUSTIFY_CENTER)
			label.set_use_markup(gtk.TRUE)
			self.aboutDialog.vbox.pack_start(label)

			frame = gtk.Frame(_("Credits"))
			box = gtk.HBox(spacing=3)
			frame.add(box)

			logo = gtk.Image()
			logo.set_from_file("data/img/chprod.png")
			box.pack_start(logo,gtk.FALSE)

			label = gtk.Label(_("Main coder: Choplair.\nAssisted by: Pachilor.")+"\n\nhttp://choplair.tuxfamily.org/")
			label.set_justify(gtk.JUSTIFY_CENTER)
			box.pack_start(label)

			self.aboutDialog.vbox.pack_start(frame)

			#Button at bottom..
			button = gtk.Button(stock=gtk.STOCK_CLOSE)
			button.connect("clicked",self.destroy,[self.aboutDialog,1])
			self.aboutDialog.action_area.pack_end(button)

			self.aboutDialog.show_all()
	
	def config(self,widget=None,section=0,firstrun=0):
		if self.busyState!=1:
			self.busy(1)

			self.configDialog = gtk.Dialog(_("Configuration"))

			if firstrun==1: self.configDialog.connect("delete_event",self.quit)
			else: self.configDialog.connect("destroy",self.destroy,[self.configDialog,1])

			notebook = gtk.Notebook()

			#
			# PATH section
			#
			box = gtk.VBox(spacing=4) #The box :p
			notebook.append_page(box,gtk.Label(_("Path")))

			frame = gtk.Frame(_("Roms & Bios directory:"))
			self.rompath = gtk.Entry()
			self.rompath.set_text(self.param["rompath"])
			frame.add(self.rompath)
			box.pack_start(frame)

			frame = gtk.Frame(_("Path to romrc:"))
			box2 = gtk.HBox(spacing=5)
			self.romrc = gtk.Entry()
			self.romrc.set_text(self.param["romrc"])
			box2.pack_start(self.romrc)
			button = gtk.Button(stock=gtk.STOCK_OPEN)
			button.connect("clicked",self.fileSelect,[[_('Select the "%s" file.') % "romrc",self.romrc.get_text()],[self.setPath,"romrc"]])
			box2.pack_end(button,gtk.FALSE)
			frame.add(box2)
			box.pack_start(frame)

			frame = gtk.Frame(_("Path to libGL.so (optional):"))
			box2 = gtk.HBox(spacing=5)	
			self.libglpath = gtk.Entry()
			self.libglpath.set_text(self.param["libglpath"])
			box2.pack_start(self.libglpath)
			button = gtk.Button(stock=gtk.STOCK_OPEN)
			button.connect("clicked",self.fileSelect,[[_('Select the "%s" file.') % "libGL.so",self.libglpath.get_text()],[self.setPath,"libglpath"]])
			box2.pack_end(button,gtk.FALSE)
			frame.add(box2)
			box.pack_end(frame)

			#
			# GRAPHIC section
			#
			box = gtk.VBox(spacing=4) #The box :p
			notebook.append_page(box,gtk.Label(_("Graphic")))

			table = gtk.Table(3,3)

			#Fullscreen
			self.fullscreen = gtk.CheckButton(_("Fullscreen"))
			if self.param["fullscreen"]=="true": self.fullscreen.set_active(1)
			table.attach(self.fullscreen,0,1,0,1)
			#Interpolation
			self.interpolation = gtk.CheckButton(_("Interpolation"))
			if self.param["interpolation"]=="true": self.interpolation.set_active(1)
			table.attach(self.interpolation,0,1,1,2)
			#Show FPS
			self.showfps = gtk.CheckButton(_("Show FPS"))
			if self.param["showfps"]=="true": self.showfps.set_active(1)
			table.attach(self.showfps,1,2,0,1)
			#Auto Frameskip
			self.autoframeskip = gtk.CheckButton(_("Auto Frameskip"))
			if self.param["autoframeskip"]=="true": self.autoframeskip.set_active(1)
			table.attach(self.autoframeskip,1,2,1,2)

			#Scale
			adjustment = gtk.Adjustment(float(self.param["scale"]),1,5,1)

			frame = gtk.Frame(_("Scale:"))
			self.scale = gtk.HScale(adjustment)
			self.scale.set_size_request(60,-1)
			self.scale.set_digits(0)
			frame.add(self.scale)
			table.attach(frame,2,3,0,2)
		
			box.pack_start(table)

			# BLITTER
			self.blitter = self.param["blitter"]
			frame = gtk.Frame(_("Blitter:"))
	
			opt = gtk.OptionMenu()
			menu = gtk.Menu() 

			blitter = os.popen("gngeo --blitter help")
			lines = blitter.readlines() #Get Gngeo's available blitter
			blitter.close()
			i=0
			for line in lines:
				if string.find(line,":")>0:
					splited = string.split(line,":") #Syntax is "REF : FULLNAME"
					ref,fullname = splited[0].strip(),splited[1].strip()

					menu_item = gtk.MenuItem(fullname)
					menu_item.connect("activate",self.optParam,["blitter",ref])
					menu.append(menu_item)
					#Set active the last selection
					if ref==self.param["blitter"]: menu.set_active(i)
					i+=1
			opt.set_menu(menu)
			frame.add(opt)
			box.pack_start(frame)

			# EFFECT
			self.effect = self.param["effect"]
			frame = gtk.Frame(_("Effect:"))

			opt = gtk.OptionMenu()
			menu = gtk.Menu() 

			effect = os.popen("gngeo --effect help")
			lines = effect.readlines() #Get Gngeo's available blitter
			effect.close()
			i=0
			for line in lines:
				if string.find(line,":")>0:
					splited = string.split(line,":") #Syntax is "REF : FULLNAME"
					ref,fullname = splited[0].strip(),splited[1].strip()

					menu_item = gtk.MenuItem(fullname)
					menu_item.connect("activate",self.optParam,["effect",ref])
					menu.append(menu_item)
					#Set active the last selection
					if ref==self.param["effect"]: menu.set_active(i)
					i+=1
			opt.set_menu(menu)
			frame.add(opt)
			box.pack_start(frame)

			#
			# AUDIO section
			#
			box = gtk.VBox(spacing=4) #The Box
			notebook.append_page(box,gtk.Label(_("Audio")))

			self.sound = gtk.CheckButton(_("Enable sound"))
			if self.param["sound"]=="true": self.sound.set_active(1)
			box.pack_start(self.sound)

			#Sample rate
			self.samplerate = self.param["samplerate"]
			box2 = gtk.HBox(spacing=5)

			label = gtk.Label(_("Sample rate:"))
			box2.pack_start(label)

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
			box2.pack_start(opt)
			box.pack_start(box2)

			#
			# SYSTEM section
			#
			box = gtk.VBox(spacing=4) #The box :p
			notebook.append_page(box,gtk.Label(_("System")))

			#Type
			frame2 = gtk.Frame(_("Neo Geo type:"))
			box2 = gtk.HBox()
			self.type_arcade = gtk.RadioButton(None,_("Arcade"))
			if self.param["system"]=="arcade": self.type_arcade.set_active(1)
			box2.pack_start(self.type_arcade)
			self.type_home = gtk.RadioButton(self.type_arcade,_("Home"))
			if self.param["system"]=="home": self.type_home.set_active(1)
			box2.pack_start(self.type_home)
			frame2.add(box2)
			box.pack_start(frame2)

			#Contry
			frame2 = gtk.Frame(_("Country:"))

			table = gtk.Table(3,2)
			self.country_japan = gtk.RadioButton(None,_("Japan"))
			if self.param["country"]=="japan": self.country_japan.set_active(1)
			table.attach(self.country_japan,0,1,0,1)
			image = gtk.Image()
			image.set_from_file("data/img/japan.png")
			table.attach(image,0,1,1,2)

			self.country_usa = gtk.RadioButton(self.country_japan,_("USA"))
			if self.param["country"]=="usa": self.country_usa.set_active(1)
			table.attach(self.country_usa,1,2,0,1)
			image = gtk.Image()
			image.set_from_file("data/img/usa.png")
			table.attach(image,1,2,1,2)

			self.country_europe = gtk.RadioButton(self.country_japan,_("Europe"))
			if self.param["country"]=="europe": self.country_europe.set_active(1)
			table.attach(self.country_europe,2,3,0,1)
			image = gtk.Image()
			image.set_from_file("data/img/europe.png")
			table.attach(image,2,3,1,2)
			frame2.add(table)
			box.pack_start(frame2)

			#
			# OTHER Section
			#
			box = gtk.VBox(spacing=4) #The box :p
			notebook.append_page(box,gtk.Label(_("Other")))

			box2 = gtk.HBox()
			self.autoexecrom = gtk.CheckButton(_("Auto execute Roms"))
			if self.paramXGngeo["autoexecrom"]=="true": self.autoexecrom.set_active(1)
			box2.pack_start(self.autoexecrom)

			#History size
			label = gtk.Label(_("History size:"))
			box2.pack_start(label)

			adjustment = gtk.Adjustment(float(self.paramXGngeo["historysize"]),1,10,1)

			self.historysize = gtk.SpinButton(adjustment)
			box2.pack_start(self.historysize,gtk.FALSE)
			box.pack_start(box2)

			frame = gtk.Frame(_("Preview images directory (optional):"))
			self.previewimagesdir = gtk.Entry()
			self.previewimagesdir.set_text(self.paramXGngeo["previewimagesdir"])
			frame.add(self.previewimagesdir)
			box.pack_start(frame)

			frame = gtk.Frame(_("XML file containing Rom infos (optional):"))
			box2 = gtk.HBox()
			self.rominfosxml = gtk.Entry()
			self.rominfosxml.set_text(self.paramXGngeo["rominfosxml"])
			box2.pack_start(self.rominfosxml)
			button = gtk.Button(stock=gtk.STOCK_OPEN)
			button.connect("clicked",self.fileSelect,[[_('Select the XML file containing Rom infos.'),self.paramXGngeo["rominfosxml"]],[self.setPath,"rominfosxml"]])
			box2.pack_end(button,gtk.FALSE)
			frame.add(box2)
			box.pack_start(frame)

			self.configDialog.vbox.pack_start(notebook) #Packing the Notebook

			#"Save" Button
			button = gtk.Button(stock=gtk.STOCK_SAVE)
			button.connect("clicked",self.configWrite,(None,"firstrun")[firstrun])
			self.configDialog.action_area.pack_start(button)

			#"Cancel" Button
			button = gtk.Button(stock=gtk.STOCK_CANCEL)
			if firstrun==1:	button.connect("clicked",self.quit)
			else: button.connect("clicked",self.destroy,[self.configDialog,5])
			self.configDialog.action_area.pack_end(button)

			self.configDialog.show_all()
			notebook.set_current_page(section)

	def configWrite(self,widget,special=None):
		letsWrite = 0

		if special=="keysConfig":
			# Keyboard - order : A,B,C,D,START,COIN,UP,DOWN,LEFT,RIGHT
			# This is important! Without it, keys-values are arranged wrongly!
			keys_list = ["A","B","C","D","START","COIN","UP","DOWN","LEFT","RIGHT"]

			#P1KEY
			self.param["p1key"] = "" #Empty the variable
			for x in keys_list:
				self.param["p1key"] += ","+self.p1keysButt[x].get_label()
			self.param["p1key"] = self.param["p1key"][1:] #Remove the first ","

			#P2KEY
			self.param["p2key"] = "" #Empty the variable
			for x in keys_list:
				self.param["p2key"] += ","+self.p2keysButt[x].get_label()
			self.param["p2key"] = self.param["p2key"][1:] #Remove the first ","

			letsWrite = 1 #Let's write!

		else:
			error = ""
			#Looking for errors :p
			if not os.path.exists(self.rompath.get_text()): error += _("Roms & Bios directory doesn't exist.")+"\n" #rompath
			elif not os.path.isdir(self.rompath.get_text()): error += _("Roms & Bios directory is not a directory! O_o;")+"\n"
			if not os.path.exists(self.romrc.get_text()): error += _("Path to \"romrc\" doesn't exist.")+"\n" #romrc
			elif not os.path.isfile(self.romrc.get_text()): error += _("Path to \"romrc\" is not a file!")+"\n"

			if len(error)>0: #Display the warning dialog...
				self.configDialog.set_sensitive(gtk.FALSE) #Busying Configuration window

				self.warningDialog = gtk.Dialog(_("Configuration error!"))
				self.warningDialog.connect("destroy",self.destroy,[self.warningDialog,4])

				box = gtk.HBox()
				image = gtk.Image()
				image.set_from_stock(gtk.STOCK_DIALOG_WARNING,gtk.ICON_SIZE_DIALOG)
				image.set_padding(5,5)
				box.pack_start(image)
				box2 = gtk.VBox(spacing=0)
				label = gtk.Label(_("Sorry, I'm unable to save the configuration because:")+"\n")
				box2.pack_start(label)
				label = gtk.Label(error)
				label.modify_fg(gtk.STATE_NORMAL,label.get_colormap().alloc_color("#b00"))
				box2.pack_start(label)
				label = gtk.Label(_("Please check it up then save again... ^^;"))
				box2.pack_end(label)
				box.pack_end(box2,padding=5)
				self.warningDialog.vbox.pack_end(box)

				#Ok button
				button = gtk.Button(stock=gtk.STOCK_OK)
				button.connect("clicked",self.destroy,[self.warningDialog,4])
				self.warningDialog.action_area.pack_start(button)

				self.warningDialog.show_all()
			else: 
				#Define all params
				self.param["rompath"] = self.rompath.get_text() #rompath
				self.param["romrc"] = self.romrc.get_text() #romrc
				self.param["libglpath"] = self.libglpath.get_text() #libglpath
				self.param["fullscreen"] = ("false","true")[self.fullscreen.get_active()] #fullscreen
				self.param["interpolation"] = ("false","true")[self.interpolation.get_active()] #interpolation
				self.param["autoframeskip"] = ("false","true")[self.autoframeskip.get_active()] #showfps
				self.param["showfps"] = ("false","true")[self.showfps.get_active()] #autoframeskip
				self.param["scale"] = int(self.scale.get_value()) #scale
				self.param["blitter"] = self.blitter #blitter
				self.param["effect"] = self.effect #effect
				self.param["samplerate"] = self.samplerate #sample rate
				self.param["sound"] = ("false","true")[self.sound.get_active()] #fullscreen
				if self.type_arcade.get_active(): self.param["system"] = "arcade" #system
				else: self.param["system"] = "home"
				if self.country_japan.get_active(): self.param["country"] = "japan" #country
				elif self.country_usa.get_active(): self.param["country"] = "usa"
				else: self.param["country"] = "europe"

				#XGngeo's own params
				self.paramXGngeo["autoexecrom"] = ("false","true")[self.autoexecrom.get_active()] #autoexecrom
				self.paramXGngeo["historysize"] = int(self.historysize.get_value()) #historysize
				self.paramXGngeo["previewimagesdir"] = self.previewimagesdir.get_text() #previewimagesdir
				self.paramXGngeo["rominfosxml"] = self.rominfosxml.get_text() #rominfosxml

				letsWrite = 1 #Let's write!

		if letsWrite==1: #Save configuration

			self.configfile.write(self.param,self.paramXGngeo,VERSION)

			if special=="keysConfig": self.keysDialog.destroy()
			else: self.configDialog.destroy()
			self.busy(0)
			if special=="firstrun": self.main() #Program has been configured, then now we can use it!
			else: self.statusbar.push(self.context_id,_("Configuration has been saved.")) #Update Status message

	def busy(self,state=0):
		if state==1: self.window.set_state(gtk.STATE_INSENSITIVE); self.busyState=1
		else: self.window.set_sensitive(gtk.TRUE); self.busyState=0

	def destroy(self,widget,data):
		data[0].destroy()
		if data[1]==1: self.busy(0) #Unbusy the main window
		elif data[1]==2: self.config(firstrun=1) #Configure Gngeo for the first time
		elif data[1]==3: self.main() #Display the main window
		elif data[1]==4: self.configDialog.set_sensitive(gtk.TRUE) #Unbusy the Configuration window
		elif data[1]==5: self.busy(0); self.statusbar.push(self.context_id,_("Configuration was not saved.")) #If Configuration cancelled
	
	def quit(self,widget,event=None):
		gtk.main_quit() #Stop waiting for event...
		return gtk.FALSE

	def __init__(self):
		#Default values...
		self.busyState=0
		self.busyStatus = "off"
		self.param = {
			#PATH
			"libglpath":"/path/to/libGL.so",
			"rompath":"/path/to/roms_and_bios/",
			"romrc":"/path/to/romrc",
			#GRAPHIC
			"blitter":"soft",
			"effect":"none",
			"fullscreen":"false",
			"interpolation":"false",
			"showfps":"false",
			"autoframeskip":"true",
			"scale":1,
			#AUDIO
			"sound":"true",
			"samplerate":22050,
			#SYSTEM
			"system":"arcade",
			"country":"europe",
			#KEYS
			"p1key":"119,120,113,115,38,34,273,274,276,275",
			"p2key":"108,109,111,112,233,39,264,261,260,262",
			}
		self.paramXGngeo = {
			"autoexecrom":"false",
			"historysize":5,
			"previewimagesdir":"data/previewimages/",
			"rominfosxml":"data/rominfos.xml",
			"showavailableromsonly":"true"
			}
		self.romPath = None
		self.configfile = configfile.Configfile(gngeo=os.path.join(gngeoPath,"gngeorc"),xgngeo="data/xgngeo.conf")
		self.history = history.History(path=os.path.join(gngeoPath,"history"))

		self.execMenu_item = gtk.ImageMenuItem(gtk.STOCK_EXECUTE)
		self.stopMenu_item = gtk.ImageMenuItem(gtk.STOCK_STOP)

		#Window
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)

		#Statusbar
		self.statusbar = gtk.Statusbar()
		self.context_id = self.statusbar.get_context_id("Info")
		self.welcomemess = _("Welcome to XGngeo version %i.") % VERSION

	def main(self):
		self.window.set_title("XGngeo")
		self.window.connect("delete_event",self.quit)

		box = gtk.VBox(gtk.FALSE,0)
		self.window.add(box)
		menu_bar = gtk.MenuBar()

		#
		# FILE Menu
		#
		menu = gtk.Menu()
		self.file_menu_item = gtk.MenuItem(_("_File"))
		self.file_menu_item.set_submenu(menu)
		menu_bar.append(self.file_menu_item )

		self.loadfromfile_menu_item = gtk.MenuItem(_("Load from _File"))
		self.loadfromfile_menu_item.connect("activate",self.fileSelect,[[_("Select a Rom"),self.param["rompath"]],[self.setPath,"rom"]])
		menu.append(self.loadfromfile_menu_item)

		self.loadfromlist_menu_item = gtk.MenuItem(_("Load from _List"))
		self.loadfromlist_menu_item.connect("activate",self.romList)
		menu.append(self.loadfromlist_menu_item)

		menu.append(gtk.SeparatorMenuItem()) #Separator

		#exeMenu_item (yet defined)
		self.execMenu_item.connect("activate",self.gngeoExec)
		self.execMenu_item.set_state(gtk.STATE_INSENSITIVE)
		menu.append(self.execMenu_item)

		#stopMenu_item (yet defined)
		self.stopMenu_item.connect("activate",self.gngeoStop)
		self.stopMenu_item.set_state(gtk.STATE_INSENSITIVE)
		menu.append(self.stopMenu_item)

		menu.append(gtk.SeparatorMenuItem()) #Separator

		self.history_menu_item = gtk.MenuItem(_("_History"))
		self.historyMenu = gtk.Menu()
		self.history_menu_item.set_submenu(self.historyMenu)
		#Generate history menu from history file
		for x in self.history.getList(size=self.paramXGngeo["historysize"]):
			menu_item2 = gtk.MenuItem(x[0])
			menu_item2.connect("activate",self.setPathFromRecent,(x[0],x[1]))
			self.historyMenu.append(menu_item2)
		menu.append(self.history_menu_item)

		menu.append(gtk.SeparatorMenuItem()) #Separator

		menu_item = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		menu_item.connect("activate",self.quit)		
		menu.append(menu_item)

		#
		# CONFIG Menu
		#
		menu = gtk.Menu()
		menu_item = gtk.MenuItem(_("_Config"))
		menu_item.set_submenu(menu)
		menu_bar.append(menu_item)

		menu_item = gtk.MenuItem(_("_Path"))
		menu_item.connect("activate",self.config,0)
		menu.append(menu_item)

		menu_item = gtk.MenuItem(_("_Graphic"))
		menu_item.connect("activate",self.config,1)
		menu.append(menu_item)

		menu_item = gtk.MenuItem(_("_Audio"))
		menu_item.connect("activate",self.config,2)
		menu.append(menu_item)

		menu_item = gtk.MenuItem(_("_System"))
		menu_item.connect("activate",self.config,3)
		menu.append(menu_item)

		menu_item = gtk.MenuItem(_("_Other"))
		menu_item.connect("activate",self.config,4)
		menu.append(menu_item)

		menu.append(gtk.SeparatorMenuItem())

		menu_item = gtk.MenuItem(_("_Keys"))
		menu_item.connect("activate",self.keysConfig)
		menu.append(menu_item)

		#
		# INFO Menu
		#
		menu = gtk.Menu()
		menu_item = gtk.MenuItem(_("_Info"))
		menu_item.set_right_justified(gtk.TRUE) #At right
		menu_item.set_submenu(menu)
		menu_bar.append(menu_item)

		menu_item = gtk.MenuItem(_("_About"))
		menu_item.connect("activate",self.about)
		menu.append(menu_item)

		menu_item = gtk.MenuItem(_("_License"))
		menu_item.connect("activate",self.license)
		menu.append(menu_item)

		# Pack MemuBar into the Box
		box.pack_start(menu_bar,gtk.FALSE)

		#
		# Logo
		#
		container = gtk.EventBox()
		container.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("white"))
		logo = gtk.Image()
		logo.set_from_file("data/img/xgngeo.png")
		logo.set_padding(10,0)
		container.add(logo)
		box.pack_start(container)

		#
		# Statusbar
		#
		self.statusbar.push(self.context_id,self.welcomemess)
		box.pack_end(self.statusbar,gtk.FALSE)

		#Show All
		self.window.show_all()

	def check(self):
		if self.configfile.exists()[0]:
			params = self.configfile.getParams()
			#Replace default params by gngeorc's
			for key,val in params[0].items():
				self.param[key] = val

			if self.configfile.exists()[1]:
				#Replace default params by xgngeo's
				for key,val in params[1].items():
					self.paramXGngeo[key] = val
		
			self.main() #Display the main window
		else: self.welcome()

if __name__ == "__main__":
	gtk.threads_init()
	XGngeo().check()
	gtk.threads_enter()
	gtk.main()
	gtk.threads_leave()
