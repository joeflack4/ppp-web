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

# TODO: Refactor to run consistently wherever (browser, test suite, etc)
try:
    # noinspection PyUnresolvedReferences,PyPackageRequirements
    from app import app_config, version
except ModuleNotFoundError:
    from webui.app import app_config, version


class IndexView(MethodView):
    """
    Index view class with two handlers for GET and POST requests
    """
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
        command_line = \
            self._build_pmix_ppp_tool_run_cmd(in_file_path=temp_file.name,
                                              out_format='html',
                                              out_file_path=html_file_path)
        _, stderr = self._run_background_process(command_line)

        # if pmix.ppp tool wrote something to stderr, we should show it to user
        if stderr:
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

        # return file as response attachment, so browser will start download
        return send_file(pdf_doc_file_path,
                         as_attachment=True,
                         mimetype=mime_type,
                         attachment_filename=uploaded_file.filename
                         .replace('.xlsx', output_ext)
                         .replace('.xls', output_ext))

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
            .replace('.xls', '').replace('.html', '.doc')
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
    def _build_pmix_ppp_tool_run_cmd(in_file_path, out_format, out_file_path):
        """This method build command line command to run pmix.ppp tool.

        Returns:
            string: Command.
        """
        language = request.form.get('language', 'English')
        preset = request.form.get('preset', 'minimal')
        # options = request.form.getlist('options')
        # if preset != 'custom':
        #     options = ['preset ' + preset]

        python_path = 'python'  # TODO move this into the config file
        if 'SERVER_INFO' in os.environ and os.environ['SERVER_INFO'].lower()\
                == 'linode':
            python_path = app_config.PYTHON_PATH

        command_line = " ".join((
            python_path,
            '-m ppp',
            shlex.quote(in_file_path),
            "--language " + language,
            "--format " + out_format,
            "--preset " + preset,
            "--template " + "old",
            "--outpath " + shlex.quote(out_file_path)
            # *('--{}'.format(option) for option in options),
        ))

        return command_line
