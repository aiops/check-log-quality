import sys
import os
import logging as log

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import *

def main():
    args = setup_command_line_arg()

    input_file = args.input
    output_file = args.output

    try:
        with open(input_file, "r") as f:
            i = 0
            for idx, line in enumerate(f.readlines()):
                i += 1
            print("File {} contains {} lines.".format(input_file, i))
    except UnicodeDecodeError as ede:
        log.warning("Unable to read non-textual file {}".format(input_file))
    except Exception as e:
        log.exception(e)
        exit(-1)

    try:
        with open(output_file, "w") as f:
            f.write("File {} contains {} lines.".format(input_file, i))
    except Exception as e:
        log.exception(e)
        exit(-1)


if __name__ == "__main__":
    main()