"""Views for application."""
import os
import shlex
import subprocess
import ntpath
from copy import copy
from platform import platform
from tempfile import NamedTemporaryFile

from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from flask import url_for
from flask.views import MethodView
# noinspection PyPackageRequirements
from ppp import run, OdkException


try:
    from ppp_web.ppp_web import app_config
    from ppp_web.config import version
except ModuleNotFoundError:
    # noinspection PyUnresolvedReferences
    from ppp_web import app_config
    # noinspection PyUnresolvedReferences,PyPackageRequirements
    from config import version


class IndexView(MethodView):
    """Index view class with two handlers for GET and POST requests."""
    @staticmethod
    def get():
        """Get method."""
        return render_template('index.html',
                               version=version,
                               title='PPP for Open Data Kit')

    def post(self):
        """POST request handler. Processes form data"""

        # check if user uploaded an excel file
        uploaded_file = request.files['file']
        if uploaded_file and not (uploaded_file.filename.endswith('.xls') or
                                  uploaded_file.filename.endswith('.xlsx')):
            flash("Uploaded file is not an .xls or .xlsx file", "error")
            return redirect(url_for('index'))

        # save file to /tmp folder
        temp_file = NamedTemporaryFile()
        temp_file_name_w_extension = ntpath.basename(temp_file.name)
        temp_file.name = temp_file.name\
            .replace(temp_file_name_w_extension, uploaded_file.filename)
        uploaded_file.save(temp_file.name)

        # get output format
        output_format = request.form.get('format')
        output_ext = '.' + output_format
        # process output format and mime type for downloading
        post_process_to = None
        mime_type = 'text/html' if output_format == 'html'\
            else 'application/text'
        if output_format in ('pdf', 'doc'):
            post_process_to = output_format

        # convert uploaded file to html
        temp_html_file = NamedTemporaryFile()
        html_file_path = copy(temp_file.name).replace('.xlsx', '')\
            .replace('.xls', '') + '.' + 'html'
        temp_html_file.name = html_file_path

        # TODO: This hard-makes PPP conv to HTML. Change to doc if doc, etc.
        out_format = 'html' if output_format == 'pdf' else output_format

        command_line = \
            self._build_ppp_ppp_tool_run_cmd(in_file_path=temp_file.name,
                                             out_format=out_format,
                                             out_file_path=html_file_path)
        _, stderr = self._run_background_process(command_line)
        ''' ppp_resp = self._run_ppp_api(in_file_path=temp_file.name,
                                     out_format=out_format,
                                     out_file_path=html_file_path) '''
        is_warning = False
        if stderr:
            is_debug_msg = stderr.startswith('pydev debugger: process ') and stderr.endswith(' is connecting')
            is_warning = stderr.lower().startswith('warning')
            if is_debug_msg:
                stderr = ''
            elif is_warning is False:
                flash("STDERR:\n{}".format(stderr), "error")
                return redirect(url_for('index'))

        # output path now exists and refers to converted html file at /tmp
        pdf_doc_file_path = html_file_path

        # if output format is PDF or DOC
        if post_process_to == 'pdf':
            try:
                w_p = app_config.WKHTMLTOPDF_PATH_LOCAL
                pdf_doc_file_name, pdf_doc_file_path, mime_type = \
                    self._convert_to_pdf(_input=html_file_path,
                                         wkhtmltopdf_path=w_p)
            except OSError:
                try:
                    # TODO: This hasn't been fully implementaed
                    w_p = 'This hasnt been implemented yet. My WKTHMLTOPDF ' \
                          'is installed globally. This message will throw ' \
                          'an error.'
                    # w_p = app_config.WKHTMLTOPDF_PATH_SYSTEM
                    pdf_doc_file_name, pdf_doc_file_path, mime_type = \
                        self._convert_to_pdf(_input=html_file_path,
                                             wkhtmltopdf_path=w_p)
                except FileNotFoundError:
                    # TODO: download and install a binary
                    msg = 'PDF conversion is currently not supported for ' \
                          'this system: {}'.format(platform())
                    raise Exception(msg)
        elif post_process_to == 'doc':
            pdf_doc_file_name, pdf_doc_file_path, mime_type = \
                self._convert_to_doc(_input=html_file_path)

        attachment_filename = uploaded_file.filename\
            .replace('.xlsx', output_ext).replace('.xls', output_ext)

        # if ppp.ppp tool wrote something to stderr, we should show it to user
        if stderr:
            if is_warning:
                flash("\n{}".format(stderr), "warning")
                return render_template('index.html',
                                       version=version, **locals())

        # return file as response attachment, so browser will start download
        return send_file(pdf_doc_file_path,
                         as_attachment=True,
                         mimetype=mime_type,
                         attachment_filename=attachment_filename)

    def _convert_to_pdf(self, _input, wkhtmltopdf_path):
        """This method converts .html file to .pdf file

        Uses external tool named `wkhtmltopdf`.

        Returns:
             Path to converted file and mime type.
        """
        pdf_file_path = _input.replace('.html', '.pdf')

        # create command line string for html->pdf converter
        command_line = " ".join((
            wkhtmltopdf_path,
            shlex.quote(_input),
            shlex.quote(pdf_file_path)
        ))
        self._run_background_process(command_line)

        _, pdf_file_name = os.path.split(pdf_file_path)
        mime_type = 'text/pdf'

        return pdf_file_name, pdf_file_path, mime_type

    @staticmethod
    def _convert_to_doc(_input):
        """This method renames .html file to .doc file.

        Returns:
            path to renamed file and mime type for word files.
        """
        doc_file_path = _input.replace('.xlsx', '')\
            .replace('.xls', '')\

        os.rename(_input, doc_file_path)
        _, doc_file_name = os.path.split(doc_file_path)
        mime_type = 'application/vnd.openxmlformats-officedocument.' \
                    'wordprocessingml.document'

        return doc_file_name, doc_file_path, mime_type

    @staticmethod
    def _run_background_process(command_line):
        """This method runs external program using command line interface.

        Returns:
             stdout,stdin: Of executed program.
        """

        args = shlex.split(command_line)
        process = subprocess.Popen(args, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.wait()
        stdout = process.stdout.read().decode().strip()
        stderr = process.stderr.read().decode().strip()

        return stdout, stderr

    @staticmethod
    def _run_ppp_api(in_file_path, out_format, out_file_path):
        import sys
        from io import StringIO
        language = request.form.get('language')
        lang_option = language if language and language != 'none' else ''
        preset = request.form.get('preset', 'standard')

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        # @Bciar: I commented out next line because not used. -Joe, 2018/10/16
        # redirected_output = sys.stdout = StringIO()
        redirected_error = sys.stderr = StringIO()
        # noinspection PyBroadException
        try:
            with run(files=[in_file_path],
                     languages=[lang_option],
                     format=out_format,
                     preset=preset,
                     template='old',
                     outpath=out_file_path) as output:
                print('run de out', output)
        except OdkException as err:
            return err
        except Exception:
            import traceback
            # @Bciar: Commented next lines because not used. -Joe, 2018/10/16
            # exc = traceback.format_exc()
            # out = redirected_output.getvalue()
            err = redirected_error.getvalue()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            print('run stdout=====>', err)
            return err
            
    @staticmethod
    def _build_ppp_ppp_tool_run_cmd(in_file_path, out_format, out_file_path):
        """This method build command line command to run ppp tool.

        Returns:
            string: Command.
        """
        language = request.form.get('language')
        lang_option = \
            '--language ' + language if language and language != 'none' else ''
        preset = request.form.get('preset', 'standard')
        # Note: Options to be added in the future. - Joe 2018/10/16
        # options = request.form.getlist('options')
        command_line = ' '.join((
            'python',
            '-m ppp',
            shlex.quote(in_file_path),
            lang_option,
            '--format ' + out_format,
            '--preset ' + preset,
            '--template ' + 'old',
            '--outpath ' + shlex.quote(out_file_path)
            # *('--{}'.format(option) for option in options),
        ))

        return command_line
