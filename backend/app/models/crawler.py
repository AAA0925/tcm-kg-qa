from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CrawlerConfig(BaseModel):
    source_urls: List[str]
    max_depth: int = 3
    crawl_interval: int = 1
    timeout: int = 30
    enabled: bool = True

class CrawlTask(BaseModel):
    task_id: Optional[str] = None
    config: CrawlerConfig
    status: str = "pending"
    created_at: datetime = datetime.now()
    completed_at: Optional[datetime] = None
    items_crawled: int = 0
