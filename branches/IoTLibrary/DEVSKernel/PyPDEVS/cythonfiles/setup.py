from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

import sys

filtered = []
for arg in sys.argv:
    if "--build-" in arg:
        # Strip of the --build- part
        modname = arg[8:]
        # Strip of the .pyx part
        modname = modname[:-4]
    else:
        filtered.append(arg)
sys.argv = filtered

ext_modules = [Extension(modname, [modname + ".pyx"], extra_compile_args=["-O3", "-march=native"])]

setup(
        name = modname,
        cmdclass = {'build_ext': build_ext},
        ext_modules = ext_modules
)
