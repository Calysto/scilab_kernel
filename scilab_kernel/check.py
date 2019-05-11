import sys
from metakernel import __version__ as mversion
from . import __version__
from .kernel import ScilabKernel


if __name__ == "__main__":
    print('Scilab kernel v%s' % __version__)
    print('Metakernel v%s' % mversion)
    print('Python v%s' % sys.version)
    print('Python path: %s' % sys.executable)
    print('\nConnecting to Scilab...')
    try:
        s = ScilabKernel()
        print('Scilab connection established')
        print(s.banner)
    except Exception as e:
        print(e)
