
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

    def find_all_paths(structure: list[dict], current_path: str, target: str) -> list[str]:
        paths = []
        for item in structure:
            new_path = f"{current_path}/{item['name']}"
            if item.get("name") == target:
                if (delete.type == "folders" and item.get("children")) or (delete.type == "files" and not item.get("children")):
                    paths.append(new_path)
            if item.get("children"):
                paths.extend(find_all_paths(item.get("children"), new_path, target))
        return paths

    all_paths = find_all_paths(response.json()["files"][0]["children"], "default_repo", delete.name)

    for path in all_paths:
        formatted_path = path.replace("/", "%2F")   
        url = f"{os.getenv('BASE_URL')}/api/{delete.type}/{formatted_path}?api_key={os.getenv('API_KEY')}"

        response = requests.request("DELETE", url, headers=headers)

        if response.status_code != 200 or response.json().get("error") is not None:
            raise HTTPException(status_code=500, detail="Error deleting file!")

    return JSONResponse(f"Successfully deleted all instances of {delete.name}!", status_code=200)
