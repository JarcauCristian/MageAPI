if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@transformer
def drop_duplicate_rows(data, *args, **kwargs):
    return data.drop_duplicates()

@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'
