from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.mysql import MySQL
from os import path
import yaml
if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader

@data_loader
def load_data_from_mysql(*args, **kwargs):
    """
    Template for loading data from a MySQL database.
    Specify your configuration settings in 'io_config.yaml'.

    Docs: https://docs.mage.ai/design/data-loading#mysql
    """
    query = 'Your MySQL query'  # Specify your SQL query here
    config_path = path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'

    with open(config_path, 'r') as config:
        loaded_config = yaml.safe_load(config.read())
        loaded_config["default"]["MYSQL_DATABASE"] = "database"
        loaded_config["default"]["MYSQL_HOST"] = "host"
        loaded_config["default"]["MYSQL_PASSWORD"] = "password"
        loaded_config["default"]["MYSQL_USERNAME"] = "username"
        loaded_config["default"]["MYSQL_PORT"] = 3306

    with open(config_path, 'w') as config:
        config.write(yaml.safe_dump(loaded_config))

    with MySQL.with_config(ConfigFileLoader(config_path, config_profile)) as loader:
        return loader.load(query)
