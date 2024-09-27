import datetime
import json
import os
import requests
from io import BytesIO
from dependencies import Token
from fastapi import APIRouter, HTTPException
from starlette.responses import Response, JSONResponse


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

                        if response.status_code not in [200, 304]:
                            continue

                        content = response.json()["file_content"]["content"]
                        images.append({
                            "filename": figure["name"],
                            "content": content
                        })

    return images


@router.get("/mage/file/telemetry", tags=["FILES GET"])
async def telemetry(pipeline_name: str):
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

    telemetry_per_block = {}
    for file in files[0]["children"]:
        if file["name"] == "telemetry":
            for child in file["children"]:
                if child["name"] == pipeline_name:
                    for block in child["children"]:
                        if "json" in block["name"]:
                            url = f'{os.getenv("BASE_URL")}/api/file_contents/telemetry%2F{pipeline_name}%2F{block["name"]}?api_key={os.getenv("API_KEY")}'

                            response = requests.request("GET", url, headers=headers)

                            if response.status_code not in [200, 304]:
                                continue

                            content = response.json()["file_content"]["content"]
                            json_content = json.loads(content)
                            metrics = json_content['metrics']
                            telemetry_per_block[json_content["id"]] = {
                                "Runtime (s)": float(f"{metrics['runtime']['sum']:.2f}"),
                                "CPU Utilization (%)": float(f"{metrics['cpu_util']['sum']:.2f}"),
                                "Network Write (B)": metrics['net_write']['sum'],
                                "Network Read (B)": metrics['net_read']['sum'],
                                "DRAM Memory Usage (B)": metrics['dram_mem']['sum'],
                                "Disk Write (B)": metrics['disk_write']['sum'],
                                "Disk Read (B)": metrics['disk_read']['sum'],
                                "Last Execution Date": json_content['metadata']['last_execution_dt']
                            }

    keys = list(telemetry_per_block.keys())
    failed_keys = [x[7:] for x in keys if "failed_" in x]
    normal_keys = [x for x in keys if "failed_" not in x]
    for f in failed_keys:
        for n in normal_keys:
            if f == n:
                f_datatime = datetime.datetime.strptime(telemetry_per_block[f"failed_{f}"]["Last Execution Date"], "%Y-%m-%dT%H:%M:%S.%f")
                n_datatime = datetime.datetime.strptime(telemetry_per_block[n]["Last Execution Date"],
                                                        "%Y-%m-%dT%H:%M:%S.%f")

                if f_datatime > n_datatime:
                    del telemetry_per_block[n]
                else:
                    del telemetry_per_block[f"failed_{f}"]

    return JSONResponse(status_code=200, content=telemetry_per_block)

