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
import sys, os.path

package_dir = os.path.join(sys.prefix,"lib","python%s" % sys.version[:3],"site-packages","xgngeo")

#Append XGngeo's module directory to `sys.path'.
sys.path.append(package_dir)

#Launch the program!
execfile(os.path.join(package_dir,"__init__.py"))
