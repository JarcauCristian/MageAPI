import os
import requests
from fastapi import APIRouter
from dependencies import Token
from starlette.responses import JSONResponse


router = APIRouter()

token = Token()


@router.delete("/pipeline/delete")
async def delete_pipeline(name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.token}",
        "X-API-KEY": os.getenv("API_KEY")
    }

    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}'

    response = requests.request("DELETE", url, headers=headers)

    if response.status_code != 200:
        return JSONResponse(status_code=500, content="Something happened when deleting the pipeline!")

    if response.json().get("error") is not None:
        return JSONResponse(status_code=500, content="Something happened when deleting the pipeline!")

    return JSONResponse(status_code=200, content="Pipeline deleted successfully!")

