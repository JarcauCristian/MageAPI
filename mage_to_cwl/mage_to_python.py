import re
import ast
from typing import Optional, List


class MageToPythonTransformer(ast.NodeTransformer):
    def __init__(self, word: str, decorators: List[str]) -> None:
        self.word = word
        self.decorators = decorators
        self.collected_statements = []
        self.os_import_needed = True
        self.parent_stack = []

    def visit_Import(self, node: ast.Import) -> Optional[ast.Import]:
        node.names = [alias for alias in node.names if self.word not in alias.name]
        if not node.names:
            return None
        for alias in node.names:
            if alias.name == 'os':
                self.os_import_needed = False
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Optional[ast.ImportFrom]:
        if node.module and self.word in node.module:
            return None
        if node.module == 'os':
            self.os_import_needed = False
        return node

    def visit_If(self, node: ast.If) -> Optional[ast.stmt]:
        self.generic_visit(node)
        if not node.body:
            return None
        node.body = [stmt for stmt in node.body if not isinstance(stmt, (ast.Import, ast.ImportFrom)) or stmt.names]
        if not node.body:
            return None
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Optional[ast.FunctionDef]:
        if any(decorator.id == 'test' for decorator in node.decorator_list if isinstance(decorator, ast.Name)):
            return None

        if any(decorator.id in self.decorators for decorator in node.decorator_list if isinstance(decorator, ast.Name)):
            if len(node.body) > 0 and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
                node.body = node.body[1:]
            self.collected_statements.extend(node.body)
            return None
        return node


def remove_imports_with_word(code_string: str, word: str) -> str:
    tree = ast.parse(code_string)
    transformer = MageToPythonTransformer(word, ["data_loader", "transformer", "data_exporter", "sensor"])
    cleaned_tree = transformer.visit(tree)
    cleaned_tree = ast.fix_missing_locations(cleaned_tree)

    if_main_node = None
    for node in cleaned_tree.body:
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            if isinstance(node.test.left, ast.Name) and node.test.left.id == '__name__':
                if isinstance(node.test.comparators[0], ast.Constant) and node.test.comparators[0].value == '__main__':
                    if_main_node = node
                    break

    if not if_main_node:
        if_main_node = ast.If(
            test=ast.Compare(
                left=ast.Name(id='__name__', ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value='__main__')]
            ),
            body=[],
            orelse=[]
        )
        cleaned_tree.body.append(if_main_node)

    if_main_node.body.extend(transformer.collected_statements)

    # Add import os if needed
    if transformer.os_import_needed:
        os_import = ast.Import(names=[ast.alias(name='os', asname=None)])
        cleaned_tree.body.insert(0, os_import)

    cleaned_code = ast.unparse(cleaned_tree)
    return cleaned_code


def replace_code_patterns(code_str):
    env_vars = []
    kwargs_pattern = r'kwargs\.get\(([^)]+)\)'

    def kwargs_replacement(match):
        var_name = match.group(1).strip("'\"")
        upper_var_name = var_name.upper()
        env_vars.append(upper_var_name)
        return f"os.getenv('{upper_var_name}')"

    modified_code_str = re.sub(kwargs_pattern, kwargs_replacement, code_str)

    secret_name_pattern = r'secret_name\s*=\s*"password-" \+ os.getenv\(\'PIPELINE_NAME\'\)\s*'

    modified_code_str = re.sub(secret_name_pattern, '', modified_code_str)

    password_pattern = r'password\s*=\s*get_secret_value\(secret_name\)'

    def password_replacement(match):
        env_vars.append("PASSWORD")
        return 'password = os.getenv("PASSWORD")'

    modified_code_str = re.sub(password_pattern, password_replacement, modified_code_str)

    return modified_code_str, env_vars
