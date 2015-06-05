import os
import sys
import errno
import argparse
import logging
import tempfile
import subprocess
import traceback


Description = """\
Run the target python project through a battery of tests.
"""

DateFormat = '%Y-%m-%dT%H:%M:%S%z'

def main(args = sys.argv[1:]):
    opts = parse_args(args)
    log = logging.getLogger('main')
    log.debug('Parsed opts: %r', opts)

    try:
        run_onslaught(opts.TARGET)
    except Exception:
        log.error(traceback.format_exc())
        raise SystemExit(1)


def run_onslaught(target):
    onslaught = Onslaught(target)
    onslaught.chdir_to_workdir()

    onslaught.prepare_virtualenv()
    onslaught.install_cached_packages()
    onslaught.install_test_utility_packages()

    onslaught.run_flake8()

    sdist = onslaught.create_sdist()
    onslaught.install('install-sdist', sdist)
    onslaught.run_unit_tests_with_coverage(sdist)

    raise NotImplementedError(repr(run_onslaught))


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
            fmt='%(asctime)s %(message)s',
            datefmt=DateFormat))

    root.addHandler(handler)


class Onslaught (object):
    _TEST_DEPENDENCIES = [
        'twisted >= 14.0', # For trial
        'coverage == 3.7.1',
        ]

    def __init__(self, target):
        self._log = logging.getLogger(type(self).__name__)

        self._pipcache = self._init_pipcache()

        self._target = os.path.abspath(target)
        targetname = os.path.basename(self._target)
        self._basedir = tempfile.mkdtemp(prefix='onslaught.', suffix='.' + targetname)
        self._log.info('Onslaught results directory: %r', self._basedir)

        logpath = self._base_path('logs', 'main.log')
        self._logdir = os.path.dirname(logpath)

        os.mkdir(self._logdir)
        handler = logging.FileHandler(logpath)
        handler.setFormatter(
            logging.Formatter(
                fmt='%(asctime)s %(levelname) 5s %(name)s | %(message)s',
                datefmt=DateFormat))

        logging.getLogger().addHandler(handler)

        self._log.debug('Created debug level log in: %r', logpath)
        self._logstep = 0
        self._venv = self._base_path('venv')

    def chdir_to_workdir(self):
        """chdir to a 'workdir' so that commands which pollute cwd will put stuff there."""
        workdir = self._base_path('workdir')
        self._log.debug('Create and chdir to: %r', workdir)
        os.mkdir(workdir)
        os.chdir(workdir)

    def prepare_virtualenv(self):
        self._log.info('Preparing virtualenv.')
        self._run('virtualenv', 'virtualenv', self._venv)

    def install_cached_packages(self):
        EXTENSIONS = ['.whl', '.zip', '.tar.bz2', '.tar.gz']
        for n in os.listdir(self._pipcache):
            for ext in EXTENSIONS:
                if n.endswith(ext):
                    path = os.path.join(self._pipcache, n)
                    self.install('install-cached.{}'.format(n), path)

    def install_test_utility_packages(self):
        for spec in self._TEST_DEPENDENCIES:
            name = spec.split()[0]
            logname = 'pip-install.{}'.format(name)
            self.install(logname, spec)

    def install(self, logname, spec):
        self._venv_run(
            logname,
            'pip', '--verbose',
            'install',
            '--download-cache', self._pipcache,
            spec)

    def run_flake8(self):
        self._venv_run('flake8', 'flake8', self._target)

    def create_sdist(self):
        setup = self._target_path('setup.py')
        distdir = self._base_path('dist')
        os.mkdir(distdir)
        self._venv_run(
            'setup-sdist',
            'python',
             setup,
            'sdist',
            '--dist-dir',
            distdir)
        [distname] = os.listdir(distdir)
        sdist = os.path.join(distdir, distname)
        self._log.info('Testing generated sdist: %r', sdist)
        return sdist

    def run_unit_tests_with_coverage(self, sdist):
        pkgname = self._determine_packagename(sdist)
        self._venv_run(
            'unittests',
            'coverage',
            'run',
            '--branch',
            self._venv_bin_path('trial'),
            '--verbose',
            pkgname)

    # Private below:
    def _base_path(self, *parts):
        return os.path.join(self._basedir, *parts)

    def _target_path(self, *parts):
        return os.path.join(self._target, *parts)

    def _venv_bin_path(self, cmd):
        return os.path.join(self._venv, 'bin', cmd)

    def _init_pipcache(self):
        pipcache = os.path.join(os.environ['HOME'], '.onslaught', 'pipcache')
        try:
            os.makedirs(pipcache)
        except os.error as e:
            if e.errno != errno.EEXIST:
                raise
            else:
                # It already existed, no problem:
                return pipcache
        else:
            self._log.debug('Created %r', pipcache)
            return pipcache

    def _determine_packagename(self, sdist):
        setup = self._target_path('setup.py')
        py = self._venv_bin_path('python')
        return subprocess.check_output([py, setup, '--name']).strip()

    def _venv_run(self, logname, cmd, *args):
        self._run(logname, self._venv_bin_path(cmd), *args)

    def _run(self, logname, *args):
        logfile = 'step-{0:02}.{1}.log'.format(self._logstep, logname)
        self._logstep += 1

        logpath = os.path.join(self._logdir, logfile)
        self._log.debug('Running: %r; logfile %r', args, logfile)

        with file(logpath, 'w') as f:
            subprocess.check_call(args, stdout=f, stderr=subprocess.STDOUT)
