from pydantic import BaseModel, Field


class GlossaryUpsert(BaseModel):
    term: str = Field(min_length=1, max_length=200)
    translation: str = Field(min_length=1, max_length=200)


