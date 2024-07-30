import os
import requests
from dependencies import Token
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse

router = APIRouter()

token = Token()


@router.get("/mage/kernels", tags=["KERNEL GET"])
async def get_kernels():
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/kernels?api_key={os.getenv("API_KEY")}'

    headers = {
        "Authorization": f"Bearer {token.token}"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=response.status_code, detail=response.json().get("error")["message"])

    returns = {
        "alive": response.json()["kernels"][0]["alive"],
        "kernel_cpu": response.json()["kernels"][0]["usage"]["kernel_cpu"],
        "host_cpu": response.json()["kernels"][0]["usage"]["host_cpu_percent"],
        "cpu_count": response.json()["kernels"][0]["usage"]["cpu_count"],
        "memory": {k: (v if k == "percent" else round(v / 10**9, 2)) for k, v in response.json()["kernels"][0]["usage"]["host_virtual_memory"].items()}
    }

    return JSONResponse(status_code=200, content=returns)
