import requests
from bs4 import BeautifulSoup
from loguru import logger
import time
import random

class TCMCrawler:
    """中医数据爬虫基类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.session.headers.update(self.headers)

    def fetch_page(self, url, retries=3):
        """获取页面内容，带重试机制"""
        for i in range(retries):
            try:
                # 随机延时，模拟人类行为，防止被封
                time.sleep(random.uniform(1, 3))
                response = self.session.get(url, timeout=10)
                response.encoding = response.apparent_encoding
                if response.status_code == 200:
                    return response.text
                else:
                    logger.warning(f"请求失败 [{response.status_code}]: {url}")
            except Exception as e:
                logger.error(f"请求异常 ({i+1}/{retries}): {e}")
        return None

    def parse(self, html_content):
        """解析页面内容（子类需实现）"""
        raise NotImplementedError

    def run(self, urls):
        """运行爬虫"""
        results = []
        for url in urls:
            logger.info(f"正在爬取: {url}")
            html = self.fetch_page(url)
            if html:
                data = self.parse(html)
                if data:
                    results.append(data)
        return results
