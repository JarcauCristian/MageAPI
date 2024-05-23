import uvicorn
from fastapi import FastAPI
from fastapi import FastAPI
from routers.kernels import kernels_get
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from routers.blocks import blocks_get, blocks_post, blocks_put, blocks_delete
from routers.pipelines import pipelines_get, pipelines_post, pipelines_put, pipelines_delete
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(openapi_url="/mage/openapi.json", docs_url="/mage/docs")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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


@app.get("/mage")
async def entry():
    return JSONResponse(content="Hello from server!", status_code=200)


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0")
