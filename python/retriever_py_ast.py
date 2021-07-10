import logging as log
import re

import astroid


class LogInstructionParseError(Exception):
    """Error raised whenever a log instruction cannot be parsed."""


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


class LogRetrieverPyAST:
    DEFAULT_LOGGING_MODULES = { "logging" }
    DEFAULT_LOG_LEVEL_ALIASES = {
        "debug": ["debug"],
        "info": ["info"],
        "warning": ["warning", "warn"],
        "error": ["error", "exception"],
        "critical": ["critical"],
    }
    STRING_FORMAT_VARABLE_REG = r'(?<=[^\\])\{.*?\}|^\{.*?\}'
    STRING_BINOP_VARABLE_REG = r'%[diouxXeEfFgGcrs%a]|%.*?.[diouxXeEfFgGcrs%a]'
    
    def __init__(self, logging_modules=DEFAULT_LOGGING_MODULES, variable_token="*"):
        # The code being checked can just as easily "import logging as foo",
        # so it is necessary to process the imports and store in this field
        # what name the logging module is actually given.
        self._logging_modules = logging_modules
        self._logging_module_aliases = set()

        self.log_level_aliases = {a for k in self.DEFAULT_LOG_LEVEL_ALIASES 
                                    for a in self.DEFAULT_LOG_LEVEL_ALIASES[k]}
        self.alias_to_level = {a: k for k in self.DEFAULT_LOG_LEVEL_ALIASES 
                                    for a in self.DEFAULT_LOG_LEVEL_ALIASES[k]}
        self.log_method = "log"
        self.log_method_aliases = {self.log_method}

        self.variable_token = variable_token

        self.result = {
            "log_message": [],
            "level": [],
            "line_number": []
        }

    def get_exception(self, msg, node):
        return LogInstructionParseError("{} at line {}".format(msg, node.lineno))

    def walk(self, astroid):
        """call visit events of astroid checkers for the given node, recurse on
        its children, then leave events.
        """
        try:
            # generate events for this node on each checker
            self.visit(astroid)
            # recurse on children
            for child in astroid.get_children():
                self.walk(child)
        except Exception as e:
            log.exception(e)

    def visit(self, node):
        if isinstance(node, astroid.Import):
            self.visit_import(node)
        elif isinstance(node, astroid.ImportFrom):
            self.visit_importfrom(node)
        elif isinstance(node, astroid.Call):
            self.visit_call(node)

    def visit_import(self, node):
        """Check if logging module is imported. Check potential aliases."""
        for module, as_name in node.names:
            if module in self._logging_modules:
                self._logging_module_aliases.add(as_name or module)

    def visit_importfrom(self, node):
        """Check if logging module is imported. Check potential aliases."""
        if node.modname in self._logging_modules:
            for module, as_name in node.names:
                if module in self.alias_to_level and as_name:
                    self.log_level_aliases.add(as_name or module)
                    self.alias_to_level[as_name] = self.alias_to_level[module]
                elif module == self.log_method and as_name:
                    self.log_method_aliases.add(as_name)

    def visit_call(self, node):
        """Checks calls to logging methods."""
        def check_logging_name(node):
            return (
                isinstance(node, astroid.Name) and
                (
                    node.name in self.log_method_aliases or 
                    node.name in self.log_level_aliases
                )
            )
        def check_logging_expr(node):
            if isinstance(node.expr, astroid.Attribute):
                return check_logging_attr(node.expr)
            elif isinstance(node.expr, astroid.Name):
                return node.expr.name in self._logging_module_aliases
            else:
                return False
        def check_logging_attr(node):
            if isinstance(node, astroid.Attribute):
                return check_logging_expr(node)
            else:
                return False
        
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

        if check_logging_attr(node.func):
            name = node.func.attrname
        elif check_logging_name(node.func):
            name = node.func.name
        else:
            result, name = is_logger_class()
            if not result:
                return

        try:
            (log_message, level, line_number) = self._parse_log_instruction(node, name)
        except Exception as e:
            log.exception(e)
            return

        self.result["log_message"].append(log_message)
        self.result["level"].append(level)
        self.result["line_number"].append(line_number)
        

    def _parse_log_instruction(self, node, name):
        if name == "log":
            if node.starargs or node.kwargs or len(node.args) < 2:
                # Either a malformed call, star args, or double-star args. Beyond
                # the scope of this checker.
                return
            format_pos = 1
            level = self.infer_log_level(node.args[0])
        elif name in self.log_level_aliases:
            if node.starargs or node.kwargs or not node.args:
                # Either no args, star args, or double-star args. Beyond the
                # scope of this checker.
                return
            format_pos = 0
            level = name
        else:
            return
        level = self.alias_to_level[level]

        log_message_node = node.args[format_pos]
        log_message = self._parse_log_message(log_message_node)
        if log_message:
            log_message = log_message.value
        else:
            raise self.get_exception("Unable to parse log message.", log_message_node)
        line_number = node.lineno  

        return (log_message, level, line_number)

    def _parse_log_message(self, node):
        if not node:
            return None
        if isinstance(node, astroid.Const):
            return node
        if isinstance(node, astroid.FormattedValue):
            return self._parse_log_message(node.value)
        if (
            isinstance(node, astroid.Call) and 
            isinstance(node.func, astroid.Attribute) and
            node.func.attrname == "format"
        ):
            node = self._parse_format_attr(node.func, node.args)
            node = self._parse_log_message(node)
        elif isinstance(node, astroid.JoinedStr):
            node = self._parse_joinedstr(node)
            node = self._parse_log_message(node)
        elif isinstance(node, astroid.BinOp) and node.op == '%':
            node = self._parse_binop_format(node.left, node.right.elts)
            node = self._parse_log_message(node)
        else:
            #print(node.repr_tree())
            inferred = self.safe_infer(node)
            #print(inferred.repr_tree())
            if inferred:
                node = self._clone_node(node, inferred)
            else:
                return None
            node = self._parse_log_message(node)
        return node


    def _infer_log_level(self, arg):
        """Infer log level when e.g. logging.log(<level>, msg...) statement is given."""
        if isinstance(arg, astroid.Name) or isinstance(arg, astroid.Call):
            arg = self.safe_infer(arg)
            if isinstance(arg, astroid.Const):
                level = log.getLevelName(arg.value)
            else:
                raise self.get_exception("Unable to retrieve log level.", arg)
        elif isinstance(arg, astroid.Const):
            level = log.getLevelName(arg.value)
        elif isinstance(arg, astroid.Attribute):
            level = arg.attrname
        else:
            raise self.get_exception("Unable to retrieve log level.", arg)
        level = level.lower()
        if level not in self.log_level_aliases:
            raise self.get_exception("Invalid log level: .".format(level), arg)
        return level


    def _clone_node(self, node, new_node):
        new_node.lineno = node.lineno
        new_node.col_offset = node.col_offset
        new_node.parent = node.parent
        return new_node


    def _parse_joinedstr(self, arg):
        all_values = []
        for v in arg.values:
            v = self._parse_log_message(v)
            if v:
                all_values.append(v)
            else:
                all_values.append(astroid.Const(lineno=arg.lineno, col_offset=arg.col_offset, 
                        parent=arg.parent, value=self.variable_token))
        value = "".join([v.value for v in all_values])
        new_node = astroid.Const(lineno=arg.lineno, col_offset=arg.col_offset, 
                parent=arg.parent, value=value)
        return new_node


    def _parse_arg_list(self, arg_list):
        all_args = []
        for a in arg_list:
            a = self._parse_log_message(a)
            if a and a != "":
                all_args.append(a.value)
            else:
                all_args.append(self.variable_token)
        return all_args


    def _parse_format_attr(self, attr, args):
        expr = self._parse_log_message(attr.expr)
        if not expr:
            return None

        all_args = self._parse_arg_list(args)

        value = expr.value
        for a in all_args:
            value = re.sub(self.STRING_FORMAT_VARABLE_REG, a, value, count=1)

        return astroid.Const(lineno=attr.lineno, col_offset=attr.col_offset, 
                    parent=attr.parent, value=value)


    def _parse_binop_format(self, string_f, args):
        expr = self._parse_log_message(string_f)
        if not expr:
            return None
            
        all_args = self._parse_arg_list(args)
        value = expr.value
        for a in all_args:
            value = re.sub(self.STRING_BINOP_VARABLE_REG, a, value, count=1)
        return astroid.Const(lineno=string_f.lineno, col_offset=string_f.col_offset, 
                    parent=string_f.parent, value=value)

    
    def safe_infer(self, node, context=None):
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
            inferred_types.add(self._get_python_type_of_node(value))

        try:
            for inferred in infer_gen:
                inferred_type = self._get_python_type_of_node(inferred)
                if inferred_type not in inferred_types:
                    return None  # If there is ambiguity on the inferred node.
        except astroid.InferenceError:
            return None  # There is some kind of ambiguity
        except StopIteration:
            return value
        return value if len(inferred_types) <= 1 else None

    def _get_python_type_of_node(self, node):
        pytype = getattr(node, "pytype", None)
        if callable(pytype):
            return pytype()
        return None
        

def get_ast(filepath):

    MANAGER = astroid.MANAGER
    try:
        ast = MANAGER.ast_from_file(filepath, source=True)
    except Exception as ex:  # pylint: disable=broad-except
        return None
    return ast



if __name__ == "__main__":

    path = "./tt.py"
    lr = LogRetrieverPyAST()
    ast = get_ast(path)
    lr.walk(ast)
    print(lr.result['log_message'])
    








