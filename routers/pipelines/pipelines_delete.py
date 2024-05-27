import os
import requests
import threading
from queue import Queue
from dependencies import Token
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse


router = APIRouter()

token = Token()


@router.delete("/mage/pipeline/delete", tags=["PIPELINES DELETE"])
async def delete_pipeline(name: str):
    if token.check_token_expired():
        token.update_token()
    if token.token == "":
        raise HTTPException(status_code=500, detail="Could not get the token!")
    
    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}/pipeline_schedules?api_key={os.getenv("API_KEY")}'
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=response.status_code, detail="Could not get triggers!")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.token}",
        "X-API-KEY": os.getenv("API_KEY")
    }

    error_queue = Queue()


    def delete_schedule(schedule_id: int, headers: dict[str, str]) -> None:
        response = requests.request(
            "DELETE", 
            f'{os.getenv("BASE_URL")}/api/pipeline_schedules/{schedule_id}?api_key={os.getenv("API_KEY")}', 
            headers=headers
        )

        if response.status_code != 200 or response.json().get("error") is not None:
            error_queue.put(schedule_id)


    pipeline_schedules  = response.json()["pipeline_schedules"] if len(response.json()["pipeline_schedules"]) > 0 else None


    if pipeline_schedules  is not None:
        threads = []

        for schedule in pipeline_schedules:
            thread = threading.Thread(target=delete_schedule, args=(schedule["id"], headers))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        errors = error_queue.qsize()

        if errors > 0:
            raise HTTPException(status_code=500, detail=f"Could not delete all the triggers for pipeline {name}")
    

    url = f'{os.getenv("BASE_URL")}/api/pipelines/{name}'

    response = requests.request("DELETE", url, headers=headers)

    if response.status_code != 200 or response.json().get("error") is not None:
        raise HTTPException(status_code=500, detail=f"Encounter an error when deleting pipeline {name}!")

    return JSONResponse(status_code=200, content="Pipeline deleted successfully!")

