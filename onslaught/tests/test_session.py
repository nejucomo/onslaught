import sys
from mock import call, patch

from onslaught.session import Session
from onslaught.path import Path
from onslaught.tests.mockutil import MockingTestCase


class SessionTestBase (MockingTestCase):
    def setUp(self):
        self.s = Session()

        p = patch('onslaught.io.provider')
        self.addCleanup(p.stop)
        self.m_iop = p.start()

        # Patch-over mocks of these "functional, non-IO" path
        # manipulations with fakes that track their transformations:
        self.m_iop.abspath = lambda p: ('abs', p)
        self.m_iop.dirname = lambda p: ('dirname', p)
        self.m_iop.isabs = lambda _: True
        self.m_iop.join = lambda *a: ('join', a)

        self.s.initialize('targetfoo', 'resultsbar')

    def assert_iop_calls(self, *calls):
        self.assert_calls_equal(self.m_iop, calls)


class SessionInitializeTest (SessionTestBase):
    def test_initialize(self):
        self.assert_iop_calls(
            call.gather_output(
                sys.executable,
                ('join', (('abs', 'targetfoo'), 'setup.py')),
                '--name'),
            call.rmtree(('abs', 'resultsbar')),
            call.ensure_is_directory(('abs', 'resultsbar')),
            call.copytree(
                ('abs', 'targetfoo'),
                ('join', (('abs', 'resultsbar'), 'targetsrc'))),
            call.ensure_is_directory(
                ('dirname',
                 ('join', (('abs', 'resultsbar'), 'logs', 'main.log')))),
            call.open(
                ('join',
                 (('abs', 'resultsbar'),
                  'logs',
                  'main.log')),
                'a'))


class SessionTests (SessionTestBase):
    def setUp(self):
        SessionTestBase.setUp(self)
        self.m_iop.reset_mock()

    @patch('onslaught.session.Session._run')
    @patch('onslaught.session.Session._simplify_coverage_paths')
    @patch('onslaught.session.Session._display_coverage_to_stdout')
    def test_generate_coverage_reports(self, m_S_dcts, m_S_scp, m_S_run):
        self.s.generate_coverage_reports()

        self.assert_iop_calls()  # There is no unintercepted IO.

        self.assert_calls_equal(
            m_S_run,
            [call(
                'coverage-report-html',
                Path(('join',
                      (('join', (('abs', 'resultsbar'), 'venv', 'bin')),
                       'coverage'))),
                'html',
                '--directory',
                Path(('join', (('abs', 'resultsbar'), 'coverage.orig'))))])

        self.assert_calls_equal(
            m_S_scp,
            [call(
                Path(('join', (('abs', 'resultsbar'), 'coverage.orig'))),
                Path(('join', (('abs', 'resultsbar'), 'coverage'))))])

        self.assert_calls_equal(
            m_S_dcts,
            [call()])

    @patch('onslaught.session.Session._run')
    @patch('onslaught.session.Session._replace_venv_paths')
    def test__display_coverage_to_stdout(self, m_S_rvp, m_S_run):
        self.s._display_coverage_to_stdout()

        self.assert_iop_calls()  # There is no unintercepted IO.

        self.assert_calls_equal(
            m_S_run,
            [call(
                'coverage-report-stdout',
                Path(('join',
                      (('join', (('abs', 'resultsbar'), 'venv', 'bin')),
                       'coverage'))),
                'report'),
             call().read()])

        self.assert_calls_equal(
            m_S_rvp,
            [call(m_S_run().read(), '...')])
