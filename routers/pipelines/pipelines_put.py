import os
import json
import requests
from fastapi import APIRouter
from dependencies import Token
from utils.models import Status, Description
from starlette.responses import JSONResponse


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

