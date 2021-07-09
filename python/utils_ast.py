import string
import sys
import os
import numbers
from string import _string

import astroid


class UnsupportedFormatCharacter(Exception):
    """A format character in a format string is not one of the supported
    format characters."""

    def __init__(self, index):
        Exception.__init__(self, index)
        self.index = index


class IncompleteFormatString(Exception):
    """A format string ended in the middle of a format specifier."""


class UnsupportedFormatCharacter(Exception):
    """A format character in a format string is not one of the supported
    format characters."""

    def __init__(self, index):
        Exception.__init__(self, index)
        self.index = index


def split_format_field_names(format_string):
    try:
        return _string.formatter_field_name_split(format_string)
    except ValueError as e:
        raise IncompleteFormatString() from e


def collect_string_fields(format_string):
    """Given a format string, return an iterator
    of all the valid format fields. It handles nested fields
    as well.
    """
    formatter = string.Formatter()
    try:
        parseiterator = formatter.parse(format_string)
        for result in parseiterator:
            if all(item is None for item in result[1:]):
                # not a replacement format
                continue
            name = result[1]
            nested = result[2]
            yield name
            if nested:
                yield from collect_string_fields(nested)
    except ValueError as exc:
        # Probably the format string is invalid.
        if exc.args[0].startswith("cannot switch from manual"):
            # On Jython, parsing a string with both manual
            # and automatic positions will fail with a ValueError,
            # while on CPython it will simply return the fields,
            # the validation being done in the interpreter (?).
            # We're just returning two mixed fields in order
            # to trigger the format-combined-specification check.
            yield ""
            yield "1"
            return
        raise IncompleteFormatString(format_string) from exc


def parse_format_method_string(format_string):
    """
    Parses a PEP 3101 format string, returning a tuple of
    (keyword_arguments, implicit_pos_args_cnt, explicit_pos_args),
    where keyword_arguments is the set of mapping keys in the format string, implicit_pos_args_cnt
    is the number of arguments required by the format string and
    explicit_pos_args is the number of arguments passed with the position.
    """
    keyword_arguments = []
    implicit_pos_args_cnt = 0
    explicit_pos_args = set()
    for name in collect_string_fields(format_string):
        if name and str(name).isdigit():
            explicit_pos_args.add(str(name))
        elif name:
            keyname, fielditerator = split_format_field_names(name)
            if isinstance(keyname, numbers.Number):
                explicit_pos_args.add(str(keyname))
            try:
                keyword_arguments.append((keyname, list(fielditerator)))
            except ValueError as e:
                raise IncompleteFormatString() from e
        else:
            implicit_pos_args_cnt += 1
    return keyword_arguments, implicit_pos_args_cnt, len(explicit_pos_args)


def parse_format_string(format_string):
    """Parses a format string, returning a tuple of (keys, num_args), where keys
    is the set of mapping keys in the format string, and num_args is the number
    of arguments required by the format string.  Raises
    IncompleteFormatString or UnsupportedFormatCharacter if a
    parse error occurs."""
    keys = set()
    key_types = dict()
    pos_types = []
    num_args = 0

    def next_char(i):
        i += 1
        if i == len(format_string):
            raise IncompleteFormatString
        return (i, format_string[i])

    i = 0
    while i < len(format_string):
        char = format_string[i]
        if char == "%":
            i, char = next_char(i)
            # Parse the mapping key (optional).
            key = None
            if char == "(":
                depth = 1
                i, char = next_char(i)
                key_start = i
                while depth != 0:
                    if char == "(":
                        depth += 1
                    elif char == ")":
                        depth -= 1
                    i, char = next_char(i)
                key_end = i - 1
                key = format_string[key_start:key_end]

            # Parse the conversion flags (optional).
            while char in "#0- +":
                i, char = next_char(i)
            # Parse the minimum field width (optional).
            if char == "*":
                num_args += 1
                i, char = next_char(i)
            else:
                while char in string.digits:
                    i, char = next_char(i)
            # Parse the precision (optional).
            if char == ".":
                i, char = next_char(i)
                if char == "*":
                    num_args += 1
                    i, char = next_char(i)
                else:
                    while char in string.digits:
                        i, char = next_char(i)
            # Parse the length modifier (optional).
            if char in "hlL":
                i, char = next_char(i)
            # Parse the conversion type (mandatory).
            flags = "diouxXeEfFgGcrs%a"
            if char not in flags:
                raise UnsupportedFormatCharacter(i)
            if key:
                keys.add(key)
                key_types[key] = char
            elif char != "%":
                num_args += 1
                pos_types.append(char)
        i += 1
    return keys, num_args, key_types, pos_types


def _get_python_type_of_node(node):
    pytype = getattr(node, "pytype", None)
    if callable(pytype):
        return pytype()
    return None


def safe_infer(node, context=None):
    """Return the inferred value for the given node.
    Return None if inference failed or if there is some ambiguity (more than
    one node has been inferred of different types).
    """
    inferred_types = set()
    try:
        infer_gen = node.infer(context=context)
        value = next(infer_gen)
    except astroid.InferenceError:
        return None

    if value is not astroid.Uninferable:
        inferred_types.add(_get_python_type_of_node(value))

    try:
        for inferred in infer_gen:
            inferred_type = _get_python_type_of_node(inferred)
            if inferred_type not in inferred_types:
                return None  # If there is ambiguity on the inferred node.
    except astroid.InferenceError:
        return None  # There is some kind of ambiguity
    except StopIteration:
        return value
    return value if len(inferred_types) <= 1 else None

