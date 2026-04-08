import json
import os
from loguru import logger
from app.services.crawler.zysj_crawler import ZysjCrawler

def run_crawler():
    """运行中医数据爬虫"""
    logger.info("开始执行中医数据爬取任务...")
    
    # 示例 URL 列表 (实际使用时可以扩充为成百上千个链接)
    target_urls = [
        "https://www.zysj.com.cn/lilunshuji/zhongyijichulilun/1.html",  # 示例链接
        # 你可以添加更多具体的疾病页面链接
    ]

    crawler = ZysjCrawler()
    results = crawler.run(target_urls)

    # 保存结果
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "raw_crawled_data.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    logger.success(f"爬取完成！共获取 {len(results)} 条数据，已保存至 {output_file}")

if __name__ == "__main__":
    run_crawler()
