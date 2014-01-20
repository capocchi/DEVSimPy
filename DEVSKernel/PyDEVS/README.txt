PythonDEVS simulator
====================

Cython
------
It is possible to use a Cython version of the simulator, though this is not
done by default as Cython is not often available. To use the Cython version,
the following steps need to be done:
1) Install Cython on your system
2) Run the build.sh script, which will automatically build the required
cydevs.so file
3) Toggle the __USE_CYDEVS__ variable to True at the end of the file
simulator.py