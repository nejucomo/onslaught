import sys
import logging
import argparse
import tempfile
import traceback
import subprocess
from onslaught.path import Path, Home


Description = """\
Run the target python project through a battery of tests.
"""

DateFormat = '%Y-%m-%dT%H:%M:%S%z'

ExitUserFail = 1
ExitUnknownError = 2


def main(args=sys.argv[1:]):
    opts = parse_args(args)
    log = logging.getLogger('main')
    log.debug('Parsed opts: %r', opts)

    try:
        run_onslaught(Path(opts.TARGET))
    except Exception:
        log.error(traceback.format_exc())
        raise SystemExit(ExitUnknownError)


def run_onslaught(target):
    with target.cleanup_session():
        onslaught = Onslaught(target)
        with onslaught.pushd_workdir():
            onslaught.prepare_virtualenv()
            onslaught.install_cached_packages()
            onslaught.install_test_utility_packages()

            onslaught.run_phase_flake8()
            onslaught.run_sdist_phases()
            onslaught.run_phase_unittest()

            onslaught.generate_coverage_reports()


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


class Onslaught (object):
    _TEST_DEPENDENCIES = [
        'twisted >= 14.0',  # For trial
        'coverage == 3.7.1',
        ]

    def __init__(self, target):
        self._log = logging.getLogger(type(self).__name__)
        self._log.info('Onslaught!')

        self._pipcache = self._init_pipcache()

        self._target = target
        targetname = self._target.basename
        self._basedir = Path(
            tempfile.mkdtemp(
                prefix='onslaught.',
                suffix='.' + targetname))
        self._log.info('Preparing results directory: %r', self._basedir)

        logpath = self._basedir('logs', 'main.log')
        self._logdir = logpath.parent
        self._logdir.ensure_is_directory()

        handler = logging.FileHandler(str(logpath))
        handler.setFormatter(
            logging.Formatter(
                fmt='%(asctime)s %(levelname) 5s %(name)s | %(message)s',
                datefmt=DateFormat))

        logging.getLogger().addHandler(handler)

        self._log.debug('Created debug level log in: %r', logpath)
        self._logstep = 0
        self._vbin = self._basedir('venv', 'bin')

    def pushd_workdir(self):
        """chdir to a 'workdir' to keep caller cwd and target dir clean."""
        workdir = self._basedir('workdir')
        workdir.ensure_is_directory()
        return workdir.pushd()

    def prepare_virtualenv(self):
        self._log.debug('Preparing virtualenv.')
        self._run('virtualenv', 'virtualenv', self._basedir('venv'))

    def install_cached_packages(self):
        EXTENSIONS = ['.whl', '.zip', '.tar.bz2', '.tar.gz']
        for p in self._pipcache.listdir():
            for ext in EXTENSIONS:
                if p.basename.endswith(ext):
                    self._install('install-cached.{}'.format(p.basename), p)

    def install_test_utility_packages(self):
        for spec in self._TEST_DEPENDENCIES:
            name = spec.split()[0]
            logname = 'pip-install.{}'.format(name)
            self._install(logname, spec)

    def generate_coverage_reports(self):
        reportdir = self._basedir('coverage')
        self._log.info('Generating coverage reports in: %r', reportdir)
        self._run(
            'coverage-report',
            'coverage', 'html',
            '--directory', reportdir)

    # User test phases:
    def run_phase_flake8(self):
        self._run_phase('flake8', self._vbin('flake8'), self._target)

    def run_sdist_phases(self):
        sdist, sdistlog = self._run_phase_setup_sdist()

        self._run_phase(
            'check-sdist-log',
            'onslaught-check-sdist-log',
            sdistlog)

        self._run_phase(
            'install-sdist',
            self._vbin('pip'),
            '--verbose',
            'install',
            '--download-cache', self._pipcache,
            sdist)

    def _run_phase_setup_sdist(self):
        setup = self._target('setup.py')
        distdir = self._basedir('dist')
        distdir.ensure_is_directory()

        # If you run setup.py sdist from a different directory, it
        # happily creates a tarball missing the source. :-<
        with self._target.pushd():

            sdistlog = self._run_phase(
                'setup-sdist',
                self._vbin('python'),
                setup,
                'sdist',
                '--dist-dir',
                distdir)

        # Additionally, setup.py sdist has rudely pooped an egg-info
        # directly into the source directory, so clean that up:

        [sdist] = distdir.listdir()
        self._log.debug('Generated sdist: %r', sdist)
        return sdist, sdistlog

    def run_phase_unittest(self):
        pkgname = self._determine_packagename()
        self._run_phase(
            'unittests',
            self._vbin('coverage'),
            'run',
            '--branch',
            self._vbin('trial'),
            pkgname)

    # Private below:
    def _init_pipcache(self):
        pipcache = Home('.onslaught', 'pipcache')
        pipcache.ensure_is_directory()
        return pipcache

    def _install(self, logname, spec):
        self._run(
            logname,
            self._vbin('pip'),
            '--verbose',
            'install',
            '--download-cache', self._pipcache,
            spec)

    def _run_phase(self, phase, *args):
        self._log.debug('Test Phase %r running...', phase)
        try:
            logpath = self._run(phase, *args)
        except subprocess.CalledProcessError as e:
            (tag, path) = e.args[-1]
            assert tag == 'logpath', repr(e.args)

            with path.open('r') as f:
                info = f.read()

            self._log.warn('Test Phase %r - FAILED:\n%s', phase, info)
            raise SystemExit(ExitUserFail)
        except Exception as e:
            self._log.error('Test Phase %r - unexpected error: %s', phase, e)
            raise
        else:
            self._log.info('Test Phase %r - passed.', phase)
            return logpath

    def _determine_packagename(self):
        setup = str(self._target('setup.py'))
        py = str(self._vbin('python'))
        return subprocess.check_output([py, setup, '--name']).strip()

    def _run(self, logname, *args):
        args = map(str, args)

        logfile = 'step-{0:02}.{1}.log'.format(self._logstep, logname)
        self._logstep += 1

        self._log.debug('Running: %r; logfile %r', args, logfile)

        logpath = self._logdir(logfile)
        try:
            with logpath.open('w') as f:
                subprocess.check_call(args, stdout=f, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            e.args += (('logpath', logpath),)
            raise
        else:
            return logpath
