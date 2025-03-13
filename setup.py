from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="devsimpy",
    version="5.0",
    author="Laurent Capocchi",
    author_email="capocchi@univ-corse.fr",
    description="DEVSimPy - The Python DEVS GUI modeling and simulation software",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/capocchi/DEVSimPy",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Simulation",
    ],
    python_requires=">=3.9",
    install_requires=[
        "wxPython>=4.0",
        "PyPubSub==3.3.0",
        "numpy",
        "matplotlib",
        "psutil",
        "pyYAML",
        "ruamel.yaml"
    ],
    entry_points={
        'console_scripts': [
            'devsimpy=devsimpy.devsimpy:main',
        ],
    },
    include_package_data=True,
    package_data={
        'devsimpy': ['icons/*.png', 'icons/*.ico', 'locale/*', 'doc/*'],
    },
)
