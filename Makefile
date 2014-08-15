# Note: This is meant for Scilab2Py developer use only
.PHONY: all clean test

export KILL_SCILAB="from scilab2py import kill_scilab; kill_scilab()"

all:
	make clean
	python setup.py install

clean:
	rm -rf build
	rm -rf dist
	find . -name "*.pyc" -o -name "*.py,cover"| xargs rm -f
	python -c $(KILL_SCILAB)

test:
	make clean
	python setup.py install
	cd ~; ipython qtconsole --kernel=scilab
	make clean
