import pandas as pd

if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

def generate_case_combinations(word):
        if not word:
            return [""]

        first_char = word[0]
        rest_of_word = word[1:]

        rest_combinations = generate_case_combinations(rest_of_word)

        combinations = []

        for rest_combination in rest_combinations:
            combinations.append(first_char.upper() + rest_combination)
            combinations.append(first_char.lower() + rest_combination)

        return combinations

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
    null_values = [*generate_case_combinations("Null"), *generate_case_combinations("Nan"), *generate_case_combinations("Na"), 0, 0.0]

    null_threshold = 0.7
    if kwargs.get("column_threshold") is not None:
        null_threshold = kwargs.get("column_threshold")

    if type(data) == pd.Dataframe:
        for column in list(data.columns):
            if (data[column].isin(null_values).sum() / len(data[column])) > null_threshold:
                data = data.drop(column, axis=1)

    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'