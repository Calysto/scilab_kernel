from distutils.core import setup
import os
import json
import sys

try:
    from jupyter_client.kernelspec import install_kernel_spec
except ImportError:
    from IPython.kernel.kernelspec import install_kernel_spec
from IPython.utils.tempdir import TemporaryDirectory


kernel_json = {"argv": [sys.executable, "-m", "scilab_kernel", "-f",
                        "{connection_file}"],
               "display_name": "Scilab",
               "language": "scilab",
               "codemirror_mode": "Octave",
               "name": "scilab_kernel",
               }

# get the library version from the file
with open('scilab_kernel.py') as f:
    lines = f.readlines()
for line in lines:
    if line.startswith('__version__'):
        version = line.split()[-1][1:-1]

svem_flag = '--single-version-externally-managed'
if svem_flag in sys.argv:
    # Die, setuptools, die.
    sys.argv.remove(svem_flag)


def _is_root():
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False  # assume not an admin on non-Unix platforms


if 'develop' in sys.argv or 'install' in sys.argv:
    user = '--user' in sys.argv or not _is_root()
    with TemporaryDirectory() as td:
        os.chmod(td, 0o755)  # Starts off as 700, not user readable
        with open(os.path.join(td, 'kernel.json'), 'w') as f:
            json.dump(kernel_json, f, sort_keys=True)
        kernel_name = kernel_json['name']
        try:
            install_kernel_spec(td, kernel_name, user=user,
                                replace=True)
        except:
            install_kernel_spec(td, kernel_name, user=not user,
                                replace=True)

setup(name='scilab_kernel',
      version=version,
      description='A Scilab kernel for IPython',
      long_description=open('README.rst', 'r').read(),
      author='Steven Silvester',
      author_email='steven.silvester@ieee.org',
      url='https://github.com/blink1073/scilab_kernel',
      py_modules=['scilab_kernel'],
      install_requires=['scilab2py >= 0.3', 'IPython >= 3.0'],
      classifiers=[
          'Framework :: IPython',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Topic :: System :: Shells',
      ]
      )
