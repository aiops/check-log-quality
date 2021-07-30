
import numpy as np
from utils import *

QUALITY_TYPE_RESOLVE = "resolve"
QUALITY_TYPE_LEVEL = "level"
QUALITY_TYPE_LING = "ling"
QUALITY_TYPES = [ QUALITY_TYPE_RESOLVE, QUALITY_TYPE_LEVEL, QUALITY_TYPE_LING ]

REPORT_TEXT = "text"
REPORTS = [REPORT_TEXT]

class LogQuality:
    HEADER_LINE = 'Line'
    HEADER_LEVEL = 'Level'
    HEADER_CONTENT = 'Content'
    HEADER_FILE = 'File'
    HEADER = [HEADER_LINE, HEADER_LEVEL, HEADER_CONTENT, HEADER_FILE]
    HEADER_RESULT = 'Results' # This is a placeholder to potentially store results in the dataframe

    def __init__(self):
        '''Root class init'''
        pass

    def __call__(self, log_lines_df):
        raise NotImplemented("Please implement _get_report_instance.")


class LogQualityResolve(LogQuality):
    def __init__(self):
        super().__init__()


    def __call__(self, log_lines_df):
        mask = log_lines_df[LogQuality.HEADER_CONTENT].str.len() <= 1
        # Returns tuple. 
        # First element are lines that passed the quality check
        # Second element are lines that failed the quality check
        return log_lines_df[~mask], log_lines_df[mask]


class LogQualityModel(LogQuality):
    def __init__(self, module_name, class_name, quality_type):
        super().__init__()
        if quality_type not in QUALITY_TYPES:
            raise AttributeError("Invalid log quality type %s. Valid quality types are: ", \
                quality_type, ", ".join(QUALITY_TYPES))
        
        try:
            self.model = import_model(module_name, class_name, quality_type)
        except Exception as e:
            logging.error("Unable to import class %s from module %s.", module_name, class_name)
            raise e


class LogQualityLevel(LogQualityModel):
    def __init__(self, module_name, class_name):
        super().__init__(module_name, class_name, QUALITY_TYPE_LEVEL)

        self.label2id = {
            "info": 0, "debug": 0, "trace": 0, 
            "warning": 1, "error":1, "exception": 1, "critical": 1
        }

    def __call__(self, log_lines_df):
        mask = log_lines_df[LogQuality.HEADER_LEVEL].isin(self.label2id)

        filtered_invalid_level = log_lines_df[~mask]
        filtered_valid_level = log_lines_df[mask]

        log_lines = filtered_valid_level[LogQuality.HEADER_CONTENT].tolist()
        result = self.model.predict_batch(log_lines)
        filtered_valid_level[LogQuality.HEADER_RESULT] = result

        filtered_valid_level[LogQuality.HEADER_LEVEL] = \
            filtered_valid_level[LogQuality.HEADER_LEVEL].apply(lambda x: self.label2id[x])

        mask = filtered_valid_level[LogQuality.HEADER_LEVEL] == result

        filtered_bad_level = filtered_valid_level[~mask]
        good_logs = filtered_valid_level[mask]

        # Returns triple. 
        # First element are lines that passed the quality check
        # Second element are lines that contain invalid log levels
        # Third element are lines that contain bad log levels
        return good_logs, filtered_invalid_level, filtered_bad_level


class LogQualityLing(LogQualityModel):
    def __init__(self, module_name, class_name):
        super().__init__(module_name, class_name, QUALITY_TYPE_LING)

    def __call__(self, log_lines_df):
        log_lines = log_lines_df[LogQuality.HEADER_CONTENT].tolist()
        predictions = self.model.predict_batch(log_lines)

        overall_result = [r["prediction"] for r in predictions]

        log_lines_df[LogQuality.HEADER_RESULT] = overall_result
        mask = log_lines_df[LogQuality.HEADER_RESULT] == 0

        filtered_bad_ling = log_lines_df[~mask]
        good_logs = log_lines_df[mask]

        # Returns tuple. 
        # First element are lines that passed the quality check
        # Second element are lines that written in a bad language
        return good_logs, filtered_bad_ling, predictions
