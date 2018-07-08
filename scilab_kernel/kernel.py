from __future__ import print_function, absolute_import

import codecs
import json
import os
import shutil
import subprocess
import sys
import tempfile
from xml.dom import minidom

from metakernel import MetaKernel, ProcessMetaKernel, REPLWrapper
from metakernel.pexpect import which
from IPython.display import Image, SVG

from . import __version__


def get_kernel_json():
    """Get the kernel json for the kernel.
    """
    here = os.path.dirname(__file__)
    with open(os.path.join(here, 'kernel.json')) as fid:
        data = json.load(fid)
    data['argv'][0] = sys.executable
    return data


class ScilabKernel(ProcessMetaKernel):
    implementation = 'Scilab Kernel'
    implementation_version = __version__,
    language = 'scilab'
    language_version = __version__,
    banner = "Scilab Kernel",
    language_info = {
        'name': 'scilab',
        'file_extension': '.sci',
        "mimetype": "text/x-octave",
        "version": __version__,
        'help_links': MetaKernel.help_links,
    }
    kernel_json = get_kernel_json()

    _setup = """
    try,getd("."),end
    try,getd("%s"),end
    """ % os.path.dirname(__file__)

    _first = True

    _banner = None

    _executable = None

    @property
    def executable(self):
        if self._executable:
            return self._executable
        executable = os.environ.get('SCILAB_EXECUTABLE', None)
        if not executable or not which(executable):
            if os.name == 'nt':
                executable = 'WScilex'
            else:
                executable = 'scilab-adv-cli'
            if not which(executable):
                msg = ('Scilab Executable not found, please add to path or set'
                       '"SCILAB_EXECUTABLE" environment variable')
                raise OSError(msg)
        if 'cli' not in executable:
            executable + ' -nw'
        self._executable = executable
        return executable

    @property
    def banner(self):
        if self._banner is None:
            call = '%s -version -nwni || true' % self.executable
            banner = subprocess.check_output(call, shell=True)
            self._banner = banner.decode('utf-8')
        return self._banner

    def makeWrapper(self):
        """Start a Scilab process and return a :class:`REPLWrapper` object.
        """
        orig_prompt = '-->'
        prompt_cmd = None
        change_prompt = None
        continuation_prompt = '  >'
        self._first = True
        if os.name == 'nt':
            prompt_cmd = 'printf("-->")'
            echo = False
        else:
            echo = True
        executable = self.executable
        with open(os.path.expanduser('~/test.log'), 'w') as fid:
            fid.write('executable: ' + executable)
        wrapper = REPLWrapper(executable, orig_prompt, change_prompt,
            prompt_emit_cmd=prompt_cmd, echo=echo,
            continuation_prompt_regex=continuation_prompt)
        wrapper.child.linesep = '\r\n' if os.name == 'nt' else '\n'
        return wrapper

    def Print(self, text):
        text = [line.strip() for line in str(text).splitlines()
                if (not line.startswith(chr(27)))]
        text = '\n'.join(text)
        if text:
            super(ScilabKernel, self).Print(text)

    def do_execute_direct(self, code, silent=False):
        if self._first:
            self._first = False
            self.handle_plot_settings()
            setup = self._setup.strip()
            self.do_execute_direct(setup, True)
        resp = super(ScilabKernel, self).do_execute_direct(code, silent=silent)
        if silent:
            return resp
        if self.plot_settings.get('backend', None) == 'inline':
            plot_dir = self.make_figures()
            for image in self.extract_figures(plot_dir):
                self.Display(image)
            shutil.rmtree(plot_dir, True)

    def get_kernel_help_on(self, info, level=0, none_on_fail=False):
        obj = info.get('help_obj', '')
        if not obj or len(obj.split()) > 1:
            if none_on_fail:
                return None
            else:
                return ""
        self.do_execute_direct('help %s' % obj, True)

    def do_shutdown(self, restart):
        self.wrapper.sendline('quit')
        super(ScilabKernel, self).do_shutdown(restart)

    def get_completions(self, info):
        """
        Get completions from kernel based on info dict.
        """
        cmd = 'completion("%s")' % info['obj']
        output = self.do_execute_direct(cmd, True)
        if not output:
            return []
        output = output.output.replace('!', '')
        return [line.strip() for line in output.splitlines()
                if info['obj'] in line]

    def handle_plot_settings(self):
        """Handle the current plot settings"""
        settings = self.plot_settings
        settings.setdefault('backend', 'inline')
        settings.setdefault('format', 'svg')
        settings.setdefault('size', '560,420')

        cmds = []

        self._plot_fmt = settings['format']

        cmds.append('h = gdf();')
        cmds.append('h.figure_position = [0, 0];')

        width, height = 560, 420
        if isinstance(settings['size'], tuple):
            width, height = settings['size']
        elif settings['size']:
            try:
                width, height = settings['size'].split(',')
                width, height = int(width), int(height)
            except Exception as e:
                self.Error('Error setting plot settings: %s' % e)

        cmds.append('h.figure_size = [%s,%s];' % (width, height))
        cmds.append('h.axes_size = [%s * 0.98, %s * 0.8];' % (width, height))

        if settings['backend'] == 'inline':
            cmds.append('h.visible = "off";')
        else:
            cmds.append('h.visible = "on";')
        super(ScilabKernel, self).do_execute_direct('\n'.join(cmds), True)

    def make_figures(self, plot_dir=None):
        """Create figures for the current figures.

        Parameters
        ----------
        plot_dir: str, optional
            The directory in which to create the plots.

        Returns
        -------
        out: str
            The plot directory containing the files.
        """
        plot_dir = plot_dir or tempfile.mkdtemp()
        plot_format = self._plot_fmt.lower()
        make_figs = '_make_figures("%s", "%s");'
        make_figs = make_figs % (plot_dir, plot_format)
        super(ScilabKernel, self).do_execute_direct(make_figs, True)
        return plot_dir

    def extract_figures(self, plot_dir):
        """Get a list of IPython Image objects for the created figures.

        Parameters
        ----------
        plot_dir: str
            The directory in which to create the plots.
        """
        images = []
        for fname in reversed(os.listdir(plot_dir)):
            filename = os.path.join(plot_dir, fname)
            try:
                if fname.lower().endswith('.svg'):
                    im = self._handle_svg(filename)
                else:
                    im = Image(filename)
                images.append(im)
            except Exception as e:
                if self.error_handler:
                    self.error_handler(e)
                else:
                    raise e
        return images

    def _handle_svg(self, filename):
        """
        Handle special considerations for SVG images.
        """
        # Gnuplot can create invalid characters in SVG files.
        with codecs.open(filename, 'r', encoding='utf-8',
                         errors='replace') as fid:
            data = fid.read()
        im = SVG(data=data)
        try:
            im.data = self._fix_svg_size(im.data)
        except Exception:
            pass
        return im

    def _fix_svg_size(self, data):
        """GnuPlot SVGs do not have height/width attributes.  Set
        these to be the same as the viewBox, so that the browser
        scales the image correctly.
        """
        # Minidom does not support parseUnicode, so it must be decoded
        # to accept unicode characters
        parsed = minidom.parseString(data.encode('utf-8'))
        (svg,) = parsed.getElementsByTagName('svg')

        viewbox = svg.getAttribute('viewBox').split(' ')
        width, height = viewbox[2:]
        width, height = int(width), int(height)

        # Handle overrides in case they were not encoded.
        settings = self.plot_settings
        if settings['width'] != -1:
            if settings['height'] == -1:
                height = height * settings['width'] / width
            width = settings['width']
        if settings['height'] != -1:
            if settings['width'] == -1:
                width = width * settings['height'] / height
            height = settings['height']

        svg.setAttribute('width', '%dpx' % width)
        svg.setAttribute('height', '%dpx' % height)
        return svg.toxml()
