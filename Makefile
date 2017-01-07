# Note: This is meant for scilab_kernel developer use only
.PHONY: all clean test release

export NAME=scilab_kernel
export VERSION=`python -c "import $(NAME); print($(NAME).__version__)"`
export PY=`python -V`

all: clean
	python setup.py install

clean:
	rm -rf build
	rm -rf dist

test: clean
	pip install jupyter_kernel_test nbconvert
	python setup.py build
	python -m scilab_kernel.install
		python -V 2>&1 | grep "Python 3" && python test_scilab_kernel.py || echo "Skipping unit test"
	jupyter nbconvert --to notebook --execute --ExecutePreprocessor.kernel_name=scilab --ExecutePreprocessor.timeout=60 --stdout scilab_kernel.ipynb > /dev/null;
	make clean

release: clean
	pip install wheel
	python setup.py register
	rm -rf dist
	python setup.py bdist_wheel --universal
	python setup.py sdist
	git tag v$(VERSION)
	git push origin --all
	git push origin --tags
	twine upload dist/*
