import io
import os
import json
import yaml
import requests
from openai import OpenAI

from mage_ai.settings.repo import get_repo_path

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


@data_exporter
def export_data(data, *args, **kwargs):
    """
    Exports data to some source.

    Args:
        data: The output from the upstream parent block
        args: The output from any additional upstream blocks (if applicable)

    Output (optional):
        Optionally return any object and it'll be logged and
        displayed when inspecting the block run.
    """
    
    config_path = os.path.join(get_repo_path(), 'io_config.yaml')
    with open(config_path, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    minio_api = config["default"]["MINIO_API"]
    api_key = config["default"]["OPENAI"]
    neo4j_api = config["default"]["NEO4J_API"]

    test_prompt = {
        'column_name': 'Age',
        'content': [25,32,19,28,22,31,26,23,29,24,27,20,30,33,21,19,25,28,22,26]
    }

    client = OpenAI(api_key=api_key)

    columns_descriptions = {}

    for column in data.columns:
        prompt = {
            "column_name": column,
            "content": data[column][:20]
        }
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[{"role": "system", "content": "You are a helpful assistant that when given a column content and its name it returns the description for that column in a maximum of 6 words, by only using letters and numbers and not '."},
                      {"role": "user", "content": f"Given this column of data: {test_prompt['content']} and it's name: {test_prompt['column_name']}. Can you give me a description for this column?"},
                      {"role": "assistant", "content": "The age of a patient"},
                      {"role": "user", "content": f"Given this column of data: {prompt['content']} and it's name: {prompt['column_name']}. Can you give me a description for this column?"}]
        )

        columns_descriptions[column] = response.dict()['choices'][0]['message']['content']

    

    description = kwargs.get("description")
    category = kwargs.get("category")
    category_new = kwargs.get("category_new")

    final_category = str(category).lower() if category_new is None else str(category_new).lower()


    if category_new is not None:
        response = requests.post(f"{neo4j_api}/category/create?name={final_category}")
        if response.status_code == 201:
            print("Category Created Successfully!")
        else:
            print("Category Could Not Be Created!")

    name = kwargs.get("name")
    tags = {
        "description": description,
        "category": final_category
    }

    csv_data = data.to_csv(index=False)
    files = {
        'file': ('filename.csv', io.BytesIO(csv_data.encode('utf-8'))),
    }

    payload = {
        'name': name,
        'tags': json.dumps(tags),
        'temporary': 'false'
    }

    response = requests.put(f"{minio_api}/upload_free", files=files, data=payload)

    if response.status_code == 201:


        neo4j_payload = {
            "name": str(name.split("/")[-1]),
            "belongs_to": str(final_category),
            "url": str(response.json().get("location")),
            "tags": columns_descriptions
        }
        
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(f"{neo4j_api}/dataset/create", json=neo4j_payload, headers=headers)

        if response.status_code == 201:
            print("Dataset Created Successfully!")
        else:
            print("Dataset Could Not Be Created!")
    else:
        print("Error:", response.status_code, response.json())
