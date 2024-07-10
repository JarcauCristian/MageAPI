from mage_to_python import remove_imports_with_word, replace_code_patterns
from pathlib import Path
import tempfile
import autopep8
import black
import os


class MageToPython:
    def __init__(self, code_string: str):
        """
        Initializer function for MageToPython class.
        :param code_string: The string that contains the Mage AI formatted Python code .
        """
        self.code_string = code_string
        self.env_vars = None

    def _format_code_autopep8(self):
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

            finally:
                os.remove(tmp_file_path)

    def _format_code_black(self):
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

            finally:
                os.remove(tmp_file_path)

    def _remove_mage_imports(self):
        self.code_string, self.env_vars = replace_code_patterns(self.code_string)
        self.code_string = remove_imports_with_word(self.code_string, "mage_ai")

    def mage_to_python(self):
        self._remove_mage_imports()
        self._format_code_autopep8()
        self._format_code_black()


string = """
# Variables {"username":{"type":"str","description":"The username for the user to login inside the database.","regex":"^.*$"},"password":{"type":"secret","description":"The password for the user to login inside the database."},"host":{"type":"str","description":"The host address where the database resides.","regex":"^((25[0-5]|(2[0-4]|1\\d|[1-9]|)\\d)\\.?\\b){4}$"},"port":{"type":"int","description":"The port on which the database runs.","range":[0,65535]},"database":{"type":"str","description":"The name of the database.","regex":"^.*$"},"collection":{"type":"str","description":"The name of the collection to load data from.","regex":"^.*$"}}

import pandas as pd
from pymongo import MongoClient
from mage_ai.data_preparation.shared.secrets import get_secret_value

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test
    
def some_other_function():
    print("Here!")

@data_loader
def load_data_mongodb(*args, **kwargs):
    \"""
    Template code for loading data from a MongoDB database.

    Args:
    - kwargs should include 'username', 'password', 'host', 'port', 'database', and 'table'.

    Returns:
        pandas.DataFrame - Data loaded from the specified MongoDB collection.
    \"""

    username = kwargs.get('username')
    host = kwargs.get('host')
    port = kwargs.get('port')
    database = kwargs.get('database')
    collection = kwargs.get('collection')

    secret_name = "password-" + kwargs.get("PIPELINE_NAME")

    password = get_secret_value(secret_name)

    if None in [username, password, host, port, database, collection]:
        raise ValueError("All connection parameters (username, password, host, port, database, collection) must be provided.")

    connection_string = f"mongodb://{username}:{password}@{host}:{port}/{database}"

    client = MongoClient(connection_string)
    db = client[database]
    collection = db[collection]

    df = pd.DataFrame(list(collection.find()))

    return df

@test
def test_output(output, *args) -> None:
    \"""
    Template code for testing the output of the block.
    \"""
    assert output is not None, 'The output is undefined'
    assert isinstance(output, pd.DataFrame), 'Output is not a DataFrame'

"""
mtp = MageToPython(string)
mtp.mage_to_python()
print(mtp.code_string, mtp.env_vars)
