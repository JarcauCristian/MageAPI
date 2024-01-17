from fastapi import FastAPI, Request
from fastapi import FastAPI
from dotenv import load_dotenv
import uvicorn
from routers import pipelines_get, pipelines_post, pipelines_put, pipelines_delete, blocks_get, blocks_post, blocks_put, blocks_delete
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from statistics.csv_statistics import CSVLoader

load_dotenv()

app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://localhost:8080",
]

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


@app.get("/")
async def entry():
    return JSONResponse(content="Hello from server!", status_code=200)


@app.get('/get_statistics')
async def get_statistics(dataset_path: str, req: Request):
    auth_token = req.headers.get('Authorization')

    if auth_token is None:
        return JSONResponse(status_code=401, content="You don't have access to this component")

    csv_loader = CSVLoader(path=dataset_path)
    csv_loader.execute(auth_token.split(" ")[0])

    return JSONResponse(status_code=200, content=csv_loader.get_statistics())


# if __name__ == '__main__':
#     uvicorn.run(app, host="0.0.0.0", port=8000)
