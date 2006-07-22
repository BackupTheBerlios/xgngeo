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
    Foundation, Inc., 59 Temple Place - Suite 330, Boston, 
    MA 02111-1307, USA.

"""

__author__ = "Choplair-network"
__copyright__ = "Copyleft 2003, 2004, 2005, 2006 Choplair-network"
__license__ = "GPL"
__revision__ = "$Revision$"
# $Source$
__date__ = "$Date$"

import xml.sax
 
class XmlHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.newromset = 0
        self.currentromset = ""
        self.mapping = {}
        self.record = 0
        self.buffer = ""

    def startElement(self, name, attributes):
        if name in [u"rows", u"info"]:
            self.record = 0 # Do nothing. :p
        else:
            if name == "set":
                # Tell that we are running into a new rom set!
                self.newromset = 1 
            else: 
                # There is no new rom set...
                self.newromset = 0 

            self.buffer = "" # Empty the buffer.
            self.record = 1  # Allow reccording!

    def characters(self, data):
        if self.record:
            self.buffer += data

    def endElement(self, name):
        if name in [u"roms", u"info"]:
            pass # Do nothing. :p
        else:
            if self.newromset:
                # Set the name of the current rom set.
                self.currentromset = self.buffer 
                # Create a dictionary for the rom set.
                self.mapping[self.currentromset] = {} 
            else:
                #Update the current rom set's dict.
                self.mapping[self.currentromset][name] = self.buffer

class Rominfos:
    def __init__(self, path):
        self.path = path

    def getDict(self):
        parser = xml.sax.make_parser()
        handler = XmlHandler()
        parser.setContentHandler(handler)
        parser.parse(self.path)
        return handler.mapping

# vim:ai:et:sw=4:ts=4:sts=4:tw=78:fenc=utf-8
