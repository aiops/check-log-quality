import sys
import os
import re
import logging as log

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import *

class LogRetriver:
    def __init__(self, input_path, output_path, log_types=None):
        if not log_types:
            self.log_types = ["error", "info"]
        else:
            self.log_types = log_types

        self.input_path = input_path
        self.output_path = output_path

    def count_braces(self, line):
        print("{} --------- {}".format(len(re.findall("\(", line)), len(re.findall("\)", line))))
        return len(re.findall("\(", line)) - len(re.findall("\)", line))

    def parse_file(self, pattern=None):
        if not pattern:
            pattern = "[lL][oO][gG]\w*_?\w*\."
        matches = []
        matches_clean = []
        open_braces = 0
        try:
            with open(self.input_path, "r") as f:
                substr = ""
                for idx, line in enumerate(f.readlines()):
                    for log_type in self.log_types:
                        pattern += log_type + '\('

                        print("-------"*10)
                        # print(line)
                        if open_braces > 0:
                            substr += line.strip()
                            open_braces = self.count_braces(substr)
                            # open_braces += self.count_braces(substr) Old
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
                            matches.append((idx, log_type, self.input_path, substr))
                            matches_clean.append((idx, log_type, self.input_path, self._process(substr[re.search(pattern, substr).end():])))
        except Exception as e:
            log.exception(e)
            pass
        return matches, matches_clean

    def extract_log_messages(self):
        logs_ = []
        logs_clean = []
        for log_type in ['error', "info"]:
            l, l_clean = self.parse_file(self.input_path, log_type)
            logs_.append(l)
            logs_clean.append(l_clean)
        return logs_, logs_clean

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
            return re.sub("\*\*.", "", x)

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


def main():
    args = setup_command_line_arg()

    input_file = args.input
    output_file = args.output

    lr = LogRetriver(input_file, output_file)
    result = lr.parse_file()

    print(result)
    

if __name__ == "__main__":
    main()

