import ast
import logging
import sys
from typing import List, Set

from flake8_flask.constants import MODULE_NAME
from flake8_flask.flask_base_visitor import FlaskBaseVisitor

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stderr)
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)


FXN_NAME: str = "render_template"
escaped_extensions: Set[str] = {"html", "htm", "xml", "xhtml"}
escape_function_names: Set[str] = {"escape"}

class UnescapedTemplateFileExtensionsVisitor(FlaskBaseVisitor):
    def __init__(self):
        super(UnescapedTemplateFileExtensionsVisitor, self).__init__()

    name = "r2c-flask-unescaped-file-extension"

    def _get_template_extension(self, template_name: str) -> str:
        if not template_name: return ""
        splits: List[str] = template_name.split(".")
        extension: str = ".".join(splits[1:]) if len(splits) > 1 else ""
        return extension

    def _has_escaped_extension(self, template_name: str) -> bool:
        extension: str = self._get_template_extension(template_name)
        if extension in escaped_extensions:
            return True
        return False

    def _has_escaped_extension_substring(self, template_name: str) -> bool:
        extension: str = self._get_template_extension(template_name)
        return any([ext in extension for ext in escaped_extensions])

    def _resolve_to_possible_values(self, node) -> List[str]:
        if isinstance(node, ast.Str):
            return [node.s]
        elif isinstance(node, ast.Name):
            return self._get_possible_symbol_values(node.id)
        else:
            return ""

    def _is_kwarg_escaped(self, keyword) -> bool:
        if not isinstance(keyword.value, ast.Call):
            return False
        fxn = keyword.value.func
        if isinstance(fxn, ast.Attribute):
            return fxn.attr in escape_function_names
        elif isinstance(fxn, ast.Name):
            return fxn.id in escape_function_names

    def visit_Call(self, call_node: ast.Call):
        # Is this flask.render_template?
        if not self.is_node_method_alias_of(call_node, FXN_NAME, MODULE_NAME):
            logger.debug(f"This call is not {FXN_NAME}")
            return

        # Check if the possible values aren't an autoescape extension
        logger.debug(ast.dump(call_node))
        arg0 = call_node.args[0]
        possible_values = self._resolve_to_possible_values(arg0)
        logger.debug(possible_values)
        if all([self._has_escaped_extension(value) for value in possible_values]):
            logger.debug(
                "Template has an escaped extension; template will be autoescaped"
            )
            return

        # If not autoescaped, check for escaped vars
        if all([self._is_kwarg_escaped(kw) for kw in call_node.keywords]):
            logger.debug("All context variables are escaped.")
            return

        logger.debug(f"Found this node: {ast.dump(call_node)}")
        extensions = set(
            [self._get_template_extension(value) for value in possible_values]
        )
        extensions_to_go_in_message = extensions - escaped_extensions

        safe_extensions_substring_message = f"{self.name} Make sure to change your file extension from {str(extensions_to_go_in_message)} to .html, .htm, .xml, or .xhtml for Flask to autoescape, or check that your variables are escaped using `flask.Markup.escape`."
        unsafe_extensions_message = f"{self.name} Flask does not automatically escape Jinja templates unless they have .html, .htm, .xml, or .xhtml extensions. This could lead to XSS attacks."

        # Check if extension is close to autoescaped extensions
        report_message = safe_extensions_substring_message if any([self._has_escaped_extension_substring (value) for value in possible_values]) else unsafe_extensions_message

        self.report_nodes.append(
            {
                "node": call_node,
                "message": report_message,
            }
        )
