import re
import ast
import pickle
from typing import Optional, List


def is_picklable(obj):
    try:
        pickle.dumps(obj)
        return True
    except TypeError:
        return False


class RemoveUnusedCode(ast.NodeTransformer):
    def __init__(self):
        self.used_names = set()
        self.defined_names = set()
        self.scope_stack = []

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and self.scope_stack:
            self.scope_stack[-1].add(node.id)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.defined_names.add(node.name)

        self.scope_stack.append(set())
        self.generic_visit(node)
        used_names = self.scope_stack.pop()

        node.body = [stmt for stmt in node.body if not isinstance(stmt, ast.Assign) or 
                     any(target.id in used_names for target in stmt.targets if isinstance(target, ast.Name))]

        return node if node.name in self.used_names or self.scope_stack else None

    def visit_ClassDef(self, node: ast.ClassDef):
        self.defined_names.add(node.name)

        self.scope_stack.append(set())
        self.generic_visit(node)
        used_names = self.scope_stack.pop()

        node.body = [stmt for stmt in node.body if not isinstance(stmt, ast.FunctionDef) or stmt.name in used_names]

        return node if node.name in self.used_names or self.scope_stack else None

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id not in self.defined_names:
            return None
        self.generic_visit(node)
        return node

    def visit_With(self, node: ast.With):
        for item in node.items:
            if hasattr(item, 'context'):
                self.visit(item.context)
        self.generic_visit(node)
        return node

    def visit_Import(self, node: ast.Import):
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom):
        return node

    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.targets[0], ast.Name):
            if self.scope_stack and node.targets[0].id not in self.scope_stack[-1]:
                return None
        return node

    def remove_unused_code(self, code_string: str) -> str:
        tree = ast.parse(code_string)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                self.defined_names.add(node.name)
            self.visit(node)

        tree = self.visit(tree)
        tree = ast.fix_missing_locations(tree)

        cleaned_code = ast.unparse(tree)
        return cleaned_code
    

class MageToPythonTransformer(ast.NodeTransformer):
    def __init__(self, word: str, decorators: List[str], block_name: str, previous_block_name: str) -> None:
        self.word = word
        self.decorators = decorators
        self.collected_statements = []
        self.os_import_needed = True
        self.argparse_import_needed = True
        self.parent_stack = []
        self.first_arg_statements = []
        self.block_name = block_name
        self.previous_block_name = previous_block_name
        self.pandas_import_needed = True
        self.env_vars = []

    def visit_Import(self, node: ast.Import) -> Optional[ast.Import]:
        node.names = [alias for alias in node.names if self.word not in alias.name]
        if not node.names:
            return None
        for alias in node.names:
            if alias.name == 'os':
                self.os_import_needed = False
            if alias.name == 'argparse':
                self.argparse_import_needed = False
            if alias.name == 'pandas' or alias.asname == 'pd':
                self.pandas_import_needed = False
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Optional[ast.ImportFrom]:
        if node.module and self.word in node.module:
            return None
        if node.module == 'os':
            self.os_import_needed = False
        if node.module == 'argparse':
            self.argparse_import_needed = False
        if node.module == 'pandas':
            self.pandas_import_needed = False
        return node

    def visit_If(self, node: ast.If) -> Optional[ast.stmt]:
        self.generic_visit(node)
        if not node.body:
            return None
        node.body = [stmt for stmt in node.body if not isinstance(stmt, (ast.Import, ast.ImportFrom)) or stmt.names]
        if not node.body:
            return None
        return node

    def visit_With(self, node: ast.With):
        for item in node.items:
            if hasattr(item, 'context'):
                self.visit(item.context)
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Optional[ast.FunctionDef]:
        if any(decorator.id == 'test' for decorator in node.decorator_list if isinstance(decorator, ast.Name)):
            return None

        if any(decorator.id in self.decorators for decorator in node.decorator_list if
               isinstance(decorator, ast.Name)):
            if len(node.body) > 0 and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value,
                                                                                        ast.Str):
                node.body = node.body[1:]

            if any(decorator.id == 'data_exporter' for decorator in node.decorator_list if isinstance(decorator, ast.Name)):
                function_name = "final_output"
                write_to_file_code = f"""
def is_picklable(obj):
    try:
        pickle.dumps(obj)
        return True
    except:
        return False
        
output_file = "{function_name}"
if output_file:
    import pickle
    import matplotlib.pyplot as plt
    import types
    from inspect import currentframe
    frame = currentframe()
    variables = {{k: v for k, v in frame.f_locals.copy().items() if is_picklable(v) and (not isinstance(v, types.FunctionType) or isinstance(v, types.MethodType) or isinstance(v, types.ModuleType))}}
    with open(output_file, 'wb') as file:
        pickle.dump(variables, file)
"""
                write_to_file_ast = ast.parse(write_to_file_code).body
                node.body[-1:] = write_to_file_ast
                self.collected_statements.extend(node.body)
            else:
                for i, stmt in enumerate(node.body):
                    if isinstance(stmt, ast.Return):
                        return_var = stmt.value
                        function_name = self.block_name.upper() + '_OUTPUT_FILE'
                        self.env_vars.append(function_name)
                        write_to_file_code = f"""
output_file = os.getenv("{function_name}")
if output_file:
    with open(output_file, 'wb') as file:
        import pickle
        pickle.dump({ast.unparse(return_var)}, file)
"""
                        write_to_file_ast = ast.parse(write_to_file_code).body
                        node.body[i:i + 1] = write_to_file_ast
                        if isinstance(return_var, ast.Attribute) and return_var.attr == 'DataFrame':
                            self.pandas_import_needed = True
                self.collected_statements.extend(node.body)

            if len(node.args.args) > 0 and node.args.args[0].arg != '*args':
                first_arg = node.args.args[0].arg
                read_file_code = f"""
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('filename')
args = parser.parse_args()

{first_arg} = None
if args.filename:
    with open(args.filename, 'rb') as file:
        import pickle
        {first_arg} = pickle.load(file)
"""
                self.first_arg_statements.append(ast.parse(read_file_code).body)
            return None
        return node


def remove_imports_with_word(code_string: str, word: str, block_name: str, previous_block_name: str) -> (str, list[str], str):
    tree = ast.parse(code_string)
    transformer = MageToPythonTransformer(word, ["data_loader", "transformer", "data_exporter", "sensor", "custom"],
                                          block_name=block_name, previous_block_name=previous_block_name)
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

    if_main_node.body = transformer.first_arg_statements + if_main_node.body
    if_main_node.body.extend(transformer.collected_statements)

    if transformer.os_import_needed:
        os_import = ast.Import(names=[ast.alias(name='os', asname=None)])
        cleaned_tree.body.insert(0, os_import)

    if transformer.pandas_import_needed:
        pandas_import = ast.Import(names=[ast.alias(name='pandas as pd', asname=None)])
        cleaned_tree.body.insert(1, pandas_import)

    cleaned_code = ast.unparse(cleaned_tree)
    cleaner = RemoveUnusedCode()
    cleaned_code = cleaner.remove_unused_code(cleaned_code)
    return cleaned_code, transformer.env_vars


def replace_code_patterns(code_str, repo_name: str):
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

    repo_pattern = rf'\b{repo_name}\.+'

    modified_code_str = re.sub(repo_pattern, "", modified_code_str)

    return modified_code_str, env_vars
