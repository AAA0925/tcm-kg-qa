from fastapi import APIRouter
from app.services.kg import kg_client

router = APIRouter()

@router.get("/fulltext")
async def fulltext_search(keyword: str, limit: int = 10):
    results = kg_client.query_by_entity(keyword)
    return {"results": results, "total": len(results)}
