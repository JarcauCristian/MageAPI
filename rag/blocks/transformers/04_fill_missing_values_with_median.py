import numpy as np
if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@transformer
def fill_missing_values_with_median(data, *args, **kwargs):
    for col in data.select_dtypes(include=[np.number]).columns:
        data[col].fillna(data[col].median(), inplace=True)
    return data

@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'
