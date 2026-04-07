"""
中医知识图谱数据收集器

数据来源:
1. 《中医临床诊疗术语》- 核心数据源
2. 药智网 - 方剂、药物数据
3. 中医中药网 - 药物数据
4. A+ 医学百科 - 药物数据
5. 实验室历年收集的结构化数据

@author: TCM-KG-QA Team
@date: 2026-04
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
import requests
from bs4 import BeautifulSoup
import time
import re


class DataCollector:
    """数据收集器基类"""
    
    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_data(self, data: List[Dict], filename: str):
        """保存数据到 JSON 文件"""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已保存 {len(data)} 条数据到 {filepath}")
    
    def load_data(self, filename: str) -> List[Dict]:
        """从 JSON 文件加载数据"""
        filepath = self.output_dir / filename
        if not filepath.exists():
            return []
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)


class ClinicalTermsCollector(DataCollector):
    """《中医临床诊疗术语》数据收集器"""
    
    def __init__(self):
        super().__init__()
        self.terms_file = "中医临床诊疗术语.txt"
    
    def parse_disease_terms(self, file_path: str) -> List[Dict]:
        """
        解析疾病术语文件
        
        文件格式示例:
        疾病名称|病因|病类|症状
        痛风|湿热蕴结|筋骨病类|关节红肿热痛
        """
        diseases = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('|')
                if len(parts) >= 1:
                    disease = {
                        'name': parts[0].strip() if parts[0] else '',
                        'cause': parts[1].strip() if len(parts) > 1 and parts[1] else '',
                        'category': parts[2].strip() if len(parts) > 2 and parts[2] else '',
                        'symptoms': [s.strip() for s in parts[3].split(',') if s.strip()] if len(parts) > 3 and parts[3] else []
                    }
                    
                    if disease['name']:
                        diseases.append(disease)
            
            print(f"📄 解析到 {len(diseases)} 个疾病术语")
            return diseases
            
        except FileNotFoundError:
            print(f"⚠️  文件不存在：{file_path}")
            print("💡 请确保已将《中医临床诊疗术语》文件放在正确位置")
            return []
    
    def parse_syndrome_terms(self, file_path: str) -> List[Dict]:
        """解析证候术语文件"""
        syndromes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('|')
                if len(parts) >= 1:
                    syndrome = {
                        'name': parts[0].strip() if parts[0] else '',
                        'symptoms': [s.strip() for s in parts[1].split(',') if s.strip()] if len(parts) > 1 and parts[1] else [],
                        'therapy': parts[2].strip() if len(parts) > 2 and parts[2] else ''
                    }
                    
                    if syndrome['name']:
                        syndromes.append(syndrome)
            
            print(f"📄 解析到 {len(syndromes)} 个证候术语")
            return syndromes
            
        except FileNotFoundError:
            print(f"⚠️  文件不存在：{file_path}")
            return []
    
    def parse_therapy_terms(self, file_path: str) -> List[Dict]:
        """解析治法术语文件"""
        therapies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('|')
                if len(parts) >= 1:
                    therapy = {
                        'name': parts[0].strip() if parts[0] else '',
                        'effect': parts[1].strip() if len(parts) > 1 and parts[1] else '',
                        'syndromes': [s.strip() for s in parts[2].split(',') if s.strip()] if len(parts) > 2 and parts[2] else []
                    }
                    
                    if therapy['name']:
                        therapies.append(therapy)
            
            print(f"📄 解析到 {len(therapies)} 个治法术语")
            return therapies
            
        except FileNotFoundError:
            print(f"⚠️  文件不存在：{file_path}")
            return []


class WebCrawlerCollector(DataCollector):
    """网页爬虫数据收集器"""
    
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def crawl_yaozh_prescriptions(self, max_pages: int = 10) -> List[Dict]:
        """
        爬取药智网方剂数据
        
        数据结构:
        - 方名
        - 出处
        - 处方
        - 炮制
        - 功用
        - 主治
        """
        prescriptions = []
        base_url = "https://yp.yaozh.com/fangji"
        
        print("🕷️ 开始爬取药智网方剂数据...")
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{base_url}?page={page}"
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 解析方剂列表（需要根据实际网页结构调整选择器）
                items = soup.select('.fangji-item')
                
                for item in items:
                    prescription = {
                        'name': item.select_one('.name').get_text(strip=True) if item.select_one('.name') else '',
                        'source': item.select_one('.source').get_text(strip=True) if item.select_one('.source') else '',
                        'composition': item.select_one('.composition').get_text(strip=True) if item.select_one('.composition') else '',
                        'effects': item.select_one('.effects').get_text(strip=True) if item.select_one('.effects') else '',
                        'indications': item.select_one('.indications').get_text(strip=True) if item.select_one('.indications') else ''
                    }
                    
                    if prescription['name']:
                        prescriptions.append(prescription)
                
                print(f"  第 {page} 页：获取 {len(items)} 个方剂")
                time.sleep(1)  # 礼貌爬取
                
            except Exception as e:
                print(f"⚠️  爬取第 {page} 页失败：{e}")
                break
        
        print(f"✅ 共爬取 {len(prescriptions)} 个方剂")
        return prescriptions
    
    def crawl_herbs_from_sites(self) -> List[Dict]:
        """
        从多个网站爬取药物数据
        
        数据来源:
        - 药智网
        - 中医中药网
        - A+ 医学百科
        
        数据结构:
        - 药物名称
        - 别名
        - 性味
        - 归经
        - 功效
        - 主治
        - 典籍
        """
        herbs = []
        
        print("🕷️ 开始爬取多个网站的药物数据...")
        
        # 这里需要根据实际网站结构调整爬虫逻辑
        # 以下为示例代码
        
        # 药智网药物数据
        yaozh_herbs = self._crawl_yaozh_herbs()
        herbs.extend(yaozh_herbs)
        
        # 中医中药网药物数据
        tcm_herbs = self._crawl_tcm_herbs()
        herbs.extend(tcm_herbs)
        
        # A+ 医学百科药物数据
        apollo_herbs = self._crawl_apollo_herbs()
        herbs.extend(apollo_herbs)
        
        print(f"✅ 共爬取 {len(herbs)} 个药物")
        return herbs
    
    def _crawl_yaozh_herbs(self) -> List[Dict]:
        """爬取药智网药物数据"""
        herbs = []
        # TODO: 实现具体的爬取逻辑
        print("  📌 药智网药物数据爬取待实现")
        return herbs
    
    def _crawl_tcm_herbs(self) -> List[Dict]:
        """爬取中医中药网药物数据"""
        herbs = []
        # TODO: 实现具体的爬取逻辑
        print("  📌 中医中药网药物数据爬取待实现")
        return herbs
    
    def _crawl_apollo_herbs(self) -> List[Dict]:
        """爬取 A+ 医学百科药物数据"""
        herbs = []
        # TODO: 实现具体的爬取逻辑
        print("  📌 A+ 医学百科药物数据爬取待实现")
        return herbs


class LabDataCollector(DataCollector):
    """实验室历史数据收集器"""
    
    def __init__(self, lab_data_dir: str = "data/lab"):
        super().__init__()
        self.lab_data_dir = Path(lab_data_dir)
    
    def load_lab_prescriptions(self) -> List[Dict]:
        """加载实验室收集的方剂数据"""
        return self._load_structured_data("prescriptions.json")
    
    def load_lab_herbs(self) -> List[Dict]:
        """加载实验室收集的药物数据"""
        return self._load_structured_data("herbs.json")
    
    def _load_structured_data(self, filename: str) -> List[Dict]:
        """加载结构化数据"""
        filepath = self.lab_data_dir / filename
        
        if not filepath.exists():
            print(f"⚠️  实验室数据文件不存在：{filepath}")
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📄 加载 {len(data)} 条实验室数据 from {filename}")
        return data


def main():
    """主函数 - 演示数据收集流程"""
    
    print("=" * 60)
    print("中医知识图谱数据收集器")
    print("=" * 60)
    print()
    
    # 1. 收集《中医临床诊疗术语》数据
    print("📚 步骤 1: 收集《中医临床诊疗术语》数据")
    clinical_collector = ClinicalTermsCollector()
    
    # 假设文件已下载到 data/raw 目录
    diseases = clinical_collector.parse_disease_terms("data/raw/disease_terms.txt")
    syndromes = clinical_collector.parse_syndrome_terms("data/raw/syndrome_terms.txt")
    therapies = clinical_collector.parse_therapy_terms("data/raw/therapy_terms.txt")
    
    if diseases:
        clinical_collector.save_data(diseases, "clinical_diseases.json")
    if syndromes:
        clinical_collector.save_data(syndromes, "clinical_syndromes.json")
    if therapies:
        clinical_collector.save_data(therapies, "clinical_therapies.json")
    
    print()
    
    # 2. 爬取网页数据
    print("🕷️ 步骤 2: 爬取网页数据")
    web_collector = WebCrawlerCollector()
    
    # 爬取方剂数据
    prescriptions = web_collector.crawl_yaozh_prescriptions(max_pages=5)
    if prescriptions:
        web_collector.save_data(prescriptions, "web_prescriptions.json")
    
    # 爬取药物数据
    herbs = web_collector.crawl_herbs_from_sites()
    if herbs:
        web_collector.save_data(herbs, "web_herbs.json")
    
    print()
    
    # 3. 加载实验室数据
    print("🔬 步骤 3: 加载实验室历史数据")
    lab_collector = LabDataCollector()
    
    lab_prescriptions = lab_collector.load_lab_prescriptions()
    lab_herbs = lab_collector.load_lab_herbs()
    
    print()
    print("=" * 60)
    print("数据收集完成！")
    print("=" * 60)
    print()
    print("下一步:")
    print("1. 检查 data/raw 目录下的原始数据文件")
    print("2. 运行数据处理脚本进行清洗和对齐")
    print("3. 构建知识图谱")


if __name__ == "__main__":
    main()
