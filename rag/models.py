from pydantic import BaseModel, Field
from typing import Literal


class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )


class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""

    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )


class BlockType(BaseModel):
    """Block type to assess the type of a block based on the question."""

    block_type: Literal["loader", "transformer", "exporter"] = Field(
        description="Given a user question choose the type of the block: loader, transformer, exporter"
    )
