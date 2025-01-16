import os
import io
import httpx
import requests
from dependencies import Token
from utils.models import FileCreate
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse


router = APIRouter()

token = Token()


@router.post("/mage/files/create")
async def create_file(content: FileCreate):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token.token}',
        'X-API-KEY': os.getenv("API_KEY")
    }

    if content.type not in ["folder", "file"]:
        raise HTTPException(status_code=500, detail="Type can only be folder or file!")
            
    if content.type == "folder":
        url = f'{os.getenv("BASE_URL")}/api/folders?api_key={os.getenv("API_KEY")}'

        body = {
            "api_key": os.getenv("API_KEY"),
            "folder": {
                "name": content.name,
                "overwrite": False,
                "path": content.path
            }
        }

        response = requests.request("POST", url, json=body, headers=headers)

        if response.status_code != 200 or response.json().get("error") is not None:
            raise HTTPException(status_code=500, detail=f"Error creating the folder {content.name}!")

        return JSONResponse("Folder created successfully!")
    elif content.type == "file":
        if content.content is None:
            raise HTTPException(status_code=400, detail="Type is file, content needs to be provided!")
                
        headers = {
            "Authorization": f"Bearer {token.token}",
            "accept": "application/json",
        }

        url = f"{os.getenv('BASE_URL')}/api/files?api_key={os.getenv('API_KEY')}"

        buffer = io.BytesIO(content.content.encode('utf-8'))

        files = {
            "file": ("config.yaml", buffer, "text/yaml"),
            "json_root_body": (
                None,
                '{"api_key":"%s","dir_path":"%s","pipeline_zip":false,"overwrite":false}' % (os.getenv('API_KEY'), content.path),
            ),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, files=files)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error encountered when importing the file!")

        return JSONResponse(status_code=200, content="File imported sucessfully!")
