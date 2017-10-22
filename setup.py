"""Setup script for scilab_kernel package.
"""
import glob

DISTNAME = 'scilab_kernel'
DESCRIPTION = 'A Jupyter kernel for Scilab.'
LONG_DESCRIPTION = open('README.rst', 'rb').read().decode('utf-8')
MAINTAINER = 'Steven Silvester'
MAINTAINER_EMAIL = 'steven.silvester@ieee.org'
URL = 'http://github.com/calsto/scilab_kernel'
LICENSE = 'MIT'
REQUIRES = ["metakernel (>=0.20.10)", "jupyter_client (>=4.3.0)", "ipykernel"]
INSTALL_REQUIRES = ["metakernel >=0.20.10", "jupyter_client >=4.3.0", "ipykernel"]
PACKAGES = [DISTNAME]
PACKAGE_DATA = {
    DISTNAME: ['*.m'] + glob.glob('%s/**/*.*' % DISTNAME)
}
DATA_FILES = [
    ('share/jupyter/kernels/scilab', [
        '%s/kernel.json' % DISTNAME
     ] + glob.glob('%s/images/*.png' % DISTNAME)
    )
]
PACKAGES = [DISTNAME]
PACKAGE_DATA = {DISTNAME: ['*.sci']}
CLASSIFIERS = """\
Intended Audience :: Science/Research
License :: OSI Approved :: BSD License
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Topic :: Scientific/Engineering
Topic :: Software Development
Topic :: System :: Shells
"""
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('scilab_kernel/__init__.py', 'rb') as fid:
    for line in fid:
        line = line.decode('utf-8')
        if line.startswith('__version__'):
            version = line.strip().split()[-1][1:-1]
            break


setup(
    name=DISTNAME,
    version=version,
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    packages=PACKAGES,
    package_data=PACKAGE_DATA,
    include_package_data=True,
    data_files=DATA_FILES,
    url=URL,
    download_url=URL,
    license=LICENSE,
    platforms=["Any"],
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    classifiers=list(filter(None, CLASSIFIERS.split('\n'))),
    requires=REQUIRES,
    install_requires=INSTALL_REQUIRES
 )
