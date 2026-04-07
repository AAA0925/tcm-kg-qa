from fastapi import APIRouter, HTTPException
from app.models.qa import QuestionInput, AnswerOutput
from app.services.qa import qa_engine

router = APIRouter()

@router.post("/ask", response_model=AnswerOutput)
async def ask_question(question_input: QuestionInput):
    try:
        result = qa_engine.answer_question(
            question=question_input.question,
            top_k=question_input.top_k
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答处理失败：{str(e)}")
