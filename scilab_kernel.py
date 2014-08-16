from IPython.kernel.zmq.kernelbase import Kernel
from IPython.utils.path import locate_profile
from IPython.core.oinspect import Inspector, cast_unicode
from scilab2py import Scilab2PyError, scilab

import os
import signal
from subprocess import check_output, CalledProcessError
import re
import logging

__version__ = '0.1'

version_pat = re.compile(r'version "(\d+(\.\d+)+)')


class ScilabKernel(Kernel):
    implementation = 'scilab_kernel'
    implementation_version = __version__
    language = 'scilab'

    @property
    def language_version(self):
        self.log.info(self.banner)
        m = version_pat.search(self.banner)
        return m.group(1)

    _banner = None

    @property
    def banner(self):
        if self._banner is None:
            if os.name == 'nt':
                prog = 'Scilex'
            else:
                prog = 'scilab'

            try:
                banner = check_output([prog, '-version'])
                banner = banner.decode('utf-8')
            except CalledProcessError as e:
                banner = e.output.decode('utf-8')
            self._banner = banner
        return self._banner

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)

        self.log.setLevel(logging.INFO)

        # Signal handlers are inherited by forked processes,
        # and we can't easily reset it from the subprocess.
        # Since kernelapp ignores SIGINT except in message handlers,
        # we need to temporarily reset the SIGINT handler here
        # so that octave and its children are interruptible.
        sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            self.scilab_wrapper = scilab
            scilab.restart()
            # start scilab and override gettext function
            self.log.info('starting up')
            self.scilab_wrapper.eval('_ = ""')
            self.log.info('started')
        finally:
            signal.signal(signal.SIGINT, sig)

        try:
            self.hist_file = os.path.join(locate_profile(),
                                          'scilab_kernel.hist')
        except IOError:
            self.hist_file = None
            self.log.warn('No default profile found, history unavailable')

        self.inspector = Inspector()
        self.inspector.set_active_scheme("Linux")

        self.max_hist_cache = 1000
        self.hist_cache = []
        self.inline = False

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        """Execute a line of code in Octave."""

        code = code.strip()
        abort_msg = {'status': 'abort',
                     'execution_count': self.execution_count}

        if code and store_history:
            self.hist_cache.append(code)

        if not code or code == 'keyboard' or code.startswith('keyboard('):
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

        elif (code == 'exit' or code.startswith('exit(')
                or code == 'quit' or code.startswith('quit(')):
            # TODO: exit gracefully here
            self.do_shutdown(False)
            return abort_msg

        elif code == 'restart' or code.startswith('restart('):
            self.scilab_wrapper.restart()
            return abort_msg

        elif code.endswith('?') or code.startswith('?'):
            self._get_help(code)
            return abort_msg

        elif code == '%inline':
            self.inline = not self.inline
            output = "Inline is set to %s" % self.inline
            stream_content = {'name': 'stdout', 'data': output}
            self.send_response(self.iopub_socket, 'stream', stream_content)
            return abort_msg

        interrupted = False
        try:
            if self.inline:
                self._pre_call()
            output = self.scilab_wrapper.eval(code)

        except KeyboardInterrupt:
            self.scilab_wrapper._session.proc.send_signal(signal.SIGINT)
            interrupted = True
            output = 'Scilab Session Interrupted'

        except Scilab2PyError as e:
            return self._handle_error(str(e))

        except Exception:
            self.scilab_wrapper.restart()
            output = 'Uncaught Exception, Restarting Scilab'

        else:
            if output is None:
                output = ''
            elif output == 'Scilab Session Interrupted':
                interrupted = True
            else:
                output = str(output)

        if not silent:
            stream_content = {'name': 'stdout', 'data': output}
            self.send_response(self.iopub_socket, 'stream', stream_content)

            if self.inline:
                self._handle_figures()

        if interrupted:
            return abort_msg

        return {'status': 'ok', 'execution_count': self.execution_count,
                'payload': [], 'user_expressions': {}}

    def do_complete(self, code, cursor_pos):
        """Get code completions using Scilab's ``completions``"""

        code = code[:cursor_pos]
        default = {'matches': [], 'cursor_start': 0,
                   'cursor_end': cursor_pos, 'metadata': dict(),
                   'status': 'ok'}

        if code[-1] == ' ':
            return default

        tokens = code.replace(';', ' ').split()
        if not tokens:
            return default
        token = tokens[-1]

        start = cursor_pos - len(token)
        cmd = 'completion("%s")' % token
        output = self.scilab_wrapper.eval(cmd)

        matches = []

        if not output is None:
            matches = output.replace('!', ' ').split()
            for item in dir(self.scilab_wrapper):
                if item.startswith(token) and not item in matches:
                    matches.append(item)

        matches.extend(_complete_path(token))

        return {'matches': matches, 'cursor_start': start,
                'cursor_end': cursor_pos, 'metadata': dict(),
                'status': 'ok'}

    def do_inspect(self, code, cursor_pos, detail_level=0):
        """If the code ends with a (, try to return a calltip docstring"""
        default = {'status': 'aborted', 'data': dict(), 'metadata': dict()}
        if (not code or not len(code) >= cursor_pos or
                not code[cursor_pos - 1] == '('):
            return default

        else:
            token = code[:cursor_pos - 1].replace(';', '').split()[-1]
            info = _get_scilab_info(self.scilab_wrapper, self.inspector,
                                    token, detail_level)
            docstring = info['docstring']

        if docstring:
            data = {'text/plain': docstring}
            return {'status': 'ok', 'data': data, 'metadata': dict()}

        return default

    def do_history(self, hist_access_type, output, raw, session=None,
                   start=None, stop=None, n=None, pattern=None, unique=False):
        """Access history at startup.
        """
        if not self.hist_file:
            return {'history': []}

        if not os.path.exists(self.hist_file):
            with open(self.hist_file, 'wb') as fid:
                fid.write(''.encode('utf-8'))

        with open(self.hist_file, 'rb') as fid:
            history = fid.readlines()

        history = history[-self.max_hist_cache:]
        history = [h.decode('utf-8') for h in history]
        self.hist_cache = history
        self.log.info('**HISTORY:')
        self.log.info(self.hist_file)
        self.log.info(history[-10:])
        history = [(None, None, h) for h in history]

        return {'history': history}

    def do_shutdown(self, restart):
        """Shut down the app gracefully, saving history.
        """
        self.log.info("**Shutting down")

        if restart:
            self.scilab_wrapper.restart()

        else:
            self.scilab_wrapper.exit()

        if self.hist_file:
            with open(self.hist_file, 'wb') as fid:
                msg = '\n'.join(self.hist_cache[-self.max_hist_cache:])
                fid.write(msg.encode('utf-8'))

        return {'status': 'ok', 'restart': restart}

    def _pre_call(self):
        """Set the default figure properties"""

        code = """
        h = gdf()
        h.figure_position = [0, 0]
        h.toolbar_visible = 'off'
        h.menubar_visible = 'off'
        h.infobar_visible = 'off'
        """
        self.scilab_wrapper.eval(code)

    def _handle_figures(self):
        import tempfile
        from shutil import rmtree
        import glob
        import base64

        plot_dir = tempfile.mkdtemp().replace('\\', '/')
        plot_fmt = 'png'

        code = """
           ids_array=winsid();
           for i=1:length(ids_array)
              id=ids_array(i);
              outfile = sprintf('%(plot_dir)s/__ipy_sci_fig_%%03d', i);
              if '%(plot_fmt)s' == 'jpg' then
                xs2jpg(id, outfile + '.jpg')
              elseif '%(plot_fmt)s' == 'jpeg' then
                xs2jpg(id, outfile + '.jpeg')
              elseif '%(plot_fmt)s' == 'png' then
                xs2png(id, outfile)
              else
                xs2svg(id, outfile)
              end
              close(get_figure_handle(id));
           end
        """ % (locals())

        self.scilab_wrapper.eval(code)

        width, height = 640, 480

        _mimetypes = {'png': 'image/png',
                      'svg': 'image/svg+xml',
                      'jpg': 'image/jpeg',
                      'jpeg': 'image/jpeg'}

        images = []
        for imgfile in glob.glob("%s/*" % plot_dir):
            with open(imgfile, 'rb') as fid:
                images.append(fid.read())
        rmtree(plot_dir)

        plot_mime_type = _mimetypes.get(plot_fmt, 'image/png')

        for image in images:
            image = base64.b64encode(image).decode('ascii')
            data = {plot_mime_type: image}
            metadata = {plot_mime_type: {'width': width, 'height': height}}

            self.log.info('Sending a plot')
            stream_content = {'source': 'octave_kernel', 'data': data,
                              'metadata': metadata}
            self.send_response(self.iopub_socket, 'display_data',
                               stream_content)

    def _get_help(self, code):
        if code.startswith('??') or code.endswith('??'):
            detail_level = 1
        else:
            detail_level = 0

        code = code.replace('?', '')
        tokens = code.replace(';', ' ').split()
        if not tokens:
            return
        token = tokens[-1]

        try:
            info = _get_scilab_info(self.scilab_wrapper, self.inspector,
                                    token, detail_level)
        except Exception as e:
            self.log.error(e)
            return

        if 'built-in Scilab function.' in info['docstring']:
            self.scilab_wrapper.help(token)

            output = 'Calling Help Browser for `%s`' % token
            stream_content = {'name': 'stdout', 'data': output}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        elif info['docstring']:
            output = _get_printable_info(self.inspector, info, detail_level)
            stream_content = {'name': 'stdout', 'data': output}
            self.send_response(self.iopub_socket, 'stream', stream_content)

    def _handle_error(self, err):
        if 'parse error:' in err:
            err = 'Parse Error'

        elif 'Scilab returned:' in err:
            err = err[err.index('Scilab returned:'):]
            err = err[len('Scilab returned:'):].lstrip()

        elif 'Syntax Error' in err:
            err = 'Syntax Error'

        stream_content = {'name': 'stdout', 'data': err.strip()}
        self.send_response(self.iopub_socket, 'stream', stream_content)

        return {'status': 'error', 'execution_count': self.execution_count,
                'ename': '', 'evalue': err, 'traceback': []}


def _get_printable_info(inspector, info, detail_level=0):
    displayfields = []

    def add_fields(fields):
        for title, key in fields:
            field = info[key]
            if field is not None:
                displayfields.append((title, field.rstrip()))

    add_fields(inspector.pinfo_fields1)
    add_fields(inspector.pinfo_fields2)
    add_fields(inspector.pinfo_fields3)

    # Source or docstring, depending on detail level and whether
    # source found.
    if detail_level > 0 and info['source'] is not None:
        source = cast_unicode(info['source'])
        displayfields.append(("Source",  source))

    elif info['docstring'] is not None:
        displayfields.append(("Docstring", info["docstring"]))

    # Info for objects:
    else:
        add_fields(inspector.pinfo_fields_obj)

    # Finally send to printer/pager:
    if displayfields:
        return inspector._format_fields(displayfields)


def _get_scilab_info(scilab, inspector, obj, detail_level):
    info = dict(argspec=None, base_class=None, call_def=None,
                call_docstring=None, class_docstring=None,
                definition=None, docstring='', file=None,
                found=False, init_definition=None,
                init_docstring=None, isalias=0, isclass=None,
                ismagic=0, length=None, name='', namespace=None,
                source=None, string_form=None, type_name='')

    sci = scilab

    if obj in dir(sci):
        obj = getattr(sci, obj)
        return inspector.info(obj, detail_level=detail_level)

    exist = sci.eval('exists("%s")' % obj)
    if exist == 0 or exist is None:
        return info

    typeof = sci.eval('typeof(%s);' % obj) or 'Error'
    lookup = dict(st="structure array", ce="cell array",
                  fptr="built-in Scilab function")
    typeof = lookup.get(typeof, typeof)

    var = None

    if typeof in ['function', 'built-in Scilab function']:
        docstring = getattr(sci, obj).__doc__

    else:
        docstring = 'A %s' % typeof
        try:
            var = sci.pull(obj)
        except Scilab2PyError:
            pass

    if typeof == 'function':
        info['definition'] = docstring.strip().splitlines()[0].strip()
        docstring = '\n'.join(docstring.strip().splitlines()[1:])

    source = docstring

    info['found'] = True
    info['docstring'] = docstring
    info['type_name'] = typeof.capitalize()
    info['source'] = source
    info['string_form'] = obj if var is None else str(var)

    return info


def _listdir(root):
    "List directory 'root' appending the path separator to subdirs."
    res = []
    for name in os.listdir(root):
        path = os.path.join(root, name)
        if os.path.isdir(path):
            name += os.sep
        res.append(name)
    return res


def _complete_path(path=None):
    """Perform completion of filesystem path.

    http://stackoverflow.com/questions/5637124/tab-completion-in-pythons-raw-input
    """
    if not path:
        return _listdir('.')
    dirname, rest = os.path.split(path)
    tmp = dirname if dirname else '.'
    res = [os.path.join(dirname, p)
           for p in _listdir(tmp) if p.startswith(rest)]
    # more than one match, or single match which does not exist (typo)
    if len(res) > 1 or not os.path.exists(path):
        return res
    # resolved to a single directory, so return list of files below it
    if os.path.isdir(path):
        return [os.path.join(path, p) for p in _listdir(path)]
    # exact file match terminates this completion
    return [path + ' ']


if __name__ == '__main__':
    from IPython.kernel.zmq.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=ScilabKernel)
