import unittest

from tests.coup_action_tests import *

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(CoupActionTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
