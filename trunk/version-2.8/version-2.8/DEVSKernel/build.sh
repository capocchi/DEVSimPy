#!/bin/bash

function initFolders {
        echo -ne "Initting folder structure...\t\t"
        mkdir temp
        cd temp
        echo "[DONE]"
}

# Copy necessary Cython files
function copyCython {
        echo -ne "Copy Cython files...\t\t\t"
        cp ../cythonfiles/setup.py ./setup.py
        sed -i".bak" "s/PYDEVS/$1/g" setup.py
        echo "[DONE]"
}

# Copy the base simulator
function copyPydevs {
        echo -ne "Copy Pydevs files...\t\t\t"
        cp ../FastSimulator.py FastSimulator.pyx
        cp ../Patterns/Strategy.py Strategy.pyx
        cp ../pluginmanager.py pluginmanager.pyx
        cp ../DEVS.py DEVS.pyx
#         cp ../VCDRecord.py VCDRecord.pyx
#         cp ../infinity.py infinity.pyx
        echo "[DONE]"
}

# Clean up unnecessary imports from pydevs itself
function rmImportPydevs {
        echo -ne "Removing imports from PyDEVS...\t\t"
#         sed -i".bak" '/from DEVS import/d' FastSimulator.pyx
#         sed -i".bak" '/from Patterns.Strategy import/d' FastSimulator.pyx
#         sed -i".bak" '/from devs_exceptions import/d' simulator.pyx
#         sed -i".bak" '/from infinity import/d' DEVS.pyx
#         sed -i".bak" '/from devs_exceptions import/d' DEVS.pyx
        cp FastSimulator.pyx FastSimulator.pyx.bak
        head -n -9 FastSimulator.pyx.bak > FastSimulator.pyx
        echo "[DONE]"
}

# Optimize for Cython
function optCython {
        echo -ne "Doing cython optimisations...\t\t"
        sed -i".bak" 's/class BaseDEVS:/cdef class BaseDEVS:/' DEVS.pyx
        echo "[DONE]"
}

# Clean up unnecessary files
function clean {
        echo -ne "Clearing backup files...\t\t"
        rm *.bak
        echo "[DONE]"
}

# Generate the Cython file
function generateCythonfile {
        echo -ne "Generating the Cython include file...\t"
        for f in *
        do
                if [ $f != "setup.py" ] ; then
                        echo "include \"$f\"" >> pydevs.pyx
                fi
        done
        echo "[DONE]"
}

# Call cython...
function callCython {
        echo -ne "Calling cython...\t\t\t"
        python setup.py build_ext --inplace > /dev/null
        echo "[DONE]"
}

initFolders
copyPydevs
rmImportPydevs
copyCython "cydevs"
optCython
clean
generateCythonfile
callCython

mv cydevs.so ../cydevs.so

cd ../
rm -r temp/
