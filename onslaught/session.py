import sys
import logging
import subprocess
from onslaught.consts import DateFormat, ExitUserFail
from onslaught.path import Path, Home


class Session (object):
    _TEST_DEPENDENCIES = [
        'twisted >= 14.0',  # For trial
        'coverage == 3.7.1',
        ]

    def __init__(self, target, results):
        self._realtarget = Path(target)

        self._log = logging.getLogger(type(self).__name__)
        self._pkgname = self._init_packagename()
        self._resdir = self._init_results_dir(results)
        self._target = self._init_target()
        self._logdir = self._init_logdir()

        self._logstep = 0
        self._vbin = self._resdir('venv', 'bin')

    def pushd_workdir(self):
        """chdir to a 'workdir' to keep caller cwd and target dir clean."""
        workdir = self._resdir('workdir')
        workdir.ensure_is_directory()
        return workdir.pushd()

    def prepare_virtualenv(self):
        self._log.debug('Preparing virtualenv.')
        self._run('virtualenv', 'virtualenv', self._resdir('venv'))

    def install_test_utility_packages(self):
        for spec in self._TEST_DEPENDENCIES:
            name = spec.split()[0]
            logname = 'pip-install.{}'.format(name)
            self._install(logname, spec)

    def generate_coverage_reports(self):
        reportdir = self._resdir('coverage')
        self._log.info('Generating HTML coverage reports in: %r', reportdir)
        self._run(
            'coverage-report-html',
            'coverage', 'html',
            '--directory', reportdir)
        logpath = self._run(
            'coverage-report-stdout',
            'coverage', 'report')
        with logpath.open('r') as f:
            self._log.info('Coverage:\n%s', f.read())

    # User test phases:
    def run_phase_flake8(self):
        self._run_phase('flake8', 'flake8', self._realtarget)

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
            sdist)

    def _run_phase_setup_sdist(self):
        setup = self._target('setup.py')
        distdir = self._resdir('dist')
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
        self._run_phase(
            'unittests',
            self._vbin('coverage'),
            'run',
            '--branch',
            '--source', self._pkgname,
            self._vbin('trial'),
            self._pkgname)

    # Private below:
    def _init_packagename(self):
        setup = str(self._realtarget('setup.py'))
        py = sys.executable
        return subprocess.check_output([py, setup, '--name']).strip()

    def _init_results_dir(self, results):
        if results is None:
            results = Home('.onslaught', 'results', self._pkgname)
            logf = self._log.info
        else:
            results = Path(results)
            logf = self._log.debug

        logf('Preparing results directory: %r', results)

        results.rmtree()
        results.ensure_is_directory()
        return results

    def _init_target(self):
        target = self._resdir('targetsrc')
        self._realtarget.copytree(target)
        return target

    def _init_logdir(self):
        logpath = self._resdir('logs', 'main.log')
        logdir = logpath.parent
        logdir.ensure_is_directory()

        handler = logging.FileHandler(str(logpath))
        handler.setFormatter(
            logging.Formatter(
                fmt='%(asctime)s %(levelname) 5s %(name)s | %(message)s',
                datefmt=DateFormat))

        logging.getLogger().addHandler(handler)

        self._log.debug('Created debug level log in: %r', logpath)
        return logdir

    def _install(self, logname, spec):
        self._run(
            logname,
            self._vbin('pip'),
            '--verbose',
            'install',
            spec)

    def _run_phase(self, phase, *args):
        logpref = 'Test Phase {!r:18}'.format(phase)
        self._log.debug('%s running...', logpref)
        try:
            logpath = self._run('phase.'+phase, *args)
        except subprocess.CalledProcessError as e:
            (tag, path) = e.args[-1]
            assert tag == 'logpath', repr(e.args)

            with path.open('r') as f:
                info = f.read()

            self._log.warn('%s - FAILED:\n%s', logpref, info)
            raise SystemExit(ExitUserFail)
        except Exception as e:
            self._log.error('%s - unexpected error: %s', logpref, e)
            raise
        else:
            self._log.info('%s - passed.', logpref)
            return logpath

    def _run(self, logname, *args):
        args = map(str, args)

        logfile = '{0:02}.{1}.log'.format(self._logstep, logname)
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
