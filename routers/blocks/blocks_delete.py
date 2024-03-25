import os
import requests
from fastapi import APIRouter
from dependencies import Token
from utils.models import DeleteBlock
from starlette.responses import JSONResponse

router = APIRouter()

token = Token()


@router.delete("/mage/block/delete", tags=["BLOCKS DELETE"])
async def delete_block(block: DeleteBlock):
    if token.check_token_expired():
        token.update_token()

    if token.token == "":
        return JSONResponse(status_code=500, content="Could not get the token!")

    if block.block_name == "" and block.pipeline_name == "":
        return JSONResponse(status_code=400, content="Block should not be empty!")

    response = requests.delete(f'{os.getenv("base_url")}/api/pipelines/{block.pipeline_name}/'
                                          f'blocks/{block.block_name}?block_type={block.block_type}&'
                                          f'api_key={os.getenv("API_KEY")}&force={block.force}')

    if response.status_code != 200 or response.json().get("error") is not None:
        return JSONResponse(status_code=500, content=f"Error occurred when deleting the block {block.block_name}!")

    return JSONResponse(status_code=200, content="Block Deleted!")

