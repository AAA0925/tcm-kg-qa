from .base_crawler import TCMCrawler
from bs4 import BeautifulSoup
from loguru import logger
import re

class ZysjCrawler(TCMCrawler):
    """中医世家 (zysj.com.cn) 爬虫"""

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        data = {
            "title": "",
            "content": "",
            "symptoms": [],
            "treatments": []
        }

        # 1. 提取标题
        title_tag = soup.find('h1') or soup.find('title')
        if title_tag:
            data["title"] = title_tag.get_text(strip=True)

        # 2. 提取正文：尝试多种常见的中医网站内容容器
        content_div = (
            soup.find('div', id='content') or 
            soup.find('div', class_='content') or 
            soup.find('div', class_='article-content') or
            soup.find('div', id='article')
        )
        
        # 如果找不到特定容器，则提取所有 p 标签作为备选
        paragraphs = []
        if content_div:
            paragraphs = content_div.find_all(['p', 'div'])
        else:
            # 备选方案：抓取页面上长度超过 50 字的 p 标签
            paragraphs = [p for p in soup.find_all('p') if len(p.get_text(strip=True)) > 50]

        if paragraphs:
            texts = [p.get_text(separator=' ', strip=True) for p in paragraphs]
            full_text = '\n'.join(texts)
            # 清洗：去除多余空白和特殊字符
            data["content"] = re.sub(r'\s+', ' ', full_text).strip()
        
        return data if data["content"] else None
