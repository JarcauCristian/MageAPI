from typing import List, Literal
from typing_extensions import TypedDict


class GraphState(TypedDict):
    question: str
    generation: str
    block_type: Literal["loader", "transformer", "exporter", "sensor"]
    documents: List[str]
