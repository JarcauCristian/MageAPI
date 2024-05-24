import os
import json
import requests
from datetime import datetime
from dependencies import Token
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse
from utils.models import Status, Description, UpdateTrigger


router = APIRouter()

token = Token()


@router.put("/mage/pipeline/trigger/status", tags=["PIPELINES PUT"])
async def pipeline_enable_trigger(status: Status):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")
    
    if status.status not in ["active", "inactive"]:
        return JSONResponse(status_code=400, content="Status can only be active or inactive!")
    
    url = f'{os.getenv("BASE_URL")}/api/pipeline_schedules/{status.trigger_id}?api_key={os.getenv("API_KEY")}'

    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

    payload = json.dumps({
        "pipeline_schedule": {
            "status": status.status
        },
        "api_key": os.getenv("API_KEY")
    })

    response = requests.request("PUT", url, headers=headers, data=payload)

    if response.status_code != 200:
        return JSONResponse(status_code=response.status_code, content="Bad request!")
    
    if response.json().get("error") is not None:
        return JSONResponse(status_code=500, content="Error changing the status of the trigger!")
    
    return JSONResponse(status_code=200, content="Trigger status changed successfully!")


@router.put("/mage/pipeline/trigger/update", tags=["PIPELINES PUT"])
async def trigger_update(trigger: UpdateTrigger):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")
    
    if trigger.status not in ["start", "stop"]:
        raise HTTPException(status_code=400, detail="status entry can only be start or stop!")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.token}",
    }



    runs_url = f"{os.getenv('BASE_URL')}/api/pipeline_runs?pipeline_uuid={trigger.pipeline_uuid}&api_key={os.getenv('API_KEY')}"
        
    runs_response = requests.request("GET", runs_url, headers=headers)

    if runs_response.status_code != 200 or runs_response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail=f"Recived error when updating the status of the trigger with id: {trigger.trigger_id}!")
    
    last_run_id = None
    if len(runs_response.json()["pipeline_runs"]) != 0:
        last_run_id = runs_response.json()["pipeline_runs"][0]["id"]
    
    if trigger.status == "start" and last_run_id is not None:
        raise HTTPException(status_code=400, detail="The trigger is already started!")
    elif trigger.status == "stop" and last_run_id is None:
        raise HTTPException(status_code=400, detail="The trigger is already stoped!")

    if trigger.status == "start":
        body = {
            "api_key": os.getenv('API_KEY'),
            "pipeline_schedule": {
                "id": trigger.trigger_id,
                "status": "active",
            }
        }

        url = f"{os.getenv('BASE_URL')}/api/pipeline_schedules/{trigger.trigger_id}?api_key={os.getenv('API_KEY')}"

        response = requests.request("PUT", url, headers=headers, data=json.dumps(body, indent=4))

        if response.status_code != 200 or response.json().get("error") is not None:
            raise HTTPException(status_code=500, detail=f"Recived error when updating the status of the trigger with id: {trigger.trigger_id}!")
    elif trigger.status == "stop":
        body = {
            "api_key": os.getenv('API_KEY'),
            "pipeline_schedule": {
                "id": trigger.trigger_id,
                "status": "inactive",
            }
        }

        url = f"{os.getenv('BASE_URL')}/api/pipeline_schedules/{trigger.trigger_id}?api_key={os.getenv('API_KEY')}"

        response = requests.request("PUT", url, headers=headers, data=json.dumps(body, indent=4))

        if response.status_code != 200 or response.json().get("error") is not None:
            raise HTTPException(status_code=500, detail=f"Recived error when updating the status of the trigger with id: {trigger.trigger_id}!")

        url = f"{os.getenv('BASE_URL')}/api/pipeline_runs/{last_run_id}?api_key={os.getenv('API_KEY')}"

        response = requests.request("DELETE", url, headers=headers)

        if response.status_code != 200 or response.json().get("error") is not None:
            raise HTTPException(status_code=500, detail=f"Recived error when updating the status of the trigger with id: {trigger.trigger_id}!")
    
    return JSONResponse(status_code=200, content=f"Trigger with id {trigger.trigger_id} updated successfully!")
    


@router.put("/mage/pipeline/description", tags=["PIPELINES PUT"])
async def put_description(desc: Description):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/pipelines/{desc.name}'

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.token}",
        "X-API-KEY": os.getenv("API_KEY")
    }

    data = {
        "pipeline": {
            "description": desc.description
        }
    }

    payload = json.dumps(data, indent=4)

    response = requests.request("PUT", url, headers=headers, data=payload)

    if response.status_code != 200 or response.json().get("error") is not None:
        return JSONResponse(status_code=500, content=f"Error updating the description of {desc.name}!")

    return JSONResponse(status_code=200, content="Pipeline updated successfully!")

