__author__="Adam"
__date__ ="18-Jan-2011 12:51:42 PM"

from distutils.core import setup

setup (
  name = 'PythonModule',
  version = '2.1.8',
  description = 'Python Wrapper library for the Phidgets API',
  author = 'Adam',
  author_email = 'adam@phidgets.com',
  url = 'http://www.phidgets.com',
  packages = ['Phidgets', 'Phidgets.Devices', 'Phidgets.Events'],
  license = 'Creative Commons Attribution 2.5 Canada License',
)
