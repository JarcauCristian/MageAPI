from mage_to_cwl.mage_to_python_utils import remove_imports_with_word, replace_code_patterns
from pathlib import Path
import tempfile
import autopep8
import black
import os


class MageToPython:
    def __init__(self, code_string: str, block_name: str, repo_name: str, previous_block_name: str = None) -> None:
        """
        Initializer function for MageToPython class.
        :param code_string: The string that contains the Mage AI formatted Python code .
        """
        self.code_string = code_string
        self.env_vars = None
        self.block_name = block_name
        self.previous_block_name = previous_block_name
        self.repo_name = repo_name

    def _format_code_autopep8(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_file:
            tmp_file_path = tmp_file.name
            tmp_file.write(self.code_string.encode())
            tmp_file.close()

            try:
                formatted_code = autopep8.fix_file(tmp_file_path)
                with open(tmp_file_path, 'w') as file:
                    file.write(formatted_code)

                with open(tmp_file_path, 'r') as file:
                    formatted_code = file.read()

                self.code_string = formatted_code
            except Exception as _:
                return
            finally:
                os.remove(tmp_file_path)

    def _format_code_black(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_file:
            tmp_file_path = tmp_file.name
            tmp_file.write(self.code_string.encode())
            tmp_file.close()

            try:
                black.format_file_in_place(
                    Path(tmp_file_path), fast=False, mode=black.FileMode(), write_back=black.WriteBack.YES
                )

                with open(tmp_file_path, 'r') as file:
                    formatted_code = file.read()

                self.code_string = formatted_code
            except Exception as _:
                return
            finally:
                os.remove(tmp_file_path)

    def _remove_mage_imports(self) -> None:
        self.code_string, self.env_vars = replace_code_patterns(self.code_string, repo_name=self.repo_name)
        self.code_string, env_vars = remove_imports_with_word(self.code_string, "mage_ai", self.block_name, self.previous_block_name)
        self.env_vars = self.env_vars + env_vars

    def mage_to_python(self) -> None:
        self._remove_mage_imports()
        self._format_code_autopep8()
        self._format_code_black()

    def __str__(self):
        return f"MageToPython(code_string={self.code_string}, env_vars={self.env_vars})"

    def __repr__(self):
        return f"MageToPython(code_string={self.code_string}, env_vars={self.env_vars})"
