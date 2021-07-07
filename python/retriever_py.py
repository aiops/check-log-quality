import sys
import os
import re
import pandas as pd
import logging as log

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import *
from retriever import LogRetriver

log.basicConfig(level=log.DEBUG)

class PyLogRetriver(LogRetriver):
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
        print(regex_result)
        return self._retrieve_log_lines(lines, regex_result)

    def ____parse_file(self, file_path, log_type, pattern=None):
        if not pattern:
            pattern = r"[lL][oO][gG]\w*_?\w*\."
        pattern += log_type + r'\('
        matches = []
        matches_clean = []
        open_braces = 0
        try:
            with open(file_path, "r") as f:
                substr = ""
                for idx, line in enumerate(f.readlines()):
                    print("-------" * 10)
                    # print(line)
                    if open_braces > 0:
                        substr += line.strip()
                        open_braces = self.count_braces(substr)
                        # open_braces += self.count_braces(substr) ##### Old
                        # result = re.search(pattern, line)
                        # if result:
                        #     substr = line[result.start():].strip()
                        #     open_braces = self.count_braces(substr)
                    else:
                        result = re.search(pattern, line)
                        print(result)
                        if result:
                            substr = line[result.start():].strip()
                            open_braces = self.count_braces(substr)
                        else:
                            open_braces = 0
                            # substr = ""
                    print("The substr is {}   wrwa \n".format(substr))
                    if open_braces == 0 and result:
                        matches.append((idx, log_type, file_path, substr))
                        matches_clean.append((str(idx) + "," + str(log_type)+ "," +  file_path+ "," +  self._process(substr[re.search(pattern, substr).end():])))
        except Exception as e:
            print("IT WENT SOUTH")
            pass
        return matches, "\n".join([x for x in matches_clean])

    def extract_log_messages(self):
        logs_ = []
        logs_clean = []
        for log_type in ['error', "info", "trace"]:
            l, l_clean = self.parse_file(self.input_path, log_type)
            logs_.append(l)
            logs_clean.append(l_clean)
        return [x for x in logs_clean if x != []]

    def _process(self, log_msg):
        def replace_placeholders(x):
            patterns_alpha = ["%s"]  # [STR]
            patterns_num = ["%d", "%f", "%.2f", "%i"]  # \[NUM]
            patterns = ["{}", r"\{.*\}", "%r"]  # <*>
            try:
                for p in patterns_alpha:
                    x = re.sub(p, "[STR]", x)
                for p in patterns_num:
                    x = re.sub(p, "[NUM]", x)
                for p in patterns:
                    x = re.sub(p, "<*>", x)
                x.replace("\n", "")
            except Exception as e:
                log.exception(e)
            return x

        def replace_special_chars(x):
            pattern = re.compile(r'\<\*\>|[\w\d]+|\[STR\]|\[INT\]')
            new = " ".join(re.findall(pattern, x))
            return new

        def remove_single_words(x):
            if len(x) < 2:
                return None
            if len("".join(e for e in x if e.isalnum())) > 5:
                return x.strip()
            else:
                return None

        def remove_multiple_placeholders(x):
            return re.sub(r"\*\*.", "", x)

        def split_string(x):
            start_chars = ["'", '`', '"', 'f"', "f'", 'u"', "u'", 's"', "s'", 'e, "', "f('", "f(\""]
            patterns = ['this + "', 'cm + "', 'DefaultI18nContext.getInstance().i18n("',
                        'String.format(',
                        'indent(node.depth) + "',
                        'format("',
                        'this.hostContext.withHost(',
                        'log(seq, "',
                        'this, "',
                        'testName + "',
                        'log + " ',
                        'LOADING, "',
                        'CORE, "',
                        'WORLDPERSISTENCE,"',
                        'NETWORK',
                        'FMLHSMARKER',
                        'REGISTRIES',
                        'NETREGISTRY',
                        'CONFIG',
                        'CLIENTHOOKS',
                        'SCAN',
                        'LOADING',
                        'getLogString("',
                        'sm.getString("',
                        'this, s"',
                        '{packageName} , `',
                        'this, ()->"',
                        "LogMessage.format(",
                        'String.format("',
                        "() -> \""]

            for chars in start_chars:
                if x[:len(chars)] == chars:
                    return x.split(chars)[1]

            for pat in patterns:
                if pat in x:
                    return x.split(pat)[1]
            return None

        x = split_string(log_msg)
        x = replace_placeholders(x)
        x = replace_special_chars(x)
        x = remove_single_words(x)
        x = remove_multiple_placeholders(x)
        x = x.lower()
        x = x.strip()
        return x

    def store(self, result):
        with open(self.output_path, "w") as file:
            file.writelines(result)

def main():
    #args = setup_command_line_arg()

    #input_file = args.input
    #output_file = args.output

    lr = PyLogRetriver()
    #result = lr.extract_log_messages()

    #lr.store("\n".join([x for x in result]))
    # lr.store("\n".join([x for x in result]))
    # print()

    lines1 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()(', '))' ]
    lines2 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()(', '))', 'asd', 'asssss' ]
    lines3 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()(', ')', 'pp', 'asdas', '"asd"', "asd"]
    lines4 = ['log.error("adsffsdf",', '"asdfsdf asdf (),"', '()(']

    log_lines = lr.retrieve_log_lines(lines1)
    print(log_lines)
    log_lines = lr.retrieve_log_lines(lines2)
    print(log_lines)
    log_lines = lr.retrieve_log_lines(lines3)
    print(log_lines)
    log_lines = lr.retrieve_log_lines(lines4)
    print(log_lines)
    

if __name__ == "__main__":

    main()

