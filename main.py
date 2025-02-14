from routers.pipelines import pipelines_get, pipelines_post, pipelines_put, pipelines_delete
from fastapi import FastAPI, WebSocket, Form, UploadFile, HTTPException
from routers.blocks import blocks_get, blocks_post, blocks_put, blocks_delete
from rag.rag import retriever, run_workflow, node_description, apply_ruff
from routers.files import files_get, files_post, files_delete
from scalar_fastapi import get_scalar_api_reference
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from routers.websock import sock as websock
from utils.models import Query, Server
from langchain.schema import Document
from pydantic import ValidationError
from routers.logs import logs_get
from routers.validate import sock
from rag.data import add_document
from typing import Annotated
import asyncio
import uvicorn
import os

app = FastAPI(openapi_url="/mage/openapi.json", docs_url="/mage/docs", title="MageAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipelines_get.router)

app.include_router(pipelines_post.router)

app.include_router(pipelines_put.router)

app.include_router(pipelines_delete.router)

app.include_router(blocks_get.router)

app.include_router(blocks_post.router)

app.include_router(blocks_put.router)

app.include_router(blocks_delete.router)

app.include_router(logs_get.router)

app.include_router(files_get.router)

app.include_router(files_post.router)

app.include_router(files_delete.router)

app.include_router(websock.router)

app.include_router(sock.router)


@app.get("/mage")
async def entry():
    return JSONResponse(content="Hello from server!", status_code=200)


@app.get("/mage/scalar")
async def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title
    )


@app.post("/mage/server/set", tags=["SERVER"])
async def server_set(server: Server):
    if server.base_url is None and server.email is None and server.password is None:
        return JSONResponse("Server configuration not modified!", 304)

    if server.base_url is not None:
        os.environ["BASE_URL"] = server.base_url
    if server.email is not None:
        os.environ["EMAIL"] = server.email
    if server.password is not None:
        os.environ["PASSWORD"] = server.password
    return JSONResponse(content="Changed configuration to new Mage server!", status_code=200)


@app.post("/mage/rag/add", tags=["BLOCKS POST"])
async def add_rag(block_type: Annotated[str, Form()],
                  name: Annotated[str, Form()],
                  file: UploadFile):
    file_data = file.file.read().decode("utf-8").replace("\n", "\\n")

    result = add_document(retriever, Document(file_data, metadata={"source": "orchestrator", "block_type": block_type}))

    if not result and len(result) == 0:
        raise HTTPException(status_code=500, detail="Ingestion failed!")

    return JSONResponse(content="Ingestion completed successfully!", status_code=200)


@app.websocket("/mage/block/generate")
async def rag_endpoint(websocket: WebSocket):
    await websocket.accept()

    data = await websocket.receive_json()

    try:
        data = Query(**data)
    except ValidationError:
        await websocket.send_json({
                                      "message": "Failed parsing the input.",
                                      "generation": None,
                                      "generation_status": False
                                  })
        await websocket.close(code=1003, reason="Input data should be a JSON that contains only one key called question!")

    question = data.question

    async for (message, is_final) in run_workflow(question):
        if not is_final:
            node_desc = node_description(message) if node_description(message) is not None else message
            returns = {
                "message": node_desc,
                "generation": None,
                "generation_status": is_final
            }
        else:
            formatted_code = apply_ruff(message)
            returns = {
                "message": None,
                "generation": formatted_code,
                "generation_status": is_final
            }

        await websocket.send_json(returns)

        await asyncio.sleep(0.0)

    await websocket.close()


if __name__ == '__main__':
    # If .env exists locally, use that for environment variables
    # In a docker image is built ignoring the .env so it can't appear in a container
    if os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv(".env")


    if os.getenv('AUTH') is None:
        print("AUTH env variable is required can be [true, false]")
        exit(1)
    else:
        if os.getenv('AUTH') == 'true':
            if os.getenv('EMAIL') is None or os.getenv('PASSWORD') is None:
                print("EMAIL or PASSWORD env variable not provided. If AUTH is true they are required!")
                exit(1)

    if os.getenv('BASE_URL') is None:
        print("BASE_URL env variable is required!")
        exit(1)

    if os.getenv('OLLAMA_URL') is None:
        print("OLLAMA_URL env variable is required!")
        exit(1)

    os.environ["API_KEY"] = "zkWlN0PkIKSN0C11CfUHUj84OT5XOJ6tDZ6bDRO2"

    uvicorn.run(app, host="0.0.0.0", ws_ping_timeout=1000.0)
