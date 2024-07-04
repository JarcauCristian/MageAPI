import os
import requests
from io import BytesIO
from dependencies import Token
from starlette.responses import Response
from fastapi import APIRouter, HTTPException


router = APIRouter()

token = Token()


@router.get("/mage/file/download", tags=["FILES POST"])
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
