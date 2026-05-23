from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional

class ModelName(str, Enum):
    Gemini_Flash_Latest = "gemini-flash-latest"

class QueryInput(BaseModel):
    question: str
    session_id: str = Field(default=None)
    model: ModelName = Field(default=ModelName.Gemini_Flash_Latest)
    file_id: Optional[int] = Field(default=None)
    language: str = Field(default="English")


class SourceCitation(BaseModel):
    file_id: Optional[int] = None
    source: Optional[str] = None
    page: Optional[int] = None
    snippet: str


class QueryResponse(BaseModel):
    answer: str
    session_id: str
    model: ModelName
    sources: list[SourceCitation] = Field(default_factory=list)
    source_count: int = 0
    confidence: str = "low"

class DocumentInfo(BaseModel):
    id: int
    filename: str
    upload_timestamp: datetime

class DeleteFileRequest(BaseModel):
    file_id: int
