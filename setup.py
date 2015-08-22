from setuptools import setup
from setuptools.command.install import install
import json
import os
import sys
from distutils import log


kernel_json = {"argv": [sys.executable, "-m", "scilab_kernel", "-f",
                        "{connection_file}"],
               "display_name": "Scilab",
               "language": "scilab",
               "codemirror_mode": "Octave",
               "name": "scilab_kernel",
               }


class install_with_kernelspec(install):

    def run(self):
        user = '--user' in sys.argv
        # Regular installation
        install.run(self)

        # Now write the kernelspec
        try:
            from ipykernel.kerspec import install_kernel_spec
        except ImportError:
            from IPython.kernel.kernelspec import install_kernel_spec
        from IPython.utils.tempdir import TemporaryDirectory
        with TemporaryDirectory() as td:
            os.chmod(td, 0o755)  # Starts off as 700, not user readable
            with open(os.path.join(td, 'kernel.json'), 'w') as f:
                json.dump(kernel_json, f, sort_keys=True)
            log.info('Installing kernel spec')
            kernel_name = kernel_json['name']
            try:
                install_kernel_spec(td, kernel_name, user=user,
                                    replace=True)
            except:
                install_kernel_spec(td, kernel_name, user=not user,
                                    replace=True)


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
      install_requires=['scilab2py >= 0.3', 'IPython >= 3.0'],
      classifiers=[
          'Framework :: IPython',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Topic :: System :: Shells',
      ]
      )
