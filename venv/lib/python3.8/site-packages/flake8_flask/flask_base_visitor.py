import ast
from r2c_py_ast.dumb_scope_visitor import DumbScopeVisitor


class FlaskBaseVisitor(DumbScopeVisitor):
    def __init__(self):
        super(FlaskBaseVisitor, self).__init__("flask")

    def _get_function_name(self, call_node):
        func = call_node.func
        if isinstance(func, ast.Attribute):
            return func.attr
        elif isinstance(func, ast.Name):
            return func.id
