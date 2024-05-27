import os
import json
import requests
from utils.models import Block
from dependencies import Token
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse

router = APIRouter()

token = Token()


@router.put("/mage/block/update", tags=["BLOCKS PUT"])
async def update_block(block: Block):
    if token.check_token_expired():
        token.update_token()

    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    if block.block_name != "" and block.pipeline_name != "" and block.content != "":
        headers = {
            'Accept': 'application/json, text/plain, */*',
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token.token}",
            "X-API-KEY": os.getenv("API_KEY")
        }
        payload = f'{{"block": {{"downstream_blocks": {block.downstream_blocks}, "upstream_blocks": {block.upstream_blocks}}}}}'
        response = requests.request("PUT", url=f'{os.getenv("BASE_URL")}/api/pipelines/{block.pipeline_name}'
                                               f'/blocks/{block.block_name}?api_key={os.getenv("API_KEY")}',
                                    headers=headers, data=payload)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Error updating the block {block.block_name}!")

        return JSONResponse(status_code=200, content=json.loads(response.content.decode('utf-8')))

    raise HTTPException(status_code=400, detail="Body Should not be empty!")
