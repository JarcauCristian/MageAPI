import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Pipeline(BaseModel):
    variables: Dict[str, Any]
    run_id: int
    token: str


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
