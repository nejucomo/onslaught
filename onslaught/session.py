import re
import logging
from sys import executable as python_executable
from onslaught.consts import DateFormat, ExitUserFail
from onslaught import io
from onslaught.path import Path


class Session (object):
    _TEST_DEPENDENCIES = [
        'twisted >= 14.0',  # For trial
        'coverage == 4.0.3',
    ]

    def __init__(self):
        self._log = logging.getLogger(type(self).__name__)

    def initialize(self, target, resultstmpl):
        """Perform IO necessary to setup onslaught results directory."""
        self._realtarget = Path.from_relative(target)

        self._pkgname = self._init_packagename()

        results = Path.from_relative(
            resultstmpl.format(package=self._pkgname))

        self._resdir = self._init_results_dir(results)
        self._target = self._init_target()
        self._logdir = self._init_logdir()

        self._logstep = 0
        self._vbin = self._resdir('venv', 'bin')
        return self

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
        nicerepdir = self._resdir('coverage')
        self._log.info('Generating HTML coverage reports in: %r', nicerepdir)

        rawrepdir = self._resdir('coverage.orig')
        self._run(
            'coverage-report-html',
            self._vbin('coverage'),
            'html',
            '--directory', rawrepdir)

        self._log.debug(
            'Editing coverage report paths %r -> %r',
            rawrepdir,
            nicerepdir)

        self._simplify_coverage_paths(rawrepdir, nicerepdir)
        self._display_coverage_to_stdout()

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

        def filterlog(rawlogpath):
            logpath = rawlogpath.parent(rawlogpath.basename + '.patched')
            logpath.write(
                self._replace_venv_paths(
                    rawlogpath.read(),
                    self._realtarget.pathstr))
            return logpath

        self._run_phase(
            'unittests',
            self._vbin('coverage'),
            'run',
            '--branch',
            '--source', self._pkgname,
            self._vbin('trial'),
            self._pkgname,
            filterlog=filterlog,
        )

    # Private below:
    def _init_packagename(self):
        setup = self._realtarget('setup.py').pathstr
        return io.provider.gather_output(
            python_executable,
            setup,
            '--name')

    def _init_results_dir(self, results):
        self._log.info('Preparing results directory: %r', results)
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

        handler = logging.StreamHandler(logpath.open('a'))
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

    def _run_phase(self, phase, *args, **kw):
        logpref = 'Test Phase {!r:18}'.format(phase)
        self._log.debug('%s running...', logpref)
        try:
            logpath = self._run('phase.'+phase, *args, **kw)
        except io.CalledProcessError as e:
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

    def _run(self, logname, *args, **kw):
        filterlog = kw.pop('filterlog', lambda lp: lp)
        assert len(kw) == 0, 'Unexpected keyword args: {!r}'.format(kw)

        args = [a.pathstr if isinstance(a, Path) else a for a in args]

        logfile = '{0:02}.{1}.log'.format(self._logstep, logname)
        self._logstep += 1

        self._log.debug('Running: %r; logfile %r', args, logfile)

        rawlogpath = self._logdir(logfile)
        try:
            with rawlogpath.open('w') as f:
                io.provider.check_call(args, stdout=f, stderr=io.STDOUT)
        except io.CalledProcessError as e:
            e.args += (('logpath', filterlog(rawlogpath)),)
            raise
        else:
            return filterlog(rawlogpath)

    def _simplify_coverage_paths(self, rawrepdir, nicerepdir):
        nicerepdir.ensure_is_directory()

        for srcpath in rawrepdir.walk_files():
            dstpath = nicerepdir(srcpath.basename)
            if srcpath.basename.endswith('.html'):
                self._log.debug(
                    'Tidying paths from %r -> %r',
                    srcpath,
                    dstpath,
                )

                src = srcpath.read()
                dst = self._replace_venv_paths(src, '&#x2026;')
                dstpath.write(dst)

            elif srcpath.isfile:
                srcpath.copyfile(dstpath)
            else:
                srcpath.copytree(dstpath)

    def _display_coverage_to_stdout(self):
        logpath = self._run(
            'coverage-report-stdout',
            self._vbin('coverage'),
            'report')

        self._log.info(
            'Coverage:\n%s',
            self._replace_venv_paths(logpath.read(), '...'))

    def _replace_venv_paths(self, src, repl):
        rgx = re.compile(
            r'/[/a-z0-9._-]+/site-packages/{}'.format(
                re.escape(self._pkgname),
            ),
        )
        realrepl = '{}/{}'.format(repl, self._pkgname)
        return rgx.subn(realrepl, src)[0]
