# make the template for the DEVSimPy translatation
# Note: Before executing this script, execute first locale/makeEnPo.sh and en/LC_MESSAGES/compile.sh scripts without modyfing the DEVSimPy.Pot file.
# Then, we can copy the DEVSimPy.pot to locale/DEVSimPy.po file and modify this last. Since we can execute the makeFrPo.sh and fr/LC_MESSAGES/compile.sh scripts.
# .po files can be edited with the poedit tool on linux.
xgettext -k_ -kN_ --msgid-bugs-address=capocchi@univ-corse.fr -o ./locale/DEVSimPy.pot *.py
