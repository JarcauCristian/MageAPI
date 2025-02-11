
import os
import io
import httpx
import requests
from typing import Any
from dependencies import Token
from utils.models import FileDelete
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse


router = APIRouter()

token = Token()


@router.delete("/mage/files/delete", tags=["FILES DELETE"])
async def delete_file(delete: FileDelete):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    if delete.type not in ["files", "folders"]:
        raise HTTPException(status_code=400, detail="Type can only be files or folders!")

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token.token}',
    }

    url = f"{os.getenv('BASE_URL')}/api/files?include_pipeline_count=true&api_key={os.getenv('API_KEY')}"

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail="Error fetching files!")

    def find_path(structure: list[dict[Any, Any]], path: str) -> str:
        for item in structure:
            if item.get("name") == delete.name:
                return path
            elif item.get("children"):
                result = find_path(item.get("children"), path=path + "%2F" + item["name"])
                if result is not None:
                    return result
        return None

    path = find_path(response.json()["files"][0]["children"], "default_repo") + "%2F" + delete.name
    
    url = f"{os.getenv('BASE_URL')}/api/{delete.type}/{path}?api_key={os.getenv('API_KEY')}"

    response = requests.request("DELETE", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail="Error deleting file!")

    return JSONResponse(f"{delete.type.capitalize()[:-1]} {delete.name} deleted successfully!", status_code=200)
