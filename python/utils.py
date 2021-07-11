import argparse
import os
import pathlib
import pandas as pd


def setup_command_line_arg():
    parser = argparse.ArgumentParser(description='Parse logs from source code.')

    parser.add_argument('-i', '--input', type=str, required=True, help="input file path to read")
    parser.add_argument('-o', '--output', type=str, required=True, help="output file path where results are written to")

    return parser.parse_args()


def is_python_file(file_path):
    python_file_extension = ".py"
    _, file_extension = os.path.splitext(file_path)
    return python_file_extension == file_extension


def creat_output_dirs(dir_path):
    path = pathlib.Path(dir_path)
    path.parent.mkdir(parents=True, exist_ok=True)


def store_results(output_file, line_numbers, log_levels, log_messages):
    dir_path = os.path.dirname(os.path.realpath(output_file))
    creat_output_dirs(dir_path)

    data = {'line_number': line_numbers, 'log_level': log_levels, 'log_message': log_messages}
    df = pd.DataFrame.from_dict(data)
    df.to_csv(output_file)

