import os
import requests
from io import BytesIO
from dependencies import Token
from starlette.responses import Response
from fastapi import APIRouter, HTTPException


router = APIRouter()

token = Token()


@router.get("/mage/file/download", tags=["FILES GET"])
async def download(file_name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token.token}',
        'X-API-KEY': os.getenv("API_KEY")
    }

    url = f'{os.getenv("BASE_URL")}/api/file_contents/objects%2F{file_name}?api_key={os.getenv("API_KEY")}'

    response = requests.request("GET", url, headers=headers)

    if response.status_code not in [200, 304]:
        raise HTTPException(status_code=500, detail="Could not retrieve the file contents!")

    file_like_object = BytesIO(response.json()["file_content"]["content"].encode('utf-8'))

    # Create a response with the file-like object
    response = Response(file_like_object.getvalue(), media_type='application/octet-stream')
    response.headers["Content-Disposition"] = f"attachment; filename={file_name}"

    return response


@router.get("/mage/file/figures", tags=["FILES GET"])
async def figures(pipeline_name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token.token}',
        'X-API-KEY': os.getenv("API_KEY")
    }

    url = f'{os.getenv("BASE_URL")}/api/files?include_pipeline_count=true&api_key={os.getenv("API_KEY")}'

    response = requests.request("GET", url, headers=headers)

    if response.status_code not in [200, 304] or response.json().get("error"):
        raise HTTPException(status_code=500, detail="Could not get the Mage folder structure!")

    files = response.json().get("files", [])

    images = []
    for file in files[0]["children"]:
        if file["name"] == "figures":
            for child in file["children"]:
                if child["name"] == pipeline_name:
                    for figure in child["children"]:
                        url = f'{os.getenv("BASE_URL")}/api/file_contents/figures%2F{pipeline_name}%2F{figure["name"]}?api_key={os.getenv("API_KEY")}'

                        response = requests.request("GET", url, headers=headers)

                        print(response.status_code, response.json())

                        if response.status_code not in [200, 304]:
                            continue

                        content = response.json()["file_content"]["content"]
                        images.append({
                            "filename": figure["name"],
                            "content": content
                        })

    return images

