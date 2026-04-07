from fastapi import APIRouter, HTTPException
from app.models.crawler import CrawlTask, CrawlerConfig
from app.services.crawler import crawler_service
import uuid

router = APIRouter()

@router.post("/tasks", response_model=CrawlTask)
async def create_crawl_task(config: CrawlerConfig):
    """创建爬取任务"""
    task_id = str(uuid.uuid4())
    task = CrawlTask(task_id=task_id, config=config)
    crawler_service.start_crawl(task_id, config.dict())
    return task

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    status = crawler_service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    return status

@router.post("/tasks/{task_id}/stop")
async def stop_crawl_task(task_id: str):
    """停止爬取任务"""
    status = crawler_service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    crawler_service.stop_crawl(task_id)
    return {"message": "任务已停止", "task_id": task_id}

@router.get("/tasks")
async def list_tasks():
    """获取所有任务列表"""
    return list(crawler_service.running_tasks.values())
