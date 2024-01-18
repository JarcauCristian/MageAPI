import os
import json
import requests
from typing import Annotated
from dependencies import Token
from starlette.responses import JSONResponse
from fastapi import APIRouter, Form, UploadFile

router = APIRouter()

token = Token()


@router.post("/block/create", tags=["BLOCKS POST"])
async def block_create(block_name: Annotated[str, Form()], 
                       block_type: Annotated[str, Form()],
                       pipeline_name: Annotated[str, Form()],
                       downstream_blocks: Annotated[list[str], Form()], 
                       upstream_blocks: Annotated[list[str], Form()],
                       language: Annotated[str, Form()],
                       file: UploadFile
    ):

    if token.check_token_expired():
        token.update_token()

    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")

    file_data = file.file.read().decode("utf-8").replace("\n", "\\n")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token.token}",
        "X-API-KEY": os.getenv("API_KEY")
    }

    payload = {
        "block": {
            "name": block_name,
            "language": f"{language}",
            "type": f"{block_type}",
            "content": f"{file_data}",
            "downstream_blocks": downstream_blocks,
            "upstream_blocks": upstream_blocks
        },
        "api-key": os.getenv("API_KEY")
    }
    payload = json.dumps(payload).replace("\\\\", "\\")
    response = requests.request("POST", url=f'{os.getenv("BASE_URL")}/api/pipelines/{pipeline_name}/blocks?'
                                            f'api_key={os.getenv("API_KEY")}', headers=headers, data=payload)
    if response.status_code != 200:
        return JSONResponse(status_code=500, content="Could not create block!")

    if response.json().get("error") is not None:
        return JSONResponse(status_code=500, content="Error occurred when creating the block!")

    return JSONResponse(status_code=200, content="Block Created!")
