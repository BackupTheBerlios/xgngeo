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
__date__ = "$Date$"

from threading import Thread
from gtk import threads_enter, threads_leave
from os import popen

class ThreadedCmd(Thread):
    def __init__(self, cmd):
        Thread.__init__(self)
        self.command = cmd
        self.output = ""

    def run(self):
        threads_enter()
        pipe = popen(self.command,"r")
        threads_leave()
        self.output = pipe.read()

    def getOutput(self):
        return self.output

# vim:ai:et:sw=4:ts=4:sts=4:tw=78:fenc=utf-8
