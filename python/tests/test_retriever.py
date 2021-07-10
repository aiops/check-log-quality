import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
#sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))
from retriever import LogRetriever
from tests.helpers import *

base_path = os.path.dirname(__file__)
test_file_path = os.path.join(base_path, "test_files")

class LogRetriverTest(LogRetriever):        
    def get_comment_regex(self):
        return r"\s*#.*\s*$"

class TestLogRetriver(unittest.TestCase):

    def setUp(self):
        configure_logging()

    def test_count_braces(self):
        t1 = "((()))"
        t2 = "()()()"
        t3 = "((())))"
        t4 = "((((()))"
        lr = LogRetriever()
        self.assertEqual(lr.count_braces(t1), 0)
        self.assertEqual(lr.count_braces(t2), 0)
        self.assertEqual(lr.count_braces(t3), -1)
        self.assertEqual(lr.count_braces(t4), 2)

    def test_strip_line_for_complete_check(self):
        t1 = "log(\"this should be stripped\")"
        t2 = "log(\"this should be stripped\", \"and this\")"
        t3 = "log(\"this should be stripped\", \"and this\", but not this)"
        t4 = "log(\'this should be stripped\', \"and this\", but not this)"
        t5 = "# log(\'everything will be gone\') really"
        t6 = " log(\'this will be gone\') #this as well "

        lr = LogRetriverTest()
        self.assertEqual(lr.strip_line_for_complete_check(t1), "log()")
        self.assertEqual(lr.strip_line_for_complete_check(t2), "log(, )")
        self.assertEqual(lr.strip_line_for_complete_check(t3), "log(, , but not this)")
        self.assertEqual(lr.strip_line_for_complete_check(t4), "log(, , but not this)")
        self.assertEqual(lr.strip_line_for_complete_check(t5), "")
        self.assertEqual(lr.strip_line_for_complete_check(t6), "log()")

    def test_check_log_completeness(self):
        #True
        t1 = 'log.error("adsffsdf")'
        t2 = 'log.error((("adsffsdf")))'
        t3 = 'log.error("adsffsdf()") asdf'
        t4 = 'log.error("adsffsdf"()()())'
        #False
        t5 = 'log.error("adsffsdf"'
        t6 = 'log.error("adsffsdf"()('
        t7 = 'log.error(("adsffsdf"(()))'

        lr = LogRetriverTest()
        self.assertTrue(lr.check_log_completeness(t1))
        self.assertTrue(lr.check_log_completeness(t2))
        self.assertTrue(lr.check_log_completeness(t3))
        self.assertTrue(lr.check_log_completeness(t4))

        self.assertFalse(lr.check_log_completeness(t5))
        self.assertFalse(lr.check_log_completeness(t6))
        self.assertFalse(lr.check_log_completeness(t7))

    def test_get_log_line(self):
        t1 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()(', '))' ]
        t2 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()(', '))', 'asd', 'asssss' ]
        t3 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()(', ')', 'pp', 'asdas', '"asd"', 'asd)']
        t4 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()(']

        lr1 = LogRetriverTest(multiline_max=5)
        self.assertEqual(lr1.get_log_line(t1, 0), 'log.error("adsffsdf","asdfsdf asdf (),"()())')
        self.assertEqual(lr1.get_log_line(t2, 0), 'log.error("adsffsdf","asdfsdf asdf (),"()())')

        with self.assertRaises(Exception) as c:
            lr1.get_log_line(t3, 0)
            self.assertTrue('Maximum number for multiline logs' in context.exception)
        with self.assertRaises(Exception) as c:
            lr1.get_log_line(t4, 0)
            self.assertTrue('Log line incomplete but EOF reached' in context.exception)

        lr2 = LogRetriverTest(multiline_max=15)
        self.assertEqual(lr2.get_log_line(t3, 0), 'log.error("adsffsdf","asdfsdf asdf (),"()()ppasdas"asd"asd)')

    def test_get_log_lines(self):
        t1 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()(', '))' ]
        t2 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()(', '))', 'asd', 'asssss' ]
        t3 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()(', '))', 'pp', 'asdas', '"asd"', 'asd']
        t4 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()())']
        t = t1+t2+t3+t4

        expected = [
            'log.error("adsffsdf","asdfsdf asdf (),"()())',
            'log.error("adsffsdf","asdfsdf asdf (),"()())',
            'log.error("adsffsdf","asdfsdf asdf (),"()())',
            'log.error("adsffsdf","asdfsdf asdf (),"()())'
        ]

        lr = LogRetriverTest(multiline_max=5)
        result = lr.get_log_lines(t, [0, 4, 10, 18])
        self.assertListEqual(result, expected)

    def test_retrieve_log_lines(self):
        reg_log_start = r"^.*(?P<LogID>error)\(.*$"
        t1 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()(', '))' ]
        t2 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()(', '))', 'asd', 'asssss' ]
        t3 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()(', '))', 'pp', 'asdas', '"asd"', 'asd']
        t4 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()())']
        t = t1+t2+t3+t4

        expected = [
            'log.error("adsffsdf","asdfsdf asdf (),"()())',
            'log.error("adsffsdf","asdfsdf asdf (),"()())',
            'log.error("adsffsdf","asdfsdf asdf (),"()())',
            'log.error("adsffsdf","asdfsdf asdf (),"()())'
        ]

        lr = LogRetriverTest(multiline_max=5)
        result = lr._retrieve_log_lines(t, reg_log_start)
        self.assertListEqual(result, expected)
    

if __name__ == '__main__':
    unittest.main()