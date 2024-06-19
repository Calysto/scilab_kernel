A Jupyter kernel for Scilab

Prerequisites
-------------
`Jupyter Notebook <http://jupyter.readthedocs.org/en/latest/install.html>`_, and `Scilab <http://www.scilab.org/download/latest>`_.

Installation
------------
To install using pip::

    pip install scilab_kernel

Add ``--user`` to install in the user-level environment instead of the system environment.

This kernel needs the Scilab executable to be run, it which will be searched in this order:
 - Using environment variable ``SCILAB_EXECUTABLE``,
 - Under Windows, based on registry,
 - Under macOS, based on Spotlight database,
 - Using the ``PATH`` environment variable.

Use the ``scilab-adv-cli`` executable if using a Posix-like OS, and ``WScilex-cli.exe`` if using Windows.

Usage
-----

To use the kernel, run one of:

.. code:: shell

    jupyter notebook  # or ``jupyter lab``, if available
    # In the notebook interface, select Scilab from the 'New' menu
    jupyter qtconsole --kernel scilab
    jupyter console --kernel scilab

If ``jupyter`` executable is not found in your ``PATH``, try ``python -m notebook`` instead.

This kernel is based on `MetaKernel <http://pypi.python.org/pypi/metakernel>`_,
which means it features a standard set of magics (such as ``%%html``). For a full list of magics,
run ``%lsmagic`` in a cell.

A sample notebook is available online_.

Configuration
-------------
The kernel can be configured by adding an ``scilab_kernel_config.py`` file to the
``jupyter`` config path (for example ``~/.jupyter/scilab_kernel_config.py``.  The ``ScilabKernel`` class offers ``plot_settings`` as a configurable traits.
The available plot settings are:

 - 'format': 'svg' (default), 'png', 'jpg',
 - 'backend': 'inline',
 - 'size': '<width>,<height>' ('560,420' by default),
 - 'antialiasing': for 'svg' backend only, True by default.

.. code:: python

    c.ScilabKernel.plot_settings = dict(format='svg', backend='inline', size='560,420', antialiasing=False)

Scilab default behavior is setup using `lines(0, 800)` and `mode(0)`. You can change these behaviors using scilab code on cells.

Files ending with `.sci` in the current directory are loaded.

Troubleshooting
---------------

Kernel Times Out While Starting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If the kernel does not start, run the following command from a terminal:

.. code:: shell

  python -m scilab_kernel.check

This can help diagnose problems with setting up integration with Scilab.  If in doubt,
create an issue with the output of that command.

Kernel is Not Listed
~~~~~~~~~~~~~~~~~~~~
If the kernel is not listed as an available kernel, first try the following command:

.. code:: shell

    python -m scilab_kernel install --user

If the kernel is still not listed, verify that the following point to the same
version of python:

.. code:: shell

    which python  # use "where" if using cmd.exe
    which jupyter

Advanced Installation Notes
---------------------------
We automatically install a Jupyter kernelspec when installing the
python package.  This location can be found using ``jupyter kernelspec list``.
If the default location is not desired, you can remove the directory for the
``scilab`` kernel, and install using `python -m scilab_kernel install`.  See
``python -m scilab_kernel install --help`` for available options.

.. _online: http://nbviewer.ipython.org/github/calysto/scilab_kernel/blob/master/scilab_kernel.ipynb
