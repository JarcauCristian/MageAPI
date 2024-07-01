import os
import json
import random
import string
import requests
from datetime import datetime
from dependencies import Token
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse
from utils.models import Pipeline, Secret, Trigger, Variables

router = APIRouter()

token = Token()


@router.post("/mage/pipeline/create", tags=["PIPELINES POST"])
async def pipeline_create(name: str, ptype: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    if ptype not in ["python", "streaming"]:
        raise HTTPException(status_code=400, detail="Only python and streaming are required for type")

    url = f'{os.getenv("BASE_URL")}/api/pipelines'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token.token}',
        'X-API-KEY': os.getenv("API_KEY")
    }

    data = {
        "pipeline": {
            "name": name,
            "type": ptype,
            "description": "not created"
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail=f"An error occurred when creating the pipeline {name}!")

    return JSONResponse(status_code=201, content="Pipeline Created")


@router.post("/mage/pipeline/create/trigger", tags=["PIPELINES POST"])
async def pipeline_create_trigger(trigger: Trigger):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    if trigger.trigger_type not in ["time", "api"]:
        raise HTTPException(status_code=400, detail="Type can be only schedule and api!")
    
    if trigger.trigger_type == "time":
        if trigger.interval not in ["hourly", "daily", "monthly"]:
            raise HTTPException(status_code=400, detail="Interval can be only hourly, daily and monthly!")

    url = f'{os.getenv("BASE_URL")}/api/pipelines/{trigger.name}/pipeline_schedules?api_key={os.getenv("API_KEY")}'
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

    payload = {}
    if trigger.trigger_type == "api":
        payload = json.dumps({
            "pipeline_schedule": {
                "name": ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10)),
                "schedule_type": trigger.trigger_type,
                "status": "active"
            },
            "api_key": os.getenv("API_KEY")
        })
    else:
        payload = json.dumps({
            "pipeline_schedule": {
                "name": ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10)),
                "schedule_type": trigger.trigger_type,
                "schedule_interval": "null" if trigger.interval is None else f"@{trigger.interval}",
                "start_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S%z') if trigger.start_time is None else trigger.start_time.strftime('%Y-%m-%d %H:%M:%S%z')
            },
            "api_key": os.getenv("API_KEY")
        })

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail="Encounter and error when creating the trigger!")

    return JSONResponse(status_code=200, content="Trigger created successfully!")


@router.post("/mage/pipeline/run", tags=["PIPELINES POST"])
async def run_pipeline(pipe: Pipeline):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    url = f"{os.getenv('BASE_URL')}/api/pipeline_schedules/{pipe.run_id}/api_trigger"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pipe.token}"
    }

    body = {
        "pipeline_run": {
            "variables": {

            }
        }
    }
    for k, v in pipe.variables.items():
        body['pipeline_run']['variables'][k] = v

    response = requests.post(url, headers=headers, data=json.dumps(body, indent=4))

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail="Starting the pipeline didn't work!")

    return JSONResponse(status_code=201, content="Pipeline Started Successfully!")


@router.post("/mage/pipeline/variables", tags=["PIPELINES POST"])
async def create_variables(variables: Variables):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")
    
    if len(variables.variables.keys()) == 0:
        raise HTTPException(status_code=400, detail="Should be at least one variable!")
    
    error_counter = 0
    
    for k, v in variables.variables.items():

        url = f'{os.getenv("BASE_URL")}/api/pipelines/{variables.name}/variables?api_key={os.getenv("API_KEY")}'

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token.token}",
            "X-API-KEY": os.getenv("API_KEY")
        }

        data = {
            "variable": {
                "name": k,
                "value": v
            },
            "api_key": os.getenv("API_KEY")
        }

        payload = json.dumps(data, indent=4)

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code != 200:
            error_counter += 1

    if error_counter > 0:
        raise HTTPException(status_code=500, detail=f"{error_counter} variables could not be created!")

    return JSONResponse(status_code=200, content="Variables added successfully!")


@router.post("/mage/pipeline/secret", tags=["PIPELINES POST"])
async def create_secret(secret: Secret):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")
    
    url = f'{os.getenv("BASE_URL")}/api/secrets?api_key={os.getenv("API_KEY")}'

    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json",
        "X-API-KEY": os.getenv("API_KEY")
    }

    body = {
        "secret": {
            "name": secret.name,
            "value": secret.value
        },
        "api_key": os.getenv("API_KEY")
    }

    response = requests.request("POST", url, headers=headers, json=body)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail="Could not create the secret!")
    
    return JSONResponse(status_code=200, content="Secret created successfully!")
