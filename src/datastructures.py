import uuid
from enum import Enum
from typing import List

from pydantic import BaseModel


class GenerationRequest(BaseModel):
    source: str
    query_id: uuid.UUID = uuid.uuid4()


class CheckRequest(BaseModel):
    id: uuid.UUID = uuid.uuid4()
    source: str
    chunk: str


class CheckResponseItem(BaseModel):
    sentence: str
    reason: str
    facts_in_source: str


class CheckResponse(BaseModel):
    id: uuid.UUID
    reason: str
    result: str
    input_sentence: str
    answers: List[CheckResponseItem]


class OpenAiModel(Enum):
    gpt51 = ("GPT-5.1", "BR-GPT-5.1-2025-11-13-Misc")

    def __init__(self, public_name, deployment):
        self._value_ = public_name
        self.deployment = deployment
