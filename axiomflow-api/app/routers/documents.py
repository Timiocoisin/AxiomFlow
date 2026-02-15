from pathlib import Path
import io
import base64

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, Response

from ..repo import repo
from ..core.dependencies import get_current_user
from ..db.schema import User

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}", response_model=dict)
async def get_document(document_id: str) -> dict:
    """
    获取文档的完整 JSON 数据。
    如果文档还在解析中（JSON 尚未创建），返回基本信息。
    """
    try:
        return repo.load_document_json(document_id)
    except FileNotFoundError:
        # 文档还在解析中，返回基本信息
        # 直接从数据库获取文档基本信息
        if hasattr(repo, "_get_session"):
            from ..db.schema import Document as DocumentModel
            with repo._get_session() as session:
                doc = session.query(DocumentModel).filter(DocumentModel.id == document_id).first()
                if not doc:
                    raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
                
                # 返回基本信息结构，与完整 JSON 格式兼容
                return {
                    "document": {
                        "document_id": doc.id,
                        "title": doc.title or "",
                        "num_pages": doc.num_pages or 0,
                        "lang_in": doc.lang_in or "en",
                        "lang_out": doc.lang_out or "zh",
                        "status": doc.status or "parsing",
                        "source_pdf_path": doc.source_pdf_path or "",
                    },
                    "pages": [],  # 解析中，页面为空
                }
        else:
            # InMemoryRepo 或其他实现，返回 404
            raise HTTPException(status_code=404, detail=f"Document {document_id} JSON not yet created")
    except KeyError as e:
        if "document_not_found" in str(e):
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        raise


@router.get("/{document_id}/source")
async def download_source_pdf(document_id: str):
    """
    下载原始上传的 PDF（给前端 pdf.js 画布渲染用）。
    """
    data = repo.load_document_json(document_id)
    src = (data.get("document") or {}).get("source_pdf_path")
    if not src:
        raise HTTPException(status_code=404, detail="source_pdf_not_found")

    path = Path(str(src))
    # 安全：必须位于 uploads 目录下（避免任意文件读取）
    try:
        uploads_root = repo.paths.uploads.resolve()
        if uploads_root not in path.resolve().parents and path.resolve() != uploads_root:
            raise HTTPException(status_code=400, detail="invalid_source_pdf_path")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid_source_pdf_path") from exc

    if not path.exists():
        raise HTTPException(status_code=404, detail="source_pdf_missing_on_disk")

    filename = path.name
    return FileResponse(path, filename=filename, media_type="application/pdf")


@router.get("/{document_id}/translated")
async def download_translated_pdf(document_id: str):
    """
    下载翻译后的 PDF（给前端 pdf.js 画布渲染用）。
    """
    try:
        data = repo.load_document_json(document_id)
        translated_path = (data.get("document") or {}).get("translated_pdf_path")
        
        if not translated_path:
            raise HTTPException(status_code=404, detail="translated_pdf_not_found")

        # 处理路径：支持绝对路径和相对路径
        path = Path(str(translated_path))
        
        # 如果是相对路径，则相对于 exports 目录
        if not path.is_absolute():
            path = repo.paths.exports / path
        
        # 安全：必须位于 exports 目录下（避免任意文件读取）
        try:
            exports_root = repo.paths.exports.resolve()
            path_resolved = path.resolve()
            if exports_root not in path_resolved.parents and path_resolved != exports_root:
                raise HTTPException(status_code=400, detail="invalid_translated_pdf_path")
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid_translated_pdf_path") from exc

        if not path.exists():
            raise HTTPException(status_code=404, detail="translated_pdf_missing_on_disk")

        filename = f"{document_id}_translated.pdf"
        return FileResponse(path, filename=filename, media_type="application/pdf")
    except (KeyError, FileNotFoundError):
        raise HTTPException(status_code=404, detail="translated_pdf_not_found")


@router.get("/{document_id}/progress", response_model=dict)
async def get_document_progress(document_id: str) -> dict:
    """
    获取文档的实时进度信息（包括上传、解析、翻译等阶段）
    
    返回：
    - status: "uploading" | "parsing" | "parsed" | "translating" | "translated"
    - parse_progress: 0.0-100.0 (解析进度)
    - num_pages: 页面数（解析完成后才有）
    - parse_job: 解析任务信息（包含done/total/eta_s）
    - translate_job: 翻译任务信息（如果有）
    """
    try:
        data = repo.load_document_json(document_id)
        doc_info = data.get("document", {})
        num_pages = doc_info.get("num_pages", 0)
        pages = data.get("pages", [])
        
        # 检查是否有解析完成的标志
        is_parsed = num_pages > 0 or len(pages) > 0
        
        # 如果num_pages为0但pages有数据，更新num_pages
        if num_pages == 0 and len(pages) > 0:
            num_pages = len(pages)
        
        # 查找文档的解析Job（最新的parsing或success状态的job）
        parse_job = None
        try:
            jobs = repo.get_jobs_by_document_id(document_id)
            # 查找解析任务（stage为parsing的job）
            for job in jobs:
                stage = job.get("stage", "")
                # 解析任务通常是parsing阶段
                if stage == "parsing":
                    parse_job = job
                    break
        except Exception as e:
            logger = __import__("logging").getLogger(__name__)
            logger.warning(f"获取jobs失败: {e}")
        
        # 如果已解析完成
        if is_parsed:
            parse_progress = 100.0
            status = "parsed"
        else:
            # 如果文档存在但没有页面数据，尝试从Job获取真实进度
            if parse_job:
                parse_progress = float(parse_job.get("progress", 0.0)) * 100.0
                status = "parsing"
            else:
                # 没有Job信息，返回中间值
                parse_progress = 50.0
                status = "parsing"
        
        # 查找文档的翻译Job（stage为translating或success的job，但不是解析job）
        translate_job = None
        try:
            jobs = repo.get_jobs_by_document_id(document_id)
            for job in jobs:
                stage = job.get("stage", "")
                job_id = job.get("id")
                # 翻译任务（不是解析任务）
                if stage in ("translating", "success") and job_id != parse_job.get("id") if parse_job else True:
                    translate_job = job
                    break
        except Exception:
            pass
        
        return {
            "document_id": document_id,
            "status": status,
            "num_pages": num_pages,
            "parse_progress": parse_progress,
            "parse_job": parse_job,
            "translate_job": translate_job,
        }
    except (KeyError, FileNotFoundError, PermissionError) as e:
        # 文档JSON不存在或无法读取（可能还在上传/解析中）
        logger = __import__("logging").getLogger(__name__)
        logger.debug(f"文档JSON不存在或无法读取: {e}")
        
        # 如果是因为 document_not_found，先查找 Job
        if isinstance(e, KeyError) and "document_not_found" not in str(e):
            raise
        
        # 查找解析Job
        parse_job = None
        try:
            jobs = repo.get_jobs_by_document_id(document_id)
            for job in jobs:
                stage = job.get("stage", "")
                if stage == "parsing":
                    parse_job = job
                    break
        except Exception:
            pass
        
        if parse_job:
            # 有解析Job，说明在上传或解析中
            parse_progress = float(parse_job.get("progress", 0.0)) * 100.0
            status = "parsing" if parse_progress < 100 else "parsed"
        else:
            # 没有Job，可能还在上传
            parse_progress = 0.0
            status = "uploading"
        
        return {
            "document_id": document_id,
            "status": status,
            "num_pages": 0,
            "parse_progress": parse_progress,
            "parse_job": parse_job,
            "translate_job": None,
        }


@router.get("/{document_id}/thumbnail")
async def get_document_thumbnail(document_id: str, width: int = 300, height: int = 400):
    """
    获取PDF文档第一页的缩略图
    
    Args:
        document_id: 文档ID
        width: 缩略图宽度（默认300px）
        height: 缩略图高度（默认400px）
    
    Returns:
        PNG图片响应
    """
    try:
        # 直接从数据库获取 source_pdf_path，不依赖 JSON 数据
        # 这样即使文档还在解析中，也能生成缩略图
        src = None
        
        # 优先从数据库获取（适用于 MySQLRepo）
        if hasattr(repo, "_get_session"):
            from ..db.schema import Document as DocumentModel
            with repo._get_session() as session:
                doc = session.query(DocumentModel).filter(DocumentModel.id == document_id).first()
                if doc and doc.source_pdf_path:
                    src = doc.source_pdf_path
        
        # 如果数据库中没有，尝试从 JSON 获取（兼容 InMemoryRepo 或旧数据）
        if not src:
            try:
                data = repo.load_document_json(document_id)
                src = (data.get("document") or {}).get("source_pdf_path")
            except (FileNotFoundError, KeyError):
                pass  # JSON 不存在时继续，可能文档还在解析中
        
        if not src:
            raise HTTPException(status_code=404, detail="source_pdf_not_found")
        
        path = Path(str(src))
        # 安全：必须位于 uploads 目录下
        try:
            uploads_root = repo.paths.uploads.resolve()
            if uploads_root not in path.resolve().parents and path.resolve() != uploads_root:
                raise HTTPException(status_code=400, detail="invalid_source_pdf_path")
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid_source_pdf_path") from exc
        
        if not path.exists():
            raise HTTPException(status_code=404, detail="source_pdf_missing_on_disk")
        
        # 使用 PyMuPDF 生成第一页缩略图
        import fitz  # PyMuPDF
        from PIL import Image
        
        doc = fitz.open(path.as_posix())
        if len(doc) == 0:
            doc.close()
            raise HTTPException(status_code=400, detail="pdf_has_no_pages")
        
        # 获取第一页
        page = doc[0]
        
        # 计算缩放比例，保持宽高比
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height
        
        scale_x = width / page_width
        scale_y = height / page_height
        scale = min(scale_x, scale_y)  # 保持宽高比
        
        # 渲染页面为图片
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # 转换为PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # 如果图片尺寸小于目标尺寸，创建白色背景并居中
        if img.width < width or img.height < height:
            bg = Image.new("RGB", (width, height), color=(255, 255, 255))
            # 居中粘贴
            x = (width - img.width) // 2
            y = (height - img.height) // 2
            bg.paste(img, (x, y))
            img = bg
        
        # 转换为PNG字节流
        output = io.BytesIO()
        img.save(output, format="PNG")
        output.seek(0)
        
        doc.close()
        
        return Response(content=output.read(), media_type="image/png")
        
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"生成缩略图失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成缩略图失败: {str(e)}")


@router.patch("/{document_id}/blocks/{block_id}", response_model=dict)
async def edit_block_translation(document_id: str, block_id: str, payload: dict) -> dict:
    translated_text = (payload.get("translation") or "").strip()
    apply_all = bool(payload.get("apply_all_same_source", False))

    if apply_all:
        data = repo.load_document_json(document_id)
        target_src = None
        for page in data.get("pages", []):
            for block in page.get("blocks", []):
                if block.get("id") == block_id:
                    target_src = (block.get("text") or "").strip()
                    break
            if target_src:
                break
        if target_src:
            for page in data.get("pages", []):
                for block in page.get("blocks", []):
                    if (block.get("text") or "").strip() == target_src:
                        block["translation"] = translated_text
                        block["edited"] = True
                        block["edited_at"] = __import__("datetime").datetime.utcnow().isoformat()
            repo.save_document_json(document_id, data)
        else:
            repo.update_block_translation(document_id, block_id, translated_text)
    else:
        repo.update_block_translation(document_id, block_id, translated_text)
    return {"ok": True}


@router.delete("/{document_id}", response_model=dict)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    删除文档（只有文档所有者才能删除）
    
    Args:
        document_id: 文档ID
        current_user: 当前登录用户
        
    Returns:
        dict: 删除结果
    """
    # 验证文档是否存在以及用户权限
    if hasattr(repo, "_get_session"):
        from ..db.schema import Document as DocumentModel
        with repo._get_session() as session:
            doc = session.query(DocumentModel).filter(DocumentModel.id == document_id).first()
            if not doc:
                raise HTTPException(status_code=404, detail="文档不存在")
            
            # 检查用户权限：只有文档所有者才能删除
            if doc.user_id and doc.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="无权删除此文档")
    
    # 删除文档（包括数据库记录和相关文件）
    try:
        if hasattr(repo, "delete_document"):
            repo.delete_document(document_id)
        else:
            # InMemoryRepo 不支持删除，返回错误
            raise HTTPException(status_code=501, detail="当前存储后端不支持删除操作")
        
        return {"ok": True, "message": "文档已删除"}
    except KeyError as e:
        if "document_not_found" in str(e):
            raise HTTPException(status_code=404, detail="文档不存在")
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"删除文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")


@router.post("/batch/delete", response_model=dict)
async def batch_delete_documents(
    payload: dict,
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    批量删除文档（只有文档所有者才能删除）
    
    Args:
        payload: 包含 document_ids 列表的字典
        current_user: 当前登录用户
        
    Returns:
        dict: 删除结果，包含成功和失败的文档ID
    """
    document_ids = payload.get("document_ids", [])
    if not document_ids or not isinstance(document_ids, list):
        raise HTTPException(status_code=400, detail="document_ids 必须是文档ID列表")
    
    if len(document_ids) == 0:
        raise HTTPException(status_code=400, detail="至少需要提供一个文档ID")
    
    if len(document_ids) > 100:
        raise HTTPException(status_code=400, detail="一次最多只能删除100个文档")
    
    success_ids = []
    failed_ids = []
    
    if hasattr(repo, "_get_session"):
        from ..db.schema import Document as DocumentModel
        
        # 批量验证权限
        with repo._get_session() as session:
            docs = session.query(DocumentModel).filter(
                DocumentModel.id.in_(document_ids)
            ).all()
            
            # 检查每个文档的权限
            for doc in docs:
                if doc.user_id and doc.user_id != current_user.id:
                    failed_ids.append({
                        "document_id": doc.id,
                        "reason": "无权删除此文档"
                    })
                else:
                    success_ids.append(doc.id)
            
            # 检查是否有不存在的文档
            existing_ids = {doc.id for doc in docs}
            for doc_id in document_ids:
                if doc_id not in existing_ids:
                    failed_ids.append({
                        "document_id": doc_id,
                        "reason": "文档不存在"
                    })
    
    # 批量删除文档
    if hasattr(repo, "delete_document"):
        for doc_id in success_ids:
            try:
                repo.delete_document(doc_id)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"删除文档 {doc_id} 失败: {e}", exc_info=True)
                failed_ids.append({
                    "document_id": doc_id,
                    "reason": f"删除失败: {str(e)}"
                })
                # 从成功列表中移除
                if doc_id in success_ids:
                    success_ids.remove(doc_id)
    else:
        raise HTTPException(status_code=501, detail="当前存储后端不支持删除操作")
    
    return {
        "ok": True,
        "success_count": len(success_ids),
        "failed_count": len(failed_ids),
        "success_ids": success_ids,
        "failed_ids": failed_ids
    }

