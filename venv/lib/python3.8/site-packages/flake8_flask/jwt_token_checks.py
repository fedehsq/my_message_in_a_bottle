import ast
import logging
import sys
from typing import List, Tuple, Any, Dict

from flake8_flask.flask_base_visitor import FlaskBaseVisitor

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stderr)
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)

SUPPORTED_JWT_MODULES = ["flask_jwt", "flask_jwt_simple", "flask_jwt_extended"]
SUPPORTED_JWT_DECORATORS = ["jwt_required", "jwt_optional", "fresh_jwt_required", "jwt_refresh_token_required"]
SUPPORTED_JWT_CALLS = ["JWT", "get_jwt_identity", "get_current_user", "create_refresh_token", "create_access_token", "set_access_cookies", "get_jwt_claims", "verify_jwt_in_request", "current_identity", "decode_token", "JWTManager"]

class JWTTokenChecksVisitor(FlaskBaseVisitor):
    name = "r2c-flask-missing-jwt-token"

    jwt_token_message = f"{name} This file has `flask_jwt`, `flask_jwt_extended`, or `flask_jwt_simple` imported, but no authentication protection with `@jwt_required` or `@jwt_optional`. This means JWT tokens aren't being checked for access to your API routes, which may be a security oversight."

    reported = False

    def __init__(self):
        super(JWTTokenChecksVisitor, self).__init__()

    def _is_jwt_decorator_present(self, node: ast.FunctionDef) -> bool:
        name_list = []

        for decorator in node.decorator_list:
            d = decorator.func if isinstance(decorator, ast.Call) else decorator
            name_list.append(d.attr if isinstance(d, ast.Attribute) else d.id)

        return any([name == decorator for name in name_list for decorator in SUPPORTED_JWT_DECORATORS])

    def _remove_message(self) -> None:
        for node in self.report_nodes:
            if node['message'] == self.jwt_token_message:
                self.report_nodes.remove(node)
                return

    def _is_decorator_assignment(self, assign_node: ast.Assign) -> bool:
        if not isinstance(assign_node, ast.Assign):
            logger.debug("Is not ast.Assign, don't care. Move on")
            return False

        def check_assign_target(target: Any) -> bool:
            if not isinstance(target, ast.Name):
                logger.debug("Not a Name node. Moving on")
                return False
            
            if target.id == "decorators":
                logger.debug("Found a class property assignment to 'decorators'")
                return True

        return any([check_assign_target(target) for target in assign_node.targets])

    def _get_decorators(self, node: ast.Assign) -> List[str]:
        if not (isinstance(node.value, ast.List) or isinstance(node.value, ast.Tuple)):
            return []

        try:
            decorators = [e.id for e in node.value.elts if isinstance(e, ast.Name)]
        except Exception:
            logger.warning("Could not read decorator assigned to 'decorators' class attribute.")
            return []

        return decorators

    def _propogate_class_decorators(self, node: ast.ClassDef, decorators: List[str]) -> None:
        def add_class_decorator(node: ast.FunctionDef, decorators: List[str]) -> None:
            node.decorator_list += [ast.Call(func=ast.Name(ctx="Load", id=decorator)) for decorator in decorators]

        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                add_class_decorator(child, decorators)

    def generic_visit(self, node: ast.AST) -> None:
        ast.NodeVisitor.generic_visit(self, node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if not any([self.is_imported(i) for i in SUPPORTED_JWT_MODULES]): return

        # I should be checking if this inherits from View or MethodView,
        # but that's hard. So I'm erring on the side of more FPs than FNs,
        # which means only considering when the variable 'decorators' is assigned.
        # However, I'll at least check to see it inherits from SOMETHING.
        if len(node.bases) == 0:
            logger.debug("Class does not inherit. Won't matter. Moving on.")
            return

        # OK, this probably isn't a super good idea... the exisiting logic looks for
        # the presence of JWT stuff somewhere in the file. This makes it hard to integrate
        # a new visitor with visit_ClassDef because this behavior is very tightly coupled
        # to the existing visitor methods. Because I don't want to refactor right now, I'm
        # 'hacking' this by 'propogating' the decorators attribute down to the class function
        # definitions.
        for child in node.body:
            logger.debug("Checking for assignment to 'decorators'")
            logger.debug(ast.dump(child))
            if self._is_decorator_assignment(child):
                decorators = self._get_decorators(child)
                logger.debug(f"Propogating class decorators {decorators}")
                self._propogate_class_decorators(node, decorators)

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if not any([self.is_imported(i) for i in SUPPORTED_JWT_MODULES]): return

        if not self.reported:
            self.report_nodes.append(
                {
                    "node": node,
                    "message": self.jwt_token_message,
                }
            )
            self.reported = True
        
        if self._is_jwt_decorator_present(node):
            self._remove_message()
            return

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if not any([self.is_imported(i) for i in SUPPORTED_JWT_MODULES]): return

        if isinstance(node.func, ast.Attribute): 
            call = node.func.attr 
        elif isinstance(node.func, ast.Name):
            call = node.func.id 
        else:
            call = ""
        
        if call in SUPPORTED_JWT_CALLS:
            self.reported = True
            self._remove_message()
            return

        self.generic_visit(node)
