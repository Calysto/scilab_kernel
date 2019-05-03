A Jupyter kernel for Scilab

Prerequisites
-------------
`Jupyter Notebook <http://jupyter.readthedocs.org/en/latest/install.html>`_, and `Scilab <http://www.scilab.org/download/latest>`_.

Installation
------------

    pip install scilab_kernel

To use it, run one of:

.. code:: shell

    ipython notebook
    # In the notebook interface, select Scilab from the 'New' menu
    ipython qtconsole --kernel scilab
    ipython console --kernel scilab

This kernel is based on `MetaKernel <http://pypi.python.org/pypi/metakernel>`_,
which means it features a standard set of magics.  For a full list of magics,
run ``%lsmagic`` in a cell.

A sample notebook is available online_.

You can specify the path to your Scilab executable by creating a ``SCILAB_EXECUTABLE`` environmental variable.  Use the ``scilab-adv-cli`` executable if using a Posix-like OS, and ``WScilex-cli.exe`` if using Windows.


Troubleshooting
---------------
If the kernel is not starting, try running the following from a terminal.

.. code
  python -m scilab_kernel.check

Please include that output if opening an issue.


Advanced Installation Notes
---------------------------
We automatically install a Jupyter kernelspec when installing the
python package.  This location can be found using ``jupyter kernelspec list``.
If the default location is not desired, you can remove the directory for the
``scilab`` kernel, and install using `python -m scilab_kernel install`.  See
``python -m scilab_kernel install --help`` for available options.

.. _online: http://nbviewer.ipython.org/github/calysto/scilab_kernel/blob/master/scilab_kernel.ipynb
