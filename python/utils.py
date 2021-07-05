import argparse


def setup_command_line_arg():
    parser = argparse.ArgumentParser(description='Parse logs from source code.')

    parser.add_argument('-i', '--input', type=str, required=True, help="input file path to read")
    parser.add_argument('-o', '--output', type=str, required=True, help="output file path where results are written to")

    return parser.parse_args()
