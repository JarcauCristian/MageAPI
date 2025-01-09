from typing import Any
import numpy as np
import subprocess
import requests
import time

BASE_URL = "https://endpoints.sedimark.work"
times = []


def time_wrapper(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        times.append(round(end_time - start_time, 4))
        print(f"Execution time: {end_time - start_time:.2f} seconds")
        return result
    return wrapper


def pipe_info(name: str) -> dict[str, Any]:
    url = f"{BASE_URL}/mage/pipeline/triggers?name={name}"

    response = requests.request("GET", url)

    response.raise_for_status()

    return response.json()


@time_wrapper
def run_pipe(name: str, info: dict[str, Any]) -> None:
    url = f"{BASE_URL}/mage/pipeline/run"

    body = {
        "variables": info["variables"],
        "run_id": info["id"],
        "token": info["token"],
    }

    response = requests.request("POST", url, json=body)

    response.raise_for_status()

    url = f"{BASE_URL}/mage/pipeline/status/batch?pipeline_id={info['id']}"

    response = requests.request("GET", url)
    response.raise_for_status()

    status = response.text
    counter = 0

    while status not in ['"completed"', '"failed"', '"cancelled"'] or counter < 60:
        response = requests.request("GET", url)
        if response.status_code == 200:
            status = response.text
        if status == '"completed"':
            break
        counter += 1


@time_wrapper
def run_cwl(name: str):
    try:
        subprocess.run(["chmod", "+x", "run.sh"], cwd=f"cwl/{name}", check=True)
        subprocess.run(f"./run.sh", cwd=f"cwl/{name}", check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Pipeline: {e}")


def process(name: str):
    times.clear()

    info = pipe_info(name)

    info["variables"] = {}

    print("Getting times for Mage AI pipeline...")

    for i in range(5):
        run_pipe(name, info)

    print(f"Avg. time for Mage AI: {np.mean(times)}")

    times.clear()
    print("Getting times for CWL...")

    for i in range(5):
        run_cwl(name)

    print(f"Avg. time for CWL: {np.mean(times)}")


if __name__ == "__main__":
    print("Running for bowtie pipeline")
    process("bowtie")
    print("Running for cwl_test_1 pipeline")
    process("cwl_test_1")
