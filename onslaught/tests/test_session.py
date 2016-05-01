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
        m_iop.join = lambda *a: ('join', a)

        self.s.initialize('targetfoo', 'resultsbar')

        self.assert_calls_equal(
            m_iop,
            [call.gather_output(
                sys.executable,
                ('abs', ('join', (('abs', 'targetfoo'), 'setup.py'))),
                '--name'),
             call.rmtree(('abs', 'resultsbar')),
             call.ensure_is_directory(('abs', 'resultsbar')),
             call.copytree(
                 ('abs', 'targetfoo'),
                 ('abs', ('join', (('abs', 'resultsbar'), 'targetsrc')))),
             call.ensure_is_directory(
                 ('abs',
                  ('dirname',
                   ('abs',
                    ('join', (('abs', 'resultsbar'), 'logs', 'main.log')))))),
             call.open(
                 ('abs',
                  ('join',
                   (('abs', 'resultsbar'),
                    'logs',
                    'main.log'))),
                 'a')])
