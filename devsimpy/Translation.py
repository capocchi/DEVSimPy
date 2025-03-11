# -*- coding: utf-8 -*-

import os

# make the template
os.system("xgettext -k_ -kN_ --msgid-bugs-address=capocchi@univ-corse.fr -o ./locale/DEVSimPy.pot *.py")

# what language you want trnaslate
language = input("What po file do you want changed ? (fr or en):")

if language =='en':

	# make po file
	os.system("msginit -i ./locale/DEVSimPy.pot -o ./locale/en/LC_MESSAGES/DEVSimPy.po")
	# compile it
	os.system("msgfmt ./locale/en/LC_MESSAGES/DEVSimPy.po -o ./locale/en/LC_MESSAGES/DEVSimPy.mo")

else:

	# for french, you can only update or rewrite the .po
	update = input("Do you want to update the fr .po ? (y,n):")

	if update == 'y':
		os.system("msgmerge -U ./locale/fr/LC_MESSAGES/DEVSimPy.po ./locale/DEVSimPy.pot")
	else:
		os.system("msginit -i ./locale/DEVSimPy.pot -o ./locale/fr/LC_MESSAGES/DEVSimPy.po")

	# edit the .po file for update or write
	#os.system("kwrite ./locale/fr/LC_MESSAGES/DEVSimPy.po")

	#compile
	os.system("msgfmt ./locale/fr/LC_MESSAGES/DEVSimPy.po -o ./locale/fr/LC_MESSAGES/DEVSimPy.mo")