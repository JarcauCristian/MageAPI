from pathlib import Path
import subprocess
import autoimport
import tempfile
import black
import ast
import os


class Linter:
    def __init__(self, alias_dict: dict[str, str]) -> None:
        self.alias_dict = alias_dict

    def __find_missing_imports(self, code: str) -> set[str]:
        tree = ast.parse(code)
        missing_imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if node.id in self.alias_dict:
                    missing_imports.add(f"import {self.alias_dict[node.id]} as {node.id}")

        return missing_imports

    @staticmethod
    def __fix_code(code: str) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_file:
            tmp_file_path = tmp_file.name
            tmp_file.write(code.encode())
            tmp_file.close()

            try:
                black.format_file_in_place(
                    Path(tmp_file_path), fast=False, mode=black.FileMode(), write_back=black.WriteBack.YES
                )

                with open(tmp_file_path, 'r') as file:
                    formatted_code = file.read()

                code = formatted_code
                return code
            finally:
                os.remove(tmp_file_path)
                return code

    @staticmethod
    def __add_imports(code: str):
        code = autoimport.fix_code(code)
        return code

    @staticmethod
    def __remove_dangling_ifs(code: str) -> str:
        lines = code.split('\n')
        clean_lines = []
        skip_next = False

        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue

            stripped_line = line.strip()
            if stripped_line.startswith('if ') and stripped_line.endswith(':'):
                if i + 1 >= len(lines) or lines[i + 1].strip() == '':
                    skip_next = True
                    continue

            clean_lines.append(line)

        return '\n'.join(clean_lines)

    def process(self, code: str) -> str:
        missing_imports = self.__find_missing_imports(code)
        import_lines = '\n'.join(missing_imports)
        code = f"{import_lines}\n\n{code}"

        code = self.__add_imports(code)
        code = self.__fix_code(code)
        code = self.__remove_dangling_ifs(code)

        return code
