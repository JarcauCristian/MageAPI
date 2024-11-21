from routers.pipelines import pipelines_get, pipelines_post, pipelines_put, pipelines_delete
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form, UploadFile, HTTPException
from routers.blocks import blocks_get, blocks_post, blocks_put, blocks_delete
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from routers.websock import sock as websock
from contextlib import asynccontextmanager
from routers.logs import logs_get
from utils.models import Query, Server
from pydantic import ValidationError
from routers.files import files_get
from routers.validate import sock
from rag.ingester import Ingester
from rag.rag import RAGPipeline
from utils.linter import Linter
from typing import Annotated
from ollama import Client
import rag.utils as utils
from pathlib import Path
import chromadb
import uvicorn
import os


@asynccontextmanager
async def lifespan(_):
    global ing, rag, lint
    ollama_client = Client(os.getenv("OLLAMA_URL"))
    db_path_exists = os.path.exists("db")
    chroma_client = chromadb.PersistentClient("./db")
    ing = Ingester(ollama_client, chroma_client, "nomic-embed-text:latest", "nomic-ai/nomic-embed-text-v1", 1500)
    common_aliases = {
        "pd": "pandas",
        "np": "numpy",
        "plt": "matplotlib.pyplot",
        "sns": "seaborn",
        "nn": "torch.nn"
    }

    lint = Linter(common_aliases)

    if not db_path_exists:
        for p in Path("./blocks").glob("*"):
            if p.is_dir() and p.name in ["loaders", "transformers", "exporters", "configs"]:
                if p.name == "loaders":
                    utils.add_loaders(p.__str__(), ing)
                elif p.name == "transformers":
                    utils.add_transformers(p.__str__(), ing)
                elif p.name == "exporters":
                    utils.add_exporters(p.__str__(), ing)
                elif p.name == "configs":
                    utils.add_configs(p.__str__(), ing)

    rag = RAGPipeline(os.getenv("OLLAMA_URL"), "llama3.1:latest", ollama_client,
                      "nomic-embed-text:latest", chroma_client, "etl_pipelines_collection")

    yield
    del rag, ing, lint


app = FastAPI(openapi_url="/mage/openapi.json", docs_url="/mage/docs", lifespan=lifespan)

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

app.include_router(websock.router)

app.include_router(sock.router)


@app.get("/mage", tags=["ENTRY POINT"])
async def entry():
    return JSONResponse(content="Hello from server!", status_code=200)


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
                  description: Annotated[str, Form()],
                  file: UploadFile):
    file_data = file.file.read().decode("utf-8").replace("\n", "\\n")

    try:
        ing.ingest(file_data, f"{name}.py", block_type, description, os.getenv("CHROMA_COLLECTION"))
    except:
        raise HTTPException(detail="Encountered an error when ingesting data in the RAG. ", status_code=500)

    return JSONResponse(content="Ingestion completed successfully!", status_code=200)


@app.websocket("/mage/block/generate")
async def socket(websocket: WebSocket):
    await websocket.accept()
    validated_data = None
    try:
        while True:
            data = await websocket.receive_json()
            validated_data = Query(**data)

            if validated_data.block_type not in ["loader", "transformer", "exporter"]:
                await websocket.send_json({"detail": "Invalid block_type. Only loader, transformer and exporter are allowed!"})
            else:
                result_block = await get_model_response(validated_data)

                if result_block == "":
                    await websocket.send_json({"error": "Could not receive generated block from LLM. Please try again!"})
                else:
                    linted_code = lint.process(result_block)
                    await websocket.send_text(linted_code)
    except WebSocketDisconnect:
        await websocket.send_json({"detail": "Websocket disconnect successfully!"})
    except ValidationError:
        await websocket.send_json({"detail": "JSON validation error!"})


async def get_model_response(query: Query) -> str:
    block = f"[block_type={query.block_type}] {query.description}"
    result = rag.invoke(block)

    print(result)

    code = utils.preprocess_string(result)

    if code == "":
        return ""

    return code

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

    uvicorn.run(app, host="0.0.0.0")
