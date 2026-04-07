from typing import Dict, List
import requests
from bs4 import BeautifulSoup
from loguru import logger
import time
from datetime import datetime

class CrawlerService:
    def __init__(self):
        self.running_tasks = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def start_crawl(self, task_id: str, config: Dict):
        """启动爬虫任务"""
        logger.info(f"启动爬虫任务：{task_id}")
        self.running_tasks[task_id] = {
            'config': config,
            'status': 'running',
            'items': 0,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'error': None
        }
        
        # 异步执行爬取任务
        import threading
        thread = threading.Thread(target=self._crawl_task, args=(task_id, config))
        thread.daemon = True
        thread.start()
    
    def _crawl_task(self, task_id: str, config: Dict):
        """实际执行的爬取任务"""
        try:
            url = config.get('url', '')
            depth = config.get('depth', 1)
            
            if not url:
                raise ValueError("请提供 URL")
            
            logger.info(f"开始爬取：{url}, 深度：{depth}")
            
            # 简单的单页面爬取示例
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            title = soup.find('h1')
            title_text = title.get_text().strip() if title else "无标题"
            
            # 提取所有链接
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().strip()
                if href.startswith('http') and text:
                    links.append({'text': text, 'url': href})
            
            # 更新任务状态
            self.running_tasks[task_id].update({
                'status': 'completed',
                'items': len(links),
                'end_time': datetime.now().isoformat(),
                'result': {
                    'title': title_text,
                    'links_count': len(links),
                    'sample_links': links[:10]  # 只保存前 10 个链接
                }
            })
            
            logger.info(f"爬取完成：{task_id}, 找到 {len(links)} 个链接")
            
        except Exception as e:
            logger.error(f"爬取失败：{task_id}, 错误：{e}")
            self.running_tasks[task_id].update({
                'status': 'failed',
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })
    
    def stop_crawl(self, task_id: str):
        """停止爬虫任务"""
        if task_id in self.running_tasks:
            self.running_tasks[task_id]['status'] = 'stopped'
            logger.info(f"已停止任务：{task_id}")
    
    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        return self.running_tasks.get(task_id, {})

crawler_service = CrawlerService()
