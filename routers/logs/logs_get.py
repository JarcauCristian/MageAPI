import os
import json
from json import JSONDecodeError

import requests
from dependencies import Token
from collections import defaultdict
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse

router = APIRouter()

token = Token()


@router.get("/mage/log/pipeline/{pipeline_name}", tags=["LOGS GET"])
async def pipeline_logs(pipeline_name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/pipelines/{pipeline_name}/logs?&api_key={os.getenv("API_KEY")}'

    headers = {
        "Authorization": f"Bearer {token.token}"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=response.status_code, detail=response.json().get("error")["exception"])

    grouped_by_name = defaultdict(list)

    scheduler_logs = [scheduler_log for scheduler_log in response.json()["logs"][0]["pipeline_run_logs"] if scheduler_log["name"] == "scheduler.log"]

    for log in scheduler_logs:
        grouped_by_name[log["name"]].append(log)

    latest_logs_by_name = [max(logs, key=lambda x: x["modified_timestamp"]) for name, logs in
                           grouped_by_name.items()][0]

    usage = json.loads(latest_logs_by_name["content"].split('\n')[-2][20:])
    usage["cpu"] = float(f"{usage['cpu'] * 100:.2f}")
    usage["cpu_usage"] = float(f"{usage['cpu_usage'] * 100:.2f}")
    usage["memory_usage"] = float(f"{usage['memory_usage'] * 100:.2f}")

    key_mapping = {
        'cpu': 'CPU Utilization (%)',
        'cpu_total': 'Total CPU Cores',
        'cpu_usage': 'CPU Usage Ratio (%)',
        'memory': 'Memory Used (MB)',
        'memory_total': 'Total Memory (MB)',
        'memory_usage': 'Memory Usage Ratio (%)'
    }

    returns = {key_mapping[key]: value for i, (key, value) in enumerate(usage.items()) if i < 6}

    return JSONResponse(status_code=200, content=returns)


@router.get("/mage/log/pipeline/{pipeline_name}/{block_name}", tags=["LOGS GET"])
async def block_logs(pipeline_name: str, block_name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")

    url = f'{os.getenv("BASE_URL")}/api/pipelines/{pipeline_name}/logs?&api_key={os.getenv("API_KEY")}'

    headers = {
        "Authorization": f"Bearer {token.token}"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=response.status_code, detail=response.json().get("error")["exception"])

    grouped_by_name = defaultdict(list)

    block_logs = [block_logs for block_logs in response.json()["logs"][0]["block_run_logs"] if block_logs["name"] == f"{block_name}.log"]

    if len(block_logs) == 0:
        raise HTTPException(status_code=500, detail="Block does not exists or it does not have any logs yet!")

    for log in block_logs:
        grouped_by_name[log["name"]].append(log)

    latest_logs_by_name = [max(logs, key=lambda x: x["modified_timestamp"]) for name, logs in
                           grouped_by_name.items()][0]

    contents = []
    for content in latest_logs_by_name["content"].split("\n"):
        try:
            contents.append(json.loads(content[20:]))
        except JSONDecodeError:
            continue

    returns = []
    start = False
    for content in contents:
        if not start:
            if content["message"] != "Start executing block with BlockExecutor.":
                continue
            else:
                start = True
        elif "-----" in content["message"]:
            break
        else:
            returns.append({
                "Log Level": content["level"],
                "Timestamp": content["timestamp"],
                "Message": content["message"],
            })

    return JSONResponse(status_code=200, content=returns)
