import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='devsimpy',  
    version='3.0',
     scripts=['devsimpy.py'] ,
     author="L. Capocchi",
     author_email="capocchi@univ-corse.fr",
     description="The Python DEVS GUI modeling and simulation software",
     long_description=long_description,
   long_description_content_type="text/markdown",
     url="https://github.com/capocchi/DEVSimPy",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 2",
         "License :: OSI Approved :: GPL v3.0",
         "Operating System :: OS Independent",
     ],
 )