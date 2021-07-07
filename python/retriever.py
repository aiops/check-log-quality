import re
import logging as log


class LogRetriver:    
    reg_string = r"\".*?\"|\'.*?\'"

    def __init__(self, multiline_max=5):
        self.multiline_max = multiline_max

    def get_comment_regex(self):
        raise NotImplementedError("Please implement get_comment_string method.")

    def count_braces(self, line):
        return len(re.findall(r"\(", line)) - len(re.findall(r"\)", line))

    def get_log_line_indices(self, lines, reg_log_start):
        log_line_indices = []
        for idx, line in enumerate(lines):
            if re.match(reg_log_start, line):
                log_line_indices.append(idx)
        return log_line_indices

    def strip_comments(self, line):
        stripped_line = re.sub(self.get_comment_regex(), '', line)
        return stripped_line

    def strip_line_for_complete_check(self, line):
        stripped_line = re.sub(self.reg_string, '', line)
        stripped_line = self.strip_comments(stripped_line).strip("\n").strip()
        
        log.debug("Received line: {} | Stripped line: {}".format(line, stripped_line))

        return stripped_line

    def check_log_completeness(self, line):
        brace_count = self.count_braces(line)
        if brace_count == 0:
            return True
        elif brace_count > 0:
            return False
        else:
            raise ValueError("Invalid log line format: {}".format(line))

    def get_log_line(self, lines, idx):
        log.debug("Checking code line {}: {}".format(idx+1, lines[idx]))
        start_idx = idx
        stripped_line = self.strip_line_for_complete_check(lines[idx])
        log_complete = self.check_log_completeness(stripped_line)
        # A log statement can go over several lines. This is what we handle here.
        while not log_complete:
            idx += 1
            line_in_file = idx + 1

            if idx >= len(lines):
                raise ValueError("Line {}: Log line incomplete but EOF reached: {}".format(
                    line_in_file, "".join(lines[start_idx:idx])))
            if (idx - start_idx) >= self.multiline_max:
                raise ValueError("Line {}: Maximum number for multiline logs ({}) reached: {}".format(
                    line_in_file, self.multiline_max, "".join(lines[start_idx:idx])))
            
            log.debug("Checking code line {}: {}".format(line_in_file, lines[idx]))
            stripped_line += lines[idx]
            stripped_line = self.strip_line_for_complete_check(stripped_line)
            log_complete = self.check_log_completeness(stripped_line)
        
        cleaned_lines = [self.strip_comments(l.strip()) for l in lines[start_idx:idx+1]]
        result_log_line = "".join(cleaned_lines).strip()
        log.debug("Result log line: {}".format(result_log_line))

        return result_log_line
        
    def get_log_lines(self, lines, log_line_indices):
        log_lines = []
        for idx in log_line_indices:
            try:
                log_line = self.get_log_line(lines, idx)
                log_lines.append(log_line)
            except ValueError as e:
                log.info("Skipping log line {}".format(lines[idx]))
                if log.root.level <= log.DEBUG: # Only print if debug is enabled
                    log.exception(e)
        return log_lines

    def _retrieve_log_lines(self, lines, reg_log_start):
        try:
            log_lines = []
            log_line_indices = self.get_log_line_indices(lines, reg_log_start)
            if len(log_line_indices) > 0:
                log_lines = self.get_log_lines(lines, log_line_indices)
        except Exception as e:
            log.exception(e)
        return log_lines
