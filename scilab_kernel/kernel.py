from __future__ import print_function

from metakernel import MetaKernel, ProcessMetaKernel, REPLWrapper, u
from metakernel.pexpect import which
from IPython.display import Image, SVG
import subprocess
from xml.dom import minidom
import os
import sys
import tempfile


from . import __version__


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

    _setup = """
    try
      getd(".");
    catch
    end
    """

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
                executable = 'Scilex'
            else:
                executable = 'scilab'
            if not which(executable):
                msg = ('Scilab Executable not found, please add to path or set'
                       '"SCILAB_EXECUTABLE" environment variable')
                raise OSError(msg)
        self._executable = executable
        return executable

    @property
    def banner(self):
        if self._banner is None:
            call = '%s -version; true' % self.executable
            banner = subprocess.check_output(call, shell=True)
            self._banner = banner.decode('utf-8')
        return self._banner

    def makeWrapper(self):
        """Start a Scilab process and return a :class:`REPLWrapper` object.
        """
        if os.name == 'nt':
            orig_prompt = u(chr(3))
            prompt_cmd = u('disp(char(3))')
            change_prompt = None
        else:
            orig_prompt = u('-->')
            prompt_cmd = None
            change_prompt = None

        self._first = True

        executable = self.executable + ' -nw'
        wrapper = REPLWrapper(executable, orig_prompt, change_prompt,
                prompt_emit_cmd=prompt_cmd)
        wrapper.child.linesep = '\n'
        return wrapper

    def _do_execute_direct(self, code):
        'disp(char(2));' + code
        resp = super(ScilabKernel, self).do_execute_direct(code)
        resp = [line for line in str(resp).splitlines()
                if not line.startswith(chr(27))]
        return '\n'.join(resp)

    def Print(self, text):
        text = [line.strip() for line in str(text).splitlines()
                if (not line.startswith(chr(27)))]
        text = '\n'.join(text)
        if text:
            super(ScilabKernel, self).Print(text)

    def do_execute_direct(self, code):
        if self._first:
            self._first = False
            self.handle_plot_settings()
            self._do_execute_direct(self._setup)

        self._skipping = os.name != 'nt'
        super(ScilabKernel, self).do_execute_direct(code, self.Print)
        if self.plot_settings.get('backend', None) == 'inline':
            plot_dir = tempfile.mkdtemp()
            self._make_figs(plot_dir)
            width, height = 0, 0
            for fname in os.listdir(plot_dir):
                filename = os.path.join(plot_dir, fname)
                try:
                    if fname.lower().endswith('.svg'):
                        im = SVG(filename)
                        if ',' in self.plot_settings['size']:
                            size = self.plot_settings['size']
                            width, height = size.split(',')
                            width, height = int(width), int(height)
                            im.data = self._fix_svg_size(im.data,
                                size=(width, height))
                    else:
                        im = Image(filename)
                    self.Display(im)
                except Exception as e:
                    self.Error(e)

    def get_kernel_help_on(self, info, level=0, none_on_fail=False):
        obj = info.get('help_obj', '')
        if not obj or len(obj.split()) > 1:
            if none_on_fail:
                return None
            else:
                return ""
        self._do_execute_direct('help %s' % obj)

    def do_shutdown(self, restart):
        self.wrapper.sendline('quit')
        super(ScilabKernel, self).do_shutdown(restart)

    def get_completions(self, info):
        """
        Get completions from kernel based on info dict.
        """
        cmd = 'completion("%s")' % info['obj']
        output = self._do_execute_direct(cmd)
        if not output:
            return
        output = output.replace('!', '')
        return [line.strip() for line in output.splitlines()
                if info['obj'] in line]

    def handle_plot_settings(self):
        """Handle the current plot settings"""
        settings = self.plot_settings
        if settings.get('format', None) is None:
            settings.clear()
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

        if settings['backend'] == 'inline' and 'linux' not in sys.platform:
            cmds.append('h.visible = "off";')
        else:
            cmds.append('h.visible = "on";')
        super(ScilabKernel, self).do_execute_direct('\n'.join(cmds))

    def _make_figs(self, plot_dir):
        plot_dir = plot_dir.replace(os.sep, '/')
        plot_format = self._plot_fmt
        cmd = """
        ids_array=winsid();
        for i=1:length(ids_array)
          id=ids_array(i);
          outfile = sprintf('%(plot_dir)s/__ipy_sci_fig_%%03d', i);
          disp(outfile)
          if '%(plot_format)s' == 'jpg' then
            xs2jpg(id, outfile + '.jpg');
          elseif '%(plot_format)s' == 'jpeg' then
            xs2jpg(id, outfile + '.jpeg');
          elseif '%(plot_format)s' == 'png' then
            xs2png(id, outfile);
          else
            xs2svg(id, outfile);
          end
          close(get_figure_handle(id));
        end
        """ % locals()
        super(ScilabKernel, self).do_execute_direct(cmd)

    def _fix_svg_size(self, image, size=None):
        """
        Scilab SVGs do not have height/width attributes.  Set
        these to be the same as the viewBox, so that the browser
        scales the image correctly.

        Parameters
        ----------
        image : str
            SVG data.
        size : tuple of int
            Image width, height.

        """
        (svg,) = minidom.parseString(image).getElementsByTagName('svg')
        viewbox = svg.getAttribute('viewBox').split(' ')

        if size is not None and size[0] is not None:
            width, height = size
        else:
            width, height = viewbox[2:]

        svg.setAttribute('width', '%dpx' % int(width))
        svg.setAttribute('height', '%dpx' % int(height))
        return svg.toxml()
