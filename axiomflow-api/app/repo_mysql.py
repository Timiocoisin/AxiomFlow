from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from .core.ids import new_id
from .db.schema import (
    Batch as BatchModel,
    Document as DocumentModel,
    GlossaryTerm as GlossaryTermModel,
    Job as JobModel,
    Project as ProjectModel,
    TranslationMemory as TranslationMemoryModel,
    init_db,
)


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


class MySQLRepo:
    """
    基于 MySQL 的数据持久化仓库
    使用 SQLAlchemy ORM 进行数据库操作，文件（PDF、JSON、导出文件）仍存储在磁盘上。
    """

    def __init__(self, paths: RepoPaths, database_url: str):
        self.paths = paths
        self.paths.uploads.mkdir(parents=True, exist_ok=True)
        self.paths.docs.mkdir(parents=True, exist_ok=True)
        self.paths.exports.mkdir(parents=True, exist_ok=True)
        self.paths.assets.mkdir(parents=True, exist_ok=True)

        # 初始化数据库连接
        self._engine, self._SessionLocal = init_db(database_url)

    @contextmanager
    def _get_session(self) -> Session:
        """获取数据库会话（上下文管理器）"""
        session = self._SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # --- Projects ---

    def create_project(self, name: str, user_id: str | None = None) -> str:
        project_id = new_id("proj")
        now = datetime.utcnow().isoformat()
        with self._get_session() as session:
            project = ProjectModel(id=project_id, name=name, user_id=user_id, created_at=now)
            session.add(project)
        return project_id

    # --- Documents ---

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
        user_id: str | None = None,
    ) -> None:
        """创建文档记录（在数据库中）"""
        now = datetime.utcnow().isoformat()
        with self._get_session() as session:
            doc = DocumentModel(
                id=document_id,
                project_id=project_id,
                user_id=user_id,
                title=title,
                num_pages=0,
                lang_in=lang_in,
                lang_out=lang_out,
                status="parsing",  # 初始状态为解析中
                json_path="",  # 解析完成后会更新
                source_pdf_path=source_pdf_path,
                created_at=now,
                updated_at=now,
            )
            session.add(doc)

    def save_document_json(self, document_id: str, payload: dict[str, Any]) -> Path:
        """保存文档 JSON 数据到数据库（不再使用文件系统）"""
        import json
        
        # 将 JSON 数据序列化为字符串
        json_str = json.dumps(payload, ensure_ascii=False)

        # 更新数据库中的文档记录
        with self._get_session() as session:
            doc = session.query(DocumentModel).filter(DocumentModel.id == document_id).first()
            doc_info = payload.get("document", {})
            
            if doc:
                # 存储 JSON 数据到数据库
                doc.json_data = json_str
                doc.updated_at = datetime.utcnow().isoformat()
                # 如果 payload 中包含文档信息，同步更新
                if doc_info:
                    doc.title = doc_info.get("title", doc.title)
                    doc.num_pages = doc_info.get("num_pages", doc.num_pages)
                    doc.lang_in = doc_info.get("lang_in", doc.lang_in)
                    doc.lang_out = doc_info.get("lang_out", doc.lang_out)
                    doc.status = doc_info.get("status", doc.status)
                    doc.source_pdf_path = doc_info.get("source_pdf_path", doc.source_pdf_path)
            else:
                # 如果文档不存在，创建记录
                project_id = doc_info.get("project_id", "") if doc_info else ""
                now = datetime.utcnow().isoformat()
                doc = DocumentModel(
                    id=document_id,
                    project_id=project_id,
                    title=doc_info.get("title", ""),
                    num_pages=doc_info.get("num_pages", 0),
                    lang_in=doc_info.get("lang_in", "en"),
                    lang_out=doc_info.get("lang_out", "zh"),
                    status=doc_info.get("status", "parsed"),
                    json_data=json_str,  # 存储 JSON 数据
                    json_path="",  # 不再使用文件路径
                    source_pdf_path=doc_info.get("source_pdf_path"),
                    created_at=now,
                    updated_at=now,
                )
                session.add(doc)

        # 返回一个虚拟路径（保持接口兼容性）
        return self.paths.docs / f"{document_id}.json"

    def load_document_json(self, document_id: str) -> dict[str, Any]:
        """从数据库加载文档 JSON 数据（不再从文件系统读取）"""
        import json
        
        with self._get_session() as session:
            doc = session.query(DocumentModel).filter(DocumentModel.id == document_id).first()
            if not doc:
                raise KeyError("document_not_found")
            
            # 优先从数据库的 json_data 字段读取
            if doc.json_data and doc.json_data.strip() and doc.json_data != "{}":
                return json.loads(doc.json_data)
            
            # 兼容旧数据：如果 json_data 为空但 json_path 存在，尝试从文件读取
            if doc.json_path and doc.json_path.strip():
                json_path = Path(doc.json_path)
                if json_path.exists():
                    data = json.loads(json_path.read_text(encoding="utf-8"))
                    # 迁移到数据库：保存到 json_data 字段
                    doc.json_data = json.dumps(data, ensure_ascii=False)
                    session.commit()
                    return data
            
            # 如果都没有，说明文档还在解析中
            raise FileNotFoundError(f"Document JSON not yet created: {document_id}")

    def get_documents_by_project_id(self, project_id: str, user_id: str | None = None) -> list[dict[str, Any]]:
        """获取项目下的所有文档列表（按用户ID过滤）"""
        with self._get_session() as session:
            query = session.query(DocumentModel).filter(
                DocumentModel.project_id == project_id
            )
            # 如果提供了user_id，只返回该用户的文档
            if user_id:
                query = query.filter(DocumentModel.user_id == user_id)
            
            docs = query.order_by(DocumentModel.created_at.desc()).all()
            
            return [
                {
                    "document_id": doc.id,
                    "title": doc.title or "",
                    "num_pages": doc.num_pages or 0,
                    "lang_in": doc.lang_in or "en",
                    "lang_out": doc.lang_out or "zh",
                    "status": doc.status or "parsed",
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at,
                }
                for doc in docs
            ]
    
    def get_documents_by_user_id(self, user_id: str) -> list[dict[str, Any]]:
        """获取用户的所有文档列表（不依赖项目）"""
        with self._get_session() as session:
            query = session.query(DocumentModel).filter(
                DocumentModel.user_id == user_id
            )
            docs = query.order_by(DocumentModel.created_at.desc()).all()
            
            return [
                {
                    "document_id": doc.id,
                    "project_id": doc.project_id,
                    "title": doc.title or "",
                    "num_pages": doc.num_pages or 0,
                    "lang_in": doc.lang_in or "en",
                    "lang_out": doc.lang_out or "zh",
                    "status": doc.status or "parsed",
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at,
                }
                for doc in docs
            ]

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

    # --- Exports & Assets ---

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

    # --- Glossary ---

    def upsert_glossary_term(self, project_id: str, term: str, translation: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._get_session() as session:
            existing = (
                session.query(GlossaryTermModel)
                .filter(GlossaryTermModel.project_id == project_id, GlossaryTermModel.term == term)
                .first()
            )
            if existing:
                existing.translation = translation
                existing.updated_at = now
            else:
                term_id = new_id("term")
                new_term = GlossaryTermModel(
                    id=term_id,
                    project_id=project_id,
                    term=term,
                    translation=translation,
                    created_at=now,
                    updated_at=now,
                )
                session.add(new_term)

    def get_glossary(self, project_id: str) -> dict[str, str]:
        with self._get_session() as session:
            terms = session.query(GlossaryTermModel).filter(GlossaryTermModel.project_id == project_id).all()
            return {term.term: term.translation for term in terms}

    def delete_glossary_term(self, project_id: str, term: str) -> None:
        with self._get_session() as session:
            existing = (
                session.query(GlossaryTermModel)
                .filter(GlossaryTermModel.project_id == project_id, GlossaryTermModel.term == term)
                .first()
            )
            if existing:
                session.delete(existing)

    # --- Translation Memory (Parameterized Cache) ---

    def tm_get(
        self,
        translate_engine: str,
        translate_params: dict[str, Any],
        original_text: str,
    ) -> str | None:
        """
        获取翻译缓存（参数化版本，使用组合唯一约束查询）。
        
        Args:
            translate_engine: 翻译服务名称
            translate_params: 参数字典（会被规范化）
            original_text: 原文
        
        Returns:
            缓存的译文，如果不存在则返回 None
        """
        from ..services.cache_utils import serialize_params
        
        params_str = serialize_params(translate_params)
        
        with self._get_session() as session:
            tm = (
                session.query(TranslationMemoryModel)
                .filter(
                    TranslationMemoryModel.translate_engine == translate_engine,
                    TranslationMemoryModel.translate_params == params_str,
                    TranslationMemoryModel.original_text == original_text,
                )
                .first()
            )
            return tm.translated_text if tm else None

    def tm_set(
        self,
        translate_engine: str,
        translate_params: dict[str, Any],
        original_text: str,
        translated_text: str,
    ) -> None:
        """
        设置翻译缓存（参数化版本，自动去重）。
        
        使用 MySQL 的唯一约束实现自动去重：
        - 如果记录已存在，则更新 translated_text 和 updated_at
        - 如果不存在，则创建新记录
        
        Args:
            translate_engine: 翻译服务名称
            translate_params: 参数字典（会被规范化）
            original_text: 原文
            translated_text: 译文
        """
        from ..services.cache_utils import serialize_params
        
        params_str = serialize_params(translate_params)
        now = datetime.utcnow().isoformat()
        
        with self._get_session() as session:
            existing = (
                session.query(TranslationMemoryModel)
                .filter(
                    TranslationMemoryModel.translate_engine == translate_engine,
                    TranslationMemoryModel.translate_params == params_str,
                    TranslationMemoryModel.original_text == original_text,
                )
                .first()
            )
            
            if existing:
                # 更新现有记录（自动去重）
                existing.translated_text = translated_text
                existing.updated_at = now
            else:
                # 创建新记录
                new_tm = TranslationMemoryModel(
                    translate_engine=translate_engine,
                    translate_params=params_str,
                    original_text=original_text,
                    translated_text=translated_text,
                    created_at=now,
                    updated_at=now,
                )
                session.add(new_tm)

    # --- Jobs ---

    def create_job(self, document_id: str, *, stage: str = "pending") -> str:
        job_id = new_id("job")
        now = datetime.utcnow().isoformat()
        with self._get_session() as session:
            job = JobModel(
                id=job_id,
                document_id=document_id,
                stage=stage,
                progress=0.0,
                message="",
                created_at=now,
                updated_at=now,
            )
            session.add(job)
        return job_id

    def update_job(self, job_id: str, **fields: Any) -> None:
        with self._get_session() as session:
            job = session.query(JobModel).filter(JobModel.id == job_id).first()
            if not job:
                raise KeyError("job_not_found")
            for key, value in fields.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            job.updated_at = datetime.utcnow().isoformat()

    def get_job(self, job_id: str) -> dict[str, Any]:
        with self._get_session() as session:
            job = session.query(JobModel).filter(JobModel.id == job_id).first()
            if not job:
                raise KeyError("job_not_found")
            return {
                "id": job.id,
                "document_id": job.document_id,
                "stage": job.stage,
                "progress": job.progress,
                "message": job.message,
                "done": getattr(job, "done", None),
                "total": getattr(job, "total", None),
                "eta_s": getattr(job, "eta_s", None),
                "control": getattr(job, "control", None),
                "celery_task_id": getattr(job, "celery_task_id", None),
                "created_at": job.created_at,
                "updated_at": job.updated_at,
            }

    def get_jobs_by_document_id(self, document_id: str) -> list[dict[str, Any]]:
        """根据document_id查找所有相关的jobs"""
        with self._get_session() as session:
            jobs = session.query(JobModel).filter(JobModel.document_id == document_id).order_by(JobModel.created_at.desc()).all()
            return [
                {
                    "id": job.id,
                    "document_id": job.document_id,
                    "stage": job.stage,
                    "progress": job.progress,
                    "message": job.message,
                    "done": getattr(job, "done", None),
                    "total": getattr(job, "total", None),
                    "eta_s": getattr(job, "eta_s", None),
                    "control": getattr(job, "control", None),
                    "celery_task_id": getattr(job, "celery_task_id", None),
                    "created_at": job.created_at,
                    "updated_at": job.updated_at,
                }
                for job in jobs
            ]

    # --- Batch management ---

    def create_batch(self, *, project_id: str, document_ids: list[str]) -> str:
        batch_id = new_id("batch")
        now = datetime.utcnow().isoformat()
        with self._get_session() as session:
            batch = BatchModel(
                id=batch_id,
                project_id=project_id,
                document_ids=document_ids,
                job_ids=[],
                created_at=now,
                updated_at=now,
            )
            session.add(batch)
        return batch_id

    def get_batch(self, batch_id: str) -> dict[str, Any]:
        with self._get_session() as session:
            batch = session.query(BatchModel).filter(BatchModel.id == batch_id).first()
            if not batch:
                raise KeyError("batch_not_found")
            return {
                "id": batch.id,
                "project_id": batch.project_id,
                "document_ids": batch.document_ids or [],
                "job_ids": batch.job_ids or [],
                "created_at": batch.created_at,
                "updated_at": batch.updated_at,
            }

    def update_batch(self, batch_id: str, **fields: Any) -> None:
        """更新批次信息（例如添加 job_ids）"""
        with self._get_session() as session:
            batch = session.query(BatchModel).filter(BatchModel.id == batch_id).first()
            if not batch:
                raise KeyError("batch_not_found")
            for key, value in fields.items():
                if hasattr(batch, key):
                    setattr(batch, key, value)
            batch.updated_at = datetime.utcnow().isoformat()


def get_repo_mysql(database_url: str) -> MySQLRepo:
    """获取 MySQL Repository 实例"""
    # root = AxiomFlow/axiomflow-api
    root = Path(__file__).resolve().parents[1]
    return MySQLRepo(RepoPaths(root=root), database_url=database_url)

