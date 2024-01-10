from sklearn.impute import SimpleImputer
import pandas as pd

if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

def is_numeric(column):
    try:
        pd.to_numeric(column)
        return True
    except ValueError:
        return False


@transformer
def transform(data, *args, **kwargs):
    """
    Template code for a transformer block.

    Add more parameters to this function if this block has multiple parent blocks.
    There should be one parameter for each output variable from each parent block.

    Args:
        data: The output from the upstream parent block
        args: The output from any additional upstream blocks (if applicable)

    Returns:
        Anything (e.g. data frame, dictionary, array, int, str, etc.)
    """
    strategy = "mean"
    if kwargs.get("strategy") is not None:
        strategy = kwargs.get("strategy")

    imputer = SimpleImputer(strategy=strategy)

    for column in data.columns:
        if not is_numeric(data[column]) or data[column].dtype.name == "bool":
            continue

        original_dtype = data[column].dtype

        data[column] = imputer.fit_transform([data[column].tolist()])[0]

        data[column] = data[column].astype(original_dtype)

    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
