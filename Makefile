# Note: This is meant for Scilab2Py developer use only
.PHONY: all clean test release

export KILL_SCILAB="from scilab2py import kill_scilab; kill_scilab()"
export NAME=scilab_kernel
export VERSION=`python -c "import $(NAME); print($(NAME).__version__)"`

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
	python setup.py sdist --formats=gztar,zip upload
	git tag v$(VERSION)
	git push origin --all

test: clean
	python setup.py install
	cd ~; ipython qtconsole --kernel scilab
	make clean
