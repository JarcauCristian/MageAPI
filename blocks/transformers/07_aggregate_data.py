
if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@transformer
def aggregate_data(data, *args, **kwargs):
    by =  None if kwargs.get('aggregate_by') is None else kwargs.get('aggregate_by')
    if by in data.columns:
        return data.groupby(by).mean().reset_index()
    return data

@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'
