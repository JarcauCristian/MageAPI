import os
import json
import requests
import randomname


def create_temp_pipeline(token: str) -> str:
    url = f'{os.getenv("BASE_URL")}/api/pipelines'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
        'X-API-KEY': os.getenv("API_KEY")
    }

    name = randomname.get_name(sep="_")

    data = {
        "pipeline": {
            "name": name,
            "type": "python",
            "description": "not created"
        }
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(data))

    if response.status_code != 200 or response.json().get("error") is not None:
        return ""

    return name


def create_temp_pipeline_trigger(name: str, token: str) -> bool:
    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}/pipeline_schedules?api_key={os.getenv("API_KEY")}'
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = json.dumps({
        "pipeline_schedule": {
            "name": randomname.get_name(sep="_"),
            "schedule_type": "api",
            "status": "active"
        },
        "api_key": os.getenv("API_KEY")
    })

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code != 200 or response.json().get("error") is not None:
        return False

    return True


def run_temp_pipeline(name: str, token: str) -> bool:
    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}/pipeline_schedules?api_key={os.getenv("API_KEY")}'
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return False

    trigger_config = {
        "id": response.json()["pipeline_schedules"][0]["id"],
        "token": response.json()["pipeline_schedules"][0]["token"]
    }

    url = f"{os.getenv('BASE_URL')}/api/pipeline_schedules/{trigger_config['id']}/api_trigger"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {trigger_config['token']}"
    }

    response = requests.request("POST", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return False

    return True


def create_block(name: str, token: str, btype: str, content: str) -> bool:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}",
        "X-API-KEY": os.getenv("API_KEY")
    }

    bname = randomname.get_name(sep="_")
    if "transformer" in btype or "exporter" in btype:
        loader = randomname.get_name(sep="_")
        payload = {
            "block": {
                "name": loader,
                "language": "python",
                "type": "data_loader",
                "content": """
import pandas as pd

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data(*args, **kwargs):
    # Specify your data loading logic here

    return pd.DateFrame()
                """,
                "downstream_blocks": [bname],
                "upstream_blocks": []
            },
            "api-key": os.getenv("API_KEY")
        }

        response = requests.request("POST", url=f'{os.getenv("BASE_URL")}/api/pipelines/{name}/blocks?'
                                                f'api_key={os.getenv("API_KEY")}', headers=headers, json=payload)

        if response.status_code != 200 or response.json().get("error") is not None:
            return False

        payload = {
            "block": {
                "name": bname,
                "language": "python",
                "type": btype,
                "content": content,
                "downstream_blocks": [],
                "upstream_blocks": [loader]
            },
            "api-key": os.getenv("API_KEY")
        }

        response = requests.request("POST", url=f'{os.getenv("BASE_URL")}/api/pipelines/{name}/blocks?'
                                                f'api_key={os.getenv("API_KEY")}', headers=headers, json=payload)

        if response.status_code != 200 or response.json().get("error") is not None:
            return False
    else:
        payload = {
            "block": {
                "name": bname,
                "language": "python",
                "type": btype,
                "content": content,
                "downstream_blocks": [],
                "upstream_blocks": []
            },
            "api-key": os.getenv("API_KEY")
        }

        response = requests.request("POST", url=f'{os.getenv("BASE_URL")}/api/pipelines/{name}/blocks?'
                                                f'api_key={os.getenv("API_KEY")}', headers=headers, json=payload)

        if response.status_code != 200 or response.json().get("error") is not None:
            return False

    return True


def check_temp_pipeline_status(name: str, token: str) -> str:
    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}/pipeline_schedules?api_key={os.getenv("API_KEY")}'
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return ""

    trigger_id = response.json()["pipeline_schedules"][0]["id"]

    url = f'{os.getenv("BASE_URL")}/api/pipeline_schedules/{trigger_id}/pipeline_runs?api_key={os.getenv("API_KEY")}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return ""

    body = json.loads(response.content.decode('utf-8'))['pipeline_runs']

    if len(body) == 0:
        return ""

    return body[0]["status"]


def delete_temp_pipeline(name: str, token: str) -> bool:
    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}/pipeline_schedules?api_key={os.getenv("API_KEY")}'
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return False

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-API-KEY": os.getenv("API_KEY")
    }

    pipeline_schedule = response.json()["pipeline_schedules"][0]

    response = requests.request(
            "DELETE",
            f'{os.getenv("BASE_URL")}/api/pipeline_schedules/{pipeline_schedule["id"]}?api_key={os.getenv("API_KEY")}',
            headers=headers
        )

    if response.status_code != 200 or response.json().get("error") is not None:
        return False

    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}'

    response = requests.request("DELETE", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return False

    return True
