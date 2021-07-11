import re
import logging as log

from python.utils import *
from python.retriever import LogRetriever

log.basicConfig(level=log.DEBUG)

class LogRetrieverPy(LogRetriever):
    log_level_aliases = {
        "debug": ["debug"],
        "info": ["info"],
        "warning": ["warning", "warn"],
        "error": ["error", "exception"],
        "critical": ["critical"],
        "log": ["log"]
    }
    placeholder = "#LOGID#"
    reg_log_start = r"^.*({})\(.*$".format(placeholder)
    reg_comment = r"\s*#.*\s*$"

    def __init__(self, multiline_max=5):
        super().__init__(multiline_max)

    def get_comment_regex(self):
        return self.reg_comment

    def retrieve_log_lines(self, lines):
        regex_elements = []
        for key in self.log_level_aliases:
            for value_element in self.log_level_aliases[key]:
                regex_elements.append(self.reg_log_start.replace(self.placeholder, value_element))
        regex_result = "|".join(regex_elements)
        return self._retrieve_log_lines(lines, regex_result)

