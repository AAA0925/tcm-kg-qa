from pydantic import BaseModel
from typing import Optional, List

class EntityBase(BaseModel):
    name: str
    category: str
    description: Optional[str] = None

class EntityCreate(EntityBase):
    properties: Optional[dict] = {}

class Entity(EntityBase):
    id: Optional[str] = None
    
    class Config:
        from_attributes = True

class RelationBase(BaseModel):
    source_entity: str
    target_entity: str
    relation_type: str

class RelationCreate(RelationBase):
    properties: Optional[dict] = {}

class Relation(RelationBase):
    id: Optional[str] = None
    
    class Config:
        from_attributes = True
