import re
import subprocess
from pathlib import Path

from .version import VERSION

THIS_DIR = Path(__file__).parent.resolve()
WK_PATH = THIS_DIR / 'bin' / 'wkhtmltopdf'


def execute_wk(*args, input=None):
    """
    Generate path for the wkhtmltopdf binary and execute command.

    :param args: args to pass straight to subprocess.Popen
    :return: stdout, stderr
    """
    wk_args = (str(WK_PATH),) + args
    return subprocess.run(wk_args, input=input, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def generate_pdf(source, *,
                 title=None,
                 author=None,
                 subject=None,
                 creator=None,
                 producer=None,
                 # from here on arguments are passed via the commandline to wkhtmltopdf
                 cache_dir=None,
                 grayscale=False,
                 lowquality=False,
                 margin_bottom=None,
                 margin_left=None,
                 margin_right=None,
                 margin_top=None,
                 orientation=None,
                 page_height=None,
                 page_width=None,
                 page_size=None,
                 image_dpi=None,
                 image_quality=None,
                 **extra_kwargs):
    """
    Generate a pdf from either a url or a html string.

    After the html and url arguments all other arguments are
    passed straight to wkhtmltopdf

    For details on extra arguments see the output of get_help()
    and get_extended_help()

    All arguments whether specified or caught with extra_kwargs are converted
    to command line args with "'--' + original_name.replace('_', '-')"

    Arguments which are True are passed with no value eg. just --quiet, False
    and None arguments are missed, everything else is passed with str(value).

    :param source: html string to generate pdf from or url to get
    :param grayscale: bool
    :param lowquality: bool
    :param margin_bottom: string eg. 10mm
    :param margin_left: string eg. 10mm
    :param margin_right: string eg. 10mm
    :param margin_top: string eg. 10mm
    :param orientation: Portrait or Landscape
    :param page_height: string eg. 10mm
    :param page_width: string eg. 10mm
    :param page_size: string: A4, Letter, etc.
    :param image_dpi: int default 600
    :param image_quality: int default 94
    :param extra_kwargs: any exotic extra options for wkhtmltopdf
    :return: string representing pdf
    """
    if source.lstrip().startswith(('http', 'www')):
        raise ValueError('pdf generation from urls is not supported')

    py_args = dict(
        cache_dir=cache_dir,
        grayscale=grayscale,
        lowquality=lowquality,
        margin_bottom=margin_bottom,
        margin_left=margin_left,
        margin_right=margin_right,
        margin_top=margin_top,
        orientation=orientation,
        page_height=page_height,
        page_width=page_width,
        page_size=page_size,
        image_dpi=image_dpi,
        image_quality=image_quality,
    )
    py_args.update(extra_kwargs)
    cmd_args = []
    for name, value in py_args.items():
        if value in {None, False}:
            continue
        arg_name = '--' + name.replace('_', '-')
        if value is True:
            cmd_args.append(arg_name)
        else:
            cmd_args.extend([arg_name, str(value)])

    # read from stdin and write to stdout
    cmd_args += ['-', '-']

    p = execute_wk(*cmd_args, input=source.encode())
    pdf_bytes = p.stdout

    # it seems wkhtmltopdf's error codes can be false, we'll ignore them if we
    # seem to have generated a pdf
    if p.returncode != 0 and pdf_bytes[:4] != b'%PDF':
        raise RuntimeError('error running wkhtmltopdf, command: {!r}\n'
                           'response: "{}"'.format(cmd_args, p.stderr.strip()))

    fields = [
        ('Title', title),
        ('Author', author),
        ('Subject', subject),
        ('Creator', creator),
        ('Producer', producer),
    ]
    metadata = '\n'.join(f'/{name} ({value})' for name, value in fields if value)
    if metadata:
        pdf_bytes = re.sub(b'/Title.*\n.*\n/Producer.*', metadata.encode(), pdf_bytes, count=1)
    return pdf_bytes


def _string_execute(*args):
    return execute_wk(*args).stdout.decode().strip(' \n')


def get_version():
    """
    Get version of pydf and wkhtmltopdf binary

    :return: version string
    """
    try:
        wk_version = _string_execute('-V')
    except Exception as e:
        # we catch all errors here to make sure we get a version no matter what
        wk_version = '%s: %s' % (e.__class__.__name__, e)
    return 'pydf version: %s\nwkhtmltopdf version: %s' % (VERSION, wk_version)


def get_help():
    """
    get help string from wkhtmltopdf binary
    uses -h command line option

    :return: help string
    """
    return _string_execute('-h')


def get_extended_help():
    """
    get extended help string from wkhtmltopdf binary
    uses -H command line option

    :return: extended help string
    """
    return _string_execute('-H')
