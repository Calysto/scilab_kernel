# Note: This is meant for Scilab2Py developer use only
.PHONY: all clean test release

export KILL_SCILAB="from scilab2py import kill_scilab; kill_scilab()"

all: clean
	python setup.py install

clean:
	rm -rf build
	rm -rf dist
	find . -name "*.pyc" -o -name "*.py,cover"| xargs rm -f
	python -c $(KILL_SCILAB)

release: clean
	pip install wheel
	python setup.py register
	python setup.py bdist_wheel upload
	python setup.py sdist --formats=gztar,zip upload
	git tag v`python -c "import scilab_kernel;print(scilab_kernel.__version__)"`
	git push origin --all

test: clean
	python setup.py install
	cd ~; ipython qtconsole --kernel=scilab
	make clean
