from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import qa, kg_management, crawler, search, auth, admin
from app.core.config import settings

app = FastAPI(
    title="中医知识图谱问答系统",
    description="基于知识图谱的中医智能问答平台",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理员"])
app.include_router(qa.router, prefix="/api/qa", tags=["问答"])
app.include_router(kg_management.router, prefix="/api/kg", tags=["知识图谱管理"])
app.include_router(crawler.router, prefix="/api/crawler", tags=["爬虫管理"])
app.include_router(search.router, prefix="/api/search", tags=["检索"])

@app.get("/")
async def root():
    return {"message": "中医知识图谱问答系统 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
