from pydantic import BaseModel, Field


class TranslateJobCreate(BaseModel):
    document_id: str
    lang_in: str = Field(default="en", min_length=2)
    lang_out: str = Field(default="zh", min_length=2)
    provider: str = Field(default="google", min_length=1)

    # v0.8+: 高级翻译策略（可选；不传则使用后端默认策略）
    use_context: bool | None = None
    context_window_size: int | None = Field(default=None, ge=0, le=10)
    use_term_consistency: bool | None = None
    use_smart_batching: bool | None = None


class TranslateJobCreated(BaseModel):
    job_id: str


