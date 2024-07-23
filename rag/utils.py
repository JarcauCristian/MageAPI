import os
import logging
from pathlib import Path
from rag.ingester import Ingester


def clean_files(directory: str) -> None:
    for path in Path(directory).rglob("*.py"):
        print(f"Cleaning {path.name}")
        with open(path, 'r') as f:
            res = ""
            lines = f.readlines()
            for line in lines:
                if "{%" in line or '{{' in line:
                    continue

                res += line

            with open(path, 'w') as w:
                w.write(res)


def add_loaders(directory: str, ingester: Ingester) -> None:
    etl_loader_descriptions = {
        "default.py": "Default loader block which can be shaped in any way by",
        "api.py": "Template for loading data from an API, using requests to fetch data and returning it as a pandas DataFrame.",
        "file.py": "Template for loading data from the filesystem, either from a single file or multiple file directories, using Mage's FileIO.",
        "bigquery.py": "Template for loading data from a BigQuery warehouse, with configuration settings specified in 'io_config.yaml'.",
        "chroma.py": "Template for loading data from Chroma, specifying query embeddings and texts to retrieve results.",
        "druid.py": "Template for loading data from a Druid warehouse, with configuration settings specified in 'io_config.yaml'.",
        "duckdb.py": "Template for loading data from a DuckDB database, with configuration settings specified in 'io_config.yaml'.",
        "google_cloud_storage.py": "Template for loading data from a Google Cloud Storage bucket, with configuration settings specified in 'io_config.yaml'.",
        "google_sheets.py": "Template for loading data from a Google Sheets worksheet, with configuration settings specified in 'io_config.yaml'.",
        "azure_blob_storage.py": "Template for loading data from Azure Blob Storage, with configuration settings specified in 'io_config.yaml'.",
        "mssql.py": "Template for loading data from a MSSQL database, with configuration settings specified in 'io_config.yaml'.",
        "mysql.py": "Loader block for loading data from a table present in a MySQL database, with configuration settings specified by the user.",
        "oracledb.py": "Template for loading data from an OracleDB database, with configuration settings specified in 'io_config.yaml'.",
        "pinot.py": "Template for loading data from a Pinot warehouse, with configuration settings specified in 'io_config.yaml'.",
        "postgres.py": "Loader block for loading data from a table present in a PostgreSQL database, with configuration settings specified by the user.",
        "qdrant.py": "Template for loading data from Qdrant, using SentenceTransformer for query vector generation.",
        "redshift.py": "Template for loading data from a Redshift cluster, with configuration settings specified in 'io_config.yaml'.",
        "s3.py": "Template for loading data from an S3 bucket, with configuration settings specified in 'io_config.yaml'.",
        "snowflake.py": "Template for loading data from a Snowflake warehouse, with configuration settings specified in 'io_config.yaml'.",
        "mongodb.py": "Template for loading data from MongoDB, with configuration settings specified in 'io_config.yaml'.",
        "weaviate.py": "Template for loading data from Weaviate, specifying properties, collection, query text, and limit."
    }

    for path in Path(directory).rglob("*.py"):
        print("Creating embeddings for %s" % path.name)
        logging.info("Creating embeddings for %s" % path.name)
        with open(path, "r") as f:
            file_content = f.read()
            ingester.ingest(file_content, path.name, "loader", etl_loader_descriptions[path.name], os.getenv("CHROMA_COLLECTION"))


def add_transformers(directory: str, ingester: Ingester) -> None:
    transformer_descriptions = {
        "01_impute_missing_values.py": "Impute missing values in the data by filling them with zeros.",
        "02_remove_columns_with_missing_values.py": "Remove columns with a high percentage of missing values, based on a specified threshold.",
        "03_remove_rows_with_missing_values.py": "Remove rows with a high percentage of missing values, based on a specified threshold.",
        "04_fill_missing_values_with_median.py": "Fill missing values in numeric columns with the median value of each column.",
        "05_remove_outliers.py": "Remove outliers from the data using the IQR method.",
        "06_normalize_numeric_columns.py": "Normalize numeric columns by subtracting the mean and dividing by the standard deviation.",
        "07_aggregate_data.py": "Aggregate data by a specified column, computing the mean of other columns.",
        "08_drop_duplicate_rows.py": "Drop duplicate rows from the data.",
        "09_one_hot_encode.py": "Perform one-hot encoding on categorical columns, dropping the first level to avoid multicollinearity.",
        "10_rename_columns_to_lowercase.py": "Rename all columns in the data to lowercase.",
        "default.py": "Template code for a transformer block, specifying transformation logic and returning any type of data.",
        "max.py": "Execute a transformer action to calculate the maximum value in specified columns, optionally grouping by other columns."
    }

    for path in Path(directory).rglob("*.py"):
        print("Creating embeddings for %s" % path.name)
        logging.info("Creating embeddings for %s" % path.name)

        with open(path, "r") as f:
            file_content = f.read()

        ingester.ingest(file_content, path.name, "transformer", transformer_descriptions[path.name],
                        os.getenv("CHROMA_COLLECTION"))


def add_exporters(directory: str, ingester: Ingester) -> None:
    exporter_descriptions = {
        "duckdb.py": "Template for exporting data to a DuckDB database, with configuration settings specified in 'io_config.yaml'.",
        "file.py": "Template for exporting data to the filesystem using Mage's FileIO.",
        "google_cloud_storage.py": "Template for exporting data to a Google Cloud Storage bucket, with configuration settings specified in 'io_config.yaml'.",
        "google_sheets.py": "Template for exporting data to a worksheet in a Google Sheet, with configuration settings specified in 'io_config.yaml'.",
        "mongodb.py": "Template for exporting data to MongoDB, with configuration settings specified in 'io_config.yaml'.",
        "algolia.py": "Template for exporting data to an Algolia index, with configuration settings specified in 'io_config.yaml'.",
        "azure_blob_storage.py": "Template for exporting data to Azure Blob Storage, with configuration settings specified in 'io_config.yaml'.",
        "bigquery.py": "Template for exporting data to a BigQuery warehouse, with configuration settings specified in 'io_config.yaml'.",
        "chroma.py": "Template for exporting data to Chroma, with configuration settings specified in 'io_config.yaml'.",
        "default.py": "Template code for exporting data to any source, specifying data exporting logic.",
        "oracledb.py": "Template for exporting data to OracleDB, with configuration settings specified in 'io_config.yaml'.",
        "postgres.py": "Template for exporting data to PostgreSQL, with configuration settings specified in 'io_config.yaml'.",
        "qdrant.py": "Template for exporting data to Qdrant, with configuration settings specified in 'io_config.yaml'.",
        "redshift.py": "Template for exporting data to a Redshift cluster, with configuration settings specified in 'io_config.yaml'.",
        "s3.py": "Template for exporting data to an S3 bucket, with configuration settings specified in 'io_config.yaml'.",
        "snowflake.py": "Template for exporting data to a Snowflake warehouse, with configuration settings specified in 'io_config.yaml'.",
        "weaviate.py": "Template for exporting data to Weaviate, with configuration settings specified in 'io_config.yaml'.",
        "mssql.py": "Template for exporting data to MSSQL, with configuration settings specified in 'io_config.yaml'.",
        "mysql.py": "Template for exporting data to MySQL, with configuration settings specified in 'io_config.yaml'."
    }

    for path in Path(directory).rglob("*.py"):
        print("Creating embeddings for %s" % path.name)
        logging.info("Creating embeddings for %s" % path.name)

        with open(path, "r") as f:
            file_content = f.read()

        ingester.ingest(file_content, path.name, "exporter", exporter_descriptions[path.name],
                        os.getenv("CHROMA_COLLECTION"))


def add_configs(directory: str, ingester: Ingester) -> None:
    for path in Path(directory).rglob("*.yaml"):
        print("Creating embeddings for %s" % path.name)
        logging.info("Creating embeddings for %s" % path.name)

        with open(path, "r") as f:
            file_content = f.read()

        ingester.ingest(file_content, path.name, "config", "Config file containing connections to various data loaders.",
                        os.getenv("CHROMA_COLLECTION"))


def preprocess_yaml_string(yaml_string: str) -> str:
    lines = yaml_string.split('\n')
    processed_lines = []
    found = False
    count = 0
    for i, line in enumerate(lines):
        if count == 2 and i < len(lines):
            break
        if "`" in line:
            count += 1
            found = True
            continue

        if not found:
            continue

        if "|" in line:
            processed_lines.append('  ' + line.strip())
        else:
            processed_lines.append('    ' + line)

    return '\n'.join(processed_lines)
