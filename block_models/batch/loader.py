import pandas as pd
import requests
import io

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data(*args, **kwargs):
    """
    Template code for loading data from any source.

    Returns:
        Anything (e.g. data frame, dictionary, array, int, str, etc.)
    """
    if kwargs.get("initial_name") is None:
        return {}

    name = kwargs.get("initial_name")

    response = requests.get(f"http://62.72.21.79:10000/get_object?dataset_path=temp/{name}&forever=false")

    if response.status_code != 200:
        return {}
    
    next_response = requests.get(response.json()["url"])

    if next_response.status_code == 200:
        content = next_response.content.decode('utf-8')

    return pd.read_csv(io.StringIO(content))


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
