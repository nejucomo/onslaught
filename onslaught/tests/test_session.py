import sys
from mock import call, patch

from onslaught.session import Session
from onslaught.tests.mockutil import MockingTestCase


class SessionTests (MockingTestCase):
    def setUp(self):
        self.s = Session()

    @patch('onslaught.io.provider')
    def test_initialize(self, m_iop):
        # Patch-over mocks of these "functional, non-IO" path
        # manipulations with fakes that track their transformations:
        m_iop.abspath = lambda p: ('abs', p)
        m_iop.dirname = lambda p: ('dirname', p)
        m_iop.isabs = lambda _: True
        m_iop.join = lambda *a: ('join', a)

        self.s.initialize('targetfoo', 'resultsbar')

        self.assert_calls_equal(
            m_iop,
            [call.gather_output(
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
                 'a')])
