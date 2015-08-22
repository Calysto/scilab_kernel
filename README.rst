A simple IPython kernel for Scilab

This requires IPython 3+ and `scilab2py <http://pypi.python.org/pypi/scilab2py>`_.

To test it, install with ``setup.py``, then::

    ipython qtconsole --kernel scilab

It supports command history, the ``?`` help magic and calltips,
plotting, and completion.  You can toggle inline plotting using ``%inline``.

For details of how this works, see IPython's docs on `wrapper kernels
<http://ipython.org/ipython-doc/dev/development/wrapperkernels.html>`_.
