for f in `ls -1 *.py`
do
    sed -i".bak" 's/ #assert/ assert/' $f
    rm ${f}.bak
done
