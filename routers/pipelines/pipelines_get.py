import os
import json
import requests
from datetime import datetime
from fastapi import APIRouter
from dependencies import Token
from starlette.responses import JSONResponse
from utils.pipelines import parse_pipeline, parse_pipelines
from redis_cache.cache import get_data_from_redis, is_data_stale, set_data_in_redis, update_timestamp

router = APIRouter()

token = Token()


@router.get("/mage/pipeline/status_once", tags=["PIPELINES GET"])
async def pipeline_status_once(pipeline_id: int, block_name: str = ""):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/pipeline_schedules/{pipeline_id}/pipeline_runs?api_key={os.getenv("API_KEY")}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token.token}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return JSONResponse(status_code=response.status_code, content=f"Error getting the status of the block {block_name}!")

    body = json.loads(response.content.decode('utf-8'))['pipeline_runs']
    if len(body) == 0:
        return JSONResponse(status_code=500, content="No pipelines runs")
    else:
        needed_block = None
        for block in body[0]["block_runs"]:
            if block["block_uuid"] == block_name:
                needed_block = block

    return needed_block["status"]


@router.get("/mage/pipeline/triggers", tags=["PIPELINES GET"])
async def pipeline_triggers(name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}/pipeline_schedules?api_key={os.getenv("API_KEY")}'
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return JSONResponse(status_code=response.status_code, content=f"Error getting the trigger for {name}")

    returns = {
        "id": response.json()["pipeline_schedules"][0]["id"],
        "token": response.json()["pipeline_schedules"][0]["token"]
    }

    return JSONResponse(status_code=200, content=returns)


@router.get("/mage/pipeline/run/status", tags=["PIPELINES GET"])
async def pipeline_status(pipeline_id: int):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
            return JSONResponse(status_code=500, content="Could not get the token!")
        
    url = f'{os.getenv("BASE_URL")}/api/pipeline_schedules/{pipeline_id}/pipeline_runs?api_key={os.getenv("API_KEY")}'
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token.token}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return JSONResponse(status_code=500, content=f"Error getting the status of the run with id {pipeline_id}")
    
    return JSONResponse(status_code=200, content=response.json())


@router.get("/mage/pipeline/trigger/status", tags=["PIPELINES GET"])
async def pipeline_status_trigger(name: str):

    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")
    
    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}/pipeline_schedules?api_key={os.getenv("API_KEY")}'
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return JSONResponse(status_code=response.status_code, content="There was an error getting the status of the trigger!")

    return JSONResponse(status_code=200, content=response.json()["pipeline_schedules"][0]["status"])


@router.get("/mage/pipeline/status", tags=["PIPELINES GET"])
async def pipeline_status(name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}/pipeline_schedules?api_key={os.getenv("API_KEY")}'
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return JSONResponse(status_code=response.status_code, content="There was an error getting the status of pipeline!")

    returns = {
        "last_status": response.json()["pipeline_schedules"][0]["last_pipeline_run_status"],
        "next_run": response.json()["pipeline_schedules"][0]["next_pipeline_run_date"]
    }

    return JSONResponse(status_code=200, content=returns)


@router.get("/mage/pipeline/batch_status", tags=["PIPELINES GET"])
async def pipeline_status_once(pipeline_id: int):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/pipeline_schedules/{pipeline_id}/pipeline_runs?api_key={os.getenv("API_KEY")}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token.token}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return JSONResponse(status_code=response.status_code, content=f"Error getting the status of the pipeline with id {pipeline_id}!")

    body = json.loads(response.content.decode('utf-8'))['pipeline_runs']
    
    if len(body) == 0:
        return JSONResponse(status_code=500, content="No runs yet!")

    return body[0]["status"]


@router.get("/mage/pipelines", tags=["PIPELINES GET"])
async def pipelines():
    pipelines_url = os.getenv('BASE_URL') + f'/api/pipelines?api_key={os.getenv("API_KEY")}'

    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token.token}'
    }

    response = requests.get(pipelines_url, headers=headers)

    if response.status_code != 200:
        return JSONResponse(status_code=response.status_code, content="An error occurred when getting the pipelines!")

    json_response = dict(response.json())

    names = []
    for pipe in json_response["pipelines"]:
        tag = None
        for t in pipe.get("tags"):
            if t in ["train", "data_preprocessing"]:
                tag = t
                break
        names.append({
            "name": pipe.get("name"),
            "type": tag
        })
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
          return JSONResponse(status_code=response.status_code, content=f"Error getting the pipelines for user with id {contains}!")

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
        return JSONResponse(status_code=500, content="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/pipelines?api_key={os.getenv("API_KEY")}'
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.token}"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
      return JSONResponse(status_code=response.status_code, content=f"Error getting the pipelines for user with id {contains}!")

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
        return JSONResponse(status_code=500, content="Could not get the token!")

    if pipeline_name != "":
        headers = {
            "Authorization": f"Bearer {token.token}"
        }

        response = requests.get(f'{os.getenv("BASE_URL")}/api/pipelines/{pipeline_name}?api_key='
                                f'{os.getenv("API_KEY")}', headers=headers)

        if response.status_code != 200:
            return JSONResponse(status_code=500, content="Could not get pipeline result!")

        result = parse_pipeline(response.json().get("pipeline"))

        return JSONResponse(status_code=200, content=result)

    return JSONResponse(status_code=400, content="Pipeline name should not be empty!")


@router.get("/mage/pipeline/read/full", tags=["PIPELINES GET"])
async def read_full_pipeline(pipeline_name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")
    
    if pipeline_name != "":
        headers = {
            "Authorization": f"Bearer {token.token}"
        }

        response = requests.get(f'{os.getenv("BASE_URL")}/api/pipelines/{pipeline_name}?api_key='
                                f'{os.getenv("API_KEY")}', headers=headers)

        if response.status_code != 200:
            return JSONResponse(status_code=500, content="Could not get pipeline result!")

        return JSONResponse(status_code=200, content=json.loads(response.content.decode('utf-8')))

    return JSONResponse(status_code=400, content="Pipeline name should not be empty!")


@router.get("/mage/pipeline/read/predict/full", tags=["PIPELINES GET"])
async def read_full_pipeline(model_name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")
    
    if model_name != "":
        headers = {
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json",
            "X-API-KEY": os.getenv("API_KEY")
        }

        response = requests.get(f'{os.getenv("BASE_URL")}/api/pipelines?api_key={os.getenv("API_KEY")}', headers=headers)

        if response.status_code != 200 or response.json().get("error") is not None:
            return JSONResponse(status_code=500, content="Could not get pipeline result!")
        
        return_pipeline = None
        for pipeline in response.json()["pipelines"]:
            if model_name in pipeline["tags"]:
                return_pipeline = pipeline
                break

        if return_pipeline is None:
            return JSONResponse(status_code=404, content="Could not find the pipeline you are looking for!")

        return JSONResponse(status_code=200, content=return_pipeline)

    return JSONResponse(status_code=400, content="Pipeline name should not be empty!")


@router.get("/mage/pipeline/history")
async def pipeline_history(pipeline_name: str, limit: int = 30):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")
    
    url = f'{os.getenv("BASE_URL")}/api/pipeline_schedules?api_key={os.getenv("API_KEY")}'

    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return JSONResponse(content=f"Error getting the informations for {pipeline_name}!", status_code=500)

    run_id = None
    for schedule in response.json()["pipeline_schedules"]:
        if schedule["pipeline_uuid"] == pipeline_name:
            run_id = schedule["id"]

    if run_id is None:
        return JSONResponse("Pipeline does not have any active runs!", status_code=404)
    
    url = f'{os.getenv("BASE_URL")}/api/pipeline_schedules/{run_id}/pipeline_runs?_limit={limit}&_offset=0&api_key={os.getenv("API_KEY")}'

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return JSONResponse(content=f"Error getting the history of runs for {pipeline_name}!", status_code=500)

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
            return_data["running_date"] = datetime.strftime(datetime.strptime(entry["execution_date"], "%Y-%m-%d %H:%M:%S.%f"), "%Y-%m-%d %H:%M")
            return_data["last_completed_block"] = entry["block_runs"][-1]["block_uuid"]
            return_data["last_failed_block"] = "-"
            return_data["error_message"] = "-"
        else:
            return_data["status"] = entry["status"]
            return_data["variables"] = entry["variables"]
            return_data["running_date"] = datetime.strftime(datetime.strptime(entry["execution_date"], "%Y-%m-%d %H:%M:%S.%f"), "%Y-%m-%d %H:%M")
            return_data["last_completed_block"] = entry["block_runs"][failed_index - 1]["block_uuid"]
            return_data["last_failed_block"] = entry["block_runs"][failed_index]["block_uuid"]
            return_data["error_message"] = entry["block_runs"][failed_index]["metrics"]["error"]["error"] if len(entry["block_runs"][failed_index]["metrics"].keys()) else "-"

        returns.append(return_data)

    return JSONResponse(returns, status_code=200)


@router.get("/mage/pipeline/description", tags=["PIPELINES GET"])
async def description(name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}?api_key={os.getenv("API_KEY")}'

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.token}"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return JSONResponse(status_code=500, content="Error getting pipeline's description!")

    return JSONResponse(status_code=200, content=response.json()["pipeline"]["description"])


@router.get("/mage/pipeline/templates", tags=["PIPELINES GET"])
async def description(pipeline_type: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")

    if pipeline_type not in ["batch", "stream"]:
        return JSONResponse(content="Only batch and stream values are allowed for pipeline_type!", status_code=400)

    url = f'{os.getenv("BASE_URL")}/api/custom_templates?object_type=blocks&api_key={os.getenv("API_KEY")}'

    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return JSONResponse(content="Could not load the templates!", status_code=500)
    
    body = response.json()["custom_templates"]

    templates = []
    for entry in body:
        if pipeline_type in entry["description"]:
            templates.append({
                "type": entry["block_type"],
                "name": entry["template_uuid"],
                "description": entry["description"].replace("(" + pipeline_type + ") ", "")
            })

    return JSONResponse(content=templates, status_code=200)
