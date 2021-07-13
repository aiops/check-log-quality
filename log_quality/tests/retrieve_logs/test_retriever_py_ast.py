import unittest
import os
import logging as log

import astroid

from log_quality.retrieve_logs.retriever_py_ast import LogRetrieverPyAST
from log_quality.tests.helpers import *

base_path = os.path.dirname(__file__)
test_file_path = os.path.join(base_path, "test_files")

class TestLogRetriverPyAST(unittest.TestCase):

    def setUp(self):
        configure_logging()

    def get_default_node(self):
        return astroid.parse(
            """
            import string
            print("Helo world")
            """
        )

    def test_walk_for_crash(self):
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
            self.fail("LogRetrieverPyAST.visit_importfrom() raised an exception unexpectedly!")
        
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
            self.fail("LogRetrieverPyAST._infer_log_level() raised an exception unexpectedly!")
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
            self.fail("LogRetrieverPyAST._clone_node() raised an exception unexpectedly!")
        
        self.assertEqual(node, node2)


    def _get_walk_test_cases(self):
        c1_msg = "Testing basic logging"
        c1 = astroid.parse(
            '''
            import logging

            logging.warn("Warning")
            logging.warning("Warning")
            logging.error("Error")
            logging.exception("Exception")
            '''
        )
        c1_log_message = ["Warning", "Warning", "Error", "Exception"]
        c1_level = ["warning", "warning", "error", "error"]

        c2_msg = "Testing logging alias"
        c2 = astroid.parse(
            '''
            import logging as l

            l.warn("Warning")
            l.warning("Warning")
            '''
        )
        c2_log_message = ["Warning", "Warning"]
        c2_level = ["warning", "warning"]

        c3_msg = "Testing logging attribute import"
        c3 = astroid.parse(
            '''
            from logging import warning

            warning("Warning")
            '''
        )
        c3_log_message = ["Warning"]
        c3_level = ["warning"]

        c4_msg = "Testing logging attribute import alias"
        c4 = astroid.parse(
            '''
            from logging import warning as w

            w("Warning")
            '''
        )
        c4_log_message = ["Warning"]
        c4_level = ["warning"]

        c5_msg = "Testing string concatination in logging statement"
        c5 = astroid.parse(
            '''
            import logging

            logging.warning("Warning " + "W" + " W")
            '''
        )
        c5_log_message = ["Warning W W"]
        c5_level = ["warning"]

        c6_msg = "Testing string concatination in logging statement with indirection (variabel, call)"
        c6 = astroid.parse(
            '''
            import logging

            i_w = input("Enter your name: ")
            def w_f():
                return "W"
            w = "W"
            logging.warning("Warning " + "W" + " W")
            logging.warning("Warning " + w_f() + " " + w)
            logging.warning("Warning " + i_w)
            '''
        )
        c6_log_message = ["Warning W W", "Warning W W", "Warning *"]
        c6_level = ["warning", "warning", "warning"]

        c7_msg = "Testing loging internal string formatting"
        c7 = astroid.parse(
            '''
            import logging

            i_w = input("Enter your name: ")

            logging.warning("Warning %s %d", "W", 5)
            logging.warning("Warning %s %s", "W", i_w)
            logging.warning("%s %s %s", "Warning", "W", "W", exc_info="")
            '''
        )
        c7_log_message = ["Warning W 5", "Warning W *", "Warning W W"]
        c7_level = ["warning", "warning", "warning"]

        c8_msg = "Testing log method call with level as parameter"
        c8 = astroid.parse(
            '''
            import logging

            level = logging.WARNING
            def get_level():
                return logging.WARNING
            logging.log(logging.WARNING, "Warning")
            logging.log(level, "Warning")
            logging.log(get_level(), "Warning")
            logging.log(10, "Debug")
            '''
        )
        c8_log_message = ["Warning", "Warning", "Warning", "Debug"]
        c8_level = ["warning", "warning", "warning", "debug"]

        c9_msg = "Testing string formating with f"
        c9 = astroid.parse(
            '''
            import logging

            i_w = input("Enter your name: ")
            w = "W"

            logging.warning(f"{w}")
            logging.warning(f"Warning {w}")
            logging.warning(f"Warning {i_w}")
            '''
        )
        c9_log_message = ["W", "Warning W", "Warning *"]
        c9_level = ["warning", "warning", "warning"]

        c10_msg = "Testing string formating format method"
        c10 = astroid.parse(
            '''
            import logging

            i_w = input("Enter your name: ")
            w = "W"

            logging.warning("{}".format("Warning"))
            logging.warning("Warning {}".format(w))
            logging.warning("Warning {} {}".format(w, i_w))
            '''
        )
        c10_log_message = ["Warning", "Warning W", "Warning W *"]
        c10_level = ["warning", "warning", "warning"]

        c11_msg = "Testing string formating with %"
        c11 = astroid.parse(
            '''
            import logging

            i_w = input("Enter your name: ")
            w = "W"

            logging.warning("%s" % ("Warning"))
            logging.warning("Warning %s %d" % (w, 5))
            logging.warning("Warning %s %%" % (w, i_w))
            '''
        )
        c11_log_message = ["Warning", "Warning W 5", "Warning W *"]
        c11_level = ["warning", "warning", "warning"]

        c12_msg = "Testing get logger method call"
        c12 = astroid.parse(
            '''
            import logging

            a2 = logging.getLogger('aa')

            a2.debug('A debug message')
            a2.warn('A warning message')
            a4.info('This should not be parsed')
            '''
        )
        c12_log_message = ["A debug message", "A warning message"]
        c12_level = ["debug", "warning"]

        test_cases = {
            c1: (c1_log_message, c1_level, c1_msg),
            c2: (c2_log_message, c2_level, c2_msg),
            c3: (c3_log_message, c3_level, c3_msg),
            c4: (c4_log_message, c4_level, c4_msg),
            c5: (c5_log_message, c5_level, c5_msg),
            c6: (c6_log_message, c6_level, c6_msg),
            c7: (c7_log_message, c7_level, c7_msg),
            c8: (c8_log_message, c8_level, c8_msg),
            c9: (c9_log_message, c9_level, c9_msg),
            c10: (c10_log_message, c10_level, c10_msg),
            c11: (c11_log_message, c11_level, c11_msg),
            c12: (c12_log_message, c12_level, c12_msg)
        }
        return test_cases

    def test_walk(self):
        test_cases = self._get_walk_test_cases()
        for node, (expct_msg, expct_level, msg) in test_cases.items():
            lr = LogRetrieverPyAST()
            with self.subTest(msg=msg):
                try:
                    lr.walk(node)
                except Exception as e:
                    log.exception(e)
                    self.fail("LogRetrieverPyAST.walk() raised an exception unexpectedly!")
                self.assertListEqual(lr.log_messages, expct_msg)
                self.assertListEqual(lr.log_levels, expct_level)
        

if __name__ == '__main__':
    unittest.main()