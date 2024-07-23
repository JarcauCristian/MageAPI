import numpy as np
if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@transformer
def normalize_numeric_columns(data, *args, **kwargs):    
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    data[numeric_cols] = (data[numeric_cols] - data[numeric_cols].mean()) / data[numeric_cols].std()
    return data

@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'
