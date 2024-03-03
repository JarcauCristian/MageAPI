import os
import requests
from fastapi import APIRouter
from dependencies import Token
from starlette.responses import JSONResponse


router = APIRouter()

token = Token()


@router.delete("/mage/pipeline/delete", tags=["PIPELINES DELETE"])
async def delete_pipeline(name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")
    
    response = requests.request("GET", f"https://ingress.sedimark.work/mage/pipeline/triggers?name={name}")

    if response.status_code != 200 or response.json().get("error") is not None:
        return JSONResponse(status_code=500, conetent="Could not get some information about the pipeline!")
    
    schedule_id = response.json()["id"]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.token}",
        "X-API-KEY": os.getenv("API_KEY")
    }

    response = requests.request("DELETE", f'{os.getenv("BASE_URL")}/api/pipeline_schedules/{schedule_id}?api_key={os.getenv("API_KEY")}', headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        return JSONResponse(status_code=500, conetent="Could not delete some information about the pipeline!")

    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}'

    response = requests.request("DELETE", url, headers=headers)

    if response.status_code != 200:
        return JSONResponse(status_code=500, content="Something happened when deleting the pipeline!")

    if response.json().get("error") is not None:
        return JSONResponse(status_code=500, content="Something happened when deleting the pipeline!")
    

    return JSONResponse(status_code=200, content="Pipeline deleted successfully!")

