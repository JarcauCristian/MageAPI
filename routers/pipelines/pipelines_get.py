import io
import os
import re
import yaml
import json
import zipfile
import requests
import urllib.parse
from typing import Optional
from datetime import datetime
from dependencies import Token
from fastapi import APIRouter, HTTPException
from mage_to_cwl.mage_to_cwl import MageToCWL
from utils.pipelines import parse_pipeline, parse_pipelines
from starlette.responses import JSONResponse, StreamingResponse
from redis_cache.cache import get_data_from_redis, is_data_stale, set_data_in_redis, update_timestamp

router = APIRouter()

token = Token()


@router.get("/mage/pipeline/triggers", tags=["PIPELINES GET"])
async def pipeline_triggers(name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}/pipeline_schedules?api_key={os.getenv("API_KEY")}'
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail=response.json().get("error")["exception"])

    returns = {
        "id": response.json()["pipeline_schedules"][0]["id"],
        "token": response.json()["pipeline_schedules"][0]["token"]
    }

    return JSONResponse(status_code=200, content=returns)


@router.get("/mage/pipeline/status/streaming", tags=["PIPELINES GET"])
async def pipeline_streaming_status(pipeline_name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.token}",
    }

    url = f"{os.getenv('BASE_URL')}/api/pipeline_runs?pipeline_uuid={pipeline_name}&api_key={os.getenv('API_KEY')}"

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500,
                            detail=response.json().get("error")["exception"])

    return JSONResponse("active" if len(response.json()["pipeline_runs"]) != 0 else "inactive", status_code=200)


@router.get("/mage/pipeline/status/batch", tags=["PIPELINES GET"])
async def pipeline_batch_status(pipeline_id: int):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/pipeline_schedules/{pipeline_id}/pipeline_runs?api_key={os.getenv("API_KEY")}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token.token}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail=response.json().get("error")["exception"])

    body = json.loads(response.content.decode('utf-8'))['pipeline_runs']

    if len(body) == 0:
        raise HTTPException(status_code=500, detail="No runs yet!")

    return JSONResponse(status_code=200, content=body[0]["status"])


@router.get("/mage/pipelines", tags=["PIPELINES GET"])
async def pipelines(tag: Optional[str] = None):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    valid_tags = ["train", "data_preprocessing", "streaming"]

    if tag and tag not in valid_tags:
        raise HTTPException(status_code=400, detail="tag parameter should be train, data_preprocessing or streaming.")

    pipelines_url = os.getenv('BASE_URL') + f'/api/pipelines?api_key={os.getenv("API_KEY")}' if not tag else os.getenv('BASE_URL') + f'/api/pipelines?tag[]={tag}&api_key={os.getenv("API_KEY")}'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token.token}'
    }

    response = requests.get(pipelines_url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail=response.json().get("error")["exception"])

    names = []
    for pipe in response.json()["pipelines"]:
        if not tag:
            if len(pipe["tags"]) > 0:
                if pipe["tags"][0] not in valid_tags:
                    continue
            else:
                continue
        names.append(pipe.get("uuid"))

    return JSONResponse(status_code=200, content=names)


@router.get("/mage/pipelines/specific", tags=["PIPELINES GET"])
async def specific_pipelines(contains: str, changed: bool = False):
    cache_key = f"pipelines:{contains}"

    if changed:
        if token.check_token_expired():
            token.update_token()
        if token.token == "":
            return JSONResponse(status_code=500, content="Could not get the token!")

        url = f'{os.getenv("BASE_URL")}/api/pipelines?api_key={os.getenv("API_KEY")}'
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token.token}"
        }

        response = requests.request("GET", url, headers=headers)

        if response.status_code != 200 or response.json().get("error") is not None:
            raise HTTPException(status_code=500,
                                detail=response.json().get("error")["exception"])

        if len(response.json().get("pipelines")) == 0:
            return JSONResponse(status_code=200, content=[])

        pipes = []
        for pipeline in response.json().get("pipelines"):
            resp = requests.request("GET", f'{os.getenv("BASE_URL")}/api/pipelines/{pipeline.get("uuid")}?'
                                           f'api_key={os.getenv("API_KEY")}', headers=headers)

            if resp.status_code == 200:
                if resp.json().get("error") is None:
                    pipes.append(resp.json().get("pipeline"))

        pipes = parse_pipelines(pipes, contains)

        set_data_in_redis(cache_key, json.dumps(pipes), expire_time_seconds=60)

        update_timestamp(cache_key)

        return JSONResponse(status_code=200, content=pipes)

    cached_data = get_data_from_redis(cache_key)
    if cached_data and not is_data_stale(cache_key, expire_time_seconds=60):
        return JSONResponse(status_code=200, content=json.loads(cached_data.decode()))

    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/pipelines?api_key={os.getenv("API_KEY")}'
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.token}"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500,
                            detail=response.json().get("error")["exception"])

    if len(response.json().get("pipelines")) == 0:
        return JSONResponse(status_code=200, content=[])

    pipes = []
    for pipeline in response.json().get("pipelines"):
        resp = requests.request("GET", f'{os.getenv("BASE_URL")}/api/pipelines/{pipeline.get("uuid")}?'
                                       f'api_key={os.getenv("API_KEY")}', headers=headers)

        if resp.status_code == 200:
            if resp.json().get("error") is None:
                pipes.append(resp.json().get("pipeline"))

    pipes = parse_pipelines(pipes, contains)

    set_data_in_redis(cache_key, json.dumps(pipes), expire_time_seconds=60)

    update_timestamp(cache_key)

    return JSONResponse(status_code=200, content=pipes)


@router.get("/mage/pipeline/read", tags=["PIPELINES GET"])
async def read_pipeline(pipeline_name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    if pipeline_name != "":
        headers = {
            "Authorization": f"Bearer {token.token}"
        }

        response = requests.get(f'{os.getenv("BASE_URL")}/api/pipelines/{pipeline_name}?api_key='
                                f'{os.getenv("API_KEY")}', headers=headers)

        if response.status_code != 200 or response.json().get("error") is not None:
            raise HTTPException(status_code=500, detail=response.json().get("error")["exception"])

        result = parse_pipeline(response.json().get("pipeline"))

        return JSONResponse(status_code=200, content=result)

    raise HTTPException(status_code=400, detail="Pipeline name should not be empty!")


@router.get("/mage/pipeline/read/full", tags=["PIPELINES GET"])
async def read_full_pipeline(pipeline_name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    if pipeline_name != "":
        headers = {
            "Authorization": f"Bearer {token.token}"
        }

        response = requests.get(f'{os.getenv("BASE_URL")}/api/pipelines/{pipeline_name}?api_key='
                                f'{os.getenv("API_KEY")}', headers=headers)

        if response.status_code != 200 or response.json().get("error") is not None:
            raise HTTPException(status_code=500, detail=response.json().get("error")["exception"])

        return JSONResponse(status_code=200, content=json.loads(response.content.decode('utf-8')))

    raise HTTPException(status_code=400, detail="Pipeline name should not be empty!")


@router.get("/mage/pipeline/read/predict/full", tags=["PIPELINES GET"])
async def read_full_pipeline(model_name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    if model_name != "":
        headers = {
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json",
            "X-API-KEY": os.getenv("API_KEY")
        }

        response = requests.get(f'{os.getenv("BASE_URL")}/api/pipelines?api_key={os.getenv("API_KEY")}',
                                headers=headers)

        if response.status_code != 200 or response.json().get("error") is not None:
            raise HTTPException(status_code=500, detail=response.json().get("error")["exception"])

        return_pipeline = None
        for pipeline in response.json()["pipelines"]:
            if model_name in pipeline["tags"]:
                return_pipeline = pipeline
                break

        if return_pipeline is None:
            raise HTTPException(status_code=404, detail="Could not find the pipeline you are looking for!")

        return JSONResponse(status_code=200, content=return_pipeline)

    raise HTTPException(status_code=400, detail="Pipeline name should not be empty!")


@router.get("/mage/pipeline/history", tags=["PIPELINES GET"])
async def pipeline_history(pipeline_name: str, limit: int = 30):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

    url = f'{os.getenv("BASE_URL")}/api/pipeline_runs?_limit={limit}&_offset=0&pipeline_uuid={}&disable_retries_grouping=true&api_key={os.getenv("API_KEY")}'

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(detail=response.json().get("error")["exception"], status_code=500)

    returns = []

    for entry in response.json()["pipeline_runs"]:
        failed_index = None
        for i, block_run in enumerate(entry["block_runs"]):
            if block_run["status"] == "failed":
                failed_index = i
                break

        return_data = {}
        if failed_index is None:
            return_data["status"] = entry["status"]
            return_data["variables"] = entry["variables"]
            return_data["running_date"] = datetime.strftime(
                datetime.strptime(entry["execution_date"], "%Y-%m-%d %H:%M:%S.%f"), "%Y-%m-%d %H:%M")
            return_data["last_completed_block"] = entry["block_runs"][-1]["block_uuid"]
            return_data["last_failed_block"] = "-"
            return_data["error_message"] = "-"
        else:
            return_data["status"] = entry["status"]
            return_data["variables"] = entry["variables"]
            return_data["running_date"] = datetime.strftime(
                datetime.strptime(entry["execution_date"], "%Y-%m-%d %H:%M:%S.%f"), "%Y-%m-%d %H:%M")
            return_data["last_completed_block"] = entry["block_runs"][failed_index - 1]["block_uuid"]
            return_data["last_failed_block"] = entry["block_runs"][failed_index]["block_uuid"]
            return_data["error_message"] = entry["block_runs"][failed_index]["metrics"]["error"]["error"] if len(
                entry["block_runs"][failed_index]["metrics"].keys()) else "-"

        returns.append(return_data)

    return JSONResponse(returns, status_code=200)


@router.get("/mage/pipeline/description", tags=["PIPELINES GET"])
async def description(name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}?api_key={os.getenv("API_KEY")}'

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.token}"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail=response.json().get("error")["exception"])

    return JSONResponse(status_code=200, content=response.json()["pipeline"]["description"])


@router.get("/mage/pipeline/templates", tags=["PIPELINES GET"])
async def description(pipeline_type: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/custom_templates?object_type=blocks&api_key={os.getenv("API_KEY")}'

    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(detail=response.json().get("error")["exception"], status_code=500)

    body = response.json()["custom_templates"]

    templates = []
    for entry in body:
        pattern = r"\([\w\s_-]+\) "
        if pipeline_type in entry["description"] or len(re.findall(pattern, entry["description"])) == 0:
            templates.append({
                "type": entry["block_type"],
                "name": entry["template_uuid"],
                "description": entry["description"].replace("(" + pipeline_type + ") ", "")
            })

    return JSONResponse(content=templates, status_code=200)


@router.get("/mage/pipeline/export/cwl", tags=["PIPELINES GET"])
async def export_pipeline_cwl(pipeline_name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    headers = {
        "Authorization": f"Bearer {token.token}"
    }

    response = requests.get(f'{os.getenv("BASE_URL")}/api/pipelines/{pipeline_name}?api_key='
                            f'{os.getenv("API_KEY")}', headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail=response.json().get("error")["exception"])

    repository_name = get_repo_name(local_token=token.token)

    blocks = response.json()["pipeline"]["blocks"]
    blocks.sort(key=lambda x: (len(x['upstream_blocks']) == 0, len(x['downstream_blocks']) != 0))

    sorted_data = [blocks[0]]

    while len(sorted_data) < len(blocks):
        last_uuid = sorted_data[-1]['uuid']
        next_block = next((block for block in blocks if last_uuid in block['upstream_blocks']), None)
        if next_block:
            sorted_data.append(next_block)
        else:
            break

    remaining_blocks = [block for block in blocks if block not in sorted_data]
    sorted_data.extend(remaining_blocks)

    sorted_data.reverse()

    download_utils = False

    for block in sorted_data:
        if f"from {repository_name}" in block["content"] or f"import {repository_name}" in block["content"]:
            download_utils = True
            break

    mtc = MageToCWL(sorted_data, pipeline_name, repository_name)
    mtc.process()
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path, content in mtc.files.items():
            if content is None:
                zipf.writestr(file_path, '')
            else:
                zipf.writestr(file_path, content)

        if download_utils:
            files = get_folder("utils", local_token=token.token)
            if files is not None:
                for file_info in files:
                    try:
                        file_content = download_file(file_info["encoded_path"], token.token)

                        zipf.writestr(pipeline_name + "/scripts/" + file_info["full_path"], file_content)

                    except Exception as e:
                        print(f"Failed to download or add {file_info['full_path']} to zip: {str(e)}")
                        raise HTTPException(status_code=500,
                                            detail=f"Failed to download or add {file_info['full_path']} to zip!")

    zip_buffer.seek(0)

    response = StreamingResponse(zip_buffer, media_type="application/x-zip-compressed")
    response.headers["Content-Disposition"] = f"attachment; filename={pipeline_name}.zip"

    return response


@router.get("/mage/pipeline/export")
async def export_pipeline(pipeline_name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    pipeline_folder = get_folder(f"pipelines/{pipeline_name}", local_token=token.token)

    if pipeline_folder is None:
        raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline_name}' not found!")

    file_contents = []
    readme = f"# {' '.join(pipeline_name.split('_')).title()} configuration \n- Add the folder called **{pipeline_name}** inside the **pipelines** folder in MageAI."
    metadata = None
    for entry in pipeline_folder:
        file_content = download_file(urllib.parse.quote(f'pipelines/{entry["encoded_path"]}'), token.token)
        if "metadata.yaml" in entry["encoded_path"]:
            metadata = yaml.safe_load(file_content)

        file_contents.append({"path": entry["full_path"], "content": file_content})

    if metadata:
        for block in metadata["blocks"]:
            block_type = block["type"]
            block_name = block["name"]
            block_content = download_file(urllib.parse.quote(f'{block_type}s/{block_name}.py'), token.token)
            file_contents.append({"path": f'{block_name}.py', "content": block_content})
            readme += f"\n- Add file **{block_name}.py** to **{block_type}s** folder in MageAI."

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_info in file_contents:
            zipf.writestr(file_info["path"], file_info["content"])
        zipf.writestr("README.md", readme)

    zip_buffer.seek(0)

    response = StreamingResponse(zip_buffer, media_type="application/x-zip-compressed")
    response.headers["Content-Disposition"] = f"attachment; filename={pipeline_name}.zip"

    return response


def get_repo_name(local_token: str) -> str | None:
    url = f'{os.getenv("BASE_URL")}/api/statuses?api_key={os.getenv("API_KEY")}'

    headers = {
        "Authorization": f"Bearer {local_token}"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code not in [200, 304] or response.json().get("error"):
        return

    if response.json().get("statuses"):
        if len(response.json().get("statuses")) > 0:
            return response.json().get("statuses")[0]["repo_path_relative"]

    return


def download_file(encoded_file_name: str, local_token: str):
    url = f'{os.getenv("BASE_URL")}/api/file_contents/{encoded_file_name}?api_key={os.getenv("API_KEY")}'

    headers = {
        "Authorization": f"Bearer {local_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code not in [200, 304]:
        raise ValueError(f"Could not retrieve the file contents for {encoded_file_name}!")

    return response.json()["file_content"]["content"].encode('utf-8')


def parse_file_structure(node, current_path=""):
    files = []

    if "children" not in node and not node.get("disabled", False):
        # Build full path and URL encode it
        full_path = f"{current_path}/{node['name']}".lstrip("/")
        encoded_path = urllib.parse.quote(full_path)
        files.append({
            "encoded_path": encoded_path,
            "full_path": full_path
        })

    if "children" in node:
        for child in node["children"]:
            files.extend(parse_file_structure(child, f"{current_path}/{node['name']}"))

    return files


def get_folder(folder_name: str, local_token: str):
    url = f'{os.getenv("BASE_URL")}/api/files?include_pipeline_count=true&api_key={os.getenv("API_KEY")}'

    headers = {
        "Authorization": f"Bearer {local_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code not in [200, 304] or response.json().get("error"):
        return None

    i = 0
    file_names = None  # Will contain the encoded_path and full_path for the files in that specified folder
    folder_names = folder_name.split("/")  # Split the folder_name at "/" if there is a multilayer path
    files_data = response.json().get("files", [])  # All the files in the root structure folder
    current_path = files_data[0].get("children", [])  # The current children of the root structure folder

    if current_path:
        while i < len(folder_names) and current_path:
            for file in current_path:
                if file["name"] == folder_names[i]:
                    if i == len(folder_names) - 1:
                        file_names = parse_file_structure(file)
                        break
                    current_path = file.get("children", [])
                    break
            i += 1

    return file_names if file_names else None
