import os
import json
import requests
import tempfile
import subprocess
from typing import Annotated
from dependencies import Token
from starlette.responses import JSONResponse
from fastapi import APIRouter, HTTPException, Form, UploadFile

router = APIRouter()

token = Token()


@router.put("/mage/block/update", tags=["BLOCKS PUT"])
async def update_block(block_name: Annotated[str, Form()],
                       block_type: Annotated[str, Form()],
                       content: UploadFile):
    def run_pylint(file_path: str) -> int:
        result = subprocess.run(
            ['pylint', file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode

    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(await content.read())
            temp_file_path = temp_file.name

        return_code = run_pylint(temp_file_path)

        os.remove(temp_file_path)

        if return_code not in [0, 22]:
            raise HTTPException(detail="Could not proceed further, python code is incorrectly formatted!", status_code=500)

    except Exception:
        raise HTTPException(detail="Could not proceed further, python code is incorrectly formatted!", status_code=500)

    if token.check_token_expired():
        token.update_token()

    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    block_type = block_type.replace("\n", "")
    block_name = block_name.replace("\n", "")

    url = f'{os.getenv("BASE_URL")}/api/file_contents/%2Fhome%2Fsrc%2F{os.getenv("REPOSITORY_NAME")}%2F{block_type}s%2F{block_name}.py?api_key={os.getenv("API_KEY")}'

    headers = {
        'Accept': 'application/json, text/plain, */*',
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.token}",
        "X-API-KEY": os.getenv("API_KEY")
    }

    content.file.seek(0)
    file_data = content.file.read().decode("utf-8").replace("\\n", "\n")

    data = {
        "api_key": os.getenv("API_KEY"),
        "file_content": {
            "name": block_name,
            "path": f"/home/src/{os.getenv('REPOSITORY_NAME')}/{block_type}/{block_name}.py",
            "content": f"{file_data}"
        }
    }

    data = json.dumps(data)

    response = requests.request("PUT", url=url, headers=headers, data=data)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail=f"Error updating the block {block_name}!")

    return JSONResponse(status_code=200, content=f"Block {block_name} created successfully!")
