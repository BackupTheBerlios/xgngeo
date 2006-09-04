#!/usr/bin/env python
""" XGngeo: a frontend for Gngeo in GTK. ^_^.

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

__author__ = "Choplair-network"
__copyright__ = "Copyleft 2003, 2004, 2005, 2006 Choplair-network"
__license__ = "GPL"
__revision__ = "$Revision$"
# $Source$
__date__ = "$Date$"

# Psyco module (Just in time compiler)
try:
	import psyco
except ImportError:
	pass
else:
	print "Loading psyco...",
	psyco.full()
	print "psyco loaded."

# Imports
import sys
import os
import gettext

import gtk
if gtk.pygtk_version[:2] < (2, 6):
	sys.exit("Error: PyGTK version 2.6 or more is required.")

from string import capwords
from re import match
from threading import Timer

# Internal modules.
import configfile
import emulator
import history
import rominfos

# Global variables
VERSION = "16"
xgngeoUserDir = os.path.expanduser("~/.xgngeo")
gngeoUserDir = os.path.expanduser("~/.gngeo")
datarootpath = os.path.join(sys.prefix, 'share', 'xgngeo')

# Internationalization.
gettext.install("xgngeo", os.path.join(datarootpath, "locale"))

class XGngeo:
	def __init__(self):
		# Default values...
		self.tempparam = {}
		self.widgets = {"config": {}}
		self.romPath = None

		# Loading emulator/frontend configuration.
		self.configfile = configfile.Configfile(datarootpath, xgngeoUserDir,
		gngeoUserDir)
		self.params = {"temp": {}}
		self.params["gngeo"], self.params["xgngeo"] = self.configfile\
			.get_default_params()
		# Overwriting default params by the ones in configuration files.
		dict = self.configfile.get_params()
		for key,val in dict[0].items(): self.params["gngeo"][key] = val
		for key,val in dict[1].items(): self.params["xgngeo"][key] = val

		self.emulator = emulator.Emulator(self.params["xgngeo"]["gngeopath"])
		self.history = history.History()

		# Statusbar.
		self.widgets["statusbar"] = gtk.Statusbar()
		self.context_id = self.widgets["statusbar"].get_context_id("Info")

		# Main window inital attributes.
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		gtk.window_set_default_icon_from_file(os.path.join(datarootpath, "img",
			"icon.png"))
	
	def check_error(self):
		#Checking for Gngeo's home directory.
		if not os.path.isdir(gngeoUserDir):
			os.mkdir(gngeoUserDir)

		def callback(widget, response):
			dialog.destroy()
			if response == gtk.RESPONSE_DELETE_EVENT: self.quit() #Exit all.
			else:
				# Going to important path configuration window.
				self.config(firstrun=1)

		dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL,
			type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK,
			message_format = _("It seems that the important path parameters "
			"are not all valid. That is normal if Gngeo configuration file "
			"hasn't been yet created. Anyway, correct values should be "
			"specified for the emulation to work. Press OK to do so..."))
		dialog.connect("response", callback)
		dialog.show_all()

	def display_file(self, widget, filename):
		display = 1
		textbuffer = gtk.TextBuffer()
		filename = os.path.join(datarootpath, filename)

		if os.path.isfile(filename):
			file = open(filename, "r")
			textbuffer.set_text(file.read())
			file.close()
		else:
			if filename[-11:] == "LICENSE.txt":
				textbuffer.set_text(_("Error: Unable to open the file \"%s\"!\n"
				"You can read the GNU GPL license at:\n"
				"http://www.gnu.org/licenses/gpl.html") % filename)
			else: display = 0

		if display:
			dialog = gtk.Dialog((filename, _("License"))[filename[-11:] == \
				"LICENSE.txt"], self.window, gtk.DIALOG_NO_SEPARATOR |
				gtk.DIALOG_MODAL, (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

			if filename[-11:]=="LICENSE.txt":
				label = gtk.Label(_("This program is released under the terms "
					"of the GNU General Public License."))
				label.set_padding(2, 4)
				dialog.vbox.pack_start(label, False)

			textview = gtk.TextView(textbuffer)
			tag = textbuffer.create_tag(family="monospace", editable=False)
			textbuffer.apply_tag(tag, textbuffer.get_start_iter(),
				textbuffer.get_end_iter())

			scrolled_window = gtk.ScrolledWindow()
			scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
				gtk.POLICY_AUTOMATIC)
			scrolled_window.add(textview)
			scrolled_window.set_size_request(550, 342)

			dialog.vbox.pack_end(scrolled_window)
			dialog.connect('response', lambda *args: dialog.destroy())
			dialog.show_all()

	def gngeo_get_output(self):
		"""This function is embeded in a thread and perform
			some Gngeo post-execution instructions after it
			terminates.
		
		"""
		# Waiting for Gngeo to hang up...
		self.emulator.rom_waiting_for_hanging_up()

		gtk.threads_enter() # Without this, it often bugs. :p
		
		# Simple post-execution instruction.
		self.history_add(self.romFullName,self.romPath) # Appendding ROM too history.
		self.widgets["statusbar"].push(self.context_id,_("ROM stopped (%s).") %
			self.romMameName) # Updating status bar.

		# --------------------------------------------------------
		# Introducing our exclusive and innovative system
		# to catch and display error returned by Gngeo, aka :
		#         `` DA XGNGEO CRAP DETECTOR " !
		# Covererd by patents 2173965, 1004076, 5867297, etc.
		# --------------------------------------------------------
		# We'll check whether there was a f*ck then try to display
		# the error/warning message returned by Gngeo if it's the case.
		# We do not so when the game was stopped from XGngeo.
		if not self.gngeokilledbyme:
			output = self.emulator.rom_get_process_output() #Raw ouput of Gngeo.
			message = "" #Nothing for start!
			#Parsing the output, line per line, looking for error...
			for line in output.split("\n"):
				for line in line.split("\r"):
					# We ignore usual messages:
					# 1: ROM loading progression.
					# 2 & 3: YUV driver output.
					# 4: ROM driver creation message (in Gngeo 0.6.5beta).
					# 5: Screenshot saving message.
					# 6: Joystick device init message.
					if not line.strip()=="" \
						and not match(".* [[][\-|\*]{62}[]]?", line)\
						and not match("Update sai .*", line)\
						and not match("deltaptr=(\S)* sai", line)\
						and not line[:4]=="Add "\
						and not line[:8]=="save to "\
						and not match("joy .*, axe:\d+, button:\d+", line):
						# The line contains a unexpected message which is thus
						# certainly important, so we record it.
						message += "%s\n" % line.strip()

			if message != "": 
				# Oh dear! There was a f*ck! Let's display the info dialog.
				dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL,
					gtk.MESSAGE_INFO,  gtk.BUTTONS_OK)
				dialog.set_markup("%s\n\n<span color='#b00'>%s</span>" %
					(_("Gngeo returned the following message:"),
					unicode(message[:-1], 'iso-8859-1').replace('&',
					'&amp;')))
				dialog.connect("response", lambda *args: dialog.destroy())
				dialog.show_all()
		#-------------------------------------------------------------------------

		# Performing some modifications on the menu.
		self.loadrom_menu_item.set_sensitive(True)
		self.history_menu_item.set_sensitive(True)
		for x in self.widgets["history_menu"].get_children(): x.set_sensitive(True)
		self.stopMenu_item.set_sensitive(False)
		self.execMenu_item.set_sensitive(True)
		for x in self.configMenu.get_children(): x.set_sensitive(True)
		gtk.threads_leave()
	
	def rom_loading_in_progress(self):
		"""Graphicaly indicate the user that, although he
			see nothing, the program is actually working, trying
			to load the ROM.
		
		"""
		import time
		message = _("Starting ROM (%s)") % self.romMameName
		for x in range(42): #Don't panic!
			if not self.emulator.rom_running_state(): break
			gtk.threads_enter()
			self.widgets["statusbar"].push(self.context_id, ("%s%s" %
				(message, ("." * x))))
			gtk.threads_leave()
			time.sleep(0.42)

	def gngeo_exec(self,widget=None):
		Timer(0, self.rom_loading_in_progress).start()

		# Performing some modifications on the menu.
		self.loadrom_menu_item.set_sensitive(False)
		self.history_menu_item.set_sensitive(False)
		for x in self.widgets["history_menu"].get_children():
			x.set_sensitive(False)
		self.stopMenu_item.set_sensitive(True)
		self.execMenu_item.set_sensitive(False)
		for x in self.configMenu.get_children(): x.set_sensitive(False)

		self.emulator.rom_launching(self.romPath)

		self.gngeokilledbyme = 0
		# Starting another thread which watchs out the last one!
		Timer(0,self.gngeo_get_output).start()

	def gngeo_stop(self, widget=None):
		"""``Close you eyes and prey, Gngeo!"
		This function kills gngeo if it is alive."""
		if self.emulator.rom_running_state():
			Timer(0, os.system,('killall -9 "%s"' %
				self.params["xgngeo"]["gngeopath"].replace('"','\"'),)).start()
			self.gngeokilledbyme = 1

	def rom_list(self, widget):
		def button_pressed(widget, event):
			"""Popping-up a menu on rigth clicking over an available ROM
				in the list.
			
			"""
			if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
				def confirm_deletion_dial(*args):
					liststore, iter = treeselection.get_selected()
					if iter:  # Is there anything selected?
						fullname =  liststore.get_value(iter, 0)
						availability = liststore.get_value(iter, 1)
						filepath =  liststore.get_value(iter, 2)

						if availability:
							def response(widget, response_id):
								if response_id == gtk.RESPONSE_YES:
									try:
										# Proceeding with deletion.
										os.remove(filepath)
									except:
										# A problem happend in doing so.
										dialog2 = gtk.MessageDialog(
											self.window, gtk.DIALOG_MODAL,
											gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
											_("An error occured while trying "
											"to delete the ROM archive."))
										dialog2.connect("response",
											lambda *args: dialog2.destroy())
									else:
										# Deletion succeded. Now refreshing the list.
										refreshing_rom_list()
										
								#Closing the dialog in any case.
								dialog.destroy()
							
							dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, 
								gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO)
							dialog.set_markup(_("Should XGngeo proceed with the "
								"deletion of the ROM <b>%s</b> located at <i>%s</i>?" %
								(fullname, filepath)))
							dialog. format_secondary_text(_("Please note this "
								"operation is irremediable."))
							dialog.connect("response", response)
						else: 
							dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, 
								gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, _("Cannot "
								"delete a ROM which unavailable!"))
							dialog.connect("response", lambda *args: dialog.destroy())
						dialog.show_all()
			
				menu = gtk.Menu()
				item = gtk.ImageMenuItem(gtk.STOCK_DELETE)
				item.connect("activate", confirm_deletion_dial)
				item.show()
				menu.append(item)
				menu.popup(None, None, None, event.button, event.time)

		def new_list_selection(*args):
				#Ensure that the set the right side is no more insensitive.
				if not rightside.get_property("sensitive"): rightside.set_sensitive(True)

				liststore, iter = treeselection.get_selected()
				
				if iter: #Is there anything selected?
					fullname = liststore.get_value(iter, 0)
					availability = liststore.get_value(iter, 1)
					filepath =  liststore.get_value(iter, 2)
					mamename = romlist[fullname]

					#Temporary select the ROM for loading if available.
					if availability:
						self.romFromList, self.romFromListName,\
							self.romFromListPath = mamename, fullname, filepath
					else:
						self.romFromList, self.romFromListName,\
							self.romFromListPath = None, None, None
					open_button.set_sensitive(availability)

					#Update mame name and availability icon.
					self.mamename = mamename #The current selected mamename is exported.
					self.widgets['mamename_label'].set_text("<b>%s</b>" %
					mamename)
					self.widgets['mamename_label'].set_use_markup(True)
					self.avail_image.set_from_stock((gtk.STOCK_NO,
						gtk.STOCK_YES)[availability], gtk.ICON_SIZE_MENU)

					#Update preview image.
					if self.params["xgngeo"]["previewimages"] == "true":
						if os.path.isfile(os.path.join(self.params["xgngeo"]["previewimagedir"],
							"%s.png" % mamename)): 
							self.previewImage.set_from_file(os.path.join(self.params["xgngeo"]\
								["previewimagedir"], "%s.png" % mamename))
						elif os.path.isfile(os.path.join(self.params["xgngeo"]["previewimagedir"],
							"unavailable.png")):
							self.previewImage.set_from_file(os.path.join(self.params["xgngeo"]\
								["previewimagedir"], "unavailable.png"))

					# Updating rom infos.
					if self.params["xgngeo"]["rominfos"] == "true" and \
						os.path.isfile(self.params["xgngeo"]["rominfoxml"]):
						# Checking for game informations.
						if self.romInfos.has_key(mamename):
							for x in ("desc", "manufacturer", "year", "genre",
								"players", "rating"):
								self.romInfosWidget[x].set_text(("--",self.romInfos[mamename][x], "--")\
									[self.romInfos[mamename].has_key(x)])
							if self.romInfos[mamename].has_key("size"):
								self.romInfosWidget["size"].set_text("%sMbit" %
									self.romInfos[mamename]["size"])
						else:
							for x in ("desc", "manufacturer", "year", "genre",
								"players", "rating", "size"):
								self.romInfosWidget[x].set_text("--")

					#Update specific configuration buttons.
					path = os.path.join(gngeoUserDir,"%s.cf" % mamename)
					if os.path.isfile(path):
						self.widgets['specconf_new'].hide()
						self.widgets['specconf_properties'].show()
						self.widgets['specconf_clear'].show()
					else:
						self.widgets['specconf_new'].show()
						self.widgets['specconf_properties'].hide()
						self.widgets['specconf_clear'].hide()

		def set_rom_from_list(widget):
			if self.romFromList: #Is something selected?
				self.setting_current_rom(self.romFromListPath, self.romFromList,
				self.romFromListName)
			dialog.destroy()

		def refreshing_rom_list(*args):
			liststore.clear() #First clearing the list out.

			available_rom = {}
			for dir in self.romdir_list:
				for mame, file in  self.emulator.scan_rom_in_directory(dir).items():
					available_rom[mame] = os.path.join(dir, file)
			
			#Adding ROM rows.
			self.emulator.get_all_supported_roms()
			romlist_fullname = self.emulator.get_rom_full_names()
			romlist = self.emulator.get_rom_full_to_mame()
			
			for name in romlist_fullname:
				if romlist[name] in available_rom:
					#Alway putting available ROMs.
					liststore.append([name,True,available_rom[romlist[name]]])
				elif not buttonShowAvailable.get_active():
					#Also putting unavailable ROMs if the box is unchecked.
					liststore.append([name,False,''])

			labelAvailableRoms.set_text(_("<b>%s</b> available ROMs.")	%
				len(available_rom.keys()))
			labelAvailableRoms.set_use_markup(True)

		def rom_directories(widget, parent):
			temp_romdir_list = list(tuple(self.romdir_list)) #Not affecting in-use param (yet).
			dialog = gtk.Dialog(_("Setting ROM directories."), parent,
				gtk.DIALOG_MODAL, (gtk.STOCK_APPLY, gtk.RESPONSE_APPLY,
				gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
			label = gtk.Label(_("Here you can add multiple directories to "
				"scan for ROMs (this is not recursive)."))
			label.set_justify(gtk.JUSTIFY_CENTER)
			label.set_padding(3, 4)
			label.set_line_wrap(True)
			dialog.vbox.pack_start(label, False)

			box = gtk.HBox()

			def add_directory(widget,response):
				if response == gtk.RESPONSE_OK:
					dir = self.widgets["fileselect_dialog"].get_filename()
					if not dir in temp_romdir_list:
						temp_romdir_list.append(dir)
						liststore.append([dir])
					else:  # No need to put the same directory twice.
						dialog2 = gtk.MessageDialog(dialog, gtk.DIALOG_MODAL,
							gtk.MESSAGE_ERROR,  gtk.BUTTONS_OK, _("This "
							"directory is already in the ROM directory list!"))
						dialog2.connect("response", lambda *args: dialog2.destroy())
						dialog2.show_all()

			def rem_directory(*args):
				model,iter = treeview.get_selection().get_selected()
				if iter:
					dir = model.get_value(iter,0)
					temp_romdir_list.remove(dir)
					liststore.remove(iter)

			def response(widget, response):
				if response == gtk.RESPONSE_APPLY:
					self.romdir_list = temp_romdir_list  # Validating the ROM list.

					# Saving it in the appropriate file.
					content = ""
					for dir in self.romdir_list:
						content += "%s\n" % dir
					file = open(os.path.join(xgngeoUserDir, "romdirs"), "w")
					file.write(content)
					file.close()

					# Refreshing ROM list (using the new ROM directories).
					refreshing_rom_list()

				dialog.destroy()

			box2 = gtk.VBox()
			button = gtk.Button(stock=gtk.STOCK_REMOVE)
			button.set_border_width(5)
			button.connect("clicked", rem_directory)
			box2.pack_start(button)
			button = gtk.Button(stock=gtk.STOCK_ADD)
			if len(temp_romdir_list) >= 1: folder = temp_romdir_list[-1]
			else: folder = None
			button.connect("clicked",self.file_select, _("Select a ROM "
				"directory to add."), folder, add_directory, 1, None)
			button.set_border_width(5)
			box2.pack_start(button)
			box.pack_start(box2, False, padding=2)

			# Da ROM directory list!
			liststore = gtk.ListStore(str)
			treeview = gtk.TreeView(liststore)
			treeview.set_headers_visible(False)
			tvcolumn = gtk.TreeViewColumn("Directory")
			treeview.append_column(tvcolumn)
			for dir in temp_romdir_list:
				# Inserting content.
				liststore.append([dir])
			cell = gtk.CellRendererText()
			tvcolumn.pack_start(cell, True)
			tvcolumn.set_attributes(cell, text=0)
			frame = gtk.Frame()
			frame.add(treeview)
			box.pack_start(frame, padding=2)
	
			dialog.vbox.pack_start(box)
			dialog.show_all()
			dialog.connect("response", response)

		self.romFromList = None  # Selected ROM.
		dialog = gtk.Dialog(_("Your Neo Geo ROM list."), self.window,
			gtk.DIALOG_MODAL)

		table = gtk.Table(4, 3)

		label = gtk.Label(_("Select a ROM by clicking on its name, then press "
			"<b>Open</b> to load it if available (colored background)."))
		label.set_use_markup(True)
		label.set_line_wrap(True)
		label.set_justify(gtk.JUSTIFY_CENTER)
		table.attach(label, 0, 3, 0, 1, yoptions=gtk.SHRINK, xpadding=0,
			ypadding=2)

		# DA ROM list!
		scrolled_window = gtk.ScrolledWindow()
		scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,  gtk.POLICY_ALWAYS)
		scrolled_window.set_size_request(500, 250)  # Setting scrolled window's height.
		table.attach(scrolled_window, 0, 3, 1, 2, xpadding=2, ypadding=5)

		# The list will contain the ROM full name and an availability indicator.
		liststore = gtk.ListStore(str, "gboolean", str)
		treeview = gtk.TreeView(liststore)
		treeview.set_headers_visible(False)
		treeselection = treeview.get_selection()
		treeselection.connect("changed", new_list_selection)
		treeview.connect("button_press_event", button_pressed)

		# Columns to display data.
		tvcolumn = gtk.TreeViewColumn("Fullname")
		treeview.append_column(tvcolumn)

		# Rendering data.
		cell = gtk.CellRendererText()
		cell.set_property("cell-background", self.params["xgngeo"]["availableromcolor"])
		tvcolumn.pack_start(cell,True)
		tvcolumn.set_attributes(cell, text=0, cell_background_set=1)

		treeview.set_search_column(0)  # Making treeview searchable.
		tvcolumn.set_sort_column_id(0)  # Make columns sortable.

		scrolled_window.add_with_viewport(treeview)

		button = gtk.Button(_("ROM directories..."))
		button.connect("clicked", rom_directories, dialog)
		table.attach(button, 0, 1, 2, 3, yoptions=gtk.SHRINK)

		labelAvailableRoms = gtk.Label()
		table.attach(labelAvailableRoms, 1, 2, 2, 3, yoptions=gtk.SHRINK,
			xpadding=3, ypadding=0)

		buttonShowAvailable = gtk.CheckButton(_("Show available ROMs only."))
		if self.params["xgngeo"]["showavailableromsonly"] == "true":
			buttonShowAvailable.set_active(True)  # Activating button. 
		# Connecting the toggled event (*after* potential button activation).
		buttonShowAvailable.connect("toggled", refreshing_rom_list) 
		table.attach(buttonShowAvailable, 2, 3, 2, 3, yoptions=gtk.SHRINK)

		#
		# Mame name/preview image/info side. :P
		#
		rightside = gtk.VBox(spacing=3)
		noteisthere = 0
		# Using add-ons if activated and valid.
		if((self.params["xgngeo"]["previewimages"] == "true" and os.path.isdir(
			self.params["xgngeo"]["previewimagedir"])) or (self.params["xgngeo"]\
			["rominfos"] == "true" and os.path.isfile(self.params["xgngeo"]\
			["rominfoxml"]))):
			notebook = gtk.Notebook()
			rightside.pack_start(notebook, padding=4)
			noteisthere = 1

			#Preview images.
			if self.params["xgngeo"]["previewimages"] == "true"\
				and os.path.isdir(self.params["xgngeo"]["previewimagedir"]):
				self.previewImage = gtk.Image()
				self.previewImage.set_padding(3, 3)
				path = os.path.join(self.params["xgngeo"]["previewimagedir"],
					"unavailable.png")
				if os.path.isfile(path):
					# Displaying the ``unavailable" image by default.
					self.previewImage.set_from_file(path) 
				container = gtk.EventBox()
				container.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
				container.add(self.previewImage)
				notebook.append_page(container, gtk.Label(_("Preview image")))

			# ROM infos.s
			if(self.params["xgngeo"]["rominfos"] == "true" and os.path.isfile(
				self.params["xgngeo"]["rominfoxml"])):
				self.romInfos = rominfos.Rominfos(path=self.params["xgngeo"]\
					["rominfoxml"]).getDict()
				self.romInfosWidget = {}

				box2 = gtk.VBox()

				# Description.
				self.romInfosWidget["desc"] = gtk.TextBuffer()
				self.romInfosWidget["desc"].set_text("--")
				textview = gtk.TextView(self.romInfosWidget["desc"])
				textview.set_editable(0)
				textview.set_wrap_mode(gtk.WRAP_WORD)
				scrolled_window = gtk.ScrolledWindow()
				scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
				box2.set_size_request(220, -1)  # Set width.
				scrolled_window.add(textview)
				frame = gtk.Frame(_("Description:"))
				frame.add(scrolled_window)
				box2.pack_start(frame)

				# Other infos.
				table2 = gtk.Table(3, 2, True)

				frame = gtk.Frame(_("Manufacturer:"))
				self.romInfosWidget["manufacturer"] = gtk.Entry()
				self.romInfosWidget["manufacturer"].set_text("--")
				self.romInfosWidget["manufacturer"].set_editable(0)
				frame.add(self.romInfosWidget["manufacturer"])
				table2.attach(frame, 0, 1, 0, 1)

				frame = gtk.Frame(_("Year:"))
				self.romInfosWidget["year"] = gtk.Entry()
				self.romInfosWidget["year"].set_text("--")
				self.romInfosWidget["year"].set_editable(0)
				frame.add(self.romInfosWidget["year"])
				table2.attach(frame, 0, 1, 1, 2)

				frame = gtk.Frame(_("Genre:"))
				self.romInfosWidget["genre"] = gtk.Entry()
				self.romInfosWidget["genre"].set_text("--")
				self.romInfosWidget["genre"].set_editable(0)
				frame.add(self.romInfosWidget["genre"])
				table2.attach(frame, 0, 1, 2, 3)

				frame = gtk.Frame(_("Players:"))
				self.romInfosWidget["players"] = gtk.Entry()
				self.romInfosWidget["players"].set_text("--")
				self.romInfosWidget["players"].set_editable(0)
				frame.add(self.romInfosWidget["players"])
				table2.attach(frame, 1, 2, 0, 1)

				frame = gtk.Frame(_("Rating:"))
				self.romInfosWidget["rating"] = gtk.Entry()
				self.romInfosWidget["rating"].set_text("--")
				self.romInfosWidget["rating"].set_editable(0)
				frame.add(self.romInfosWidget["rating"])
				table2.attach(frame, 1, 2, 1, 2)

				frame = gtk.Frame(_("Size:"))
				self.romInfosWidget["size"] = gtk.Entry()
				self.romInfosWidget["size"].set_text("--")
				self.romInfosWidget["size"].set_editable(0)
				frame.add(self.romInfosWidget["size"])
				table2.attach(frame, 1, 2, 2, 3)

				box2.pack_start(table2, False)

				notebook.append_page(box2, gtk.Label(_("Informations")))

		box2 = gtk.HBox()
		self.widgets['mamename_label'] = gtk.Label("<b>-----</b>")
		self.widgets['mamename_label'].set_use_markup(True)
		box2.pack_start(self.widgets['mamename_label'])
		self.avail_image = gtk.Image()
		self.avail_image.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_MENU)
		box2.pack_end(self.avail_image, False)
		rightside.pack_start(box2, not noteisthere)

		# ROM-specific configuration.
		def delete_rom_conf(*args):
			os.remove(os.path.join(gngeoUserDir, "%s.cf" % self.mamename))
			# Update buttons.
			self.widgets['specconf_new'].show()
			self.widgets['specconf_properties'].hide()
			self.widgets['specconf_clear'].hide()

		self.specconf = {}
		frame = gtk.Frame(_("Specific configuration:"))
		frame.set_label_align(0.5, 0.5)  # Center is better. :p
		box2 = (gtk.VBox(),gtk.HBox())[noteisthere]

		self.widgets['specconf_new'] = gtk.Button(stock=gtk.STOCK_NEW)
		self.widgets['specconf_new'].connect("clicked",self.config, 1, 0, 1)
		box2.pack_start(self.widgets['specconf_new'])

		self.widgets['specconf_properties'] = gtk.Button(stock=gtk.STOCK_EDIT)
		self.widgets['specconf_properties'].connect("clicked",self.config, 1,
			0, 1)
		box2.pack_start(self.widgets['specconf_properties'])

		self.widgets['specconf_clear'] = gtk.Button(stock=gtk.STOCK_CLEAR)
		self.widgets['specconf_clear'].connect("clicked",delete_rom_conf)
		box2.pack_start(self.widgets['specconf_clear'])

		frame.add(box2)
		rightside.pack_end(frame, not noteisthere)

		table.attach(rightside, 3, 4, 0, 3, gtk.SHRINK)
		dialog.vbox.pack_start(table)
		rightside.set_sensitive(False)

		# Creating a list of of all availbable ROMs (after scanning all ROM
		# directories).
		self.romdir_list = []
		if os.path.exists(os.path.join(xgngeoUserDir, "romdirs")):
			file = open(os.path.join(xgngeoUserDir, "romdirs"), "r")
			for line in file.readlines():
				if line.strip(): self.romdir_list.append(line[:-1])
			file.close()
		available_rom = {}

		# Initial ROM list generation.
		refreshing_rom_list()

		# Initialize ROM names (MAME <=> full name) correspondency list (only
		# needed once).
		self.emulator.get_all_supported_roms()
		romlist_fullname = self.emulator.get_rom_full_names()
		romlist = self.emulator.get_rom_full_to_mame()
		
		# Buttons at bottom.
		open_button = gtk.Button(stock = gtk.STOCK_OPEN)
		open_button.set_sensitive(False)
		open_button.connect("clicked", set_rom_from_list)
		dialog.action_area.pack_start(open_button)

		button = gtk.Button(stock = gtk.STOCK_CANCEL)
		button.connect("clicked", lambda *args: dialog.destroy())
		dialog.action_area.pack_start(button)

		dialog.show_all()
		# Let's hide ourselves!
		self.widgets['specconf_properties'].hide()
		self.widgets['specconf_clear'].hide()

	def file_select(self, widget, title, folder=None, callback=None,
		dirselect=0, filter=None, rompreview=False):
		self.widgets["fileselect_dialog"] = gtk.FileChooserDialog(title, action=(
			gtk.FILE_CHOOSER_ACTION_OPEN, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)\
			[dirselect], buttons=(gtk.STOCK_OPEN, gtk.RESPONSE_OK,
			gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

		if folder:
			self.widgets["fileselect_dialog"].set_current_folder(
				os.path.dirname(folder))

		if callback:
			if type(callback) == str:
				def response(dialog,response):
					"""Ouputing the selected file or directory path to a 
						particular text entry.
					
					"""
					if response == gtk.RESPONSE_OK:
						self.widgets["config"][callback].set_text(dialog.get_filename())

				self.widgets["fileselect_dialog"].connect("response", response)
			else:
				self.widgets["fileselect_dialog"].connect("response", callback)
	
		#Closing the file selection dialog anyway.
		self.widgets["fileselect_dialog"].connect('response', lambda *args:
			self.widgets["fileselect_dialog"].destroy())

		if filter: #Using file selection filter(s).
			for name,patern in filter.items():
				filter = gtk.FileFilter()
				filter.set_name("%s (%s)" % (name, patern))
				filter.add_pattern(patern)
				self.widgets["fileselect_dialog"].add_filter(filter)
			#Setting filter to the last entry.
			self.widgets["fileselect_dialog"].set_filter(filter)

		#Displaying ROM preview infos.
		if rompreview:
			show_image = self.params["xgngeo"]["previewimages"]

			def scan_dir_for_roms(*args):
				#Updating the ROM scan infos to match the new current directory.
				self.params["temp"]["currdir_romscaninfos"] = \
					self.emulator.scan_rom_in_directory(self.widgets["fileselect_dialog"]\
					.get_current_folder(), True)

			def update_preview(*args):
				selection = self.widgets["fileselect_dialog"].get_preview_filename()

				if selection and os.path.isfile(selection): 
					filename = os.path.basename(selection)
					if self.params["temp"]["currdir_romscaninfos"].has_key(filename):
						#Current selection has been detected as a ROM: updating preview!
						tuple =  self.params["temp"]["currdir_romscaninfos"][filename]

						#With image mode.
						if show_image == "true":
							if os.path.isfile(os.path.join(self.params["xgngeo"]\
								["previewimagedir"], "%s.png" % tuple[0])):
								self.widgets["fileselect_preview_image"].set_from_file(
									os.path.join(self.params["xgngeo"]["previewimagedir"],
									"%s.png" % tuple[0]))
							elif os.path.isfile(os.path.join(self.params["xgngeo"]\
								["previewimagedir"],"unavailable.png")):
								self.widgets["fileselect_preview_image"].set_from_file(
									os.path.join(self.params["xgngeo"]["previewimagedir"],
									"unavailable.png"))

						#Full name label.
						self.widgets["fileselect_preview_label"].set_text(((_(
							"Detected ROM: <b>%s</b>."), "<b>%s</b>")[
							show_image == "true"]) % tuple[1])

					else:
						# Current selection has *not* been detected as a ROM: no preview.
						if show_image == "true": # With image mode.
							if os.path.isfile(os.path.join(self.params["xgngeo"]\
								["previewimagedir"],"unavailable.png")):
								self.widgets["fileselect_preview_image"]\
									.set_from_file(os.path.join(self.params["xgngeo"]["previewimagedir"],
									"unavailable.png"))
							self.widgets["fileselect_preview_label"].set_text("<b>--</b>")
						else:
							self.widgets["fileselect_preview_label"].set_text(_("Detected ROM: "
								"<b>%s</b>.") % "--")

				else: # Not a file: no preview. :p
					if show_image == "true": # With image mode.
						if os.path.isfile(os.path.join(self.params["xgngeo"]\
							["previewimagedir"], "unavailable.png")):
							self.widgets["fileselect_preview_image"].set_from_file(
								os.path.join(self.params["xgngeo"]\
									["previewimagedir"], "unavailable.png"))
						self.widgets["fileselect_preview_label"].set_text(
							"<b>--</b>")
					else:
						self.widgets["fileselect_preview_label"].set_text(_(
							"Detected ROM: <b>%s</b>.") % "--")

				# Setting use markup for the label which is displayed in any case.
				self.widgets["fileselect_preview_label"].set_use_markup(True) 

			box = gtk.VBox()

			if show_image=="true": #With image mode.
				self.widgets["fileselect_preview_image"] = gtk.Image()
				frame = gtk.Frame()
				frame.add(self.widgets["fileselect_preview_image"])
				box.pack_start(frame,False)

			self.widgets["fileselect_preview_label"] = gtk.Label()
			self.widgets["fileselect_preview_label"].set_justify(gtk.JUSTIFY_CENTER)
			box.pack_start(self.widgets["fileselect_preview_label"])
			box.show_all()

			if show_image=="true": #With image mode.
				self.widgets["fileselect_preview_label"].set_size_request(280,
					-1)
				self.widgets["fileselect_preview_label"].set_line_wrap(True)
				self.widgets["fileselect_dialog"].set_preview_widget(box)
				self.widgets["fileselect_dialog"].set_preview_widget_active(True)
			else:
				self.widgets["fileselect_dialog"].set_extra_widget(box)
			
			self.widgets["fileselect_dialog"].connect("selection-changed",
				update_preview)
			self.widgets["fileselect_dialog"].connect("current-folder-changed",
				scan_dir_for_roms)

			#Performing ROM scanning for the initial folder (if valid).
			if self.widgets["fileselect_dialog"].get_current_folder():
				scan_dir_for_roms()

		self.widgets["fileselect_dialog"].run()

	def load_rom_from_history(self,fullname,path,availability):
		if os.path.exists(path): #ROM exists on file system, continuing...
			archive_infos = self.emulator.archive_recognition(path)

			if archive_infos:
				#Okay. Loading ROM using the obtained infos.
				self.setting_current_rom(path,archive_infos[0], archive_infos[1])

			else: #Unknow ROM that cannot be loaded.
				dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL,
					type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
					message_format=_("Gngeo is not recognizing this ROM "
					"anymore!"))
				dialog.format_secondary_text(_("Such an issue has two "
					"explanations: the ROM archive has been corrupted or the "
					"driver that used to handle this ROM has been altered/"
					"deleted (most probable)."))
				dialog.connect("response", lambda *args: dialog.destroy())
				dialog.show_all()

		else:
			#ROM not found: no loading but display of warning message and rebuilding
			#of the ROM History menu (with visual marks next to unavailable ROM).
			message = _("Cannot continue: the ROM you wanted to load was not "
				"found on the file system!")

			if availability:
				#Since a ROM marked as ``available" wasn't actually found, refreshing
				#the entire ROM History list for the sake of accuracy.
				self.history.refresh_list(size = int(self.params["xgngeo"]["historysize"]))
				self.history_menu_generation()
				message += "\n%s" % _("It is now indicated as unavailable in the ROM "
					"History menu.")

			dialog = gtk.MessageDialog(flags = gtk.DIALOG_MODAL, type = gtk.MESSAGE_WARNING,
				buttons = gtk.BUTTONS_OK, message_format = message)
			dialog.connect("response", lambda *args: dialog.destroy())
			dialog.show_all()

	def manual_rom_loading(self,dialog,response):
		"""Directly loading a ROM from the file chooser."""
		if response == gtk.RESPONSE_OK:
			path = dialog.get_filename()

			if os.path.isfile(path): #Does that file exist?
				archive_infos = self.emulator.archive_recognition(path)

				# Is the archive recognized as a ROM?
				if archive_infos:
					# Okay. Loading ROM using the obtained infos.
					self.setting_current_rom(path,archive_infos[0],archive_infos[1])

				else: # Unknow ROM that cannot be loaded.
					dialog = gtk.MessageDialog(flags=gtk.DIALOG_MODAL,type=gtk.MESSAGE_ERROR,
						buttons=gtk.BUTTONS_OK, message_format = _("This ROM "
						"is unloadable because Gngeo could not find any "
						"suitable driver to handle it."))
					dialog.connect("response", lambda *args: dialog.destroy())
					dialog.show_all()

			else: # Unexisting file!
				dialog = gtk.MessageDialog(flags = gtk.DIALOG_MODAL, type = gtk.MESSAGE_ERROR,
					buttons = gtk.BUTTONS_OK, message_format = _("Error: file doesn't exist!"))
				dialog.connect("response", lambda *args: dialog.destroy())
				dialog.show_all()

	def history_item_clicked(self,widget, event,*args):
		if event.type == gtk.gdk.BUTTON_PRESS:
			if event.button == 1: #Left click: loading ROM.
				self.load_rom_from_history(args[0], args[1], args[2])
			elif event.button == 3: #Right click: popping-up a menu.
				menu = gtk.Menu()
				item = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
				item.connect("activate", self.history_remove, widget, args[3])
				item.show()
				menu.append(item)
				menu.popup(None, None, None, event.button, event.time)

	def history_menu_generation(self):
		"""(Re)Generating ROM History menu from the current ROM History list."""

		# Removing old entries (if any) but keeping the tear-off widget.
		for x in self.widgets["history_menu"].get_children()[1:]:
			self.widgets["history_menu"].remove(x) 

		# Putting the new ones...
		pos = 0
		for val in self.history.get_list():
			if val[2]: menu_item = gtk.MenuItem(val[0])
			else:
				# Adding a ``warning" icon when the ROM is not available on
				# the file system.
				image = gtk.Image()
				image.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_MENU)
				menu_item = gtk.ImageMenuItem(val[0])
				menu_item.set_image(image)
			menu_item.connect("button_press_event", self.history_item_clicked, val[0],
				val[1], val[2], pos)
			self.widgets["history_menu"].append(menu_item)
			pos += 1
		self.widgets["history_menu"].show_all()

	def history_add(self,fullname,path):
		# Get the full name of the Rom
		infos = self.emulator.archive_recognition(path)
		if infos:
			fullname = infos[1]
		# Add  the Rom
		self.history.add_rom(fullname, path, size = int(self.params["xgngeo"]\
			["historysize"])) # Updating ROM History file.
		self.history_menu_generation() # Recreating ROM History menu.

	def history_remove(self,widget, menu_item, position):
		self.history.remove_rom(position)
		self.widgets["history_menu"].remove(menu_item)
		self.history_menu_generation()

	def setting_current_rom(self, path, mamename, fullname):
		# Updating variables.
		self.romPath = path
		self.romMameName = mamename
		self.romFullName = fullname

		# Doing generic post-selection stuffs.
		self.history_add(fullname, path) # Appending ROM to the History list.
		self.widgets["statusbar"].push(self.context_id, _("ROM: \"%s\" (%s)") %
			(fullname, mamename)) # Updating status message.
			
		if self.params["xgngeo"]["autoexecrom"] == "true":
			self.gngeo_exec() #Auto-executing the ROM...
		else:
			#Activating the ``Execute" button.
			self.execMenu_item.set_sensitive(True)

	def about(self,widget):
		dialog = gtk.Dialog(_("About XGngeo"), self.window,
			gtk.DIALOG_NO_SEPARATOR|gtk.DIALOG_MODAL,
			(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
		dialog.set_border_width(5)
		dialog.vbox.set_spacing(4)

		box = gtk.HBox()
		image = gtk.Image()
		image.set_from_file(os.path.join(datarootpath, "img", "minilogo.png"))
		box.pack_start(image, False, padding=4)
		label = gtk.Label("<span color='#008'><b>%s</b>\n%s\n%s</span>" %
			(_("XGngeo: a frontend for Gngeo. :p"), _("Version %s.") % VERSION,
			_("Running Gngeo version %s.") % self.emulator.get_gngeo_version()[1]))
		label.set_justify(gtk.JUSTIFY_CENTER)
		label.set_use_markup(True)
		box.pack_start(label)
		dialog.vbox.pack_start(box)

		label = gtk.Label(__copyright__)
		dialog.vbox.pack_start(label)
		label = gtk.Label(_("This program is released under the terms of the GNU "
			"General Public License."))
		label.set_line_wrap(True)
		label.set_justify(gtk.JUSTIFY_CENTER)
		dialog.vbox.pack_start(label)

		frame = gtk.Frame(_("Credits"))
		container = gtk.EventBox()
		container.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#c9ddff"))
		box = gtk.HBox(spacing=6)
		box.set_border_width(3)

		box2 = gtk.VBox()
		logo = gtk.Image()
		logo.set_from_file(os.path.join(datarootpath, "img", "chprod.png"))
		box2.pack_start(logo)
		label = gtk.Label("<i>http://www.choplair.org/</i>")
		label.set_selectable(True)
		label.set_use_markup(True)
		box2.pack_start(label)
		box.pack_start(box2, padding=10)

		buffer = gtk.TextBuffer()
		buffer.set_text("%s\n\n%s\n%s" % (_(
			"Lead programmer: Choplair.\n"
			"Assisted by: Pachilor.\n"
			"Documentation: Ms. Marie-Claire."),
			_("Translations"),
			_("Brazilian: Matheus Villela.\n"
			"French: Choplair.\n"
			"German: Peter Kainrad.\n"
			"Polish: Mateusz Wolsza.\n"
			"Spanish: Sheng Long Gradilla.")))
		buffer.apply_tag(buffer.create_tag(justification=gtk.JUSTIFY_CENTER,
			editable=False), buffer.get_start_iter(), buffer.get_end_iter())
		buffer.apply_tag(buffer.create_tag(weight=700), buffer.get_iter_at_line(4),
			buffer.get_iter_at_line(5))
		textview = gtk.TextView(buffer)
		textview.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("#c9ddff"))
		box.pack_start(textview)

		container.add(box)
		frame.add(container)

		dialog.vbox.pack_start(frame)
		dialog.connect('response', lambda *args: dialog.destroy())
		dialog.show_all()

	def config(self, widget = None, type = 0, firstrun = 0, romspecific = 0):
		def set_path_icon(widget, image, dir = 0, special = None):
			"""We check whether the path written in the text entry is an
				existing file or directory, and change the icon	in consequence.
				There might have some other special conditions for the icon
				to get changed.
			
			"""
			path = widget.get_text()

			if not special:
				if (dir and os.path.isdir(path)) or os.path.isfile(path):
					stock = 1
				else: stock = 0

			elif special=="biospath":
				#Check for BIOS files.
				if self.get_bios_presence(path):
					stock = 1
					txt = "<span color='darkgreen'>%s</span>" % _("BIOS OK.")
				else:
					stock = 0
					txt = "<span color='red'>%s</span>" % _("No BIOS.")

				bios_label.set_text(txt)
				bios_label.set_use_markup(True)

			elif special=="gngeopath":
				version = self.emulator.get_gngeo_version(path)
				if version:
					#Refusing obsolete Gngeo version.
					if version[0][1:3] < (6, 11):
						stock = 0
						color = "red"
					else:
						stock = 1
						color = "#008"

					gngeoversion_label.set_text("<span color='%s'>v%s</span> " % (color,
					version[1]))
					gngeoversion_label.set_use_markup(True)
					gngeoversion_label.show()

				else:
					stock = 0
					gngeoversion_label.hide()

			image.set_from_stock((gtk.STOCK_NO, gtk.STOCK_YES)[stock],
				gtk.ICON_SIZE_MENU)

		self.widgets["config"]["main_dialog"] = gtk.Dialog(parent=self.window,
			flags=gtk.DIALOG_MODAL)

		if firstrun:
			self.widgets["config"]["main_dialog"].connect("delete_event", self.quit)
		elif not romspecific:
			self.widgets["config"]["main_dialog"].connect("destroy", lambda *args:\
				self.widgets["statusbar"].push(self.context_id, _("Configuration "
				"was not saved.")))

		if type==0:
			#
			# Important path configuration.
			#
			self.widgets["config"]["main_dialog"].set_title(_("Important "
				"path configuration"))
			box = gtk.VBox(spacing=5) #The box. :p
			box.set_border_width(4)
			self.imppathicons = []

			box.pack_start(gtk.Label(_("These paths must be valid for a working "
				"emulation.")))

			frame = gtk.Frame(_("BIOS files location:"))
			box2 = gtk.HBox()

			self.imppathicons.append(gtk.Image())
			box2.pack_start(self.imppathicons[0], False, padding=3)
			bios_label = gtk.Label()
			box2.pack_start(bios_label, False, padding= 3)
			self.widgets["config"]['biospath'] = gtk.Entry()
			self.widgets["config"]['biospath'].connect("changed",
				set_path_icon, self.imppathicons[0], 1, "biospath")
			self.widgets["config"]['biospath'].set_text(self.params["gngeo"]\
				["biospath"])
			box2.pack_start(self.widgets["config"]['biospath'])
			button = gtk.Button()
			image = gtk.Image()
			image.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU)
			button.add(image)
			button.connect("clicked", self.file_select, _("Select the BIOS"
				"files location."), self.widgets["config"]['biospath']\
				.get_text(), "biospath", 1)
			box2.pack_end(button, False)
			frame.add(box2)
			box.pack_start(frame)

			frame = gtk.Frame(_('ROM drivers directory:'))
			box2 = gtk.HBox() 	 
	
			self.imppathicons.append(gtk.Image()) 	 
			box2.pack_start(self.imppathicons[1], False, padding=3) 	 
			self.widgets["config"]['romrcdir'] = gtk.Entry() 	 
			self.widgets["config"]['romrcdir'].connect("changed", set_path_icon, 	 
					self.imppathicons[1]) 	 
			self.widgets["config"]['romrcdir'].set_text(self.params["gngeo"]\
				["romrcdir"])
			box2.pack_start(self.widgets["config"]['romrcdir']) 	 
			button = gtk.Button() 	 
			image = gtk.Image() 	 
			image.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU) 	 
			button.add(image) 	 
			button.connect("clicked", self.file_select, _("Select the ROM "
				"drivers directory."), self.widgets["config"]['romrcdir']\
				.get_text(), "romrcdir", 1)
			box2.pack_end(button, False) 	 
			frame.add(box2) 	 
			box.pack_start(frame)

			frame = gtk.Frame(_("Gngeo executable:"))
			box2 = gtk.HBox()

			self.imppathicons.append(gtk.Image())
			box2.pack_start(self.imppathicons[2], False, padding=3)
			gngeoversion_label = gtk.Label()
			box2.pack_start(gngeoversion_label, False, padding=3)
			self.widgets["config"]['gngeopath'] = gtk.Entry()
			self.widgets["config"]['gngeopath'].connect("changed", set_path_icon,
				self.imppathicons[1], 0, "gngeopath")
			self.widgets["config"]['gngeopath'].set_text(self.params["xgngeo"]\
				["gngeopath"])
			box2.pack_start(self.widgets["config"]['gngeopath'])
			button = gtk.Button()
			image = gtk.Image()
			image.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU)
			button.add(image)
			button.connect("clicked", self.file_select, _("Select the Gngeo executable."),
				self.widgets["config"]['gngeopath'].get_text(), "gngeopath")
			box2.pack_end(button, False)
			frame.add(box2)
			box.pack_start(frame)

			self.widgets["config"]["main_dialog"].vbox.pack_start(box)

		elif type in (1, 2, 3, 4):
			# By default the parameters of these sections will be set with the
			# values of the previously saved global emulation options.
			temp_param = {}
			for key, val in self.params["gngeo"].items(): temp_param[key] = val
			if romspecific:
				# Replace global params by (hypotheticaly) previously saved
				# ROM-specific ones.
				for key,val in self.configfile.get_params(self.mamename).items():
					temp_param[key] = val

			#
			# Global emulation configuration.
			#
			if not romspecific:
				self.widgets["config"]["main_dialog"].set_title(_("Global "
					"emulation configuration."))
			else: self.widgets["config"]["main_dialog"].set_title(_(
				"Specific emulation options for \"%s\".") % self.mamename)
			notebook = gtk.Notebook()

			#
			# DISPLAY section.
			#
			box = gtk.VBox(spacing=4) #The Box. :p
			box.set_border_width(4)
			notebook.append_page(box, gtk.Label(_("Graphic")))

			table = gtk.Table(2, 3)

			#Fullscreen.
			self.widgets["config"]['fullscreen'] = gtk.CheckButton(_("Fullscreen"))
			if temp_param["fullscreen"] == "true":
				self.widgets["config"]['fullscreen'].set_active(1)
			table.attach(self.widgets["config"]['fullscreen'], 0, 1, 0, 1)
			#Interpolation.
			self.widgets["config"]['interpolation'] = gtk.CheckButton(_("Interpolation"))
			if temp_param["interpolation"] == "true":
				self.widgets["config"]['interpolation'].set_active(1)
			table.attach(self.widgets["config"]['interpolation'], 0, 1, 1, 2)
			#Show FPS.
			self.widgets["config"]['showfps'] = gtk.CheckButton(_("Show FPS"))
			if temp_param["showfps"] == "true":
				self.widgets["config"]['showfps'].set_active(1)
			table.attach(self.widgets["config"]['showfps'], 1, 2, 0, 1)
			#Auto Frameskip.
			self.widgets["config"]['autoframeskip'] = gtk.CheckButton(_(
				"Auto Frameskip"))
			if temp_param["autoframeskip"] == "true":
				self.widgets["config"]['autoframeskip'].set_active(1)
			table.attach(self.widgets["config"]['autoframeskip'], 1, 2, 1, 2)
			#Raster effect.
			self.widgets["config"]['raster'] = gtk.CheckButton(_("Raster effect"))
			if temp_param["raster"] == "true":
				self.widgets["config"]['raster'].set_active(True)
			table.attach(self.widgets["config"]['raster'], 0, 1, 2, 3)
			#Hardware surface.
			self.widgets["config"]['hwsurface'] = gtk.CheckButton(_("Hardware surface"))
			if temp_param["hwsurface"] == "true":
				self.widgets["config"]['hwsurface'].set_active(True)
			table.attach(self.widgets["config"]['hwsurface'], 1, 2, 2, 3)

			frame = gtk.Frame(_("Windowed mode"))
			frame.set_label_align(0.5, 0.5)
			box2 = gtk.VBox()

			#Scale.
			adjustment = gtk.Adjustment(float(temp_param["scale"]), 1, 5, 1)
			label = gtk.Label(_("Scale:"))
			box2.pack_start(label)
			self.widgets["config"]['scale'] = gtk.HScale(adjustment)
			self.widgets["config"]['scale'].set_value_pos(gtk.POS_TOP)
			def bouyaka(widget, value): return u"\xd7%i" % value
			self.widgets["config"]['scale'].connect("format-value", bouyaka)
			box2.pack_start(self.widgets["config"]['scale'])

			#320x224 window size.
			self.widgets["config"]['screen320'] = gtk.CheckButton(_("Larger screen"))
			if temp_param["screen320"] == "true": self.widgets["config"]\
				['screen320'].set_active(True)
			box2.pack_end(self.widgets["config"]['screen320'])

			frame.add(box2)
			table.attach(frame, 2, 3, 0, 3)
			box.pack_start(table)

			self.combo_params = {}

			# BLITTER
			frame = gtk.Frame(_("Blitter:"))

			#Translation of known blitter fullnames.
			i18n_dict = {
				"soft": _("Software blitter"),
				"opengl": _("OpenGL blitter"),
				"yuv": _("YUV blitter (YV12)")}

			self.widgets["config"]['blitter'] = gtk.combo_box_new_text()
			i = 0; blitter_list = []
			pipe = os.popen('"%s" --blitter help' % self.params["xgngeo"]\
				["gngeopath"].replace('"','\"'))
			for line in pipe.readlines():
				plop = match("(\S*)\s*:(.*)",line) #Syntax is `REF : FULLNAME'.
				if plop:
					ref,fullname = plop.group(1).strip(),plop.group(2).strip()
					self.widgets["config"]['blitter'].append_text((fullname,
						i18n_dict[ref])[i18n_dict.has_key(ref)])
					blitter_list.append(ref)
					#Setting active the last selection.
					if ref == temp_param["blitter"]:
						self.widgets["config"]['blitter'].set_active(i)
					i += 1
			pipe.close()

			self.combo_params['blitter'] = blitter_list
			frame.add(self.widgets["config"]['blitter'])
			box.pack_start(frame)

			# EFFECT
			frame = gtk.Frame(_("Effect:"))

			#Translation of known effect fullnames.
			i18n_dict = {
				"none": _("No effect"),
				"scanline": _("Scanline effect"),
				"scanline50": _("Scanline 50% effect"),
				"scale2x": _("Scale2x effect"),
				"scale3x": _("Scale3x effect"),
				"scale4x": _("Scale4x effect"),
				"scale2x50": _("Scale2x effect with 50% scanline"),
				"scale2x75": _("Scale2x effect with 75% scanline"),
				"hq2x": _("HQ2X effect. High quality"),
				"hq3x": _("HQ3X effect. High quality"),
				"lq2x": _("LQ2X effect. Low quality"),
				"lq3x": _("LQ3X effect. Low quality"),
				"doublex": _("Double the x resolution (soft blitter only)"),
				"sai": _("SAI effect"),
				"supersai": _("SuperSAI effect"),
				"eagle": _("Eagle effect")}

			self.widgets["config"]['effect'] = gtk.combo_box_new_text()
			self.widgets["config"]['effect'].set_wrap_width(2)
			i=0; effect_list = []
			pipe = os.popen('"%s" --effect help' % self.params["xgngeo"]["gngeopath"]\
				.replace('"', '\"'))
			for line in pipe.readlines():
				plop = match("(\S*)\s*:(.*)",line) #Syntax is "REF : FULLNAME"
				if plop:
					ref, fullname = plop.group(1).strip(), plop.group(2).strip()
					self.widgets["config"]['effect'].append_text((fullname,
						i18n_dict[ref])[i18n_dict.has_key(ref)])
					effect_list.append(ref)
					#Setting active the last selection.
					if ref == temp_param["effect"]:
						self.widgets["config"]['effect'].set_active(i)
					i += 1
			pipe.close()

			self.combo_params['effect'] = effect_list
			frame.add(self.widgets["config"]['effect'])
			box.pack_start(frame)

			def bouyaka(*args):
				"""Overlay does not support effect. So, when this blitter is selected, we
					set the effect to ``none" and prevent it from being changed by user.
					Effects are also not (yet) supported when enabling hardware surface.
				
				"""
				if self.combo_params['blitter'][self.widgets["config"]['blitter']\
					.get_active()]=="yuv" or self.widgets["config"]['hwsurface']\
					.get_active():
					temp_param['effect'] = "none" #Changing param.
					self.widgets["config"]['effect'].set_active(0) #Changing widget.
					#Effect cannot be changed any more.
					self.widgets["config"]['effect'].set_sensitive(False) 
				else: 
					#Resetting widget's sensibility.
					self.widgets["config"]['effect'].set_sensitive(True) 

			#Performing special actions over effect widget regarding blitter selection
			#or hardware surface activation.
			bouyaka()
			self.widgets["config"]['blitter'].connect("changed", bouyaka)
			self.widgets["config"]['hwsurface'].connect("toggled", bouyaka)

			box2 = gtk.HBox()
			label = gtk.Label(_("Transparency pack (optional):"))
			box2.pack_start(label)
			image = gtk.Image()
			box2.pack_start(image, False, padding=3)
			self.widgets["config"]['transpack'] = gtk.Entry()
			self.widgets["config"]['transpack'].connect("changed",
				set_path_icon, image)
			self.widgets["config"]['transpack'].set_text(self.params["gngeo"]\
				["transpack"] or "--")
			box2.pack_start(self.widgets["config"]['transpack'])
			set_path_icon(self.widgets["config"]['transpack'], image)
			button = gtk.Button()
			image = gtk.Image()
			image.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU)
			button.add(image)
			button.connect("clicked", self.file_select, _("Select a "
				"transparency pack."), self.widgets["config"]['transpack']\
				.get_text(), "transpack")
			box2.pack_end(button, False)
			box.pack_start(box2, False)

			#
			# AUDIO / JOYSTICK section.
			#
			box = gtk.VBox(spacing=4) #The Box.
			box.set_border_width(4)
			notebook.append_page(box,gtk.Label(_("Audio / Joystick")))

			frame = gtk.Frame(_("Audio"))
			box2 = gtk.VBox()

			def bouyaka(widget, target):
				"""Setting widget sensitive state according to another
					widget's activation state.
				
				"""
				target.set_sensitive(widget.get_active())

			self.widgets["config"]['sound'] = gtk.CheckButton(_("Enable sound"))
			box2.pack_start(self.widgets["config"]['sound'])

			#Sample rate.
			box3 = gtk.HBox()
			box2.pack_end(box3)
			label = gtk.Label(_("Sample rate:"))
			box3.pack_start(label)

			self.widgets["config"]['samplerate'] = gtk.combo_box_new_text()
			i=0
			self.combo_params['samplerate'] = ["8192", "11025", "22050",
				"32000", "44100", "48000"]
			for val in self.combo_params['samplerate']:
				self.widgets["config"]['samplerate'].append_text("%sHz" % val)
				#Setting active the last selection
				if val==temp_param["samplerate"]:
					self.widgets["config"]['samplerate'].set_active(i)
				i += 1
			box3.pack_start(self.widgets["config"]['samplerate'])
			#Bouyaka!
			self.widgets["config"]['sound'].connect("toggled", bouyaka, box3)
			if temp_param['sound'] == 'true':
				self.widgets["config"]['sound'].set_active(1)
			else: bouyaka(self.widgets["config"]['sound'], box3)

			frame.add(box2)
			box.pack_start(frame)

			frame = gtk.Frame(_("Joystick"))
			box2 = gtk.VBox()

			self.widgets["config"]['joystick'] = gtk.CheckButton(
				_("Enable joystick support"))
			box2.pack_start(self.widgets["config"]['joystick'])

			table = gtk.Table(2,2)
			box2.pack_end(table)

			label = gtk.Label(_("Player 1 device:"))
			table.attach(label,0,1,0,1)
			self.widgets["config"]['p1joydev'] = gtk.combo_box_new_text()
			for x in range(4): self.widgets["config"]['p1joydev'].append_text(
				"/dev/js%s" % x)
			#Setting active the last selection
			self.widgets["config"]['p1joydev'].set_active(int(temp_param["p1joydev"])) 
			table.attach(self.widgets["config"]['p1joydev'], 1, 2, 0, 1)

			label = gtk.Label(_("Player 2 device:"))
			table.attach(label,0,1,1,2)
			self.widgets["config"]['p2joydev'] = gtk.combo_box_new_text()
			for x in range(4): self.widgets["config"]['p2joydev'].append_text(
				"/dev/js%s" % x)
			#Setting active the last selection
			self.widgets["config"]['p2joydev'].set_active(int(temp_param["p2joydev"])) 
			table.attach(self.widgets["config"]['p2joydev'], 1, 2, 1, 2)

			#Bouyaka!
			self.widgets["config"]['joystick'].connect("toggled",bouyaka,table)
			if temp_param['joystick']=='true':
				self.widgets["config"]['joystick'].set_active(1)
			else: bouyaka(self.widgets["config"]['joystick'],table)

			frame.add(box2)
			box.pack_start(frame)

			#
			# CONTROLS section.
			#
			self.toggled = None

			# Key order : A, B, C, D, START, COIN, UP, DOWN, LEFT, RIGHT,
			#                       hotkey1, hotkey2, hotkey3, hotkey4
			key_list = ["A", "B", "C", "D", "START", "COIN", "UP", "DOWN",
				"LEFT", "RIGHT", "hotkey1", "hotkey2", "hotkey3", "hotkey4"]

			# The Gngeo compliant keymap (all in lowercase)!
			compliant_KeyMap = {
				"backspace":8, "tab":9, "return":13, "pause":19, "space":32, "exclam":33,
				"quotedbl":34, "dollar":36, "ampersand":38, "apostrophe":39, "parenleft":\
				40, "parenright":41, "comma":44, "minus":45, "colon":58, "semicolon":59,
				"less":60, "equal":61, "asciicircum":94, "underscore":95, "a":97, "b":98,
				"c":99, "d":100, "e":101, "f":102, "g":103, "h":104, "i":105, "j":106,
				"k":107, "l":108, "m":109, "n":110, "o":111, "p":112, "q":113, "r":114,
				"s":115, "t":116, "u":117, "v":118, "w":119, "x":120, "y":121, "z":122,
				"delete":127, "twosuperior":178, "agrave":224, "ccedilla":231, "egrave":\
				232, "eacute":233, "ugrave":249, "kp_0":256, "kp_1":257, "kp_2":258,
				"kp_3":259, "kp_4":260, "kp_5":261, "kp_6":262, "kp_home":263, "kp_7":263,
				"kp_up":264, "kp_8":264, "kp_9":265, "kp_decimal":266, "kp_divide":267,
				"kp_multiply":268, "kp_subtract":269, "kp_add":270, "kp_enter":271, "up":\
				273, "down":274, "right":275, "left":276, "insert":277, "home":278, "end":\
				279, "page_up":280, "page_down":281, "num_lock":300, "caps_lock":301,
				"scroll_lock":302, "shift_r":303, "shift_l":304, "control_r":305,
				"control_l":306, "super_l":311, "super_r":312, "print":316}
			# Reverse mode.
			compliant_KeyMap_reverse = {
				8:"backspace", 9:"tab", 13:"return", 19:"pause", 32:"space", 33:"exclam",
				34:"quotedbl", 36:"dollar", 38:"ampersand", 39:"apostrophe", 40:\
				"parenleft", 41:"parenright", 44:"comma", 45:"minus", 58:"colon", 59:\
				"semicolon",60:"less", 61:"equal", 94:"asciicircum", 95:"underscore", 97:\
				"a", 98:"b", 99:"c", 100:"d", 101:"e", 102:"f", 103:"g", 104:"h", 105:"i",
				106:"j", 107:"k", 108:"l", 109:"m", 110:"n", 111:"o", 112:"p", 113:"q",
				114:"r", 115:"s", 116:"t", 117:"u", 118:"v", 119:"w", 120:"x", 121:"y",
				122:"z", 127:"delete", 178:"twosuperior", 224:"agrave", 231:"ccedilla",
				232:"egrave", 233:"eacute", 249:"ugrave", 256:"kp_0", 257:"kp_1", 258:\
				"kp_2", 259:"kp_3", 260:"kp_4", 261:"kp_5", 262:"kp_6", 263:"kp_home",\
				263:"kp_7", 264:"kp_up", 264:"kp_8", 265:"kp_9", 266:"kp_decimal", 267:\
				"kp_divide", 268:"kp_multiply", 269:"kp_subtract", 270:"kp_add", 271:\
				"kp_enter", 273:"up", 274:"down", 275:"right", 276:"left", 277:"insert",
				278:"home", 279:"end", 280:"page_up", 281:"page_down", 300:"num_lock",
				301:"caps_lock", 302:"scroll_lock", 303:"shift_r", 304:"shift_l", 305:\
				"control_r", 306:"control_l", 311:"super_l", 312:"super_r", 316:"print"}

			def get_pressed(widget, event, key_pos, secondplayer=0):
				if widget.get_active() and event.keyval:  # Only when widget is active.
					key_val = gtk.gdk.keyval_to_lower(event.keyval)  # Get the value (lower only).

					# GTK's keys of XGngeo are not same as SDL's used by Gngeo. T_T
					# So, a Gngeo compatible key-value is given according to its
					# GTK's name (set in lowercase).
					key_name = gtk.gdk.keyval_name(key_val).lower()

					if key_name in compliant_KeyMap.keys():
						if secondplayer:
							self.p2key_int_vals[key_pos] = compliant_KeyMap[key_name]
						else: self.p1key_int_vals[key_pos] = compliant_KeyMap[key_name]

						# Putting the key name (in an elegant form :p) as button label.
						widget.set_label(capwords(key_name.replace("_", " ")))
						if not key_name in ("return", "space"): widget.clicked()

			def toggled(widget):
				# Ensuring that only one key button is toggled...
				if self.toggled and self.toggled != widget:
					if self.toggled.get_active():
						# Previous button goes back to normal state.
						self.toggled.set_active(False)

				#Changing current toggled button state.
				self.toggled = widget

			box = gtk.VBox(spacing=4) # The box. :p
			box.set_border_width(4)
			notebook.append_page(box, gtk.Label(_("Controls")))

			label = gtk.Label(_("To modify a key, click on the button under "
				"it's icon, then push your new key. It works for keyboard "
				"only."))
			label.set_justify(gtk.JUSTIFY_CENTER)
			label.set_line_wrap(True)
			box.pack_start(label, False)

			table = gtk.Table(6, 6)  # The sweet table O_o;;

			def playerChanged(widget,justloaded=False):
				"""Perform some interface modifications when another player
					selection is changed.
				
				"""
				player = self.widgets["config"]['player1controls_radio']\
					.get_active() or 2

				#Changing the hotkey edition label.
				self.widgets["config"]['edithotkeys_label'].set_text(
					_("Edit player %i hotkeys...") % player)

				if player == 1:  # Showing P1 keys and hidding P2's.
					if not justloaded:  # P1 keys are already shown after window loading.
						for x in p1keywidgets: x.show()
					for x in p2keywidgets: x.hide()
				else:  # Showing P2 keys and hidding P1's.
					for x in p2keywidgets: x.show()
					for x in p1keywidgets: x.hide()

			# Control allocation.
			frame = gtk.Frame(_("Allocation:"))
			frame.set_border_width(4)
			box2 = gtk.VBox()
			frame.add(box2)
			self.widgets["config"]['player1controls_radio'] = gtk.RadioButton(
				None, _("Player 1"))
			self.widgets["config"]['player1controls_radio'].connect("toggled",
				playerChanged)
			box2.pack_start(self.widgets["config"]['player1controls_radio'])
			radio = gtk.RadioButton(self.widgets["config"]['player1controls_radio'],
				_("Player 2"))
			radio.connect("toggled", playerChanged)
			box2.pack_start(radio)
			table.attach(frame, 0, 2, 0, 2, xpadding=15, ypadding=0)

			def editHotkeys(widget):
				player = int(self.widgets["config"]['player1controls_radio']\
					.get_active()) or 2
				buttval_convertion = {"1":  "A", "2": "B", "4": "C", "8": "D"}
				hk_boxes = []

				# Initial blank matrix (if not yet created & filled).
				if not self.params["temp"].has_key("hotkey_matrix_p%i" %
					player):
					self.params["temp"]["hotkey_matrix_p%i" % player]  =  \
						[[None] * 4, [None] * 4, [None] * 4, [None] * 4]
					# The initial matrix is used to revert previous hotkeys
					# configuration (if the changes are cancelled).
					self.params["temp"]["backup_matrix_p%i" % player]  =  \
						[[None] * 4, [None] * 4, [None] * 4, [None] * 4]
					for hotkey in range(4):
						if self.params["gngeo"]["p%ihotkey%i" % (player,
							hotkey)]:
							i = 0
							for butt in self.params["gngeo"]["p%ihotkey%i" %
								(player, hotkey)].split(","):
								self.params["temp"]["hotkey_matrix_p%i" %
									player ][hotkey][i] = butt
								self.params["temp"]["backup_matrix_p%i" %
									player][hotkey][i] = butt
								i += 1

				def dialResponse(widget, response):
					if response == gtk.RESPONSE_ACCEPT:
						# Saving current matrix for hypothetical restoration.
						for hotkey in range(4):
							i = 0
							for butt in self.params["temp"]["hotkey_matrix_p%i" %
								player][hotkey]:
								self.params["temp"]["backup_matrix_p%i" %
									player][hotkey][i] = butt
								i += 1
					elif response == gtk.RESPONSE_REJECT:
						# Restoring the previously saved matrix.
						for hotkey in range(4):
							i = 0
							for butt in self.params["temp"]["backup_matrix_p%i" %
								player][hotkey]:
								self.params["temp"]["hotkey_matrix_p%i" %
								player ][hotkey][i] = butt
								i += 1
					widget.destroy()

				def buttonClicked(button, event, image, player, hotkey, pos, 
					addition=False):
					def buttChanged(widget, value):
						self.params["temp"]["hotkey_matrix_p%i" % player]\
							[hotkey][pos] = value
						image.set_from_file(os.path.join(datarootpath, "img",
							"key_%s.png" %	buttval_convertion[value]))
						if addition: 
							# One button has been added: let's regen hotkey's row.
							gen_hotkey_row(hotkey) 

					def buttRemoved(*args):
						del self.params["temp"]["hotkey_matrix_p%i" % player ]\
							[hotkey][pos]
						self.params["temp"]["hotkey_matrix_p%i" % player ]\
							[hotkey].append(None)
						genHotkeyRow(hotkey)

					firebuttons = buttval_convertion.keys()
					firebuttons.sort()
					hkbinding = self.params["temp"]["hotkey_matrix_p%i" %
						player ][hotkey]
					for x in hkbinding:
						if x: firebuttons.remove(x)

					menu = gtk.Menu()
					if hkbinding[pos]:
						item = gtk.ImageMenuItem()
						image2 = gtk.Image()
						image2.set_from_stock(gtk.STOCK_REMOVE,
							gtk.ICON_SIZE_BUTTON)
						item.add(image2)
						item.connect("activate", buttRemoved)
						menu.append(item)

					for butt in firebuttons:
						item = gtk.ImageMenuItem()
						image2 = gtk.Image()
						image2.set_from_file(os.path.join(datarootpath, "img",
							"key_%s.png" %	buttval_convertion[butt]))
						item.connect("activate", buttChanged,butt)
						item.add(image2)
						menu.append(item)

					menu.popup(None,None,None,event.button,event.time)
					menu.show_all()

				def genHotkeyRow(row,firstgen=False):
					if firstgen: # Creating & attaching the box.
						hk_boxes.append(gtk.HBox())
						table.attach(hk_boxes[row], 2, 3, row, row + 1)
					else: # Emptying the box.
						for x in hk_boxes[row].get_children():
							hk_boxes[row].remove(x)

					j = 1
					for butt in self.params["temp"]["hotkey_matrix_p%i" %
						player ][row]:
						if not butt:
							# Hot key's end has been reached, getting out the ``for".
							break

						if firstgen: # Filling the hot key matrix with the right values.
							self.params["temp"]["hotkey_matrix_p%i" % player ]\
								[row][ j -1] = butt

						image = gtk.Image()
						image.set_from_file(os.path.join(datarootpath,"img",
							"key_%s.png" %	buttval_convertion[butt]))
						button = gtk.Button()
						button.add(image)
						button.connect("button_press_event", buttonClicked, image,
							player, row, j - 1)
						hk_boxes[row].pack_start(button)
						if j<4:
							label = gtk.Label("+")
							hk_boxes[row].pack_start(label)
						j += 1

					if j<=4:
						button = gtk.Button()
						image = gtk.Image()
						image.set_from_stock(gtk.STOCK_ADD,
							gtk.ICON_SIZE_BUTTON)
						button.add(image)
						button.connect("button_press_event", buttonClicked, image,
							player, row, j - 1, True)
						hk_boxes[row].pack_start(button)

					hk_boxes[row].show_all()

				dialog = gtk.Dialog(_("Hotkeys edition for player %i.") % player,
					self.widgets["config"]["main_dialog"],gtk.DIALOG_MODAL,(
					gtk.STOCK_OK,	gtk.RESPONSE_ACCEPT, gtk.STOCK_CANCEL,
					gtk.RESPONSE_REJECT))
				dialog.connect("response", dialResponse)
				label = gtk.Label(_("Here you can bind hotkeys to your desired "
					"combinations of fire buttons."))
				label.set_justify(gtk.JUSTIFY_CENTER)
				label.set_padding(3, 4)
				label.set_line_wrap(True)
				dialog.vbox.pack_start(label, False)

				table = gtk.Table(4, 3)
				table.set_col_spacings(4)
				for i in range(4):
					image = gtk.Image()
					image.set_from_file(os.path.join(datarootpath, "img",
						"hotkey%i.png" % (i + 1)))
					table.attach(image, 0, 1, i, i + 1, xoptions=gtk.SHRINK)
					label = gtk.Label("=")
					table.attach(label, 1, 2, i, i + 1, xoptions=gtk.SHRINK)
					genHotkeyRow(i, True)

				box.set_border_width(4)
				dialog.vbox.pack_end(table)
				dialog.show_all()

			# Hotkeys edition.
			button = gtk.Button()
			self.widgets["config"]['edithotkeys_label'] = gtk.Label()
			self.widgets["config"]['edithotkeys_label'].set_size_request(100,
				-1)
			self.widgets["config"]['edithotkeys_label'].set_line_wrap(True)
			self.widgets["config"]['edithotkeys_label'].set_justify\
				(gtk.JUSTIFY_CENTER)
			button.add(self.widgets["config"]['edithotkeys_label'])
			button.connect("clicked",editHotkeys)
			table.attach(button, 0, 2, 4, 6, xpadding=15, ypadding=15)

			if len(temp_param["p1key"].split(",")) == len(key_list):
				# Given values seems to be okay.
				plop = temp_param["p1key"]
			else: # There's a crap, let's use default key values.
				plop = self.configfile.get_default_params()[0]["p1key"]
			self.p1key_int_vals = plop.split(",")

			p1key_names = []
			#Display the names of known key values.
			for x in self.p1key_int_vals:
				if int(x) in compliant_KeyMap_reverse.keys():
					p1key_names.append(capwords(compliant_KeyMap_reverse\
						[int(x)].replace("_", " ")))
				else: p1key_names.append(x)

			p1keywidgets = []; i=0
			for x in p1key_names:
				#Generate P1key's buttons.
				p1keywidgets.append(gtk.ToggleButton((x, "--")[x == "-1"]))
				p1keywidgets[i].connect("toggled", toggled)
				p1keywidgets[i].connect("key_press_event", get_pressed, i)
				p1keywidgets[i].set_use_underline(False)
				i+=1

			if len(temp_param["p2key"].split(",")) == len(key_list):
				#Given values seems to be okay.
				plop = temp_param["p2key"]
			else: #There's a crap, let's use default key values.
				plop = self.configfile.get_default_params()[0]["p2key"]
			self.p2key_int_vals = plop.split(",")

			p2key_names = []
			#Display the names of known key values.
			for x in self.p2key_int_vals:
				if int(x) in compliant_KeyMap_reverse.keys():
					p2key_names.append(capwords(compliant_KeyMap_reverse\
						[int(x)].replace("_", " ")))
				else: p2key_names.append(x)

			p2keywidgets = []; i = 0
			for x in p2key_names:
				# Generate P2key's buttons.
				p2keywidgets.append(gtk.ToggleButton((x, "--")[x == "-1"]))
				p2keywidgets[i].connect("toggled", toggled)
				p2keywidgets[i].connect("key_press_event", get_pressed, i, 1)
				p2keywidgets[i].set_use_underline(False)

				# Displaying key's icon.
				image = gtk.Image()
				if i<10: 
					image.set_from_file(os.path.join(datarootpath, "img",
						"key_%s.png" % key_list[i]))
				else: # Hotkeys.
					image.set_from_file(os.path.join(datarootpath, "img",
						"%s.png" % key_list[i]))

				box2 = gtk.HBox()  # A box...
				box2.set_size_request(70, 35)
				box2.pack_start(p1keywidgets[i])  # with P1 key...
				box2.pack_start(p2keywidgets[i])  # and P2 key :p

				# Put them in table...
				if i < 6:  # First 6 keys (fire buttons + start/coin) on 2nd row.
					table.attach(image, i, i + 1, 2, 3)
					table.attach(box2, i, i + 1, 3, 4)
				elif i < 10:  # Keys from 6 to 10 (arrows) on 1st row.
					table.attach(image, i - 4, i - 3, 0, 1)
					table.attach(box2, i - 4, i - 3,1, 2)
				elif i < 14:  # Keys from 10 to 14 (hotkeys) on 3rd row.
					table.attach(image, i - 8, i - 7, 4, 5)
					table.attach(box2, i - 8, i - 7, 5, 6)
				i+=1

			box.pack_start(table)

			#
			# SYSTEM section.
			#
			box = gtk.VBox(spacing=4)  # The box :p
			box.set_border_width(4)
			notebook.append_page(box, gtk.Label(_("System")))

			# System.
			frame2 = gtk.Frame(_("Neo Geo BIOS type:"))
			box2 = gtk.HBox()
			self.widgets["config"]['system_arcade'] = gtk.RadioButton(None,
				_("Arcade"))
			box2.pack_start(self.widgets["config"]['system_arcade'])
			self.widgets["config"]['system_home'] = \
				gtk.RadioButton(self.widgets["config"]['system_arcade'],
				_("Home (AES)"))
			box2.pack_start(self.widgets["config"]['system_home'])
			radio = gtk.RadioButton(self.widgets["config"]['system_arcade'],
				_( "Universal"))
			box2.pack_start(radio)

			# Setting selection.
			if temp_param["system"] == "arcade":
				self.widgets["config"]['system_arcade'].set_active(1)
			elif temp_param["system"] == "home":
				self.widgets["config"]['system_home'].set_active(1)
			elif temp_param["system"] == "unibios": radio.set_active(1)

			# Making unavailable BIOS unselectable.
			val = self.get_bios_presence(self.params["gngeo"]["biospath"])
			if val == 7: pass
			else:
				if val in (6, 4, 2):
					self.widgets["config"]['system_arcade'].set_sensitive(False)
				if val in (5, 4, 1):
					self.widgets["config"]['system_home'].set_sensitive(False)
				if val in (3, 2, 1):
					radio.set_sensitive(False)

			frame2.add(box2)
			box.pack_start(frame2)

			# Country.
			frame2 = gtk.Frame(_("Country:"))

			table = gtk.Table(3, 3)
			self.widgets["config"]['country_japan'] = gtk.RadioButton(None,
				_("Japan"))
			table.attach(self.widgets["config"]['country_japan'], 0, 1, 0, 1)
			image = gtk.Image()
			image.set_from_file(os.path.join(datarootpath, "img", "japan.png"))
			table.attach(image, 0, 1, 1, 2)

			self.widgets["config"]['country_usa'] = gtk.RadioButton(
			self.widgets["config"]['country_japan'],_("USA"))
			table.attach(self.widgets["config"]['country_usa'], 1, 2, 0, 1)
			image = gtk.Image()
			image.set_from_file(os.path.join(datarootpath, "img", "usa.png"))
			table.attach(image, 1, 2, 1, 2)

			radio = gtk.RadioButton(self.widgets["config"]['country_japan'],
				_("Europe"))
			table.attach(radio, 2, 3, 0, 1)
			image = gtk.Image()
			image.set_from_file(os.path.join(datarootpath, "img",
				"europe.png"))
			table.attach(image, 2, 3, 1, 2)

			if temp_param["country"] == "japan":
				self.widgets["config"]['country_japan'].set_active(1)
			elif temp_param["country"] == "usa": 
				self.widgets["config"]['country_usa'].set_active(1)
			elif temp_param["country"] == "europe":
				radio.set_active(1)
				
			table.attach(gtk.Label("This option has no effect for the "
				"universal BIOS."), 0, 3, 2, 3)

			frame2.add(table)
			box.pack_start(frame2)

			table = gtk.Table(2,2)
			box.pack_start(table)

			def bouyaka(widget, value):
				if value>=1: return "+%i%%" % value
				else: return "%i%%" % value

			# 68kclock
			adjustment = gtk.Adjustment(float(temp_param["68kclock"]), -80, 80,
				10)
			label = gtk.Label(_("68K CPU clock:"))
			table.attach(label, 0, 1, 0, 1)
			self.widgets["config"]['68kclock'] = gtk.HScale(adjustment)
			self.widgets["config"]['68kclock'].set_value_pos(gtk.POS_LEFT)
			self.widgets["config"]['68kclock'].connect("format-value",bouyaka)
			table.attach(self.widgets["config"]['68kclock'], 1, 2, 0, 1)

			# Z80clock.
			adjustment = gtk.Adjustment(float(temp_param["z80clock"]), -80, 80,
				10)
			label = gtk.Label(_("Z80 CPU clock:"))
			table.attach(label, 0, 1, 1, 2)
			self.widgets["config"]['z80clock'] = gtk.HScale(adjustment)
			self.widgets["config"]['z80clock'].set_value_pos(gtk.POS_LEFT)
			self.widgets["config"]['z80clock'].connect("format-value", bouyaka)
			table.attach(self.widgets["config"]['z80clock'], 1, 2, 1, 2)

			# Packing the Notebook
			self.widgets["config"]["main_dialog"].vbox.pack_start(notebook) 

		elif type==5:
			#
			# Other things configuration.
			#
			self.widgets["config"]["main_dialog"].set_title(
				_("Other things configuration"))
			table = gtk.Table(3, 4) #The box :p
			table.set_row_spacings(5)
			table.set_border_width(6)

			# LibGL path.
			frame = gtk.Frame(_("Path to libGL.so (optional):"))
			box2 = gtk.HBox()
			image = gtk.Image()
			box2.pack_start(image, False, padding=3)
			self.widgets["config"]['libglpath'] = gtk.Entry()
			self.widgets["config"]['libglpath'].connect("changed", set_path_icon, image)
			self.widgets["config"]['libglpath'].set_text(self.params["gngeo"]\
				["libglpath"])
			box2.pack_start(self.widgets["config"]['libglpath'])
			set_path_icon(self.widgets["config"]['libglpath'],image)
			button = gtk.Button()
			image = gtk.Image()
			image.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU)
			button.add(image)
			button.connect("clicked", self.file_select, _('Select the "%s" file.') %
				"libGL.so", self.widgets["config"]['libglpath'].get_text(), "libglpath")
			box2.pack_end(button, False)
			frame.add(box2)
			table.attach(frame, 0, 1, 0, 1)

			# Bouyaka!
			def bouyaka(widget, *targets):
				"""Set list size widgets sensitive state according
				to answer mode widget selected param."""
				for x in targets: x.set_sensitive(widget.get_active())

			# Preview image directory.
			frame = gtk.Frame(_("Preview image directory (optional):"))
			box2 = gtk.HBox()
			self.widgets["config"]['previewimages'] = gtk.CheckButton()
			box2.pack_start(self.widgets["config"]['previewimages'], False)
			image = gtk.Image()
			box2.pack_start(image,False,padding=3)
			self.widgets["config"]['previewimagedir'] = gtk.Entry()
			self.widgets["config"]['previewimagedir'].connect("changed",
				set_path_icon, image, 1)
			self.widgets["config"]['previewimagedir'].set_text(
				self.params["xgngeo"]["previewimagedir"])
			box2.pack_start(self.widgets["config"]['previewimagedir'])
			button = gtk.Button()
			image2 = gtk.Image()
			image2.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU)
			button.add(image2)
			button.connect('clicked',self.file_select, _("Select the preview "
				"image directory."),self.widgets["config"]['previewimagedir']\
				.get_text(), "previewimagedir", 1)
			box2.pack_end(button,False)
			frame.add(box2)
			table.attach(frame, 0, 1, 1, 2)
			# Bouyaka.
			if self.params["xgngeo"]['previewimages'] == "true":
				self.widgets["config"]['previewimages'].set_active(1)
			else: 
				bouyaka(self.widgets["config"]['previewimages'], image,
					self.widgets["config"]['previewimagedir'], button)
			self.widgets["config"]['previewimages'].connect("toggled", bouyaka,
				image, self.widgets["config"]['previewimagedir'], button)

			# ROM infos XML.
			frame = gtk.Frame(_("XML file containing ROM infos (optional):"))
			box2 = gtk.HBox()
			self.widgets["config"]['rominfos'] = gtk.CheckButton()
			box2.pack_start(self.widgets["config"]['rominfos'], False)
			image = gtk.Image()
			box2.pack_start(image,False,padding=3)
			self.widgets["config"]['rominfoxml'] = gtk.Entry()
			self.widgets["config"]['rominfoxml'].connect("changed", set_path_icon, image)
			self.widgets["config"]['rominfoxml'].set_text(self.params["xgngeo"]\
				["rominfoxml"])
			box2.pack_start(self.widgets["config"]['rominfoxml'])
			button = gtk.Button()
			image2 = gtk.Image()
			image2.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU)
			button.add(image2)
			button.connect("clicked",self.file_select, _("Select the XML file "
				"containing ROM infos."), self.widgets["config"]['rominfoxml']\
				.get_text(), "rominfoxml")
			box2.pack_end(button, False)
			frame.add(box2)
			table.attach(frame, 0, 1, 2, 3)
			# Bouyaka.
			if self.params["xgngeo"]['rominfos'] == "true":
				self.widgets["config"]['rominfos'].set_active(1)
			else:
				bouyaka(self.widgets["config"]['rominfos'],image,self.widgets["config"]\
					['rominfoxml'], button)
			self.widgets["config"]['rominfos'].connect("toggled", bouyaka, image,
				self.widgets["config"]['rominfoxml'], button)

			# History size
			box2 = gtk.HBox()
			label = gtk.Label(_("Maximum size of the ROM history menu:"))
			box2.pack_start(label)
			adjustment = gtk.Adjustment(float(self.params["xgngeo"]["historysize"]),
				1,20,1)
			self.widgets["config"]['historysize'] = gtk.SpinButton(adjustment)
			box2.pack_start(self.widgets["config"]['historysize'],False)
			table.attach(box2, 0, 1, 3, 4)

			# Column separation.
			table.attach(gtk.VSeparator(), 1, 2, 0, 4, xpadding=6, ypadding=8)

			box2 = gtk.VBox(spacing=3)

			# Auto-execute ROMs.
			self.widgets["config"]['autoexecrom'] = gtk.CheckButton(
				_("Auto-execute ROMs after loading."))
			if self.params["xgngeo"]["autoexecrom"] == "true":
				self.widgets["config"]['autoexecrom'].set_active(True)
			box2.pack_start(self.widgets["config"]['autoexecrom'])

			# Center XGngeo window.
			self.widgets["config"]['centerwindow'] = gtk.CheckButton(
				_("Center XGngeo window on start."))
			if self.params["xgngeo"]["centerwindow"] == "true":
				self.widgets["config"]['centerwindow'].set_active(True)
			box2.pack_start(self.widgets["config"]['centerwindow'])

			# Sleep when idle.
			self.widgets["config"]['sleepidle'] = gtk.CheckButton(
				_("Let emulator sleep when idle."))
			if self.params["gngeo"]["sleepidle"] == "true":
				self.widgets["config"]['sleepidle'].set_active(True)
			box2.pack_start(self.widgets["config"]['sleepidle'])

			# Benchmark mode.
			self.widgets["config"]['bench'] = gtk.CheckButton(
				_("Execute ROMs in benchmark mode."))
			if self.params["gngeo"]["bench"] == "true":
				self.widgets["config"]['bench'].set_active(True)
			box2.pack_start(self.widgets["config"]['bench'])

			frame = gtk.Frame(_("ROM list"))
			table2 = gtk.Table(3, 2)
			
			# Show available ROMs only.
			self.widgets["config"]['showavailableromsonly'] = gtk.CheckButton(
				_("Only show available ROMs by default."))
			if self.params["xgngeo"]["showavailableromsonly"] == "true":
				self.widgets["config"]['showavailableromsonly'].set_active(True)
			table2.attach(self.widgets["config"]['showavailableromsonly'], 0,
				3, 0, 1)

			def color_select(container):
				def callback(widget, response):
					if response == gtk.RESPONSE_OK:
						# Updating color value and the container background.

						self.params["temp"]["availableromcolor"] = \
							gtk.color_selection_palette_to_string(
							[colorsel.get_current_color()])
							
						container.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(
							self.params["temp"]["availableromcolor"]))

					dialog.destroy() # Closing the dialog in any case.

				dialog = gtk.Dialog(title=_("Set available ROM background color"),
					flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
					buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
					gtk.RESPONSE_CANCEL))
				
				colorsel = gtk.ColorSelection()
				colorsel.set_current_color(gtk.color_selection_palette_from_string(
					self.params["temp"]["availableromcolor"])[0])
				dialog.vbox.pack_start(colorsel)
	
				dialog.connect("response", callback)
				dialog.show_all()

			#Available ROM background color.
			label = gtk.Label(_("Available ROM background color:"))
			table2.attach(label, 0, 1, 1, 2)
			self.params["temp"]["availableromcolor"] = self.params["xgngeo"]\
				["availableromcolor"]
			container = gtk.EventBox()
			container.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(
				self.params["temp"]["availableromcolor"]))
			table2.attach(container, 1, 2, 1, 2)
			button = gtk.Button()
			image = gtk.Image()
			image.set_from_stock(gtk.STOCK_SELECT_COLOR, gtk.ICON_SIZE_BUTTON)
			button.add(image)
			button.connect_object("clicked", color_select, container)
			table2.attach(button, 2, 3, 1, 2)

			frame.add(table2)
			box2.pack_start(frame)

			table.attach(box2, 2, 3, 0, 4)

			self.widgets["config"]["main_dialog"].vbox.pack_start(table)

		#``Save" Button
		button = gtk.Button(stock=gtk.STOCK_SAVE)

		#File writing adapted method...
		if firstrun:
			button.connect("clicked", self.config_write, type, 1)
		elif romspecific:
			button.connect("clicked", self.config_write,type, 2, self.mamename)
		else: button.connect("clicked", self.config_write, type)

		self.widgets["config"]["main_dialog"].action_area.pack_start(button)

		if not firstrun:
			# "Cancel" Button (except for the first time configuration).
			button = gtk.Button(stock=gtk.STOCK_CANCEL)
			button.connect("clicked", lambda *args: self.widgets["config"]\
				["main_dialog"].destroy())
			self.widgets["config"]["main_dialog"].action_area.pack_end(button)

		self.widgets["config"]["main_dialog"].show_all()

		#Post ``show all" operations...
		if type in (1,2,3,4):
			#Showing the right section in global emulation configuration.
			notebook.set_current_page(type-1) 
			playerChanged(None,True) #Selecting player 1 controls by default.

		#Enlarging the window width if too small.
		if self.widgets["config"]["main_dialog"].get_size()[0] < 380:
			self.widgets["config"]["main_dialog"].set_size_request(380, -1)

	def config_write(self, widget, type, special=0, mamename=None):
		letsWrite = 0

		if type == 0:
			error = 0
			#Display error dialog or not, according to value icon image stock!
			#(PATENT PENDING :p)
			for x in self.imppathicons:
				if x.get_stock()[0] == "gtk-no": error = 1

			if error:				
				dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL,
					gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "%s %s" %
					(_("Sorry, this configuration cannot be saved because "
					"one or more parameters does not look valid."),
					_("Please check it up then try to save again... ^^;")))
				dialog.connect("response", lambda *args: dialog.destroy())
				dialog.show_all()
			else:
				#Updating important path configuration params.
				self.params["gngeo"]["biospath"] = self.widgets["config"]\
					['biospath'].get_text()  #biospath
				self.params["gngeo"]["romrcdir"]	= self.widgets["config"]\
					['romrcdir'].get_text()  #romrcdir
				self.params["xgngeo"]["gngeopath"] = self.widgets["config"]\
					['gngeopath'].get_text()  #gngeopath

				letsWrite = 1 #Let's write!

		elif type in (1, 2, 3, 4):
			temp_param = {}

			#Updating global emulation configuration params.
			temp_param["fullscreen"] = ("false","true")[self.widgets["config"]\
				['fullscreen'].get_active()] #fullscreen
			temp_param["interpolation"] = ("false","true")[self.widgets["config"]\
				['interpolation'].get_active()] #interpolation
			temp_param["autoframeskip"] = ("false","true")[self.widgets["config"]\
				['autoframeskip'].get_active()] #showfps
			temp_param["showfps"] = ("false","true")[self.widgets["config"]\
				['showfps'].get_active()] #autoframeskip
			temp_param["raster"] = ("false","true")[self.widgets["config"]['raster']\
				.get_active()] #raster
			temp_param["hwsurface"] = ("false","true")[self.widgets["config"]\
				['hwsurface'].get_active()] #hwsurface
			temp_param["scale"] = int(self.widgets["config"]['scale']\
				.get_value()) #scale
			temp_param["screen320"] = ("false","true")[self.widgets["config"]\
				['screen320'].get_active()] #screen320
			temp_param["blitter"] = self.combo_params['blitter'][self.widgets\
				["config"]['blitter'].get_active()] #blitter
			temp_param["effect"] = self.combo_params['effect'][self.widgets\
				["config"]['effect'].get_active()] #effect
			temp_param["transpack"] = (None,self.widgets["config"]['transpack']\
				.get_text())[os.path.isfile(self.widgets["config"]['transpack']\
				.get_text())] #transpack
			temp_param["sound"] = ("false","true")[self.widgets["config"]['sound']\
				.get_active()] #sound
			temp_param["samplerate"] = self.combo_params['samplerate']\
				[self.widgets["config"]['samplerate'].get_active()] #sample rate
			temp_param["joystick"] = ("false","true")[self.widgets["config"]\
				['joystick'].get_active()] #joystick
			temp_param["p1joydev"] = self.widgets["config"]['p1joydev']\
				.get_active() #p1joydev
			temp_param["p2joydev"] = self.widgets["config"]['p2joydev']\
				.get_active() #p2joydev
			if self.widgets["config"]['system_arcade'].get_active():
				temp_param["system"] = "arcade" #system
			elif self.widgets["config"]['system_home'].get_active():
				temp_param["system"] = "home"
			else: temp_param["system"] = "unibios"
			if self.widgets["config"]['country_japan'].get_active():
				temp_param["country"] = "japan" #country
			elif self.widgets["config"]['country_usa'].get_active():
				temp_param["country"] = "usa"
			else: temp_param["country"] = "europe"
			temp_param["68kclock"] = int(self.widgets["config"]\
				['68kclock'].get_value()) #68kclock
			temp_param["z80clock"] = int(self.widgets["config"]\
				['z80clock'].get_value()) #z80clock

			#Controls.
			#Player 1.
			temp_param["p1key"] = str()
			for val in self.p1key_int_vals:
				temp_param["p1key"] += "%s," %  (val, "-1")[val == "--"]
			temp_param["p1key"] = temp_param["p1key"][:-1]
			#Player 2.
			temp_param["p2key"] = str()
			for val in self.p2key_int_vals:
				temp_param["p2key"] += "%s," % (val, "-1")[val == "--"]
			temp_param["p2key"] = temp_param["p2key"][:-1]

			#Hotkeys' config.
			for x in (1, 2):
				if self.params["temp"].has_key("hotkey_matrix_p%i" % x):
					i = 0
					for row in self.params["temp"]["hotkey_matrix_p%i" % x]:
						temp_param["p%ihotkey%i" % (x, i)] = ""
						for butt in row:
							if butt:
								temp_param["p%ihotkey%i" % (x, i)] += "%s," % butt
							else: break
						if len(temp_param["p%ihotkey%i" % (x, i)]):
							temp_param["p%ihotkey%i" % (x, i)] = temp_param[
							"p%ihotkey%i" % (x, i)][:-1]
						i += 1

			letsWrite = 1 #Let's write!

		elif type == 5:
			# Update Other things configuration params.
			self.params["gngeo"]["libglpath"] = self.widgets["config"]['libglpath']\
				.get_text() #libglpath
			self.params["xgngeo"]["previewimages"] = ("false", "true")\
				[self.widgets["config"]['previewimages'].get_active()] #previewimage
			self.params["xgngeo"]["previewimagedir"] = self.widgets["config"]\
				['previewimagedir'].get_text() #previewimagedir
			self.params["xgngeo"]["rominfos"] = ("false","true")\
				[self.widgets["config"]['rominfos'].get_active()] #rominfo
			self.params["xgngeo"]["rominfoxml"] = self.widgets["config"]['rominfoxml']\
				.get_text() #rominfoxml
			self.params["xgngeo"]["historysize"] = int(self.widgets["config"]\
				['historysize'].get_value()) #historysize
			self.params["xgngeo"]["autoexecrom"] = ("false", "true")\
				[self.widgets["config"]['autoexecrom'].get_active()] #autoexecrom
			self.params["xgngeo"]["centerwindow"] = ("false","true")\
				[self.widgets["config"]['centerwindow'].get_active()] #centerwindow
			self.params["xgngeo"]["showavailableromsonly"] = ("false", "true")\
				[self.widgets["config"]['showavailableromsonly'].get_active()] #showavailableromsonly
			self.params["xgngeo"]["availableromcolor"] = self.params["temp"]\
				["availableromcolor"] #availableromcolor
			self.params["gngeo"]["sleepidle"] = ("false","true")\
				[self.widgets["config"]['sleepidle'].get_active()] #sleepidle
			self.params["gngeo"]["bench"] = ("false","true")[self.widgets["config"]\
				['bench'].get_active()] #bench

			letsWrite = 1  #Let's write!

		if letsWrite:  # We are now Ok to write into configuration file(s)...
			self.widgets["config"]["main_dialog"].destroy()

			# Performing particular actions.
			if special in (0, 1):
				# Doing the default or the sligtly different ``firstrun" job.
			
				if type == 0:
					# Indicating new paths to the emulator handling module.
					self.emulator.set_path("gngeo", self.params["xgngeo"]["gngeopath"])

				elif type in (1, 2, 3, 4):
					# Putting options considered as temporary ROM-specific
					# configuration parameters to the global parameter
					# dictionnary.
					for key,val in temp_param.items():
						self.params["gngeo"][key] = val

				self.configfile.write_global_config(self.params["gngeo"],
					self.params["xgngeo"], VERSION) #Writting out! :p
				
				if not special:
					# Updating status message.
					self.widgets["statusbar"].push(self.context_id, _(
						"Configuration has been saved.")) 
				else: 
						# The program has been configured, so that we can use it!
						self.main()

			elif special == 2:  #ROM-specific configuration.
				# Writing out! :p
				self.configfile.write_rom_config(temp_param, mamename, VERSION)

				if mamename == self.mamename:
					# Updating buttons.
					self.widgets['specconf_new'].hide()
					self.widgets['specconf_properties'].show()
					self.widgets['specconf_clear'].show()

	def quit(self, *args):
		if self.emulator.rom_running_state():
			# Stopping potentialy running Gngeo.
			self.gngeo_stop()

		gtk.main_quit()  # Stopping waiting for event...
		sys.exit()
		return False

	def main(self):
		#Window attributes.
		self.window.set_title("XGngeo")
		self.window.connect("delete_event", self.quit)

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
		menu_item.connect("activate",self.rom_list)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_Manually"))
		menu_item.connect("activate", self.file_select, _("Load a ROM "
			"manually..."), self.params["gngeo"]["biospath"], 
			self.manual_rom_loading, 0,	{ _("All files") : "*",
			_("ROM archive") :  "*.zip"}, True)
		menu2.append(menu_item)

		self.history_menu_item = gtk.MenuItem(_("_History"))
		self.widgets["history_menu"] = gtk.Menu()
		self.history_menu_item.set_submenu(self.widgets["history_menu"])
		self.widgets["history_menu"].append(gtk.TearoffMenuItem())
		self.history.refresh_list(size=int(self.params["xgngeo"]\
			["historysize"]))  # Building ROM History list.
		self.history_menu_generation()  # Generating ROM History menu.
		menu.append(self.history_menu_item)

		menu.append(gtk.SeparatorMenuItem())  # Separator

		self.execMenu_item = gtk.ImageMenuItem(gtk.STOCK_EXECUTE)
		self.execMenu_item.connect("activate", self.gngeo_exec)
		self.execMenu_item.set_state(gtk.STATE_INSENSITIVE)
		menu.append(self.execMenu_item)

		self.stopMenu_item = gtk.ImageMenuItem(gtk.STOCK_STOP)
		self.stopMenu_item.connect("activate", self.gngeo_stop)
		self.stopMenu_item.set_state(gtk.STATE_INSENSITIVE)
		menu.append(self.stopMenu_item)

		menu.append(gtk.SeparatorMenuItem())  # Separator

		menu_item = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		menu_item.connect("activate", self.quit)		
		menu.append(menu_item)

		#
		# CONFIG Menu
		#
		self.configMenu = gtk.Menu()
		menu_item = gtk.MenuItem(_("_Configuration"))
		menu_item.set_submenu(self.configMenu)
		menu_bar.append(menu_item)

		menu_item = gtk.MenuItem(_("_Important paths"))
		menu_item.connect("activate", self.config, 0)
		self.configMenu.append(menu_item)

		menu2 = gtk.Menu()
		menu_item = gtk.MenuItem(_("_Global emulation"))
		menu_item.set_submenu(menu2)
		self.configMenu.append(menu_item)

		menu_item = gtk.MenuItem(_("_Display"))
		menu_item.connect("activate", self.config, 1)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_Audio / Joystick"))
		menu_item.connect("activate", self.config, 2)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_Controls"))
		menu_item.connect("activate", self.config,3)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_System"))
		menu_item.connect("activate", self.config, 4)
		menu2.append(menu_item)

		menu_item = gtk.MenuItem(_("_Other"))
		menu_item.connect("activate", self.config, 5)
		self.configMenu.append(menu_item)

		#
		# DRIVERS Menu
		#
		menu = gtk.Menu()
		menu_item = gtk.MenuItem(_("_ROM drivers"))
		menu_item.set_submenu(menu)
		menu_bar.append(menu_item)

		menu_item = gtk.MenuItem(_("_View/edit"))
	#	menu_item.connect("activate",self.driverList)
		menu_item.set_sensitive(False)
		menu.append(menu_item)

		menu_item = gtk.MenuItem(_("_Add new"))
	#	menu_item.connect("activate",self.driverAdd)
		menu_item.set_sensitive(False)
		menu.append(menu_item)

		#
		# INFO Menu
		#
		menu = gtk.Menu()
		menu_item = gtk.MenuItem(_("_Info"))
		menu_item.set_right_justified(True) #At right.
		menu_item.set_submenu(menu)
		menu_bar.append(menu_item)

		menu_item = gtk.ImageMenuItem(gtk.STOCK_HELP)
		menu_item.connect("activate", self.display_file,\
		os.path.join(datarootpath, "doc", "xgngeo-doc.txt"))
		menu.append(menu_item)

		menu_item = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
		menu_item.connect("activate", self.about)
		menu.append(menu_item)

		menu_item = gtk.MenuItem(_("_License"))
		menu_item.connect("activate", self.display_file, "LICENSE.txt")
		menu.append(menu_item)

		# Pack MemuBar into the Box
		box.pack_start(menu_bar, False)

		#
		# Logo
		#
		container = gtk.EventBox()
		container.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
		logo = gtk.Image()
		logo.set_from_file(os.path.join(datarootpath, "img", "xgngeo.png"))
		logo.set_padding(25, 2)
		container.add(logo)
		box.pack_start(container)

		#
		# Statusbar
		#
		self.widgets["statusbar"].push(self.context_id, _("Welcome to XGngeo "
			"version %s.") % VERSION)
		box.pack_end(self.widgets["statusbar"], False)

		# Window positioning.
		if self.params["xgngeo"]["centerwindow"] == "true":
			self.window.set_position(gtk.WIN_POS_CENTER)
		# Show all.
		self.window.show_all()

	def get_bios_presence(self, path):
		"""Indicate whether any BIOS files are present on a given directory
			(0 if not), with information regarding its/their type (particular
			positive integer).
			
		"""
		i = 0
		if os.path.isfile(os.path.join(path, "vs-bios.rom"))\
			or os.path.isfile(os.path.join(path, "usa_2slt.bin"))\
			or os.path.isfile(os.path.join(path, "asia-s3.rom"))\
			or os.path.isfile(os.path.join(path, "sp-s2.sp1")):
				i += 1  # Arcade BIOS detected.
		if os.path.isfile(os.path.join(path, "aes-bios.bin")):
				i += 2  # AES BIOS detected.
		if os.path.isfile(os.path.join(path, "uni-bios.rom")):
				i += 4  # Universal BIOS detected.

		return i

	def boot(self):
		if "--nobootcheck" in sys.argv:
			print _('``No boot check" option enabled: going directly to the '
				'main window (unsafe!).')
			self.main()

		else:  # Performing boot-time important checks.
			error = 0
			# Are BIOS files present?
			if not self.get_bios_presence(self.params["gngeo"]["biospath"]): error = 1
			# Is the GnGeo executable present and returning correct version
			# values?
			version = self.emulator.get_gngeo_version()
			if not version or version[0][1:3] < (6, 11): error = 1

			if error: self.check_error()  # Display value setting invitation.
			else:
					# Everything seems okay, so let's display the main window...
					self.main()

if __name__ == "__main__":
	gtk.threads_init()
	XGngeo().boot()
	gtk.main()
