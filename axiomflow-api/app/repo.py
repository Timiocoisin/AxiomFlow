from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .core.ids import new_id


@dataclass
class RepoPaths:
    root: Path

    @property
    def uploads(self) -> Path:
        return self.root / "storage" / "uploads"

    @property
    def docs(self) -> Path:
        return self.root / "storage" / "documents"

    @property
    def exports(self) -> Path:
        return self.root / "storage" / "exports"

    @property
    def assets(self) -> Path:
        return self.root / "storage" / "assets"


class InMemoryRepo:
    """
    M1/M2：先用内存索引 + 磁盘JSON持久化（结构化文档），保证链路跑通。
    后续再替换为 DB（Postgres/SQLite）与对象存储。
    """

    def __init__(self, paths: RepoPaths):
        self.paths = paths
        self.paths.uploads.mkdir(parents=True, exist_ok=True)
        self.paths.docs.mkdir(parents=True, exist_ok=True)
        self.paths.exports.mkdir(parents=True, exist_ok=True)
        self.paths.assets.mkdir(parents=True, exist_ok=True)

        self.projects: dict[str, dict[str, Any]] = {}
        self.documents: dict[str, dict[str, Any]] = {}
        self.jobs: dict[str, dict[str, Any]] = {}
        self.batches: dict[str, dict[str, Any]] = {}  # batch_id -> info
        self.glossaries: dict[str, dict[str, str]] = {}  # project_id -> {term: translation}
        self.translation_memory: dict[str, str] = {}  # key -> translated_text

    def create_project(self, name: str) -> str:
        project_id = new_id("proj")
        now = datetime.utcnow().isoformat()
        self.projects[project_id] = {"id": project_id, "name": name, "created_at": now}
        return project_id

    # --- Glossary ---

    def upsert_glossary_term(self, project_id: str, term: str, translation: str) -> None:
        if project_id not in self.glossaries:
            self.glossaries[project_id] = {}
        self.glossaries[project_id][term] = translation

    def get_glossary(self, project_id: str) -> dict[str, str]:
        return dict(self.glossaries.get(project_id, {}))

    # --- Translation memory (parameterized cache) ---

    def tm_get(
        self,
        translate_engine: str,
        translate_params: dict[str, Any],
        original_text: str,
    ) -> str | None:
        """
        获取翻译缓存（参数化版本）。
        
        Args:
            translate_engine: 翻译服务名称
            translate_params: 参数字典（会被规范化）
            original_text: 原文
        
        Returns:
            缓存的译文，如果不存在则返回 None
        """
        from .cache_utils import serialize_params, build_cache_key
        
        params_str = serialize_params(translate_params)
        key = build_cache_key(translate_engine, params_str, original_text)
        return self.translation_memory.get(key)

    def tm_set(
        self,
        translate_engine: str,
        translate_params: dict[str, Any],
        original_text: str,
        translated_text: str,
    ) -> None:
        """
        设置翻译缓存（参数化版本，自动去重）。
        
        Args:
            translate_engine: 翻译服务名称
            translate_params: 参数字典（会被规范化）
            original_text: 原文
            translated_text: 译文
        """
        from .cache_utils import serialize_params, build_cache_key
        
        params_str = serialize_params(translate_params)
        key = build_cache_key(translate_engine, params_str, original_text)
        # 自动去重：相同的 key 会覆盖旧值
        self.translation_memory[key] = translated_text

    def save_upload(self, filename: str, content: bytes) -> tuple[str, Path]:
        doc_id = new_id("doc")
        safe_name = filename or f"{doc_id}.pdf"
        pdf_path = self.paths.uploads / f"{doc_id}__{safe_name}"
        pdf_path.write_bytes(content)
        return doc_id, pdf_path

    def create_document(
        self,
        document_id: str,
        project_id: str,
        title: str,
        lang_in: str = "en",
        lang_out: str = "zh",
        source_pdf_path: str = "",
    ) -> None:
        """创建文档记录（InMemoryRepo 不需要，因为不使用数据库）"""
        pass  # InMemoryRepo 不需要创建数据库记录

    def save_document_json(self, document_id: str, payload: dict[str, Any]) -> Path:
        out = self.paths.docs / f"{document_id}.json"
        out.write_text(__import__("json").dumps(payload, ensure_ascii=False), encoding="utf-8")
        self.documents[document_id] = {"id": document_id, "json_path": str(out)}
        return out

    def save_export_file(self, filename: str, content: bytes) -> Path:
        path = self.paths.exports / filename
        path.write_bytes(content)
        return path

    def save_asset_file(self, rel_path: str, content: bytes) -> Path:
        path = self.paths.assets / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def asset_path(self, rel_path: str) -> Path:
        return self.paths.assets / rel_path

    # --- Batch management ---

    def create_batch(self, *, project_id: str, document_ids: list[str]) -> str:
        batch_id = new_id("batch")
        now = datetime.utcnow().isoformat()
        self.batches[batch_id] = {
            "id": batch_id,
            "project_id": project_id,
            "document_ids": document_ids,
            "created_at": now,
            "updated_at": now,
        }
        return batch_id

    def get_batch(self, batch_id: str) -> dict[str, Any]:
        b = self.batches.get(batch_id)
        if not b:
            raise KeyError("batch_not_found")
        return b

    def update_batch(self, batch_id: str, **fields: Any) -> None:
        """更新批次信息"""
        batch = self.batches.get(batch_id)
        if not batch:
            raise KeyError("batch_not_found")
        batch.update(fields)
        batch["updated_at"] = datetime.utcnow().isoformat()

    def delete_glossary_term(self, project_id: str, term: str) -> None:
        """删除术语"""
        if project_id in self.glossaries:
            self.glossaries[project_id].pop(term, None)

    def load_document_json(self, document_id: str) -> dict[str, Any]:
        doc = self.documents.get(document_id)
        if not doc:
            raise KeyError("document_not_found")
        return __import__("json").loads(Path(doc["json_path"]).read_text(encoding="utf-8"))

    def update_block_translation(self, document_id: str, block_id: str, translated_text: str) -> None:
        data = self.load_document_json(document_id)
        for page in data.get("pages", []):
            for block in page.get("blocks", []):
                if block.get("id") == block_id:
                    block["translation"] = translated_text
                    block["edited"] = True
                    block["edited_at"] = datetime.utcnow().isoformat()
                    self.save_document_json(document_id, data)
                    return
        raise KeyError("block_not_found")

    # --- Job management (for simple in-memory queue/monitoring) ---

    def create_job(self, document_id: str, *, stage: str = "pending") -> str:
        job_id = new_id("job")
        now = datetime.utcnow().isoformat()
        self.jobs[job_id] = {
            "id": job_id,
            "document_id": document_id,
            "stage": stage,
            "progress": 0.0,
            "message": "",
            "done": 0,
            "total": None,
            "eta_s": None,
            "control": "running",  # running|paused|canceled
            "celery_task_id": None,
            "payload": None,  # store last TranslateJobCreate dict for retry
            "created_at": now,
            "updated_at": now,
        }
        return job_id

    def update_job(self, job_id: str, **fields: Any) -> None:
        job = self.jobs.get(job_id)
        if not job:
            raise KeyError("job_not_found")
        job.update(fields)
        job["updated_at"] = datetime.utcnow().isoformat()

    def get_job(self, job_id: str) -> dict[str, Any]:
        job = self.jobs.get(job_id)
        if not job:
            raise KeyError("job_not_found")
        return job.copy()

    def get_jobs_by_document_id(self, document_id: str) -> list[dict[str, Any]]:
        """根据document_id查找所有相关的jobs"""
        return [
            job.copy() for job in self.jobs.values()
            if job.get("document_id") == document_id
        ]

    def set_job_control(self, job_id: str, control: str) -> None:
        if control not in ("running", "paused", "canceled"):
            raise ValueError("invalid_control")
        self.update_job(job_id, control=control)


def get_repo():
    """
    获取 Repository 实例（根据配置选择 MySQL 或内存存储）
    
    如果配置了 MySQL 连接字符串，使用 MySQLRepo，否则使用 InMemoryRepo
    """
    from .core.config import settings

    root = Path(__file__).resolve().parents[1]
    paths = RepoPaths(root=root)

    # 如果配置了 MySQL 连接字符串，使用 MySQL Repository
    database_url = getattr(settings, "database_url", "")
    if database_url and database_url.startswith("mysql"):
        from .repo_mysql import get_repo_mysql

        return get_repo_mysql(database_url)

    # 否则使用内存存储（向后兼容）
    return InMemoryRepo(paths)


repo = get_repo()


