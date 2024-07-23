from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.postgres import Postgres
from os import path
import yaml
if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader

@data_loader
def load_iris_from_postgres(*args, **kwargs):
    query = "your PostgreSQL query"  # SQL query to select all rows from the 'iris' table
    config_path = path.join(get_repo_path(), 'io_config.yaml')
    config_profile = "default"

    with open(config_path, 'r') as config:
        loaded_config = yaml.safe_load(config.read())
        loaded_config["default"]["POSTGRES_USER"] = "username"
        loaded_config["default"]["POSTGRES_PASSWORD"] = "password"
        loaded_config["default"]["POSTGRES_HOST"] = "host"
        loaded_config["default"]["POSTGRES_PORT"] = 5432
        loaded_config["default"]["POSTGRES_DBNAME"] = "database_name"
        loaded_config["default"]["POSTGRES_SCHEMA"] = "public"

    with open(config_path, 'w') as config:
        config.write(yaml.safe_dump(loaded_config))

    with Postgres.with_config(ConfigFileLoader(config_path, config_profile)) as loader:
        return loader.load(query)