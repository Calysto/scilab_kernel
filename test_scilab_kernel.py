"""Example use of jupyter_kernel_test, with tests for IPython."""

import unittest
import jupyter_kernel_test as jkt


class ScilabKernelTests(jkt.KernelTests):
    kernel_name = "scilab"

    language_name = "scilab"

    code_hello_world = "disp('hello, world')"

    completion_samples = [
        {
            'text': 'one',
            'matches': {'ones'},
        },
    ]

if __name__ == '__main__':
    unittest.main()
