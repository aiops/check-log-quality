import unittest
import os

from log_quality.retrieve_logs.retriever_py import LogRetrieverPy
from tests.helpers import *

base_path = os.path.dirname(__file__)
test_file_path = os.path.join(base_path, "test_files")

class TestPyLogRetriver(unittest.TestCase):

    def setUp(self):
        configure_logging()

    def get_test_cases(self):
        expected_py_simple = [
            'log.debug("debug")',
            'log.info("info")',
            'log.warning("warning")',
            'log.warn("warn")',
            'log.error("error")',
            'log.exception("exception")',
            'log.critical("critical")',
            'log.log(log.DEBUG, "debug")',
            'log.log(log.INFO, "info")',
            'log.log(log.WARNING, "warning")',
            'log.log(log.WARN, "warn")',
            'log.log(log.ERROR, "error")',
            'log.log(log.CRITICAL, "critical")'
        ]

        expected_py_hard = [
            'log.debug("debug function", "arg1", "arg2", f())',
            'log.debug("debug nested function", "arg1", "arg2", f(f(f())))',
            'log.debug("debug multi line","arg1", "arg2",a)',
            'log.debug("debug multi line nested function","arg1", "arg2",f(f(f())))',
            'log.debug("debug comment at end","arg1", "arg2",a)',
            'log.debug("debug comment in between",a)'
        ]

        test_cases = {
            os.path.join(test_file_path, "py_simple.py"): expected_py_simple,
            os.path.join(test_file_path, "py_hard.py"): expected_py_hard
        }

        return test_cases

    def read_file_content(self, file_path):
        with open(file_path, "r") as f:
            lines = f.readlines()
        return lines

    def test_retrieve_log_lines(self):
        test_cases = self.get_test_cases()
        plr = LogRetrieverPy()
        
        for file_path, expected in test_cases.items():
            lines = self.read_file_content(file_path)
            result = plr.retrieve_log_lines(lines)
            self.assertListEqual(result, expected)
        

if __name__ == '__main__':
    unittest.main()