import os
import json
import requests
from datetime import datetime
from dependencies import Token
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse
from utils.pipelines import parse_pipeline, parse_pipelines
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
        raise HTTPException(status_code=500, detail=f"Error getting the trigger for {name}")

    returns = {
        "id": response.json()["pipeline_schedules"][0]["id"],
        "token": response.json()["pipeline_schedules"][0]["token"]
    }

    return JSONResponse(status_code=200, content=returns)


@router.get("/mage/pipeline/streaming/status", tags=["PIPELINES GET"])
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
        raise HTTPException(status_code=500, detail=f"Recived error when getting the status for pipeline {pipeline_name}!")
    
    return JSONResponse("active" if len(response.json()["pipeline_runs"]) != 0 else "inactive", status_code=200)
    


@router.get("/mage/pipeline/batch_status", tags=["PIPELINES GET"])
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
        raise HTTPException(status_code=500, detail=f"Error getting the status of the pipeline with id {pipeline_id}!")

    body = json.loads(response.content.decode('utf-8'))['pipeline_runs']
    
    if len(body) == 0:
        raise HTTPException(status_code=500, detail="No runs yet!")

    return JSONResponse(status_code=200, content=body[0]["status"])


@router.get("/mage/pipelines", tags=["PIPELINES GET"])
async def pipelines(tag: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")
    
    if tag not in ["train", "data_preprocessing", "streaming"]:
        raise HTTPException(status_code=400, detail="tag parameter should be train, data_preprocessing or streaming.")

    pipelines_url = os.getenv('BASE_URL') + f'/api/pipelines?tag[]={tag}&api_key={os.getenv("API_KEY")}'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token.token}'
    }

    response = requests.get(pipelines_url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, content="An error occurred when getting the pipelines!")

    names = []
    for pipe in response.json()["pipelines"]:
        names.append(pipe.get("name"))
        
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
        raise HTTPException(status_code=500, detail="Could not get the token!")

    if pipeline_name != "":
        headers = {
            "Authorization": f"Bearer {token.token}"
        }

        response = requests.get(f'{os.getenv("BASE_URL")}/api/pipelines/{pipeline_name}?api_key='
                                f'{os.getenv("API_KEY")}', headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Could not get pipeline result!")

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

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Could not get pipeline result!")

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

        response = requests.get(f'{os.getenv("BASE_URL")}/api/pipelines?api_key={os.getenv("API_KEY")}', headers=headers)

        if response.status_code != 200 or response.json().get("error") is not None:
            raise HTTPException(status_code=500, detail="Could not get pipeline result!")
        
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
    
    url = f'{os.getenv("BASE_URL")}/api/pipeline_schedules?api_key={os.getenv("API_KEY")}'

    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(content=f"Error getting the informations for {pipeline_name}!", status_code=500)

    run_id = None
    for schedule in response.json()["pipeline_schedules"]:
        if schedule["pipeline_uuid"] == pipeline_name:
            run_id = schedule["id"]

    if run_id is None:
        raise HTTPException(status_code=404, detail="Pipeline does not have any active runs!")
    
    url = f'{os.getenv("BASE_URL")}/api/pipeline_schedules/{run_id}/pipeline_runs?_limit={limit}&_offset=0&api_key={os.getenv("API_KEY")}'

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(detail=f"Error getting the history of runs for {pipeline_name}!", status_code=500)

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
        raise HTTPException(status_code=500, detail="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}?api_key={os.getenv("API_KEY")}'

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.token}"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail="Error getting pipeline's description!")

    return JSONResponse(status_code=200, content=response.json()["pipeline"]["description"])


@router.get("/mage/pipeline/templates", tags=["PIPELINES GET"])
async def description(pipeline_type: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    if pipeline_type not in ["batch", "stream"]:
        raise HTTPException(detail="Only batch and stream values are allowed for pipeline_type!", status_code=400)

    url = f'{os.getenv("BASE_URL")}/api/custom_templates?object_type=blocks&api_key={os.getenv("API_KEY")}'

    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(detail="Could not load the templates!", status_code=500)
    
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
