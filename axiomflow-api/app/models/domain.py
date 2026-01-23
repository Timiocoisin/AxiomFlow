from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    pending = "pending"
    parsed = "parsed"
    translating = "translating"
    translated = "translated"
    exporting = "exporting"
    completed = "completed"
    failed = "failed"


class JobStage(str, Enum):
    pending = "pending"
    parsing = "parsing"
    translating = "translating"
    composing = "composing"
    exporting = "exporting"
    success = "success"
    failed = "failed"
    canceled = "canceled"


class BBox(BaseModel):
    page: int = Field(..., ge=0)
    x0: float
    y0: float
    x1: float
    y1: float


class BlockType(str, Enum):
    paragraph = "paragraph"
    heading = "heading"
    caption = "caption"
    formula = "formula"
    figure = "figure"
    table = "table"


class Document(BaseModel):
    id: str
    project_id: str
    title: Optional[str] = None
    num_pages: int
    lang_in: str
    lang_out: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime


class Block(BaseModel):
    id: str
    document_id: str
    type: BlockType
    bbox: BBox
    reading_order: int
    text: str


class TranslationUnit(BaseModel):
    id: str
    block_id: str
    source_text: str
    translated_text: Optional[str] = None
    edited: bool = False
    edited_at: Optional[datetime] = None


class Job(BaseModel):
    id: str
    document_id: str
    stage: JobStage
    progress: float = 0.0
    message: Optional[str] = None
    # v0.9+: richer progress for single-user UX
    done: Optional[int] = None
    total: Optional[int] = None
    eta_s: Optional[float] = None
    control: Optional[str] = None  # running/paused/canceled
    celery_task_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


