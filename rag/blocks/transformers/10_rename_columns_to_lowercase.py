if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@transformer
def rename_columns_to_lowercase(data, *args, **kwargs):
    data.columns = [col.lower() for col in data.columns]
    return data

@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'
