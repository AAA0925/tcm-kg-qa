from fastapi import APIRouter, HTTPException, Query
from app.models.entities import EntityCreate, RelationCreate
from app.services.kg import kg_client

router = APIRouter()

# ==================== 统计信息 ====================

@router.get("/stats")
async def get_statistics():
    try:
        return kg_client.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 实体类型和关系类型 ====================

@router.get("/entity-types")
async def get_entity_types():
    """获取所有实体类型"""
    try:
        return {"types": kg_client.get_entity_types()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/relation-types")
async def get_relation_types():
    """获取所有关系类型"""
    try:
        return {"types": kg_client.get_relation_types()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 实体CRUD ====================

@router.get("/entities")
async def list_entities(
    category: str = Query(None, description="实体类型筛选"),
    limit: int = Query(100, description="返回数量限制"),
    offset: int = Query(0, description="偏移量")
):
    """查询实体列表"""
    try:
        return kg_client.list_entities(category, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entities/{entity_name}")
async def get_entity_relations(entity_name: str, enable_fuzzy: bool = False):
    """查询实体及其关系（用于可视化）"""
    try:
        results = kg_client.query_by_entity(entity_name, enable_fuzzy)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/entities")
async def create_entity(entity: EntityCreate):
    """创建实体"""
    try:
        kg_client.create_entity(entity.name, entity.category, entity.properties)
        return {"message": "实体创建成功", "entity": entity}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/entities/{entity_name}")
async def update_entity(entity_name: str, entity: EntityCreate):
    """更新实体"""
    try:
        success = kg_client.update_entity(entity_name, entity.category, entity.properties)
        if success:
            return {"message": "实体更新成功"}
        else:
            raise HTTPException(status_code=404, detail="实体不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/entities/{entity_name}")
async def delete_entity(entity_name: str):
    """删除实体及其关系"""
    try:
        success = kg_client.delete_entity(entity_name)
        if success:
            return {"message": "实体删除成功"}
        else:
            raise HTTPException(status_code=404, detail="实体不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 关系CRUD ====================

@router.get("/relations")
async def list_relations(
    source_entity: str = Query(None, description="源实体筛选"),
    target_entity: str = Query(None, description="目标实体筛选"),
    relation_type: str = Query(None, description="关系类型筛选"),
    limit: int = Query(100, description="返回数量限制"),
    offset: int = Query(0, description="偏移量")
):
    """查询关系列表"""
    try:
        return kg_client.list_relations(source_entity, target_entity, relation_type, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/relations")
async def create_relation(relation: RelationCreate):
    """创建关系"""
    try:
        kg_client.create_relation(
            relation.source_entity,
            relation.target_entity,
            relation.relation_type,
            relation.properties
        )
        return {"message": "关系创建成功", "relation": relation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/relations/{source}/{target}/{relation_type}")
async def update_relation(
    source: str, 
    target: str, 
    relation_type: str,
    relation: RelationCreate
):
    """更新关系"""
    try:
        success = kg_client.update_relation(
            source, 
            target, 
            relation_type,
            relation.relation_type if relation.relation_type != relation_type else None,
            relation.properties
        )
        if success:
            return {"message": "关系更新成功"}
        else:
            raise HTTPException(status_code=404, detail="关系不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/relations/{source}/{target}/{relation_type}")
async def delete_relation(source: str, target: str, relation_type: str):
    """删除关系"""
    try:
        success = kg_client.delete_relation(source, target, relation_type)
        if success:
            return {"message": "关系删除成功"}
        else:
            raise HTTPException(status_code=404, detail="关系不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 图谱展开 ====================

@router.post("/expand/{entity_name}")
async def expand_entity_relations(entity_name: str, depth: int = 1, limit: int = 50):
    try:
        results = kg_client.expand_entity(entity_name, depth, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
