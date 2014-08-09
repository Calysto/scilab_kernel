from distutils.core import setup
from distutils.command.install import install
import os
import sys

if sys.argv[-1] == 'publish':
    os.system('python setup.py register')
    os.system('python setup.py sdist --formats=gztar,zip upload')
    sys.exit()


class install_with_kernelspec(install):
    def run(self):
        install.run(self)
        from IPython.kernel.kernelspec import install_kernel_spec
        install_kernel_spec('kernelspec', 'scilab', replace=True)

with open('README.rst') as f:
    readme = f.read()

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

setup(name='scilab_kernel',
      version=version,
      description='A Scilab kernel for IPython',
      long_description=readme,
      author='Steven Silvester',
      author_email='steven.silvester@ieee.org',
      url='https://github.com/blink1073/scilab_kernel',
      py_modules=['scilab_kernel'],
      cmdclass={'install': install_with_kernelspec},
      requires=['scilab2py', 'IPython (>= 3.0)'],
      classifiers=[
          'Framework :: IPython',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Topic :: System :: Shells',
      ]
)
