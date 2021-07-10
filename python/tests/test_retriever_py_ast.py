import unittest
import os
import logging as log

import astroid

from python.retriever_py_ast import LogRetrieverPyAST
from python.tests.helpers import *

base_path = os.path.dirname(__file__)
test_file_path = os.path.join(base_path, "test_files")

class TestLogRetriverPyAST(unittest.TestCase):

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

    def get_default_node(self):
        return astroid.parse(
            """
            import string
            print("Helo world")
            """
        )

    def test_walk(self):
        node = self.get_default_node()
        lr = LogRetrieverPyAST()
        try:
            lr.walk(node)
        except Exception:
            self.fail("LogRetrieverPyAST.walk() raised an exception unexpectedly!")

    def test_visit(self):
        node = self.get_default_node()
        lr = LogRetrieverPyAST()
        try:
            lr.visit(node)
        except Exception:
            self.fail("LogRetrieverPyAST.visit() raised an exception unexpectedly!") 

    def test_visit_import(self):
        node = astroid.parse(
            """
            import logging
            import logging as log
            import logging as banana
            """
        )
        expected = sorted(list({"logging", "log", "banana"}))
        lr = LogRetrieverPyAST()
        try:
            for n in node.body:
                lr.visit_import(n)
        except Exception:
            self.fail("LogRetrieverPyAST.visit_import() raised an exception unexpectedly!")
        self.assertListEqual(sorted(list(lr._logging_module_aliases)), expected)

    def test_visit_importfrom(self):
        node = astroid.parse(
            """
            from logging import info
            from logging import log
            from logging import warning as cucumber
            from logging import log as l
            """
        )
        lr = LogRetrieverPyAST()
        expected_lma = sorted(list(lr.log_method_aliases) + ["l"])
        expected_lla = sorted(list(lr.log_level_aliases) + ["cucumber"])
        try:
            for n in node.body:
                lr.visit_importfrom(n)
        except Exception:
            self.fail("LogRetrieverPyAST.visit_import() raised an exception unexpectedly!")
        
        lma = sorted(list(lr.log_method_aliases)) 
        self.assertListEqual(lma, expected_lma)

        lla = sorted(list(lr.log_level_aliases))
        self.assertListEqual(lla, expected_lla)


    def test__infer_log_level(self):
        node = astroid.parse(
            """
            logging.log(logging.DEBUG, "Test1")
            logging.log(logging.WARNING, "Test2")
            logging.log(10, "Test3")
            """
        )
        expected = ["debug", "warning", "debug"]
        lr = LogRetrieverPyAST()
        levels = []
        try:
            for n in node.body:
                print(n.value.repr_tree())
                levels.append(lr._infer_log_level(n.value.args[0]))
        except Exception as e:
            log.exception(e)
            self.fail("LogRetrieverPyAST.visit_import() raised an exception unexpectedly!")
        self.assertListEqual(levels, expected)

    def test__infer_log_level(self):
        node = astroid.parse(
            """
            logging.log(logging.DEBUG, "Test1")
            logging.log(logging.WARNING, "Test2")
            logging.log(10, "Test3")
            """
        )
        expected = ["debug", "warning", "debug"]
        lr = LogRetrieverPyAST()
        levels = []
        try:
            for n in node.body:
                levels.append(lr._infer_log_level(n.value.args[0]))
        except Exception as e:
            log.exception(e)
            self.fail("LogRetrieverPyAST.visit_import() raised an exception unexpectedly!")
        self.assertListEqual(levels, expected)

    def test__clone_node(self):
        node1 = astroid.extract_node(
            """
            print("Hello world")
            """
        )
        node2 = astroid.extract_node(
            """
            # Comment
            print("Hello world")
            """
        )
        lr = LogRetrieverPyAST()
        try:
            node = lr._clone_node(node1, node2)
        except Exception as e:
            log.exception(e)
            self.fail("LogRetrieverPyAST.visit_import() raised an exception unexpectedly!")
        
        self.assertEqual(node, node2)

    def test__parse_joinedstr(self):
        node1 = astroid.extract_node(
            """
            
            """
        )
        node2 = astroid.extract_node(
            """
            # Comment
            print("Hello world")
            """
        )
        lr = LogRetrieverPyAST()
        try:
            node = lr._clone_node(node1, node2)
        except Exception as e:
            log.exception(e)
            self.fail("LogRetrieverPyAST.visit_import() raised an exception unexpectedly!")
        
        self.assertEqual(node, node2)


if __name__ == '__main__':
    unittest.main()