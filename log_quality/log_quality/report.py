from logging import fatal

from numpy import record
from quality import *


class LogQualityReport:
    def __init__(self, log_quality: LogQuality):
        self.log_quality = log_quality
        self._report_elements = []

    def _run_quality_check(self, log_lines_df):
        result = self.log_quality(log_lines_df)
        return result

    def __call__(self, log_lines_df):
        raise NotImplemented("Please implement __call__.")
        
    def get_formatted_report():
        raise NotImplemented("Please implement get_formatted_report.")


class LogQualityReportText(LogQualityReport):
    def __init__(self, log_quality: LogQuality):
        super().__init__(log_quality)

    def get_formatted_report(self):
        return "\n".join(self._report_elements)

    def __call__(self, log_lines_df):
        super().__call__(log_lines_df)


class ReportDecoratorResolveText(LogQualityReportText):
    def __init__(self):
        super().__init__(LogQualityResolve())
        

    def __call__(self, log_lines_df):
        _, failed = self._run_quality_check(log_lines_df)
        if len(failed) > 0:
            self._report_elements.append(
                "The log quality checker was not able to " + \
                "resolve the content of the following log messages:")
            self._report_elements.append("")
            for _, row in failed.iterrows():
                self._report_elements.append(
                    "File {}, line {}".format(row[LogQuality.HEADER_FILE], row[LogQuality.HEADER_LINE])
                )

        return self.get_formatted_report()
        

class ReportDecoratorLevelText(LogQualityReportText):
    def __init__(self, quality_module, quality_class):
        super().__init__(LogQualityLevel(quality_module, quality_class))


    def _process_invalid_level(self, invalid_level):
        self._report_elements.append("Invalid log level for following log messages:")
        self._report_elements.append("Valid log levels are: {}".format(
            ", ".join(self.log_quality.label2id.keys())))
        self._report_elements.append("")

        for _, row in invalid_level.iterrows():
            self._report_elements.append(
                "File {}, line {}: Invalid log level {}".format(
                    row[LogQuality.HEADER_FILE], 
                    row[LogQuality.HEADER_LINE],
                    row[LogQuality.HEADER_LEVEL]
                )
            )
        self._report_elements.append("")
        self._report_elements.append("")

    def _get_level_recommendation(self, entry):
        level = entry[LogQuality.HEADER_LEVEL]
        prediction = entry[LogQuality.HEADER_RESULT]

        if level == 0 and prediction == 1:
            return "warning or error"
        if level == 1 and prediction == 0:
            return "debug or info"
        else:
            return ""

    def _process_bad_log_levels(self, bad_level):
        self._report_elements.append("Consider changing the log level of the following log messages:")
        self._report_elements.append("")

        for _, row in bad_level.iterrows():
            recommended_level = self._get_level_recommendation(row)
            if recommended_level:
                self._report_elements.append(
                    "{} --> Consider to change log level to {}.".format(
                        row[LogQuality.HEADER_CONTENT], recommended_level)
                )
                self._report_elements.append(
                    "\t --> file: {}, line: {}".format(
                        row[LogQuality.HEADER_FILE], 
                        row[LogQuality.HEADER_LINE]
                    )
                )

    def __call__(self, log_lines_df):
        _, invalid_level, bad_level = self._run_quality_check(log_lines_df)

        if len(invalid_level) > 0:
            self._process_invalid_level(invalid_level)
        
        if len(bad_level) > 0:
            self._process_bad_log_levels(bad_level)

        return self.get_formatted_report()


class ReportDecoratorLingText(LogQualityReportText):
    def __init__(self, quality_module, quality_class):
        super().__init__(LogQualityLing(quality_module, quality_class))

    def _get_word_class_result(self, prediction):
        if prediction["root"] == 0:
            result = "No word classes found. The log message does not contain any expressive words."
        else:
            missing_word_classes = []
            for key in prediction:
                if key == "obj" and prediction[key] == 0:
                    missing_word_classes.append("object")
                if key == "subj" and prediction[key] == 0:
                    missing_word_classes.append("subject")
            if len(missing_word_classes) > 0:
                result = "The log message will be more expressive if you add {}.".format(
                    " and ".join(missing_word_classes))
            else:
                result = ""
        return result

    def _process_bad_language(self, bad_language, predictions):
        self._report_elements.append("Following log messages are not expressive. Consider rewriting them.")
        self._report_elements.append("")

        for idx, row in bad_language.iterrows():
            p = predictions[idx]
            recommendation = self._get_word_class_result(p)

            self._report_elements.append(
                "{} --> {}".format(row[LogQuality.HEADER_CONTENT], recommendation)
            )
            self._report_elements.append(
                "\t --> file: {}, line: {}, ".format(
                    row[LogQuality.HEADER_FILE], 
                    row[LogQuality.HEADER_LINE]
                )
            )

    def __call__(self, log_lines_df):
        _, bad_language, predictions = self._run_quality_check(log_lines_df)

        if len(bad_language) > 0:
            self._process_bad_language(bad_language, predictions)

        return self.get_formatted_report()