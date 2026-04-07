from pydantic import BaseModel
from typing import Optional, List

class QuestionInput(BaseModel):
    question: str
    top_k: int = 5

class AnswerOutput(BaseModel):
    answer: str
    confidence: float
    entities: List[str]
    relations: List[str]
    evidence: Optional[str] = None

class IntentType:
    DISEASE_QUERY = "disease_query"
    HERB_RECOMMEND = "herb_recommend"
    PRESCRIPTION_QUERY = "prescription_query"
    SYMPTOM_QUERY = "symptom_query"
    GENERAL = "general"

class IntentResult(BaseModel):
    intent: str
    keywords: List[str]
    confidence: float
