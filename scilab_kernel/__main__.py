try:
    from ipykernel.kernelapp import IPKernelApp
except ImportError:
    from IPython.kernel.zmq.kernelapp import IPKernelApp
from .kernel import ScilabKernel
IPKernelApp.launch_instance(kernel_class=ScilabKernel)
