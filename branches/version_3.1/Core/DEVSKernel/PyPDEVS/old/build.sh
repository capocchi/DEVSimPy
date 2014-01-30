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
        echo "[DONE]"
}

# Copy the base simulator
function copyPydevs {
        echo -ne "Copy PyPDEVS files...\n"
        for f in `ls -1 ../*.py`
        do
            cp `readlink -f $f` .
        done
        for f in `ls -1 ../*.pxd`
        do
            cp `readlink -f $f` .
        done
        for f in `ls -1 *.py`
        do
            printf '%20s\t\t\t' "$f"
            mv $f ${f}x
            echo "[DONE]"
        done
        rm "__init__.pyx"
}

# Clean up unnecessary imports from pydevs itself
function rmAsserts {
        echo -ne "Removing asserts for maximum speed...\t"
        for f in `ls -1 *.pyx`
        do
            sed -i".bak" 's/assert/pass\n#assert/' $f
        done
        echo "[DONE]"
}

# Optimize for Cython
function optCython {
        echo -ne "Doing cython optimisations...\t\t"
        #sed -i".bak" 's/class BaseDEVS:/cdef class BaseDEVS:/' DEVS.pyx
        for f in `ls -1 *.pyx`
        do
            sed -i".bak" 's/#cython //' $f
            sed -i".bak" '/#cython-remove/d' $f
        done
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
        echo -ne "Compiling...\n"
        for f in `ls -1 *.pyx`
        do
            printf '%20s\t\t\t' "$f"
            cython -a $f
            python setup.py build_ext --inplace --build-$f > /dev/null
            echo "[DONE]"
        done
}

initFolders
copyPydevs
rmAsserts
copyCython "cypdevs"
optCython
clean
generateCythonfile

mv *.so ../../cypdevs/
mv *.html ../../cypdevs/

cd ../
rm -r temp/
