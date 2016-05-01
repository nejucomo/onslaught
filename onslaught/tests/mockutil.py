from pprint import pformat
import unittest


class MockingTestCase (unittest.TestCase):
    def assert_calls_equal(self, mockobj, expectedcalls):
        mockcalls = mockobj._mock_mock_calls
        self.assertEqual(
            len(mockcalls), len(expectedcalls),
            'len(%s) == %r != len(%s) == %r' % (
                pformat(mockcalls), len(mockcalls),
                pformat(expectedcalls), len(expectedcalls)))

        loopelems = enumerate(zip(mockcalls, expectedcalls))
        for i, (mockcall, expectedcall) in loopelems:
            try:
                self.assertEqual(
                    mockcall, expectedcall,
                    'Arg {:d}:\n{}\n  !=\n{}'.format(
                        i,
                        pformat(mockcall),
                        pformat(expectedcall)))
            except AssertionError, e:
                raise
            except Exception, e:
                e.args += (
                    'Internal unittesting exception; vars:',
                    i,
                    mockcall,
                    expectedcall)
                raise
