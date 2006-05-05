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
from distutils.core import setup
import os.path, glob, sys

setup(
	name='XGngeo',
	version='16cvs',
	description='A frontend for the Gngeo emulator.',
	author='Choplair-network',
	author_email='contact@choplair.org',
	url='http://www.choplair.org/',
	download_url='http://developer.berlios.de/project/showfiles.php?group_id=1276',
	license='GNU General Public License',
	packages=['xgngeo'],
	package_dir={'xgngeo': 'data/py'},
	data_files=[
		#Images.
		(os.path.join("share","xgngeo","img"),glob.glob(os.path.join("data","img","*.png"))),
		#Rom infos.
		(os.path.join("share","xgngeo"),glob.glob(os.path.join("data","rominfos.*"))),
		#License text.
		(os.path.join("share","xgngeo"),['LICENSE.txt']),
		#Localisation.
		(os.path.join("share","xgngeo","locale","es","LC_MESSAGES"),[os.path.join("data","locale","es","LC_MESSAGES","xgngeo.mo")]), #Spanish
		(os.path.join("share","xgngeo","locale","de","LC_MESSAGES"),[os.path.join("data","locale","de","LC_MESSAGES","xgngeo.mo")]), #Spanish
		(os.path.join("share","xgngeo","locale","fr","LC_MESSAGES"),[os.path.join("data","locale","fr","LC_MESSAGES","xgngeo.mo")]), #French
		(os.path.join("share","xgngeo","locale","pl","LC_MESSAGES"),[os.path.join("data","locale","pl","LC_MESSAGES","xgngeo.mo")]), #Polish
		(os.path.join("share","xgngeo","locale","pt_BR","LC_MESSAGES"),[os.path.join("data","locale","pt_BR","LC_MESSAGES","xgngeo.mo")]) #Portuguese of Brazil
		]
	)
	
if "install" in sys.argv:
	#Post-install stuffs (Unix).
	if os.name=="posix":
		import shutil
		startup_script = "/usr/local/bin/xgngeo"
		shutil.copy("./data/script/xgngeo_startup.py",startup_script)
		print "XGngeo start-up script put into `%s'." % os.path.dirname(startup_script)
