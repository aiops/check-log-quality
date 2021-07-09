import os
import sys
import string
import logging as log

import astroid

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from python.utils_ast import *


def is_method_call(func, types=(), methods=()):
    """Determines if a BoundMethod node represents a method call.
    Args:
      func (astroid.BoundMethod): The BoundMethod AST node to check.
      types (Optional[String]): Optional sequence of caller type names to restrict check.
      methods (Optional[String]): Optional sequence of method names to restrict check.
    Returns:
      bool: true if the node represents a method call for the given type and
      method names, False otherwise.
    """
    return (
        isinstance(func, astroid.BoundMethod)
        and isinstance(func.bound, astroid.Instance)
        and (func.bound.name in types if types else True)
        and (func.name in methods if methods else True)
    )


DEFAULT_LOGGING_MODULES = { "logging" }
LOG_LEVEL_ALIASES = {
    "debug": ["debug"],
    "info": ["info"],
    "warning": ["warning", "warn"],
    "error": ["error", "exception"],
    "critical": ["critical"],
}
LOG_LEVELS = {a for k in LOG_LEVEL_ALIASES for a in LOG_LEVEL_ALIASES[k]}
ALIAS_TO_LEVEL = {a: k for k in LOG_LEVEL_ALIASES for a in LOG_LEVEL_ALIASES[k]}


class LogRetriverPyAST:
    
    def __init__(self, logging_modules=DEFAULT_LOGGING_MODULES):
        self._logging_modules = logging_modules
        # The code being checked can just as easily "import logging as foo",
        # so it is necessary to process the imports and store in this field
        # what name the logging module is actually given.
        self._logging_alias = set()
        self._from_imports = {}
        for logging_mod in logging_modules:
            parts = logging_mod.rsplit(".", 1)
            if len(parts) > 1:
                self._from_imports[parts[0]] = parts[1]

        self.log_lines = []

    def walk(self, astroid):
        """call visit events of astroid checkers for the given node, recurse on
        its children, then leave events.
        """
        try:
            # generate events for this node on each checker
            self.visit_all(astroid)
            # recurse on children
            for child in astroid.get_children():
                self.walk(child)
        except Exception as e:
            log.exception(e)
        
    def safe_visit(self, node, callback, log_exception=False):
        try:
            callback(node)
        except Exception as e:
            if log_exception:
                log.exception(e)
    
    def visit_all(self, node):
        self.safe_visit(node, self.visit_importfrom, log_exception=False)
        self.safe_visit(node, self.visit_import, log_exception=False)
        self.safe_visit(node, self.visit_call, log_exception=False)

    def visit_importfrom(self, node):
        """Checks to see if a module uses a non-Python logging module."""
        logging_name = self._from_imports[node.modname]
        for module, as_name in node.names:
            if module == logging_name:
                self._logging_alias.add(as_name or module)

    def visit_import(self, node):
        """Checks to see if this module uses Python's built-in logging."""
        for module, as_name in node.names:
            if module in self._logging_modules:
                self._logging_alias.add(as_name or module)

    def visit_call(self, node):
        """Checks calls to logging methods."""
        def is_logging_name():
            return (
                isinstance(node.func, astroid.Attribute)
                and isinstance(node.func.expr, astroid.Name)
                and node.func.expr.name in self._logging_alias
            )

        def is_logger_class():
            try:
                for inferred in node.func.infer():
                    if isinstance(inferred, astroid.BoundMethod):
                        parent = inferred._proxied.parent
                        if isinstance(parent, astroid.ClassDef) and (
                            parent.qname() == "logging.Logger"
                            or any(
                                ancestor.qname() == "logging.Logger"
                                for ancestor in parent.ancestors()
                            )
                        ):
                            return True, inferred._proxied.name
            except astroid.exceptions.InferenceError:
                pass
            return False, None

        if is_logging_name():
            name = node.func.attrname
        else:
            result, name = is_logger_class()
            if not result:
                return
        self._check_log_method(node, name)

    def infer_log_level(self, arg):
        if isinstance(arg, astroid.Name) or isinstance(arg, astroid.Call):
            level = safe_infer(arg)
        elif isinstance(arg, astroid.Const):
            level = arg.value
            if level not in LOG_LEVELS:
                ValueError("Invalid log level: .".format(level))
        else:
            level = arg
        
        if isinstance(level, astroid.Attribute):
            level = level.attrname
        else:
            raise ValueError("Unable to retrieve log level.")
        return level.lower()

    def _check_log_method(self, node, name):
        """Checks calls to logging.log(level, format, *format_args)."""
        level = ""
        if name == "log":
            if node.starargs or node.kwargs or len(node.args) < 2:
                # Either a malformed call, star args, or double-star args. Beyond
                # the scope of this checker.
                return
            format_pos = 1
            level = self.infer_log_level(node.args[0])
        elif name in LOG_LEVELS:
            if node.starargs or node.kwargs or not node.args:
                # Either no args, star args, or double-star args. Beyond the
                # scope of this checker.
                return
            format_pos = 0
            level = name
        else:
            return
        level = ALIAS_TO_LEVEL[level]

        if isinstance(node.args[format_pos], astroid.BinOp):
            print("1")
            binop = node.args[format_pos]
            emit = binop.op == "%"
            if binop.op == "+":
                total_number_of_strings = sum(
                    1
                    for operand in (binop.left, binop.right)
                    if self._is_operand_literal_str(safe_infer(operand))
                )
                emit = total_number_of_strings > 0
            if emit:
                self.add_message(
                    "logging-not-lazy",
                    node=node,
                    args=(self._helper_string(node),),
                )
        elif isinstance(node.args[format_pos], astroid.Call):
            print("2")
            #self._check_call_func(node.args[format_pos])
            #print(node.args[format_pos].func.repr_tree())
            inferred = safe_infer(node.args[format_pos].func)
            print(inferred.repr_tree())
            if inferred and inferred.value:
                print(inferred.value)
            else:
                print(inferred)
        elif isinstance(node.args[format_pos], astroid.Const):
            print("3")
            self._check_format_string(node, format_pos)
        elif isinstance(node.args[format_pos], astroid.JoinedStr):
            print("4")
            print("Hier")
            self.add_message(
                "logging-fstring-interpolation",
                node=node,
                args=(self._helper_string(node),),
            )
        elif isinstance(node.args[format_pos], astroid.Name):
            print(5)
            try:
                node.args[format_pos] = safe_infer(node.args[format_pos])
            except:
                print("hier")

    def _helper_string(self, node):
        """Create a string that lists the valid types of formatting for this node."""
        valid_types = ["lazy %"]

        if not self.linter.is_message_enabled(
            "logging-fstring-formatting", node.fromlineno
        ):
            valid_types.append("fstring")
        if not self.linter.is_message_enabled(
            "logging-format-interpolation", node.fromlineno
        ):
            valid_types.append(".format()")
        if not self.linter.is_message_enabled("logging-not-lazy", node.fromlineno):
            valid_types.append("%")

        return " or ".join(valid_types)

    @staticmethod
    def _is_operand_literal_str(operand):
        """
        Return True if the operand in argument is a literal string
        """
        return isinstance(operand, astroid.Const) and operand.name == "str"

    def _check_call_func(self, node):
        """Checks that function call is not format_string.format().
        Args:
          node (astroid.node_classes.Call):
            Call AST node to be checked.
        """
        func = safe_infer(node.func)
        types = ("str", "unicode")
        methods = ("format",)
        if is_method_call(func, types, methods) and not is_complex_format_str(
            func.bound
        ):
            self.add_message(
                "logging-format-interpolation",
                node=node,
                args=(self._helper_string(node),),
            )

    def _check_format_string(self, node, format_arg):
        """Checks that format string tokens match the supplied arguments.
        Args:
          node (astroid.node_classes.NodeNG): AST node to be checked.
          format_arg (int): Index of the format string in the node arguments.
        """
        num_args = _count_supplied_tokens(node.args[format_arg + 1 :])
        if not num_args:
            # If no args were supplied the string is not interpolated and can contain
            # formatting characters - it's used verbatim. Don't check any further.
            return

        format_string = node.args[format_arg].value
        required_num_args = 0
        if isinstance(format_string, bytes):
            format_string = format_string.decode()
        if isinstance(format_string, str):
            try:
                if self._format_style == "old":
                    keyword_args, required_num_args, _, _ = parse_format_string(
                        format_string
                    )
                    if keyword_args:
                        # Keyword checking on logging strings is complicated by
                        # special keywords - out of scope.
                        return
                elif self._format_style == "new":
                    (
                        keyword_arguments,
                        implicit_pos_args,
                        explicit_pos_args,
                    ) = parse_format_method_string(format_string)

                    keyword_args_cnt = len(
                        {k for k, l in keyword_arguments if not isinstance(k, int)}
                    )
                    required_num_args = (
                        keyword_args_cnt + implicit_pos_args + explicit_pos_args
                    )
            except UnsupportedFormatCharacter as ex:
                char = format_string[ex.index]
                self.add_message(
                    "logging-unsupported-format",
                    node=node,
                    args=(char, ord(char), ex.index),
                )
                return
            except IncompleteFormatString:
                self.add_message("logging-format-truncated", node=node)
                return
        if num_args > required_num_args:
            self.add_message("logging-too-many-args", node=node)
        elif num_args < required_num_args:
            self.add_message("logging-too-few-args", node=node)


def is_complex_format_str(node):
    """Checks if node represents a string with complex formatting specs.
    Args:
        node (astroid.node_classes.NodeNG): AST node to check
    Returns:
        bool: True if inferred string uses complex formatting, False otherwise
    """
    inferred = safe_infer(node)
    if inferred is None or not (
        isinstance(inferred, astroid.Const) and isinstance(inferred.value, str)
    ):
        return True
    try:
        parsed = list(string.Formatter().parse(inferred.value))
    except ValueError:
        # This format string is invalid
        return False
    for _, _, format_spec, _ in parsed:
        if format_spec:
            return True
    return False


def _count_supplied_tokens(args):
    """Counts the number of tokens in an args list.
    The Python log functions allow for special keyword arguments: func,
    exc_info and extra. To handle these cases correctly, we only count
    arguments that aren't keywords.
    Args:
      args (list): AST nodes that are arguments for a log format string.
    Returns:
      int: Number of AST nodes that aren't keywords.
    """
    return sum(1 for arg in args if not isinstance(arg, astroid.Keyword))


def get_ast(filepath):
        """Return an ast(roid) representation of a module or a string.
        :param str filepath: path to checked file.
        :returns: the AST
        :rtype: astroid.nodes.Module
        """
        MANAGER = astroid.MANAGER
        try:
            return MANAGER.ast_from_file(filepath, source=True)
        except astroid.AstroidSyntaxError as ex:
            # pylint: disable=no-member
            print("TODO")
            # TODO
        except astroid.AstroidBuildingException as ex:
            print("TODO")
        except Exception as ex:  # pylint: disable=broad-except
            log.exception(ex)
        return None



if __name__ == "__main__":

    path = "./tt.py"
    lr = LogRetriverPyAST()
    ast = get_ast(path)
    lr.walk(ast)
    








