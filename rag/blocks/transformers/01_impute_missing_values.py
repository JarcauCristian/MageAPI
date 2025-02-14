if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@transformer
def impute_missing_values(data, *args, **kwargs):
    data.fillna(0, inplace=True)
    return data

@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'
