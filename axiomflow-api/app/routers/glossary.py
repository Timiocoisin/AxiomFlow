from fastapi import APIRouter

from ..repo import repo
from ..schemas.glossary import GlossaryUpsert

router = APIRouter(prefix="/projects", tags=["glossary"])


@router.get("/{project_id}/glossary", response_model=dict)
async def get_project_glossary(project_id: str) -> dict:
    return {"project_id": project_id, "glossary": repo.get_glossary(project_id)}


@router.post("/{project_id}/glossary", response_model=dict)
async def upsert_project_glossary(project_id: str, payload: GlossaryUpsert) -> dict:
    repo.upsert_glossary_term(project_id, payload.term, payload.translation)
    return {"ok": True}


@router.delete("/{project_id}/glossary", response_model=dict)
async def delete_project_glossary_term(project_id: str, term: str) -> dict:
    # 使用统一的 delete_glossary_term 方法
    if hasattr(repo, "delete_glossary_term"):
        repo.delete_glossary_term(project_id, term)
    else:
        # 向后兼容 InMemoryRepo 的直接访问
        g = repo.get_glossary(project_id)
        if term in g:
            if hasattr(repo, "glossaries"):
                repo.glossaries.setdefault(project_id, {}).pop(term, None)
    return {"ok": True}


