import os
import json
import requests
from dependencies import Token
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse

router = APIRouter()

token = Token()


def get_template(name: str):
    if token.check_token_expired():
        token.update_token()

    if token.token == "":
        return None

    url = f'{os.getenv("BASE_URL")}/api/custom_templates/{name}?object_type=blocks&api_key={os.getenv("API_KEY")}'

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.token}"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        return None
    
    if response.json().get("error") is not None:
        return None

    content = response.json()["custom_template"]["content"]
    description = response.json()["custom_template"]["description"]

    variables = ""
    if content.find("# Variables") != -1:
        variables = dict(json.loads(content[content.find("# Variables") + 12:content.find('\n')].strip()).items())

    returns = {
        "content": content,
        "variables": variables,
        "description": description.replace("(batch) ", "") if "(batch)" in description else description.replace("(stream) ", "")
    }

    return returns



@router.get("/mage/block/model", tags=["BLOCKS GET"])
async def block_model(block_name: str):
    if block_name == "export_to_minio":
            response = requests.get("https://ingress.sedimark.work/neo4j/categories", headers={
                "Authorization": f"Bearer mage_{os.getenv('NEO4J_PASSWORD')}"
            })

            categories = []
            if response.status_code == 200:
                categories = response.json()
                
            returns = get_template("export_to_minio")
            returns["variables"]["category"]["values"] = categories
            return JSONResponse(content=returns, status_code=200)
    else:
        returns = get_template(block_name)
        return JSONResponse(content=returns, status_code=200)
            

@router.get("/mage/block/read", tags=["BLOCKS GET"])
async def read_block(block_name: str, pipeline_name: str):
    if token.check_token_expired():
        token.update_token()

    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    if block_name != "" and pipeline_name != "":
        headers = {
            "Authorization": f"Bearer {token.token}"
        }
        response = requests.get(f'{os.getenv("BASE_URL")}/api/pipelines/{pipeline_name}/blocks/{block_name}?api_key='
                                f'{os.getenv("API_KEY")}', headers=headers)
        if response.status_code != 200 or response.json().get("error") is not None:
            raise HTTPException(status_code=500, detail=f"Error occured when reading the block {block_name}")

        return JSONResponse(content=response.json(), status_code=200)

    raise HTTPException(status_code=400, detail="Pipeline name and Block name should not be empty!")
