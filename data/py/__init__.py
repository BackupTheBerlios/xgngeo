#!/usr/bin/env python
"""
XGngeo: a frontend for Gngeo in GTK. ^_^.
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
import sys, gtk
if gtk.pygtk_version[:2]<(2,6): sys.exit("Error: PyGTK version 2.6 or more is required.")
import os, gettext
from string import capwords
from re import match
from threading import Timer
#Internal modules.
import configfile, emulator, history, rominfos

VERSION = 16
gngeoDir = os.path.expanduser("~/.gngeo")
datarootpath = os.path.join(sys.prefix,'share','xgngeo')

#Internationalization.
gettext.install("xgngeo",os.path.join(datarootpath,"locale"))

class XGngeo:
	def __init__(self):
		#Default values...
		self.tempparam = {}
		self.configwidgets = {}
		self.widgets = {}
		self.configmamenames = []
		self.romPath = None

		self.configfile = configfile.Configfile(datarootpath)
		self.gngeoParams, self.xgngeoParams = self.configfile.getDefaultParams()	
		self.emulator = emulator.Emulator(self.xgngeoParams['gngeopath'],self.gngeoParams['romrc'])
		self.history = history.History()

		#Statusbar.
		self.statusbar = gtk.Statusbar()
		self.context_id = self.statusbar.get_context_id("Info")

		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		gtk.window_set_default_icon_from_file(os.path.join(datarootpath,"img","icon.png"))
	
	def checkError(self):
		#Check for Gngeo's home directory.
		if not os.path.isdir(gngeoDir): os.mkdir(gngeoDir)

		def callback(widget,response_id):
			if response_id==gtk.RESPONSE_DELETE_EVENT: self.quit()
			else: self.destroy(None,widget,2)

		dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL,type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK)
		dialog.set_markup(_("It seems that the important path parameters are not all valid. That is normal if Gngeo configuration file hasn't been yet created. Anyway, correct values should be specified for the emulation to work. Press OK to do so..."))
		dialog.connect("response",callback)
		dialog.show_all()

	def displayfile(self,widget,filename):
		display = 1
		textbuffer = gtk.TextBuffer()
		filename = os.path.join(datarootpath,filename)

		if os.path.isfile(filename):
			file = open(filename,"r")
			textbuffer.set_text("%s" % file.read())
			file.close()
		else:
			if filename[-11:]=="LICENSE.txt":
				textbuffer.set_text(_("Error: Unable to open the file \"%s\"!\nYou can read the GNU GPL license at:\nhttp://www.gnu.org/licenses/gpl.html") % filename)
			else: display = 0

		if display:

			dialog = gtk.Dialog((filename,_("License"))[filename[-11:]=="LICENSE.txt"],flags=gtk.DIALOG_NO_SEPARATOR|gtk.DIALOG_MODAL)
			dialog.connect("destroy",self.destroy,dialog,1)

			if filename=="LICENSE.txt":
				label = gtk.Label(_("This program is released under the terms of the GNU General Public License."))
				label.set_padding(2,4)
				dialog.vbox.pack_start(label,False)

			textview = gtk.TextView(textbuffer)
			tag = textbuffer.create_tag(family="monospace",editable=False)
			textbuffer.apply_tag(tag,textbuffer.get_start_iter(),textbuffer.get_end_iter())

			scrolled_window = gtk.ScrolledWindow()
			scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
			scrolled_window.add(textview)
			scrolled_window.set_size_request(500,300)
			dialog.vbox.pack_end(scrolled_window)

			#Button at bottom..
			button = gtk.Button(stock=gtk.STOCK_CLOSE)
			button.connect("clicked",self.destroy,dialog)
			dialog.action_area.pack_end(button)

			dialog.show_all()

	def gngeoGetOutput(self):
		"""This function is embeded in a thread and perform
		some Gngeo post-execution instructions after it
		terminates."""
		#Waiting for Gngeo to hang up...
		self.emulator.romWaitingForHangingUp()

		gtk.threads_enter() #Without this, it often bugs. :p
		
		#Simple post-execution instruction.
		self.historyAdd(self.romFullName,self.romPath) #Append ROM too history.
		self.statusbar.push(self.context_id,_("ROM stopped (%s).") % self.romMameName) #Update status bar.

		#-------------------------------------------------------------------------
		# Introducing our exclusive and innovative system
		# to catch and display error returned by Gngeo, aka :
		#         `` DA XGNGEO CRAP DETECTOR " !
		# Covererd by patents 2173965, 1004076, 5867297, etc.
		#-------------------------------------------------------------------------
		# We'll check whether there was a f*ck then try to display
		# the error/warning message returned by Gngeo if it's the case.
		# We do not so when the game was stopped from XGngeo.
		if not self.gngeokilledbyme:
			output = self.emulator.romGetProcessOutput() #Raw ouput of Gngeo.
			message = "" #Nothing for start!
			#Parsing the output, line per line, looking for error...
			for line in output.split("\n"):
				for line in line.split("\r"):
					#We ignore usual messages:
					#1: ROM loading progression.
					#2 & 3: YUV driver output.
					#4: ROM driver creation message (in Gngeo 0.6.5beta).
					#5: Screenshot saving message.
					if not line.strip()=="" \
					and not match(".* [[][\-|\*]{62}[]]?",line)\
					and not match("Update sai .*",line)\
					and not match("deltaptr=(\S)* sai",line)\
					and not line[:4]=="Add "\
					and not line[:8]=="save to ":
						#The line contains a unexpected message, certainly an important, so we record it.
						message += "%s\n" % line.strip()

			if message!="": #Oh dear! There was a f*ck! Let's display the info dialog.
				dialog = gtk.MessageDialog(parent=self.window,flags=gtk.DIALOG_MODAL,type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK)
				dialog.set_markup("%s\n\n<span color='#b00'>%s</span>" % (_("Gngeo returned the following message:"),unicode(message[:-1],'iso-8859-1').replace("&","&amp;")))
				dialog.connect("response",lambda *args: dialog.destroy())
				dialog.show_all()
		#-------------------------------------------------------------------------

		#Performing some modifications on the menu.
		self.loadrom_menu_item.set_sensitive(True)
		self.history_menu_item.set_sensitive(True)
		for x in self.historyMenu.get_children(): x.set_sensitive(True)
		self.stopMenu_item.set_sensitive(False)
		self.execMenu_item.set_sensitive(True)
		for x in self.configMenu.get_children(): x.set_sensitive(True)
		gtk.threads_leave()
	
	def romLoadingInProgress(self):
		"""Graphicaly indicate the user that, although he
		see nothing, the program is actually working, trying
		to load the ROM."""
		import time
		message = _("Starting ROM (%s)") % self.romMameName
		for x in range(42):
			if not self.emulator.romRunningState(): break
			gtk.threads_enter()
			self.statusbar.push(self.context_id,("%s%s" % (message,("."*x))))
			gtk.threads_leave()
			time.sleep(0.4)

	def gngeoExec(self,widget=None):
		Timer(0,self.romLoadingInProgress).start()
				
		#Performing some modifications on the menu.
		self.loadrom_menu_item.set_sensitive(False)
		self.history_menu_item.set_sensitive(False)
		for x in self.historyMenu.get_children(): x.set_sensitive(False)
		self.stopMenu_item.set_sensitive(True)
		self.execMenu_item.set_sensitive(False)
		for x in self.configMenu.get_children(): x.set_sensitive(False)

		self.emulator.romLaunching(self.romPath)

		self.gngeokilledbyme = 0
		#Starting another thread which watch out the last one!
		Timer(0,self.gngeoGetOutput).start()

	def gngeoStop(self,widget=None):
		"""``Close you eyes and prey, Gngeo!"
		This function kills gngeo if it is alive."""
		if  self.emulator.romRunningState().isAlive():
			Timer(0,os.system,('killall -9 %s"' % self.xgngeoParams['gngeopath'].replace('"','\"'),)).start()
			self.gngeokilledbyme = 1

	def romList(self,widget):
		def setRomTemp(treeview,path,view_column):
			#Ensure that the set the right side is no more insensitive.
			if not rightside.get_property("sensitive"):
				rightside.set_sensitive(True)

			treeselection = treeview.get_selection()
			liststore,iter = treeselection.get_selected()

			availability = liststore.get_value(iter,1)
			fullname = liststore.get_value(iter,0)
			mamename = gamelist[fullname]

			#Temporary select the ROM for loading if available.
			if availability: self.romFromList,self.romFromListName = mamename,fullname
			else: self.romFromList,self.romFromListName = None,None
			open_button.set_sensitive(availability)

			#Update mame name and availability icon.
			self.mamename = mamename #The current selected mamename is exported.
			self.widgets['mamename'].set_text("<b>%s</b>" % mamename)
			self.widgets['mamename'].set_use_markup(True)
			self.avail_image.set_from_stock((gtk.STOCK_NO,gtk.STOCK_YES)[availability],gtk.ICON_SIZE_MENU)

			#Update preview image.
			if self.xgngeoParams["previewimages"]=="true":
				if os.path.isfile(os.path.join(self.xgngeoParams["previewimagedir"],"%s.png" % mamename)): self.previewImage.set_from_file(os.path.join(self.xgngeoParams["previewimagedir"],mamename+".png"))
				elif os.path.isfile(os.path.join(self.xgngeoParams["previewimagedir"],"unavailable.png")): self.previewImage.set_from_file(os.path.join(self.xgngeoParams["previewimagedir"],"unavailable.png"))

			#Update rom infos.
			if self.xgngeoParams["rominfos"]=="true" and os.path.isfile(self.xgngeoParams["rominfoxml"]):
				#Check for game informations.
				if self.romInfos.has_key(mamename):
					for x in ("desc","manufacturer","year","genre","players","rating"):
						if self.romInfos[mamename].has_key(x): 
							self.romInfosWidget[x].set_text(self.romInfos[mamename][x])
						else: self.romInfosWidget[x].set_text("--")
					if self.romInfos[mamename].has_key("size"): self.romInfosWidget["size"].set_text("%sMbit" % self.romInfos[mamename]["size"])
				else:
					for x in ("desc","manufacturer","year","genre","players","rating","size"):
						self.romInfosWidget[x].set_text("--")

			#Update specific configuration buttons.
			path = os.path.join(gngeoDir,"%s.cf" % mamename)
			if os.path.isfile(path):
				self.specconf['new'].hide()
				self.specconf['properties'].show()
				self.specconf['clear'].show()
			else:
				self.specconf['new'].show()
				self.specconf['properties'].hide()
				self.specconf['clear'].hide()

		def setRomFromList(widget):
			#Is something selected?
			if self.romFromList:
				#Setting important variables.
				self.romPath = os.path.join(self.gngeoParams['rompath'],"%s.zip" % self.romFromList) 
				self.romFullName = self.romFromListName
				self.romMameName = self.romFromList

				#Doing post-selection actions.
				self.historyAdd(self.romFullName,self.romPath) #Append it to the list.
				self.statusbar.push(self.context_id,_("ROM: \"%s\" (%s)") % (self.romFromListName,self.romFromList)) #Update Status message
				if self.xgngeoParams["autoexecrom"]=="true": self.gngeoExec() #Auto execute the ROM...
				else: self.execMenu_item.set_sensitive(True) #Activate the "Execute" button

			self.listDialog.destroy()

		def showAvailable(widget):
			liststore.clear()
			for name in gamelistNames:
				if os.path.isfile(os.path.join(self.gngeoParams["rompath"],"%s.zip" % gamelist[name])):
					#Alway put available ROMs.
					liststore.append([name,True])
					self.xgngeoParams["showavailableromsonly"]="false"
				elif not widget.get_active():
					#Put also unavailable ROMs if the box is unchecked.
					liststore.append([name,False])
			#Remember the preference.
			self.xgngeoParams["showavailableromsonly"] = ("false","true")[widget.get_active()]

		self.romFromList = None #Selected ROM.

		self.listDialog = gtk.Dialog(_("List of ROMs from your driver file."),flags=gtk.DIALOG_MODAL)
		self.listDialog.connect("destroy",self.destroy,self.listDialog,1)

		table = gtk.Table(3,3)

		label = gtk.Label(_("Double-click on its name to select a ROM, then press Open to load it if available (blue background)."))
		label.set_line_wrap(True)
		label.set_justify(gtk.JUSTIFY_CENTER)
		#PyGTK bug on 2005-07-18, avoid by explicitly giving a ``xpadding" value...
		#table.attach(label,0,2,0,1,yoptions=gtk.SHRINK,ypadding=2)
		table.attach(label,0,2,0,1,yoptions=gtk.SHRINK,xpadding=0,ypadding=2)

		#DA ROM list!
		scrolled_window = gtk.ScrolledWindow()
		scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_ALWAYS)
		scrolled_window.set_size_request(500,250) #Set scrolled window's height.
		table.attach(scrolled_window,0,2,1,2,xpadding=2,ypadding=5)

		self.emulator.scanRomInDirectory(self.gngeoParams['rompath'])
		gamelist = self.emulator.getRomFullToMame()
		gamelistNames = self.emulator.getRomFullNames()

		#The list will contain the ROM fullname and its availability.
		liststore = gtk.ListStore(str,"gboolean")
		treeview = gtk.TreeView(liststore)
		treeview.set_headers_visible(False)
		treeview.connect("row-activated",setRomTemp)

		#Columns to display data.
		tvcolumn = gtk.TreeViewColumn("Fullname")
		treeview.append_column(tvcolumn)

		#Add rows.
		for name in gamelistNames:
			if os.path.isfile(os.path.join(self.gngeoParams["rompath"],"%s.zip" % gamelist[name])):
				liststore.append([name,True])
			else: liststore.append([name,False])

		#Rendering data.
		cell = gtk.CellRendererText()
		cell.set_property("cell-background","#9cf")
		tvcolumn.pack_start(cell,True)
		tvcolumn.set_attributes(cell,text=0,cell_background_set=1)

		treeview.set_search_column(0) #Make treeview searchable.
		tvcolumn.set_sort_column_id(0) #Make columns sortable.

		scrolled_window.add_with_viewport(treeview)

		label = gtk.Label(_("Driver file supporting <b>%s</b> ROMs.") % len(gamelistNames))
		label.set_use_markup(True)
		table.attach(label,0,1,2,3,yoptions=gtk.SHRINK)

		buttonShowAvailable = gtk.CheckButton(_("Show available ROMs only."))
		buttonShowAvailable.connect("toggled",showAvailable)
		table.attach(buttonShowAvailable,1,2,2,3,yoptions=gtk.SHRINK)

		#
		# Mame name/preview image/info's/specific configuration. :P
		#
		rightside = gtk.VBox(spacing=3)

		noteisthere = 0
		# Use add-ons if activated and valid.
		if((self.xgngeoParams["previewimages"]=="true" and os.path.isdir(self.xgngeoParams["previewimagedir"]))\
		or (self.xgngeoParams["rominfos"]=="true" and os.path.isfile(self.xgngeoParams["rominfoxml"]))):
			notebook = gtk.Notebook()
			rightside.pack_start(notebook,padding=4)
			noteisthere = 1

			#Preview images.
			if(self.xgngeoParams["previewimages"]=="true" and os.path.isdir(self.xgngeoParams["previewimagedir"])):
				self.previewImage = gtk.Image()
				self.previewImage.set_padding(3,3)
				path = os.path.join(self.xgngeoParams["previewimagedir"],"unavailable.png")
				if os.path.isfile(path): self.previewImage.set_from_file(path) #Display the ``unavailable" image by default.
				container = gtk.EventBox()
				container.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("black"))
				container.add(self.previewImage)
				notebook.append_page(container,gtk.Label(_("Preview image")))

			#ROM infos.
			if(self.xgngeoParams["rominfos"]=="true" and os.path.isfile(self.xgngeoParams["rominfoxml"])):
				self.romInfos = rominfos.Rominfos(path=self.xgngeoParams["rominfoxml"]).getDict()
				self.romInfosWidget = {}

				box2 = gtk.VBox()

				#Description.
				self.romInfosWidget["desc"] = gtk.TextBuffer()
				self.romInfosWidget["desc"].set_text("--")
				textview = gtk.TextView(self.romInfosWidget["desc"])
				textview.set_editable(0)
				textview.set_wrap_mode(gtk.WRAP_WORD)
				scrolled_window = gtk.ScrolledWindow()
				scrolled_window.set_policy(gtk.POLICY_NEVER,gtk.POLICY_ALWAYS)
				box2.set_size_request(220,-1) #Set width.
				scrolled_window.add(textview)
				frame = gtk.Frame(_("Description:"))
				frame.add(scrolled_window)
				box2.pack_start(frame)

				#Other infos.
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

				box2.pack_start(table2,False)

				notebook.append_page(box2,gtk.Label(_("Informations")))

		box2 = gtk.HBox()
		self.widgets['mamename'] = gtk.Label("<b>-----</b>")
		self.widgets['mamename'].set_use_markup(True)
		box2.pack_start(self.widgets['mamename'])
		self.avail_image = gtk.Image()
		self.avail_image.set_from_stock(gtk.STOCK_NO,gtk.ICON_SIZE_MENU)
		box2.pack_end(self.avail_image,False)
		rightside.pack_start(box2,not noteisthere)

		#ROM-specific configuration.
		def deleteRomConf(*args):
			os.remove(os.path.join(gngeoDir,"%s.cf" % self.mamename))
			#Update buttons.
			self.specconf['new'].show()
			self.specconf['properties'].hide()
			self.specconf['clear'].hide()

		self.specconf = {}
		frame = gtk.Frame(_("Specific configuration:"))
		frame.set_label_align(0.5,0.5) #Center is better. :p
		box2 = (gtk.VBox(),gtk.HBox())[noteisthere]

		self.specconf['new'] = gtk.Button(stock=gtk.STOCK_NEW)
		self.specconf['new'].connect("clicked",self.config,1,0,1)
		box2.pack_start(self.specconf['new'])

		self.specconf['properties'] = gtk.Button(stock=gtk.STOCK_EDIT)
		self.specconf['properties'].connect("clicked",self.config,1,0,1)
		box2.pack_start(self.specconf['properties'])

		self.specconf['clear'] = gtk.Button(stock=gtk.STOCK_CLEAR)
		self.specconf['clear'].connect("clicked",deleteRomConf)
		box2.pack_start(self.specconf['clear'])

		frame.add(box2)
		rightside.pack_end(frame,not noteisthere)

		table.attach(rightside,2,3,0,3,gtk.SHRINK)
		self.listDialog.vbox.pack_start(table)
		rightside.set_sensitive(False)

		#Buttons at bottom.
		open_button = gtk.Button(stock=gtk.STOCK_OPEN)
		open_button.set_sensitive(False)
		open_button.connect("clicked",setRomFromList)
		self.listDialog.action_area.pack_start(open_button)

		button = gtk.Button(stock=gtk.STOCK_CANCEL)
		button.connect("clicked",self.destroy,self.listDialog)
		self.listDialog.action_area.pack_start(button)

		self.listDialog.show_all()
		#Let's hide ourselves!
		self.specconf['properties'].hide()
		self.specconf['clear'].hide()
		if self.xgngeoParams["showavailableromsonly"]=="true": buttonShowAvailable.set_active(True) #Activate button.

	def fileSelect(self,widget,title,folder,arg,dirselect=0):
		dialog = gtk.FileChooserDialog(title,action=(gtk.FILE_CHOOSER_ACTION_OPEN,gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)[dirselect],buttons=(gtk.STOCK_OPEN, gtk.RESPONSE_OK,gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL))
		dialog.set_current_folder((os.path.dirname(folder),folder)[os.path.isdir(folder)])
		dialog.connect("response",self.setPath,arg)

		if arg=="rom":
			filter = gtk.FileFilter()
			filter.set_name(_("ROM archive"))
			filter.add_pattern("*.zip")
			dialog.add_filter(filter)
			filter = gtk.FileFilter()
			filter.set_name(_("All files"))
			filter.add_pattern("*")
			dialog.add_filter(filter)

		dialog.run()

	def setRomFromHistory(self,widget,fullname,path):
		if os.path.exists(path): #ROM exists on file system, continuing...
			#Setting important variables.
			self.romPath = path
			self.romFullName = fullname
			if path[-4:]==".zip": self.romMameName = os.path.basename(path)[:-4]
			else: self.romMameName = os.path.basename(path)
	
			#Doing post-selection actions.
			self.historyAdd(self.romFullName,self.romPath) #Appending it to the list.
			self.statusbar.push(self.context_id,(_("ROM: \"%s\" (%s)") % (self.romFullName,self.romMameName))) #Updating status message
			if self.xgngeoParams["autoexecrom"]=="true": self.gngeoExec() #Auto execute the ROM...
			else: self.execMenu_item.set_sensitive(True) #Activating the "Execute" button
		else:
			#ROM not found: no loading but warning message and ROM History menu rebuilding.
			dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL,type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK)
			dialog.set_markup(_("Cannot continue: the ROM you wanted to load was not found on the file system!"))
			dialog.connect("response",lambda *args: dialog.destroy())
			dialog.show_all()
			self.historyMenuGeneration()

	def setPath(self,dialog,response,data):
		"""Get/set path of various things from the path of the file chooser."""
		if response==gtk.RESPONSE_OK:
			if data=="rom": #Set ROM from the file chooser.
				path = dialog.get_filename()
				#Does it exist?
				if os.path.isfile(path):
					#Setting important variables.
					self.romPath = path
					if path[-4:]==".zip": self.romMameName = os.path.basename(path)[:-4]
					else: self.romMameName = os.path.basename(path)

					#Trying to resolve ROM full name.
					romrc = romrcfile.Romrc()
					romrc.parsing(self.gngeoParams['romrc'])
					dict = romrc.getRomMameToFull()
					if self.romMameName in dict.keys(): self.romFullName = dict[self.romMameName]
					else: self.romFullName = _("Unknow ROM")

					#Doing post-selection actions.
					#Append the ROM to history list.
					self.historyAdd((self.romFullName,"%s (%s)" % (self.romFullName,self.romMameName))[self.romFullName==_("Unknow ROM")],self.romPath)
					self.statusbar.push(self.context_id,_("ROM: \"%s\" (%s)" % (self.romFullName,self.romMameName))) #Update Status message
					if self.xgngeoParams["autoexecrom"]=="true": self.gngeoExec() #Auto execute the ROM...
					else: self.execMenu_item.set_sensitive(True) #Activate the ``Execute" button.

				else: self.statusbar.push(self.context_id,"Error: file doesn't exist!")
			else:
				path = dialog.get_filename() #Get the path.
				self.configwidgets[data].set_text(path)

		dialog.destroy()

	def historyMenuGeneration(self):
		"""(Re)Generating history menu from the recently loaded ROM history file."""
		for x in self.history.getList(size=int(self.xgngeoParams["historysize"])):
			if x[2]: menu_item2 = gtk.MenuItem(x[0])
			else:
				#Adding a "warning" icon when the ROM is not available on the file system.
				menu_item2 = gtk.ImageMenuItem(x[0])
				image = gtk.Image()
				image.set_from_stock(gtk.STOCK_DIALOG_WARNING,gtk.ICON_SIZE_MENU)
				menu_item2.set_image(image)
			menu_item2.connect("activate",self.setRomFromHistory,x[0],x[1])
			self.historyMenu.append(menu_item2)

	def historyAdd(self,fullname,path):
		#Update history file and get new list...
		list = self.history.addRom(fullname,path,size=int(self.xgngeoParams["historysize"]))

		#Recreate the history menu.
		for x in self.historyMenu.get_children()[1:]: self.historyMenu.remove(x) #Remove old entries.
		for x in list: #Put the new ones.
			menu_item = gtk.MenuItem(x[0])
			menu_item.connect("activate",self.setRomFromHistory,x[0],x[1])
			self.historyMenu.append(menu_item)

		self.historyMenu.show_all()

	def about(self,widget):
		dialog = gtk.Dialog(_("About XGngeo"),flags=gtk.DIALOG_NO_SEPARATOR|gtk.DIALOG_MODAL)
		dialog.connect("destroy",self.destroy,dialog,1)
		dialog.set_border_width(5)
		dialog.vbox.set_spacing(4)

		label = gtk.Label("<span color='#008'><b>%s</b>\n%s\n%s</span>" % (_("XGngeo: a frontend for Gngeo. :p"),_("Version %i.") % VERSION,_("Running Gngeo version %s.") % self.emulator.getGngeoVersion()[1]))
		label.set_justify(gtk.JUSTIFY_CENTER)
		label.set_use_markup(True)
		dialog.vbox.pack_start(label)

		label = gtk.Label("Copyleft 2003, 2004, 2005, 2006 Choplair-network.")
		dialog.vbox.pack_start(label)
		label = gtk.Label(_("This program is released under the terms of the GNU General Public License."))
		label.set_line_wrap(True)
		dialog.vbox.pack_start(label)

		frame = gtk.Frame(_("Credits"))
		box = gtk.HBox()
		frame.add(box)

		logo = gtk.Image()
		logo.set_from_file(os.path.join(datarootpath,"img/chprod.png"))
		box.pack_start(logo,False)

		box2 = gtk.VBox(spacing=4)
		box2.set_border_width(4)
		label = gtk.Label(_("Main coder: Choplair.\nAssisted by: Pachilor."))
		label.set_justify(gtk.JUSTIFY_CENTER)
		label.set_line_wrap(True)
		box2.pack_start(label)
		label = gtk.Label("<i>http://www.choplair.org/</i>")
		label.set_use_markup(True)
		box2.pack_start(label)
		box.pack_end(box2)

		dialog.vbox.pack_start(frame)

		#Button at bottom..
		button = gtk.Button(stock=gtk.STOCK_CLOSE)
		button.connect("clicked",self.destroy,dialog,1)
		dialog.action_area.pack_end(button)

		dialog.show_all()

	def config(self,widget=None,type=0,firstrun=0,romspecific=0):
		if romspecific:
			if self.mamename not in self.configmamenames:
				self.configmamenames.append(self.mamename)
			else:	return None #Exiting.

		def setPathIcon(widget,image,dir=0,special=None):
			"""We check whether the path written in the text entry
			is an existing file or directory, and change the icon
			in consequence.
			Some other special conditions for the icon to change
			exist. As Other things than the icon which migth be
			also modified."""
			path = widget.get_text()

			if not special:
				if (dir and os.path.isdir(path)) or os.path.isfile(path): stock = 1
				else: stock = 0

			elif special=="rompath":
				#Check for BIOS files.
				if not (os.path.isfile("%s/neo-geo.rom" % path) or os.path.isfile("%s/sp-s2.sp1" % path))\
				or not (os.path.isfile("%s/ng-sfix.rom" % path) or os.path.isfile("%s/sfix.sfx" % path))\
				or not (os.path.isfile("%s/ng-lo.rom" % path) or os.path.isfile("%s/000-lo.lo" % path)):
					stock = 0; txt = "<span color='red'>%s</span>" % _("No BIOS.")
				else: stock = 1; txt = "<span color='darkgreen'>%s</span>" % _("BIOS OK.")
				bios_label.set_text(txt)
				bios_label.set_use_markup(True)

			elif special=="gngeopath":
				version = self.emulator.getGngeoVersion(path)
				if version:
					#Refusing obsolete Gngeo version.
					if version[0][1:3]<(6,11): stock = 0; color = "red"
					else: stock = 1; color = "#008"

					gngeoversion_label.set_text("<span color='%s'>v%s</span> " % (color,version[1]))
					gngeoversion_label.set_use_markup(True)
					gngeoversion_label.show()

				else:
					stock = 0;
					gngeoversion_label.hide()

			image.set_from_stock((gtk.STOCK_NO,gtk.STOCK_YES)[stock],gtk.ICON_SIZE_MENU)

		self.configDialog = gtk.Dialog(flags=gtk.DIALOG_MODAL)

		if firstrun: self.configDialog.connect("delete_event",self.quit)
		elif romspecific: self.configDialog.connect("destroy",self.destroy,self.configDialog,4,self.mamename)
		else: self.configDialog.connect("destroy",self.destroy,self.configDialog,5)

		if type==0:
			#
			# Important path configuration.
			#
			self.configDialog.set_title(_("Important path configuration"))
			box = gtk.VBox(spacing=5) #The box. :p
			box.set_border_width(4)
			self.imppathicons = []

			box.pack_start(gtk.Label(_("These paths must be valid for a working emulation.")))

			frame = gtk.Frame(_("Main ROM and BIOS directory:"))
			box2 = gtk.HBox()

			self.imppathicons.append(gtk.Image())
			box2.pack_start(self.imppathicons[0],False,padding=3)
			bios_label = gtk.Label()
			box2.pack_start(bios_label,False,padding=3)
			self.configwidgets['rompath'] = gtk.Entry()
			self.configwidgets['rompath'].connect("changed",setPathIcon,self.imppathicons[0],1,"rompath")
			self.configwidgets['rompath'].set_text(self.gngeoParams["rompath"])
			box2.pack_start(self.configwidgets['rompath'])
			button = gtk.Button()
			image = gtk.Image()
			image.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_MENU)
			button.add(image)
			button.connect("clicked",self.fileSelect,_("Select the main ROMs and BIOS directory."),self.configwidgets['rompath'].get_text(),"rompath",1)
			box2.pack_end(button,False)
			frame.add(box2)
			box.pack_start(frame)

			frame = gtk.Frame(_('ROM driver file ("romrc"):'))
			box2 = gtk.HBox()

			self.imppathicons.append(gtk.Image())
			box2.pack_start(self.imppathicons[1],False,padding=3)
			self.configwidgets['romrc'] = gtk.Entry()
			self.configwidgets['romrc'].connect("changed",setPathIcon,self.imppathicons[1])
			self.configwidgets['romrc'].set_text(self.gngeoParams["romrc"])
			box2.pack_start(self.configwidgets['romrc'])
			button = gtk.Button()
			image = gtk.Image()
			image.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_MENU)
			button.add(image)
			button.connect("clicked",self.fileSelect,_("Select the ROM driver file."),self.configwidgets['romrc'].get_text(),"romrc")
			box2.pack_end(button,False)
			frame.add(box2)
			box.pack_start(frame)

			frame = gtk.Frame(_("Gngeo executable:"))
			box2 = gtk.HBox()

			self.imppathicons.append(gtk.Image())
			box2.pack_start(self.imppathicons[2],False,padding=3)
			gngeoversion_label = gtk.Label()
			box2.pack_start(gngeoversion_label,False,padding=3)
			self.configwidgets['gngeopath'] = gtk.Entry()
			self.configwidgets['gngeopath'].connect("changed",setPathIcon,self.imppathicons[2],0,"gngeopath")
			self.configwidgets['gngeopath'].set_text(self.xgngeoParams["gngeopath"])
			box2.pack_start(self.configwidgets['gngeopath'])
			button = gtk.Button()
			image = gtk.Image()
			image.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_MENU)
			button.add(image)
			button.connect("clicked",self.fileSelect,_("Select the Gngeo executable."),self.configwidgets['gngeopath'].get_text(),"gngeopath")
			box2.pack_end(button,False)
			frame.add(box2)
			box.pack_start(frame)

			self.configDialog.vbox.pack_start(box)

		elif type in (1,2,3,4):
			#By default the parameters of these sections will be set with the values of the previously saved global emulation options.
			temp_param = {}
			for key,val in self.gngeoParams.items(): temp_param[key] = val
			if romspecific:
				#Replace global params by (hypotheticaly) previously saved specific rom ones.
				for key,val in self.configfile.getParams(self.mamename).items():
					temp_param[key] = val

			#
			# Global emulation configuration.
			#
			if not romspecific: self.configDialog.set_title(_("Global emulation configuration."))
			else: self.configDialog.set_title(_("Specific emulation options for \"%s\".") % self.mamename)
			notebook = gtk.Notebook()

			#
			# GRAPHIC section.
			#
			box = gtk.VBox(spacing=4) #The Box. :p
			box.set_border_width(4)
			notebook.append_page(box,gtk.Label(_("Graphic")))

			table = gtk.Table(2,3)

			#Fullscreen.
			self.configwidgets['fullscreen'] = gtk.CheckButton(_("Fullscreen"))
			if temp_param["fullscreen"]=="true": self.configwidgets['fullscreen'].set_active(1)
			table.attach(self.configwidgets['fullscreen'],0,1,0,1)
			#Interpolation.
			self.configwidgets['interpolation'] = gtk.CheckButton(_("Interpolation"))
			if temp_param["interpolation"]=="true": self.configwidgets['interpolation'].set_active(1)
			table.attach(self.configwidgets['interpolation'],0,1,1,2)
			#Show FPS.
			self.configwidgets['showfps'] = gtk.CheckButton(_("Show FPS"))
			if temp_param["showfps"]=="true": self.configwidgets['showfps'].set_active(1)
			table.attach(self.configwidgets['showfps'],1,2,0,1)
			#Auto Frameskip.
			self.configwidgets['autoframeskip'] = gtk.CheckButton(_("Auto Frameskip"))
			if temp_param["autoframeskip"]=="true": self.configwidgets['autoframeskip'].set_active(1)
			table.attach(self.configwidgets['autoframeskip'],1,2,1,2)

			#Scale.
			adjustment = gtk.Adjustment(float(temp_param["scale"]),1,5,1)
			frame = gtk.Frame(_("Scale:"))
			frame.set_label_align(0.5,0.5)
			self.configwidgets['scale'] = gtk.HScale(adjustment)
			self.configwidgets['scale'].set_value_pos(gtk.POS_TOP)
			self.configwidgets['scale'].set_digits(0)
			frame.add(self.configwidgets['scale'])
			table.attach(frame,2,3,0,2)

			#320x224 window size.
			self.configwidgets['screen320'] = gtk.CheckButton(_("Larger screen (windowed mode)"))
			if temp_param["screen320"]=="true": self.configwidgets['screen320'].set_active(True)
			table.attach(self.configwidgets['screen320'],1,3,2,3)

			#Raster effect.
			self.configwidgets['raster'] = gtk.CheckButton(_("Raster effect"))
			if temp_param["raster"]=="true": self.configwidgets['raster'].set_active(True)
			table.attach(self.configwidgets['raster'],0,1,2,3)

			box.pack_start(table)

			# BLITTER
			frame = gtk.Frame(_("Blitter:"))

			#Translation of known blitter fullnames.
			i18n_dict = {
				"soft":_("Software blitter"),
				"opengl":_("OpenGL blitter"),
				"yuv":_("YUV blitter (YV12)")}

			pipe = os.popen('"%s" --blitter help' % self.xgngeoParams['gngeopath'].replace('"','\"'))
			lines = pipe.readlines() #Get Gngeo's available blitter.
			pipe.close()

			def bouyaka(*args):
				"""Overlay does not support effect. So, when this blitter is selected, we
				set the effect to ``none" and prevent it from being changed by user."""
				if self.combo_params['blitter'][self.configwidgets['blitter'].get_active()]=="yuv":
					temp_param['effect'] = "none" #Changing param.
					self.configwidgets['effect'].set_active(0) #Changing widget.
					self.configwidgets['effect'].set_sensitive(False) #Effect cannot be changed any more.
				else:	self.configwidgets['effect'].set_sensitive(True) #Effect can be changed again.

			self.combo_params = {}

			self.configwidgets['blitter'] = gtk.combo_box_new_text()
			i=0; list = []
			for line in lines:
				plop = match("(\S*)\s*:(.*)",line) #Syntax is `REF : FULLNAME'.
				if plop:
					ref,fullname = plop.group(1).strip(),plop.group(2).strip()
					self.configwidgets['blitter'].append_text((fullname,i18n_dict[ref])[i18n_dict.has_key(ref)])
					list.append(ref)
					#Set active the last selection.
					if ref==temp_param["blitter"]: self.configwidgets['blitter'].set_active(i)
					i+=1

			self.combo_params['blitter'] = list
			frame.add(self.configwidgets['blitter'])
			box.pack_start(frame)

			# EFFECT
			frame = gtk.Frame(_("Effect:"))

			#Translation of known effect fullnames.
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

			pipe = os.popen('"%s" --effect help' % self.xgngeoParams['gngeopath'].replace('"','\"'))
			lines = pipe.readlines() #Get Gngeo's available blitters.
			pipe.close()

			self.configwidgets['effect'] = gtk.combo_box_new_text()
			self.configwidgets['effect'].set_wrap_width(2)
			i=0; list = []
			for line in lines:
				plop = match("(\S*)\s*:(.*)",line) #Syntax is "REF : FULLNAME"
				if plop:
					ref,fullname = plop.group(1).strip(),plop.group(2).strip()
					self.configwidgets['effect'].append_text((fullname,i18n_dict[ref])[i18n_dict.has_key(ref)])
					list.append(ref)
					#Set active the last selection.
					if ref==temp_param["effect"]: self.configwidgets['effect'].set_active(i)
					i+=1

			self.combo_params['effect'] = list
			frame.add(self.configwidgets['effect'])
			box.pack_start(frame)

			#Tell to perform special actions over effect widget according to the selected blitter.
			bouyaka()
			self.configwidgets['blitter'].connect("changed",bouyaka)

			#
			# AUDIO / JOYSTICK section.
			#
			box = gtk.VBox(spacing=4) #The Box.
			box.set_border_width(4)
			notebook.append_page(box,gtk.Label(_("Audio / Joystick")))

			frame = gtk.Frame(_("Audio"))
			box2 = gtk.VBox()

			def bouyaka(widget,target):
				"""Set widget sensitive state according to another
				widget activation state."""
				target.set_sensitive(widget.get_active())

			self.configwidgets['sound'] = gtk.CheckButton(_("Enable sound"))
			box2.pack_start(self.configwidgets['sound'])

			#Sample rate
			box3 = gtk.HBox()
			box2.pack_end(box3)
			label = gtk.Label(_("Sample rate:"))
			box3.pack_start(label)

			self.configwidgets['samplerate'] = gtk.combo_box_new_text()
			i=0
			self.combo_params['samplerate'] = ["8192","11025","22050","32000","44100","48000"]
			for val in self.combo_params['samplerate']:
				self.configwidgets['samplerate'].append_text("%sHz" % val)
				#Set active the last selection
				if val==temp_param["samplerate"]: self.configwidgets['samplerate'].set_active(i)
				i+=1
			box3.pack_start(self.configwidgets['samplerate'])
			#Bouyaka!
			self.configwidgets['sound'].connect("toggled",bouyaka,box3)
			if temp_param['sound']=='true': self.configwidgets['sound'].set_active(1)
			else: bouyaka(self.configwidgets['sound'],box3)

			frame.add(box2)
			box.pack_start(frame)

			frame = gtk.Frame(_("Joystick"))
			box2 = gtk.VBox()

			self.configwidgets['joystick'] = gtk.CheckButton(_("Enable joystick support"))
			box2.pack_start(self.configwidgets['joystick'])

			table = gtk.Table(2,2)
			box2.pack_end(table)

			label = gtk.Label(_("Player 1 device:"))
			table.attach(label,0,1,0,1)
			self.configwidgets['p1joydev'] = gtk.combo_box_new_text()
			for x in range(4): self.configwidgets['p1joydev'].append_text("/dev/js%s" % x)
			self.configwidgets['p1joydev'].set_active(int(temp_param["p1joydev"])) #Set active the last selection
			table.attach(self.configwidgets['p1joydev'],1,2,0,1)

			label = gtk.Label(_("Player 2 device:"))
			table.attach(label,0,1,1,2)
			self.configwidgets['p2joydev'] = gtk.combo_box_new_text()
			for x in range(4): self.configwidgets['p2joydev'].append_text("/dev/js%s" % x)
			self.configwidgets['p2joydev'].set_active(int(temp_param["p2joydev"])) #Set active the last selection
			table.attach(self.configwidgets['p2joydev'],1,2,1,2)

			#Bouyaka!
			self.configwidgets['joystick'].connect("toggled",bouyaka,table)
			if temp_param['joystick']=='true': self.configwidgets['joystick'].set_active(1)
			else: bouyaka(self.configwidgets['joystick'],table)

			frame.add(box2)
			box.pack_start(frame)

			#
			# KEYBOARD section.
			#
			self.toggled = None

			# Key order : A,B,C,D,START,COIN,UP,DOWN,LEFT,RIGHT
			key_list = ["A","B","C","D","START","COIN","UP","DOWN","LEFT","RIGHT"]

			# The Gngeo compliant keymap (all in lowercase)!
			compliant_KeyMap = {
				"backspace":8, "tab":9, "return":13, "pause":19, "space":32, "exclam":33, "quotedbl":34, "dollar":36, "ampersand":38, "apostrophe":39, "parenleft":40, "parenright":41, "comma":44, "minus":45,
				"colon":58, "semicolon":59,"less":60, "equal":61, "asciicircum":94, "underscore":95, "a":97, "b":98, "c":99, "d":100, "e":101, "f":102, "g":103, "h":104, "i":105, "j":106, "k":107, "l":108,
				"m":109, "n":110, "o":111, "p":112, "q":113, "r":114, "s":115, "t":116, "u":117, "v":118, "w":119, "x":120, "y":121, "z":122, "delete":127, "twosuperior":178, "agrave":224, "ccedilla":231,
				"egrave":232, "eacute":233, "ugrave":249, "kp_0":256, "kp_1":257, "kp_2":258, "kp_3":259, "kp_4":260, "kp_5":261, "kp_6":262, "kp_home":263, "kp_7":263, "kp_up":264, "kp_8":264, "kp_9":265,
				"kp_decimal":266, "kp_divide":267, "kp_multiply":268, "kp_subtract":269, "kp_add":270, "kp_enter":271, "up":273, "down":274, "right":275, "left":276, "insert":277, "home":278, "end":279,
				"page_up":280, "page_down":281, "num_lock":300, "caps_lock":301, "scroll_lock":302, "shift_r":303, "shift_l":304, "control_r":305, "control_l":306, "super_l":311, "super_r":312, "print":316}
			#Reverse mode.
			compliant_KeyMap_reverse = {
				8:"backspace", 9:"tab", 13:"return", 19:"pause", 32:"space", 33:"exclam", 34:"quotedbl", 36:"dollar", 38:"ampersand", 39:"apostrophe", 40:"parenleft", 41:"parenright", 44:"comma", 45:"minus",
				58:"colon", 59:"semicolon",60:"less", 61:"equal", 94:"asciicircum", 95:"underscore", 97:"a", 98:"b", 99:"c", 100:"d", 101:"e", 102:"f", 103:"g", 104:"h", 105:"i", 106:"j", 107:"k", 108:"l",
				109:"m", 110:"n", 111:"o", 112:"p", 113:"q", 114:"r", 115:"s", 116:"t", 117:"u", 118:"v", 119:"w", 120:"x", 121:"y", 122:"z", 127:"delete", 178:"twosuperior", 224:"agrave", 231:"ccedilla",
				232:"egrave", 233:"eacute", 249:"ugrave", 256:"kp_0", 257:"kp_1", 258:"kp_2", 259:"kp_3", 260:"kp_4", 261:"kp_5", 262:"kp_6", 263:"kp_home", 263:"kp_7", 264:"kp_up", 264:"kp_8", 265:"kp_9",
				266:"kp_decimal", 267:"kp_divide", 268:"kp_multiply", 269:"kp_subtract", 270:"kp_add", 271:"kp_enter", 273:"up", 274:"down", 275:"right", 276:"left", 277:"insert", 278:"home", 279:"end",
				280:"page_up", 281:"page_down", 300:"num_lock", 301:"caps_lock", 302:"scroll_lock", 303:"shift_r", 304:"shift_l", 305:"control_r", 306:"control_l", 311:"super_l", 312:"super_r", 316:"print"}

			def getPressed(widget,event,key_pos,secondplayer=0):
				if widget.get_active() and event.keyval: #Only when widget is active
					key_val = gtk.gdk.keyval_to_lower(event.keyval) #Get the value (lower only)

					# GTK's keys of XGngeo are not same as SDL's used by Gngeo. T_T
					# So, a Gngeo compatible key-value is given according to its GTK's name (set in lowercase).
					key_name = gtk.gdk.keyval_name(key_val).lower()

					if key_name in compliant_KeyMap.keys():
						if secondplayer: self.p2key_int_vals[key_pos] = compliant_KeyMap[key_name]
						else: self.p1key_int_vals[key_pos] = compliant_KeyMap[key_name]

						#Put the key name (in an elegant form :p) as button label.
						widget.set_label(capwords(key_name.replace("_"," ")))
						if not key_name in ("return","space"): widget.clicked()

			def toggled(widget):
				if self.toggled and self.toggled!=widget:
					if self.toggled.get_active(): self.toggled.set_active(False)
				self.toggled = widget

			def radioToggled(widget,data):
				if data: #Show P2 key and hide P1's
					for x in p2keywidgets: x.show()
					for x in p1keywidgets: x.hide()
				else: #Show P1 key and hide P2's
					for x in p1keywidgets: x.show()
					for x in p2keywidgets: x.hide()

			box = gtk.VBox(spacing=4) #The box. :p
			box.set_border_width(4)
			notebook.append_page(box,gtk.Label(_("Controls")))

			label = gtk.Label(_("To modify a key, click the button then push your new key.\nThis configuration is only for keyboard."))
			label.set_justify(gtk.JUSTIFY_CENTER)
			label.set_line_wrap(True)
			box.pack_start(label)

			table = gtk.Table(4,6,True) #The sweet table O_o;;

			#Player's keyboard selection
			frame = gtk.Frame(_("Controller:"))
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

			if len(temp_param["p1key"].split(","))==len(key_list):
				#Given values seems to be okay.
				plop = temp_param["p1key"]
			else:	#There's a crap, let's use default key values.
				plop = self.configfile.getDefaultParams()[0]["p1key"]
			self.p1key_int_vals = plop.split(",")

			p1key_names = []
			#Display the names of known key values.
			for x in self.p1key_int_vals:
				if int(x) in compliant_KeyMap_reverse.keys(): p1key_names.append(capwords(compliant_KeyMap_reverse[int(x)].replace("_"," ")))
				else: p1key_names.append(x)

			p1keywidgets = []; i=0
			for x in p1key_names:
				#Generate P1key's button.
				p1keywidgets.append(gtk.ToggleButton(x))
				p1keywidgets[i].connect("toggled",toggled)
				p1keywidgets[i].connect("key_press_event",getPressed,i)
				p1keywidgets[i].set_use_underline(False)
				p1keywidgets[i].set_size_request(40,-1)
				i+=1

			if len(temp_param["p2key"].split(","))==len(key_list):
				#Given values seems to be okay.
				plop = temp_param["p2key"]
			else:	#There's a crap, let's use default key values.
				plop = self.configfile.getDefaultParams()[0]["p2key"]
			self.p2key_int_vals = plop.split(",")

			p2key_names = []
			#Display the names of known key values.
			for x in self.p2key_int_vals:
				if int(x) in compliant_KeyMap_reverse.keys(): p2key_names.append(capwords(compliant_KeyMap_reverse[int(x)].replace("_"," ")))
				else: p2key_names.append(x)

			p2keywidgets = []; i=0
			for x in p2key_names:
				#Generate P2key's button
				p2keywidgets.append(gtk.ToggleButton(x))	
				p2keywidgets[i].connect("toggled",toggled)
				p2keywidgets[i].connect("key_press_event",getPressed,i,1)
				p2keywidgets[i].set_use_underline(False)
				p2keywidgets[i].set_size_request(40,-1)

				#Generate key's image
				image = gtk.Image()
				image.set_from_file(os.path.join(datarootpath,"img/key_%s.png" % key_list[i]))

				box2 = gtk.HBox() #A box...
				box2.pack_start(p1keywidgets[i]) #with P1 key...
				box2.pack_start(p2keywidgets[i]) #and P2 key :p

				#Put them in table
				if i<6:
					table.attach(image,i,i+1,0,1)
					table.attach(box2,i,i+1,1,2)
				else:
					table.attach(image,i-4,i-3,2,3)
					table.attach(box2,i-4,i-3,3,4)
				i+=1

			box.pack_start(table)

			#
			# SYSTEM section
			#
			box = gtk.VBox(spacing=4) #The box :p
			box.set_border_width(4)
			notebook.append_page(box,gtk.Label(_("System")))

			#System
			frame2 = gtk.Frame(_("Neo Geo BIOS type:"))
			box2 = gtk.HBox()
			self.configwidgets['system_arcade'] = gtk.RadioButton(None,_("Arcade"))
			box2.pack_start(self.configwidgets['system_arcade'])
			self.configwidgets['system_home'] = gtk.RadioButton(self.configwidgets['system_arcade'],_("Home"))
			box2.pack_start(self.configwidgets['system_home'])
			radio = gtk.RadioButton(self.configwidgets['system_arcade'],_("Universal"))
			box2.pack_start(radio)
			
			if temp_param["system"]=="arcade": self.configwidgets['system_arcade'].set_active(1)
			elif temp_param["system"]=="home": self.configwidgets['system_home'].set_active(1)
			elif temp_param["system"]=="unibios": radio.set_active(1)
			
			frame2.add(box2)
			box.pack_start(frame2)

			#Country
			frame2 = gtk.Frame(_("Country:"))

			table = gtk.Table(3,2)
			self.configwidgets['country_japan'] = gtk.RadioButton(None,_("Japan"))
			table.attach(self.configwidgets['country_japan'],0,1,0,1)
			image = gtk.Image()
			image.set_from_file(os.path.join(datarootpath,"img/japan.png"))
			table.attach(image,0,1,1,2)

			self.configwidgets['country_usa'] = gtk.RadioButton(self.configwidgets['country_japan'],_("USA"))
			table.attach(self.configwidgets['country_usa'],1,2,0,1)
			image = gtk.Image()
			image.set_from_file(os.path.join(datarootpath,"img/usa.png"))
			table.attach(image,1,2,1,2)

			radio = gtk.RadioButton(self.configwidgets['country_japan'],_("Europe"))
			table.attach(radio,2,3,0,1)
			image = gtk.Image()
			image.set_from_file(os.path.join(datarootpath,"img/europe.png"))
			table.attach(image,2,3,1,2)
			
			if temp_param["country"]=="japan": self.configwidgets['country_japan'].set_active(1)
			elif temp_param["country"]=="usa": self.configwidgets['country_usa'].set_active(1)
			elif temp_param["country"]=="europe": radio.set_active(1)
			
			frame2.add(table)
			box.pack_start(frame2)

			self.configDialog.vbox.pack_start(notebook) #Packing the Notebook

		elif type==5:
			#
			# Other things configuration.
			#
			self.configDialog.set_title(_("Other things configuration"))
			table = gtk.Table(4,2) #The box :p
			table.set_col_spacings(6)
			table.set_border_width(2)

			frame = gtk.Frame(_("Path to libGL.so (optional):"))
			box2 = gtk.HBox()
			image = gtk.Image()
			box2.pack_start(image,False,padding=3)
			self.configwidgets['libglpath'] = gtk.Entry()
			self.configwidgets['libglpath'].connect("changed",setPathIcon,image)
			self.configwidgets['libglpath'].set_text(self.gngeoParams["libglpath"])
			box2.pack_start(self.configwidgets['libglpath'])
			setPathIcon(self.configwidgets['libglpath'],image)
			button = gtk.Button()
			image = gtk.Image()
			image.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_MENU)
			button.add(image)
			button.connect("clicked",self.fileSelect,_('Select the "%s" file.') % "libGL.so",self.configwidgets['libglpath'].get_text(),"libglpath")
			box2.pack_end(button,False)
			frame.add(box2)
			table.attach(frame,0,1,0,1)

			#Bouyaka!
			def bouyaka(widget,*targets):
				"""Set list size widgets sensitive state according
				to answer mode widget selected param."""
				for x in targets: x.set_sensitive(widget.get_active())

			frame = gtk.Frame(_("Preview image directory (optional):"))
			box2 = gtk.HBox()
			self.configwidgets['previewimages'] = gtk.CheckButton()
			box2.pack_start(self.configwidgets['previewimages'],False)
			image = gtk.Image()
			box2.pack_start(image,False,padding=3)
			self.configwidgets['previewimagedir'] = gtk.Entry()
			self.configwidgets['previewimagedir'].connect("changed",setPathIcon,image,1)
			self.configwidgets['previewimagedir'].set_text(self.xgngeoParams["previewimagedir"])
			box2.pack_start(self.configwidgets['previewimagedir'])
			button = gtk.Button()
			image2 = gtk.Image()
			image2.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_MENU)
			button.add(image2)
			button.connect('clicked',self.fileSelect,_('Select the preview image directory.'),self.configwidgets['previewimagedir'].get_text(),"previewimagedir",1)
			box2.pack_end(button,False)
			frame.add(box2)
			table.attach(frame,0,1,1,2)
			#Bouyaka.
			if self.xgngeoParams['previewimages']=="true": self.configwidgets['previewimages'].set_active(1)
			else: bouyaka(self.configwidgets['previewimages'],image,self.configwidgets['previewimagedir'],button)
			self.configwidgets['previewimages'].connect("toggled",bouyaka,image,self.configwidgets['previewimagedir'],button)

			frame = gtk.Frame(_("XML file containing ROM infos (optional):"))
			box2 = gtk.HBox()
			self.configwidgets['rominfos'] = gtk.CheckButton()
			box2.pack_start(self.configwidgets['rominfos'],False)
			image = gtk.Image()
			box2.pack_start(image,False,padding=3)
			self.configwidgets['rominfoxml'] = gtk.Entry()
			self.configwidgets['rominfoxml'].connect("changed",setPathIcon,image)
			self.configwidgets['rominfoxml'].set_text(self.xgngeoParams["rominfoxml"])
			box2.pack_start(self.configwidgets['rominfoxml'])
			button = gtk.Button()
			image2 = gtk.Image()
			image2.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_MENU)
			button.add(image2)
			button.connect("clicked",self.fileSelect,_('Select the XML file containing ROM infos.'),self.xgngeoParams["rominfoxml"],"rominfoxml")
			box2.pack_end(button,False)
			frame.add(box2)
			table.attach(frame,0,1,2,3)
			
			#Bouyaka.
			if self.xgngeoParams['rominfos']=="true": self.configwidgets['rominfos'].set_active(1)
			else: bouyaka(self.configwidgets['rominfos'],image,self.configwidgets['rominfoxml'],button)
			self.configwidgets['rominfos'].connect("toggled",bouyaka,image,self.configwidgets['rominfoxml'],button)

			self.configwidgets['autoexecrom'] = gtk.CheckButton(_("Auto execute ROMs."))
			if self.xgngeoParams["autoexecrom"]=="true": self.configwidgets['autoexecrom'].set_active(1)
			table.attach(self.configwidgets['autoexecrom'],1,2,0,1)

			self.configwidgets['centerwindow'] = gtk.CheckButton(_("Center XGngeo window on start."))
			if self.xgngeoParams["centerwindow"]=="true": self.configwidgets['centerwindow'].set_active(1)
			table.attach(self.configwidgets['centerwindow'],1,2,2,3)
			
			#History size
			box2 = gtk.HBox(spacing=4)
			label = gtk.Label(_("History size:"))
			box2.pack_start(label)
			adjustment = gtk.Adjustment(float(self.xgngeoParams["historysize"]),1,20,1)
			self.configwidgets['historysize'] = gtk.SpinButton(adjustment)
			box2.pack_start(self.configwidgets['historysize'],False)
			table.attach(box2,1,2,1,2)

			self.configDialog.vbox.pack_start(table)

		#``Save" Button
		button = gtk.Button(stock=gtk.STOCK_SAVE)

		#File writing adapted method...
		if firstrun: button.connect("clicked",self.configWrite,type,1)
		elif romspecific: button.connect("clicked",self.configWrite,type,2,self.mamename)
		else: button.connect("clicked",self.configWrite,type)

		self.configDialog.action_area.pack_start(button)

		if not firstrun:
			#"Cancel" Button (except at the first time configuration).
			button = gtk.Button(stock=gtk.STOCK_CANCEL)
			button.connect("clicked",self.destroy,self.configDialog)
			self.configDialog.action_area.pack_end(button)

		self.configDialog.show_all()

		#Display the right section in global emulation configuration.
		if type in (1,2,3,4):
			notebook.set_current_page(type-1)
			#Hide the keyboard P2 keys.
			for x in p2keywidgets: x.hide();

		#Enlarge the window width if too small.
		if self.configDialog.get_size()[0]<380: self.configDialog.set_size_request(380,-1)

	def configWrite(self,widget,type,special=0,mamename=None):
		letsWrite = 0

		if type==0:
			error = 0
			#Display error dialog or not, according to value icon image stock! (PATENT PENDING :p)
			for x in self.imppathicons:
				if x.get_stock()[0]=="gtk-no": error = 1

			if error:				
				dialog = gtk.MessageDialog(parent=self.window,flags=gtk.DIALOG_MODAL,type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
				dialog.set_markup("%s %s" % (_("Sorry, this configuration cannot be saved because one or more parameters does not look valid."),_("Please check it up then try to save again... ^^;")))
				dialog.connect("response",lambda *args: dialog.destroy())
				dialog.show_all()

			else:
				#Update important path configuration params.
				self.gngeoParams["rompath"] = self.configwidgets['rompath'].get_text() #rompath
				self.gngeoParams["romrc"] = self.configwidgets['romrc'].get_text() #romrc
				self.xgngeoParams["gngeopath"] = self.configwidgets['gngeopath'].get_text() #gngeopath

				letsWrite = 1 #Let's write!

		elif type in (1,2,3,4):
			temp_param = {}

			#Update global emulation configuration params.
			temp_param["fullscreen"] = ("false","true")[self.configwidgets['fullscreen'].get_active()] #fullscreen
			temp_param["interpolation"] = ("false","true")[self.configwidgets['interpolation'].get_active()] #interpolation
			temp_param["autoframeskip"] = ("false","true")[self.configwidgets['autoframeskip'].get_active()] #showfps
			temp_param["showfps"] = ("false","true")[self.configwidgets['showfps'].get_active()] #autoframeskip
			temp_param["scale"] = int(self.configwidgets['scale'].get_value()) #scale
			temp_param["screen320"] = ("false","true")[self.configwidgets['screen320'].get_active()] #screen320
			temp_param["raster"] = ("false","true")[self.configwidgets['raster'].get_active()] #raster
			temp_param["blitter"] = self.combo_params['blitter'][self.configwidgets['blitter'].get_active()] #blitter
			temp_param["effect"] = self.combo_params['effect'][self.configwidgets['effect'].get_active()] #effect
			temp_param["sound"] = ("false","true")[self.configwidgets['sound'].get_active()] #sound
			temp_param["samplerate"] = self.combo_params['samplerate'][self.configwidgets['samplerate'].get_active()] #sample rate
			temp_param["joystick"] = ("false","true")[self.configwidgets['joystick'].get_active()] #joystick
			temp_param["p1joydev"] = self.configwidgets['p1joydev'].get_active() #p1joydev
			temp_param["p2joydev"] = self.configwidgets['p2joydev'].get_active() #p2joydev
			if self.configwidgets['system_arcade'].get_active(): temp_param["system"] = "arcade" #system
			elif self.configwidgets['system_home'].get_active(): temp_param["system"] = "home"
			else: temp_param["system"] = "unibios"
			if self.configwidgets['country_japan'].get_active(): temp_param["country"] = "japan" #country
			elif self.configwidgets['country_usa'].get_active(): temp_param["country"] = "usa"
			else: temp_param["country"] = "europe"

			# Controls.
			#p1key
			temp_param["p1key"] = str()
			for val in self.p1key_int_vals: temp_param["p1key"] += "%s," % val
			temp_param["p1key"] = temp_param["p1key"][:-1]
			#p1key	
			temp_param["p2key"] = str()
			for val in self.p2key_int_vals: temp_param["p2key"] += "%s," % val
			temp_param["p2key"] = temp_param["p2key"][:-1]

			letsWrite = 1 #Let's write!

		elif type==5:
			#Update Other things configuration params.
			self.xgngeoParams["autoexecrom"] = ("false","true")[self.configwidgets['autoexecrom'].get_active()] #autoexecrom
			self.xgngeoParams["historysize"] = int(self.configwidgets['historysize'].get_value()) #historysize
			self.xgngeoParams["centerwindow"] = ("false","true")[self.configwidgets['centerwindow'].get_active()] #centerwindow_old
			self.gngeoParams["libglpath"] = self.configwidgets['libglpath'].get_text() #libglpath
			self.xgngeoParams["previewimages"] = ("false","true")[self.configwidgets['previewimages'].get_active()] #previewimage
			self.xgngeoParams["previewimagedir"] = self.configwidgets['previewimagedir'].get_text() #previewimagedir
			self.xgngeoParams["rominfos"] = ("false","true")[self.configwidgets['rominfos'].get_active()] #rominfo
			self.xgngeoParams["rominfoxml"] = self.configwidgets['rominfoxml'].get_text() #rominfoxml

			letsWrite = 1 #Let's write!

		if letsWrite: #We are now Ok to write into configuration file(s)...
			self.configDialog.destroy()

			#Perform particular actions.
			if special in (0,1): #Do the default or the sligtly different ``firstrun" job.
			
				#Put the options considered as temporary ROM-specific configuration parameters to the global parameter dictionnary.
				if type in (1,2,3,4):
					for key,val in temp_param.items(): self.gngeoParams[key] = val

				self.configfile.writeGlobalConfig(self.gngeoParams,self.xgngeoParams,VERSION) #Writing out! :p
				
				if not special: self.statusbar.push(self.context_id,_("Configuration has been saved.")) #Updating Status message
				else: self.main() #The program has been configured, so now we can use it!

			elif special==2: #ROM-specific configuration.
				self.configfile.writeRomConfig(temp_param,mamename,VERSION) #Writing out! :p
				
				if mamename==self.mamename:
					#Update buttons.
					self.specconf['new'].hide()
					self.specconf['properties'].show()
					self.specconf['clear'].show()

	def destroy(self,widget,condamned_widget,post_action=0,*args):
		#Destroying the widget.
		condamned_widget.destroy()

		#Doing post actions.
		if post_action==2: self.config(firstrun=1) #Configure Gngeo for the first time
		elif post_action==3: self.main() #Display the main window
		elif post_action==4: self.configmamenames.remove(args[0]) #Allow a specific ROM configuration window of being opened again. 
		elif post_action==5: self.statusbar.push(self.context_id,_("Configuration was not saved.")) #When configuration was cancelled.

	def quit(self,*args):
		if self.emulator.romRunningState(): self.gngeoStop() #Stop any running Gngeo.
		gtk.main_quit() #Stop waiting for event...
		return False

	def main(self):
		#Window attributes.
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
		self.loadrom_menu_item = gtk.MenuItem(_("_Load ROM"))
		self.loadrom_menu_item.set_submenu(menu2)
		menu.append(self.loadrom_menu_item)

		menu_item = gtk.MenuItem(_("From _list"))
		menu_item.connect("activate",self.romList)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_Manually"))
		menu_item.connect("activate",self.fileSelect,_("Select a ROM"),self.gngeoParams["rompath"],"rom")
		menu2.append(menu_item)

		self.history_menu_item = gtk.MenuItem(_("_History"))
		self.historyMenu = gtk.Menu()
		self.history_menu_item.set_submenu(self.historyMenu)
		self.historyMenu.append(gtk.TearoffMenuItem())
		self.historyMenuGeneration()
		menu.append(self.history_menu_item)

		menu.append(gtk.SeparatorMenuItem()) #Separator

		self.execMenu_item = gtk.ImageMenuItem(gtk.STOCK_EXECUTE)
		self.execMenu_item.connect("activate",self.gngeoExec)
		self.execMenu_item.set_state(gtk.STATE_INSENSITIVE)
		menu.append(self.execMenu_item)

		self.stopMenu_item = gtk.ImageMenuItem(gtk.STOCK_STOP)
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
		self.configMenu = gtk.Menu()
		menu_item = gtk.MenuItem(_("_Configuration"))
		menu_item.set_submenu(self.configMenu)
		menu_bar.append(menu_item)

		menu_item = gtk.MenuItem(_("_Important paths"))
		menu_item.connect("activate",self.config,0)
		self.configMenu.append(menu_item)

		menu2 = gtk.Menu()
		menu_item = gtk.MenuItem(_("_Global emulation"))
		menu_item.set_submenu(menu2)
		self.configMenu.append(menu_item)

		menu_item = gtk.MenuItem(_("_Graphic"))
		menu_item.connect("activate",self.config,1)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_Audio / Joystick"))
		menu_item.connect("activate",self.config,2)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_Controls"))
		menu_item.connect("activate",self.config,3)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_System"))
		menu_item.connect("activate",self.config,4)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_Other"))
		menu_item.connect("activate",self.config,5)
		self.configMenu.append(menu_item)

		#
		# INFO Menu
		#
		menu = gtk.Menu()
		menu_item = gtk.MenuItem(_("_Info"))
		menu_item.set_right_justified(True) #At right.
		menu_item.set_submenu(menu)
		menu_bar.append(menu_item)

		menu_item = gtk.ImageMenuItem(gtk.STOCK_HELP)
		menu_item.connect("activate",self.displayfile,"doc/xgngeo-doc.txt")
		menu.append(menu_item)

		menu_item = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
		menu_item.connect("activate",self.about)
		menu.append(menu_item)

		menu_item = gtk.MenuItem(_("_License"))
		menu_item.connect("activate",self.displayfile,"LICENSE.txt")
		menu.append(menu_item)

		# Pack MemuBar into the Box
		box.pack_start(menu_bar,False)

		#
		# Logo
		#
		container = gtk.EventBox()
		container.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("white"))
		logo = gtk.Image()
		logo.set_from_file(os.path.join(datarootpath,"img/xgngeo.png"))
		logo.set_padding(25,2)
		container.add(logo)
		box.pack_start(container)

		#
		# Statusbar
		#
		self.statusbar.push(self.context_id,_("Welcome to XGngeo version %i.") % VERSION)
		box.pack_end(self.statusbar,False)

		#Window positioning.
		if self.xgngeoParams["centerwindow"]=="true": self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
		#Show all.
		self.window.show_all()

	def boot(self):
		#Overwrite default params by the ones in configuration files (works even if they don't exist :p).
		params = self.configfile.getParams()
		for key,val in params[0].items(): self.gngeoParams[key] = val
		for key,val in params[1].items(): self.xgngeoParams[key] = val

		if "--nobootcheck" in sys.argv:
					print _("No boot check option enabled: going directly to the main window (unsafe!).")
					self.main()

		else: #Perform boot-time important checks.
			error = 0
			#Are BIOS files present?
			if not (os.path.isfile("%s/neo-geo.rom" % self.gngeoParams["rompath"]) or os.path.isfile("%s/sp-s2.sp1" % self.gngeoParams["rompath"]))\
			or not (os.path.isfile("%s/ng-sfix.rom" % self.gngeoParams["rompath"]) or os.path.isfile("%s/sfix.sfx" % self.gngeoParams["rompath"]))\
			or not (os.path.isfile("%s/ng-lo.rom" % self.gngeoParams["rompath"]) or os.path.isfile("%s/000-lo.lo" % self.gngeoParams["rompath"])):
				error = 1
			#Is ROM driver file present?
			if not (os.path.isfile(self.gngeoParams["romrc"])): error = 1
			#Is the Gngeo executable present and returning correct version informations?
			version = self.emulator.getGngeoVersion()
			if not version or version[0][1:3]<(6,11): error = 1

			if error: self.checkError() #Display value setting invitation.
			else: self.main() #Everything seems okay, so let's display the main window...

if __name__ == "__main__":
	gtk.threads_init()
	XGngeo().boot()
	gtk.main()
