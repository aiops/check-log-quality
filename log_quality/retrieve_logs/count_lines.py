import logging as log

from .utils import *

def main():
    args = setup_command_line_arg()

    input_file = args.input
    output_file = args.output

    try:
        with open(input_file, "r") as f:
            num_lines = len(f.readlines())
            print("File {} contains {} lines.".format(input_file, num_lines))
    except UnicodeDecodeError as ede:
        log.warning("Unable to read non-textual file {}".format(input_file))
    except Exception as e:
        log.exception(e)
        exit(-1)

    try:
        with open(output_file, "w") as f:
            f.write("File {} contains {} lines.".format(input_file, num_lines))
    except Exception as e:
        log.exception(e)
        exit(-1)


if __name__ == "__main__":
    main()