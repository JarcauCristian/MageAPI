import datetime
from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class Pipeline(BaseModel):
    variables: Dict[str, Any]
    run_id: int
    token: str


class Tag(BaseModel):
    name: str
    tag: str


class Description(BaseModel):
    name: str
    description: str


class Block(BaseModel):
    block_name: str
    pipeline_name: str
    downstream_blocks: List[str]
    upstream_blocks: List[str]


class DeleteBlock(BaseModel):
    block_name: str
    block_type: str
    pipeline_name: str
    force: bool


class Trigger(BaseModel):
    name: str
    trigger_type: str
    interval: Optional[str] = None
    start_time: Optional[datetime.datetime] = None


class Status(BaseModel):
    trigger_id: int
    status: str


class Variables(BaseModel):
    name: str
    variables: Dict[str, Any]


class Secret(BaseModel):
    name: str
    value: str


class UpdateTrigger(BaseModel):
    trigger_id: int
    status: str
    pipeline_uuid: str


class Query(BaseModel):
    block_type: str
    description: str


class Server(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    base_url: Optional[str] = None


class Rename(BaseModel):
    current_name: str
    new_name: str


class Validate(BaseModel):
    block_type: str
    content: str


class FileCreate(BaseModel):
    type: str
    name: str
    path: str
    overwrite: Optional[bool] = False
    content: Optional[str] = None
