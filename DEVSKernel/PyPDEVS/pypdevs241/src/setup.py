from distutils.core import setup

setup(name="PyPDEVS",
      version="2.4.1",
      description="Python Parallel DEVS simulator",
      author="Yentl Van Tendeloo",
      author_email="Yentl.VanTendeloo@uantwerpen.be",
      url="http://msdl.cs.mcgill.ca/people/yentl",
      packages=['pypdevs', 'pypdevs.allocators', 'pypdevs.realtime', 'pypdevs.relocators', 'pypdevs.schedulers', 'pypdevs.templates', 'pypdevs.tracers']
)
