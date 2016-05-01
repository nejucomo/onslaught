import sys
import logging
import argparse
import traceback
from onslaught.consts import ExitUnknownError, DateFormat
from onslaught.session import Session
from onslaught import io


Description = """\
Run the target python project through an onslaught of style, packaging,
and unit tests.
"""


def main(args=sys.argv[1:]):
    opts = parse_args(args)
    log = logging.getLogger('main')
    log.debug('Parsed opts: %r', opts)

    try:
        run_onslaught(opts.TARGET, opts.RESULTS)
    except Exception:
        log.error(traceback.format_exc())
        raise SystemExit(ExitUnknownError)


def run_onslaught(target, results):
    s = Session().initialize(target, results)

    with s.pushd_workdir():
        s.run_phase_flake8()

        s.prepare_virtualenv()
        s.install_test_utility_packages()

        s.run_sdist_phases()
        s.run_phase_unittest()

        s.generate_coverage_reports()


def parse_args(args):
    parser = argparse.ArgumentParser(description=Description)

    loggroup = parser.add_mutually_exclusive_group()

    loggroup.add_argument(
        '--quiet',
        action='store_const',
        const=logging.WARN,
        dest='loglevel',
        help='Only log warnings and errors.')

    loggroup.add_argument(
        '--debug',
        action='store_const',
        const=logging.DEBUG,
        dest='loglevel',
        help='Log everything.')

    defres = io.provider.expanduser(
        io.provider.join(
            '~',
            '.onslaught',
            'results',
            '{package}'))

    parser.add_argument(
        '--results', '-r',
        dest='RESULTS',
        type=str,
        default=defres,
        help=('Results directory which will be overwritten. ' +
              'If "{package}" is present, it is replaced with ' +
              'the package name. Default: {defres}'
              .format(defres=defres)))

    parser.add_argument(
        'TARGET',
        type=str,
        nargs='?',
        default='.',
        help='Target python source.')

    opts = parser.parse_args(args)
    init_logging(opts.loglevel)
    return opts


def init_logging(level):
    if level is None:
        level = logging.INFO

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            fmt='%(message)s',
            datefmt=DateFormat))

    root.addHandler(handler)
