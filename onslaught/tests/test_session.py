import sys
from mock import MagicMock, call, patch

from onslaught.session import Session
from onslaught.tests.mockutil import MockingTestCase


class SessionTests (MockingTestCase):
    def setUp(self):
        self.s = Session()

    @patch('subprocess.check_output')
    def test__init_packagename(self, m_check_output):
        m_realtarget = MagicMock()
        self.s._realtarget = m_realtarget

        self.s._init_packagename()

        self.assert_calls_equal(
            m_realtarget,
            [call('setup.py')])

        self.assert_calls_equal(
            m_check_output,
            [call([
                sys.executable,
                m_realtarget.return_value.pathstr,
                '--name']),
             call().strip()])
