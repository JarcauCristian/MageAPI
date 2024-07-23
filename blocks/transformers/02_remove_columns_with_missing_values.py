if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@transformer
def remove_columns_with_missing_values(data, *args, **kwargs):
    threshold = 0.5 if kwargs.get('threshold') is not None else kwargs.get('threshold')
    return data.loc[:, data.isnull().mean() < threshold]

@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'
