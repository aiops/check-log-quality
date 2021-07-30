import traceback
import pandas as pd
from quality import *
from report import *

import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def _print_summary(quality_module_level, quality_class_level, quality_module_ling, quality_class_ling):
    eprint("Running log level analysis with class model {} from module {}".format(
        quality_class_level, quality_module_level))
    eprint("Running log language analysis with class model {} from module {}".format(
        quality_class_ling, quality_module_ling))

def _print_separator(title):
    eprint("")
    eprint("")
    eprint("#######################")
    eprint("{}".format(title))
    eprint("#######################")
    eprint("")
    eprint("")


def main():
    args = setup_command_line_arg()

    input_file = args.input
    quality_module_level = args.quality_module_level
    quality_class_level = args.quality_class_level
    quality_module_ling = args.quality_module_ling
    quality_class_ling = args.quality_class_ling

    log_message_df = pd.read_csv(input_file, names=LogQuality.HEADER)

    # Messages that are empty or contain only "*" --> py_ast was not able to parse their content.
    log_message_filtered_df = log_message_df[log_message_df[LogQuality.HEADER_CONTENT].str.len() > 1]
    log_message_filtered_df = log_message_filtered_df.reset_index(drop=True)

    _print_summary(quality_module_level, quality_class_level, quality_module_ling, quality_class_ling)

    r1 = ReportDecoratorResolveText()
    rep1 = r1(log_message_df)

    try:
        r2 = ReportDecoratorLevelText(quality_module_level, quality_class_level)
        rep2 = r2(log_message_filtered_df)
    except Exception as e:
        eprint("Failed to run log level quality checking.")
        traceback.print_exc()
        rep2 = ""

    try:
        r3 = ReportDecoratorLingText(quality_module_ling, quality_class_ling)
        rep3 = r3(log_message_filtered_df)
    except Exception as e:
        eprint("Failed to run log level quality checking.")
        traceback.print_exc()
        rep3 = ""
    
    if rep2:
        _print_separator("Log Level Quality Report")
        eprint(rep2)
    if rep3:
        _print_separator("Log Language Quality Report")
        eprint(rep3)
    if rep1:
        _print_separator("Parsing & Resolve Report")
        eprint(rep1)

    eprint("")
    eprint("")
    eprint("*****************************************************************")
    eprint("***** If you like our tool visit us at https://logsight.ai ******")
    eprint("*****************************************************************")
    eprint("")
    

if __name__ == "__main__":
    main()
