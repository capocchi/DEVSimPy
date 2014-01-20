# DEVS.so and FastSimulator.so generator
# Depends of python-pyrex and cython (install it with apt-get install)

# this will create a c1.c file - the C source code to build a python extension
cython FastSimulator.py
cython DEVS.py

# Compile the object file
gcc -c -fPIC -I/usr/include/python2.6/ FastSimulator.c
gcc -c -fPIC -I/usr/include/python2.6/ DEVS.c

# Link it into a shared library
gcc -shared FastSimulator.o -o FastSimulator.so
gcc -shared DEVS.o -o DEVS.so
