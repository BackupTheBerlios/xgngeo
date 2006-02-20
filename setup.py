#!/usr/bin/env python
from distutils.core import setup
import os

def filelist(dir):
	"""Return (not recursively) the relative path of all *files* in a directory."""
	list = []
	for x in os.listdir(dir):
		rel_path = os.path.join(dir,x)
		if os.path.isfile(rel_path):
			list.append(rel_path)
	return list

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
		('share/xgngeo/img',filelist("data/img")),
		#Rom infos.
		('share/xgngeo',['data/rominfos.dtd','data/rominfos.xml']),
		#License text.
		('share/xgngeo',['LICENSE.txt']),
		#Localisation.
		('share/xgngeo/locale/es/LC_MESSAGES',['data/locale/es/LC_MESSAGES/xgngeo.mo']), #Spanish
		('share/xgngeo/locale/fr/LC_MESSAGES',['data/locale/fr/LC_MESSAGES/xgngeo.mo']), #French
		('share/xgngeo/locale/pl/LC_MESSAGES',['data/locale/pl/LC_MESSAGES/xgngeo.mo']), #Polish
		('share/xgngeo/locale/pt_BR/LC_MESSAGES',['data/locale/pt_BR/LC_MESSAGES/xgngeo.mo']) #Portuguese of Brazil
		]
	)
