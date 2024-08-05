from routers.pipelines import pipelines_get, pipelines_post, pipelines_put, pipelines_delete
from routers.blocks import blocks_get, blocks_post, blocks_put, blocks_delete
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager
from routers.kernels import kernels_get
from utils.models import Query, Server
from pydantic import ValidationError
from routers.files import files_get
from rag.ingester import Ingester
from routers.websock import sock
from rag.rag import RAGPipeline
from utils.linter import Linter
from ollama import Client
import rag.utils as utils
from pathlib import Path
import chromadb
import uvicorn
import yaml
import os


@asynccontextmanager
async def lifespan(_):
    global ing, rag, lint
    ollama_client = Client(os.getenv("OLLAMA_URL"))
    db_path_exists = os.path.exists("db")
    chroma_client = chromadb.PersistentClient("./db")
    ing = Ingester(ollama_client, chroma_client, os.getenv("OLLAMA_EMBED_MODEL"), os.getenv("TOKENIZER"), int(os.getenv("MAX_TOKENS")))
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

    rag = RAGPipeline(os.getenv("OLLAMA_URL"), os.getenv("OLLAMA_MODEL"), ollama_client,
                      os.getenv("OLLAMA_EMBED_MODEL"), chroma_client, os.getenv("CHROMA_COLLECTION"))

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

app.include_router(kernels_get.router)

app.include_router(files_get.router)

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


@app.websocket("/mage/block/generate")
async def socket(websocket: WebSocket):
    await websocket.accept()
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
    result = rag.invoke(query.description)

    code = utils.preprocess_yaml_string(result["result"])

    if code == "":
        return ""

    yaml_response = yaml.safe_load(code)

    return yaml_response["python_code"]

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0")
