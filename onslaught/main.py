import os
import sys
import errno
import shutil
import pprint
import logging
import argparse
import tempfile
import traceback
import subprocess


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
        run_onslaught(opts.TARGET)
    except Exception:
        log.error(traceback.format_exc())
        raise SystemExit(ExitUnknownError)


def run_onslaught(target):
    with OnslaughtSession(target) as onslaught:
        onslaught.chdir_to_workdir()
        onslaught.prepare_virtualenv()
        onslaught.install_cached_packages()
        onslaught.install_test_utility_packages()

        onslaught.run_phase_flake8()

        sdist = onslaught.run_sdist_setup_phases()
        onslaught.run_phase_install_sdist(sdist)
        onslaught.run_phase_unittest(sdist)

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


class OnslaughtSession (object):
    def __init__(self, target):
        self._target = os.path.abspath(target)

    def __enter__(self):
        self._manifest = set(self._create_manifest())
        return Onslaught(self._target)

    def __exit__(self, *a):
        log = logging.getLogger('cleanup')
        log.debug(
            'Cleaning up anything created in %r during session; manifest:\n%s',
            self._target,
            pprint.pformat(self._manifest),
        )

        for p in self._create_manifest():
            log.debug('Should we remove %r?', p)
            if p not in self._manifest and os.path.exists(p):
                log.debug('Removing: %r', p)
                shutil.rmtree(p)

    def _create_manifest(self):
        for bd, ds, fs in os.walk(self._target):
            for n in ds + fs:
                yield os.path.join(bd, n)


class Onslaught (object):
    _TEST_DEPENDENCIES = [
        'twisted >= 14.0',  # For trial
        'coverage == 3.7.1',
        ]

    def __init__(self, target):
        self._log = logging.getLogger(type(self).__name__)

        self._pipcache = self._init_pipcache()

        self._target = os.path.abspath(target)
        targetname = os.path.basename(self._target)
        self._basedir = tempfile.mkdtemp(
            prefix='onslaught.',
            suffix='.' + targetname)
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
        """chdir to a 'workdir' to keep caller cwd and target dir clean."""
        workdir = self._base_path('workdir')
        self._log.debug('Create and chdir to: %r', workdir)
        os.mkdir(workdir)
        os.chdir(workdir)

    def prepare_virtualenv(self):
        self._log.debug('Preparing virtualenv.')
        self._run('virtualenv', 'virtualenv', self._venv)

    def install_cached_packages(self):
        EXTENSIONS = ['.whl', '.zip', '.tar.bz2', '.tar.gz']
        for n in os.listdir(self._pipcache):
            for ext in EXTENSIONS:
                if n.endswith(ext):
                    path = os.path.join(self._pipcache, n)
                    self._install('install-cached.{}'.format(n), path)

    def install_test_utility_packages(self):
        for spec in self._TEST_DEPENDENCIES:
            name = spec.split()[0]
            logname = 'pip-install.{}'.format(name)
            self._install(logname, spec)

    # User test phases:
    def run_phase_flake8(self):
        self._run_phase('flake8', self._venv_bin('flake8'), self._target)

    def run_sdist_setup_phases(self):
        setup = self._target_path('setup.py')
        distdir = self._base_path('dist')
        os.mkdir(distdir)

        # If you run setup.py sdist from a different directory, it
        # happily creates a tarball missing the source. :-<
        with pushdir(self._target):

            sdistlog = self._run_phase(
                'setup-sdist',
                self._venv_bin('python'),
                setup,
                'sdist',
                '--dist-dir',
                distdir)

        # Additionally, setup.py sdist has rudely pooped an egg-info
        # directly into the source directory, so clean that up:

        [distname] = os.listdir(distdir)
        sdist = os.path.join(distdir, distname)
        self._log.debug('Testing generated sdist: %r', sdist)
        self._run_phase(
            'check-sdist-log',
            'onslaught-check-sdist-log',
            sdistlog)
        return sdist

    def run_phase_install_sdist(self, sdist):
        self._run_phase(
            'install-sdist',
            self._venv_bin('pip'),
            '--verbose',
            'install',
            '--download-cache', self._pipcache,
            sdist)

    def run_phase_unittest(self, sdist):
        pkgname = self._determine_packagename(sdist)
        self._run_phase(
            'unittests',
            self._venv_bin('coverage'),
            'run',
            '--branch',
            self._venv_bin('trial'),
            pkgname)

    # Private below:
    def _base_path(self, *parts):
        return os.path.join(self._basedir, *parts)

    def _target_path(self, *parts):
        return os.path.join(self._target, *parts)

    def _venv_bin(self, cmd):
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

    def _install(self, logname, spec):
        self._run(
            logname,
            self._venv_bin('pip'),
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

            with file(path, 'r') as f:
                info = f.read()

            self._log.warn('Test Phase %r - FAILED:\n%s', phase, info)
            raise SystemExit(ExitUserFail)
        except Exception as e:
            self._log.error('Test Phase %r - unexpected error: %s', phase, e)
            raise
        else:
            self._log.info('Test Phase %r - passed.', phase)
            return logpath

    def _determine_packagename(self, sdist):
        setup = self._target_path('setup.py')
        py = self._venv_bin('python')
        return subprocess.check_output([py, setup, '--name']).strip()

    def _run(self, logname, *args):
        logfile = 'step-{0:02}.{1}.log'.format(self._logstep, logname)
        self._logstep += 1

        logpath = os.path.join(self._logdir, logfile)
        self._log.debug('Running: %r; logfile %r', args, logfile)

        try:
            with file(logpath, 'w') as f:
                subprocess.check_call(args, stdout=f, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            e.args += (('logpath', logpath),)
            raise
        else:
            return logpath


class pushdir (object):
    def __init__(self, d):
        self._d = d
        self._old = os.getcwd()

    def __enter__(self):
        os.chdir(self._d)

    def __exit__(self, *a):
        os.chdir(self._old)
