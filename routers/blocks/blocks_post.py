import os
import json
import requests
from typing import Annotated
from dependencies import Token
from starlette.responses import JSONResponse
from fastapi import APIRouter, Form, UploadFile, HTTPException

router = APIRouter()

token = Token()


@router.post("/mage/block/create", tags=["BLOCKS POST"])
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
        raise HTTPException(status_code=500, detail="Could not get the token!")

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
    
    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail=response.json().get("error")["message"])

    return JSONResponse(status_code=200, content="Block Created!")


@router.post("/mage/block/template/create", tags=["BLOCKS POST"])
async def create_template(block_type: Annotated[str, Form()],
                          language: Annotated[str, Form()],
                          name: Annotated[str, Form()],
                          description: Annotated[str, Form()],
                          user_id: Annotated[str, Form()],
                          code: UploadFile):
    if token.check_token_expired():
        token.update_token()

    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    if block_type not in ["data_loader", "transformer", "data_exporter", "sensor"]:
        raise HTTPException(status_code=500, detail=f"Bad block_type for template accepted values are: {', '.join(['data_loader', 'transformer', 'data_exporter', 'sensor'])}")

    if language not in ["python", "yaml"]:
        raise HTTPException(status_code=500, detail="Bad language for template accepted value are: python, yaml")

    url = f'{os.getenv("BASE_URL")}/api/custom_templates?api_key={os.getenv("API_KEY")}'

    data = {
        "api_key": os.getenv("API_KEY"),
        "custom_template": {
            "block_type": block_type,
            "language": language,
            "object_type": "blocks",
            "template_uuid": name
        }
    }

    data = json.dumps(data)

    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, data=data, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail=response.json().get("error")["message"])

    url = f'{os.getenv("BASE_URL")}/api/custom_templates/{name}?object_type=blocks&api_key={os.getenv("API_KEY")}'

    file_data = code.file.read().decode("utf-8").replace("\n", "\\n")

    data = {
        "api_key": os.getenv("API_KEY"),
        "custom_template": {
            "block_type": block_type,
            "color": None,
            "configuration": None,
            "content": file_data,
            "description": description,
            "language": language,
            "name": " ".join(name.split("_")).title(),
            "object_type": "blocks",
            "pipeline": {},
            "tags": [user_id],
            "template_uuid": name,
            "user": {"username": "admin"},
            "uuid": f"custom_templates/blocks/{name}"
        }
    }

    data = json.dumps(data).replace("\\\\", "\\")

    response = requests.request("PUT", url, data=data, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail=response.json().get("error")["message"])

    return JSONResponse(f"Template {name} created successfully!", status_code=200)
