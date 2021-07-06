import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
#sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))
from retrieve_log_lines import *
from tests.helpers import *

base_path = os.path.dirname(__file__)
test_file_path = os.path.join(base_path, "test_files")

class TestRetrieveLogLines(unittest.TestCase):

    def get_test_files(self):
        test_files = [f for f in os.listdir(test_file_path) \
                      if os.path.isfile(os.path.join(test_file_path, f))]
        return test_files

    def setUp(self):
        configure_logging()

    def test_parser(self):
        files = self.get_test_files()
        for f in files:
            print("Test run for {}".format(f))


if __name__ == '__main__':
    unittest.main()