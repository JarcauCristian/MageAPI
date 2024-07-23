
import pandas as pd
if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@transformer
def one_hot_encode(data, *args, **kwargs):
    return pd.get_dummies(data, drop_first=True)

@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'
