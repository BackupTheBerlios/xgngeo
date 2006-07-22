""" XGngeo: a frontend for Gngeo in GTK ^^.

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

import os.path
from re import match

class History:
    def __init__(self):
        self.path = os.path.expanduser("~/.xgngeo/history")
        self.list = []

    def refresh_list(self, size):
        """ Reading content of the ROM History file to build a list 
            containing tuple with full name, path and file system
            presence for each of the recently loaded ROMs.
        
        """

        self.list = [] #(Re)Creating ROM History list from scratch.

        if os.path.isfile(self.path):
            file = open(self.path, "r") #Opening.
            content = file.readlines() #Reading.
            file.close() #And closing. :p

            for line in content[:size]:
                plop = match('"(.*)" (.*)', line)
                if plop: 
                    path = plop.group(2)
                    self.list.append((plop.group(1), path, 
                                      os.path.exists(path)))

    def get_list(self):
        "Returning current, up-to-date ROM History list."
        return self.list

    def update_file(self):
        "Updating ROM History file."
        content = ""
        for line in self.list:
            content += '"%s" %s\n' % (line[0], line[1])

        file = open(self.path, "w") #Opening (creating if doesn't exist)
        file.write(content) #Writing.
        file.close() #And closing. :p

    def add_rom(self, name, path, size):
        "Adding a new Rom to the list, with duplicate entries prevention."

        #Popping the ROM out of the list if already mentioned (similar path).
        i = 0
        for rom_path in self.list[:size]:
            if rom_path[1] == path: 
                self.list.pop(i)
            i += 1

        #Prepending it to the recent Rom list (indicating the file exists).
        self.list.insert(0, (name, path, True)) 
        self.list = self.list[:size] #Removing any extra item.
        self.update_file() #Writing changes.

    def remove_rom(self, position):
        "Popping the ROM out of the list."
        self.list.pop(position)
        self.update_file() #Writing changes.

# vim:ai:et:sw=4:ts=4:sts=4:tw=78:fenc=utf-8
