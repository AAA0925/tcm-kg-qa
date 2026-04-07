"""
中医知识图谱数据处理器

功能:
1. 文本清洗（正则表达式）
2. 数据去重
3. 实体对齐（字典法）
4. 数据转换（转换为结构化格式）

@author: TCM-KG-QA Team
@date: 2026-04
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import defaultdict


class DataProcessor:
    """数据处理器"""
    
    def __init__(self, input_dir: str = "data/raw", output_dir: str = "data/processed"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 实体别名映射字典（用于实体对齐）
        self.entity_aliases = {
            '证候': {},  # 如：{'阴虚血热': '阴虚血热证', '血虚阳浮发热': '阴虚血热证'}
            '疾病': {},
            '症状': {},
            '治法': {},
            '药物': {},
            '方剂': {}
        }
    
    def clean_text(self, text: str) -> str:
        """
        清洗文本
        
        - 去除多余空格
        - 去除特殊字符
        - 规范化标点
        """
        if not text:
            return ""
        
        # 去除首尾空格
        text = text.strip()
        
        # 去除多余空格（多个空格变一个）
        text = re.sub(r'\s+', ' ', text)
        
        # 去除特殊字符（保留中文标点和基本符号）
        text = re.sub(r'[^\w\u4e00-\u9fff，。、；：？！（）《》【】""''…—]', '', text)
        
        # 规范化标点
        text = text.replace(',', '，')
        text = text.replace('.', '。')
        text = text.replace(';', '；')
        text = text.replace(':', '：')
        
        return text
    
    def split_herbs(self, prescription_text: str) -> List[str]:
        """
        从方剂处方中提取药物列表
        
        示例输入："柴胡 1 两，黄芩 1 分半，人参 1 分半"
        输出：['柴胡', '黄芩', '人参']
        """
        if not prescription_text:
            return []
        
        # 按逗号或空格分割
        items = re.split(r'[，,\s]+', prescription_text)
        
        herbs = []
        for item in items:
            item = item.strip()
            if not item:
                continue
            
            # 去除剂量（数字和单位）
            herb_name = re.sub(r'[\d 一二三四五六七八九十百千万亿两钱分克毫升]+', '', item)
            herb_name = herb_name.strip()
            
            # 去除常见后缀
            herb_name = re.sub(r' (炮 | 炙 | 炒 | 生 | 酒|醋)$', '', herb_name)
            
            if herb_name and len(herb_name) <= 10:  # 合理的药物名称长度
                herbs.append(herb_name)
        
        return herbs
    
    def deduplicate_entities(self, entities: List[Dict], key_field: str = 'name') -> List[Dict]:
        """
        实体去重
        
        根据关键字段去重，保留第一条出现的记录
        """
        seen = set()
        unique_entities = []
        
        for entity in entities:
            key = entity.get(key_field, '')
            if key and key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        print(f"📊 去重：{len(entities)} -> {len(unique_entities)} 条记录")
        return unique_entities
    
    def align_entity_name(self, name: str, entity_type: str) -> str:
        """
        实体名称对齐
        
        使用字典法将不同的表达方式统一为标准名称
        例如：'阴虚血热' -> '阴虚血热证'
        """
        if not name:
            return ""
        
        # 先去除前后空格
        name = name.strip()
        
        # 查找别名映射
        if entity_type in self.entity_aliases:
            aliases = self.entity_aliases[entity_type]
            # 检查是否是需要对齐的别名
            if name in aliases:
                return aliases[name]
        
        return name
    
    def load_alias_dict(self, filepath: str):
        """
        加载实体别名字典
        
        文件格式示例:
        标准名|别名 1, 别名 2, 别名 3
        阴虚血热证 | 阴虚血热，血虚阳浮发热证
        """
        if not Path(filepath).exists():
            print(f"⚠️  别名字典文件不存在：{filepath}")
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('|')
                if len(parts) >= 2:
                    standard_name = parts[0].strip()
                    aliases = [a.strip() for a in parts[1].split(',')]
                    
                    # 确定实体类型（通过文件名或内容判断）
                    # 这里简化处理，需要根据实际情况调整
                    for alias in aliases:
                        if '证' in standard_name:
                            self.entity_aliases['证候'][alias] = standard_name
                        elif any(d in standard_name for d in ['病', '症']):
                            self.entity_aliases['疾病'][alias] = standard_name
                        else:
                            self.entity_aliases['症状'][alias] = standard_name
        
        print(f"✅ 加载别名字典：共 {sum(len(v) for v in self.entity_aliases.values())} 个别名映射")
    
    def process_clinical_diseases(self, input_file: str, output_file: str):
        """
        处理临床疾病数据
        
        输出格式:
        {
            "name": "痛风",
            "category": "Disease",
            "cause": "湿热蕴结",
            "disease_class": "筋骨病类",
            "symptoms": ["关节红肿热痛"]
        }
        """
        input_path = self.input_dir / input_file
        if not input_path.exists():
            print(f"⚠️  输入文件不存在：{input_path}")
            return
        
        with open(input_path, 'r', encoding='utf-8') as f:
            diseases = json.load(f)
        
        processed = []
        for disease in diseases:
            # 清洗和规范化
            name = self.clean_text(disease.get('name', ''))
            cause = self.clean_text(disease.get('cause', ''))
            category = self.clean_text(disease.get('category', ''))
            symptoms = [self.clean_text(s) for s in disease.get('symptoms', [])]
            
            # 实体对齐
            name = self.align_entity_name(name, '疾病')
            category = self.align_entity_name(category, '病类')
            symptoms = [self.align_entity_name(s, '症状') for s in symptoms if s]
            
            if name:
                processed.append({
                    'name': name,
                    'category': 'Disease',
                    'cause': cause,
                    'disease_class': category,
                    'symptoms': symptoms
                })
        
        # 去重
        processed = self.deduplicate_entities(processed)
        
        # 保存
        output_path = self.output_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 处理完成：{len(processed)} 个疾病 -> {output_path}")
    
    def process_prescriptions(self, input_file: str, output_file: str):
        """
        处理方剂数据
        
        输出格式:
        {
            "name": "小柴胡汤",
            "category": "Prescription",
            "alias": "",
            "composition": ["柴胡", "黄芩", "人参", "甘草"],
            "source": "《伤寒论》",
            "effects": "和解少阳",
            "indications": "伤寒少阳证"
        }
        """
        input_path = self.input_dir / input_file
        if not input_path.exists():
            print(f"⚠️  输入文件不存在：{input_path}")
            return
        
        with open(input_path, 'r', encoding='utf-8') as f:
            prescriptions = json.load(f)
        
        processed = []
        for prescription in prescriptions:
            name = self.clean_text(prescription.get('name', ''))
            alias = self.clean_text(prescription.get('alias', ''))
            source = self.clean_text(prescription.get('source', ''))
            effects = self.clean_text(prescription.get('effects', ''))
            indications = self.clean_text(prescription.get('indications', ''))
            
            # 提取药物组成
            composition_text = self.clean_text(prescription.get('composition', ''))
            composition = self.split_herbs(composition_text)
            
            if name:
                processed.append({
                    'name': name,
                    'category': 'Prescription',
                    'alias': alias,
                    'composition': composition,
                    'source': source,
                    'effects': effects,
                    'indications': indications
                })
        
        # 去重
        processed = self.deduplicate_entities(processed)
        
        # 保存
        output_path = self.output_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 处理完成：{len(processed)} 个方剂 -> {output_path}")
    
    def process_herbs(self, input_file: str, output_file: str):
        """
        处理药物数据
        
        输出格式:
        {
            "name": "黄连",
            "category": "Herb",
            "alias": "川连",
            "property": "寒",
            "meridian": "心",
            "effects": "清热燥湿",
            "indications": "温热病"
        }
        """
        input_path = self.input_dir / input_file
        if not input_path.exists():
            print(f"⚠️  输入文件不存在：{input_path}")
            return
        
        with open(input_path, 'r', encoding='utf-8') as f:
            herbs = json.load(f)
        
        processed = []
        for herb in herbs:
            name = self.clean_text(herb.get('name', ''))
            alias = self.clean_text(herb.get('alias', ''))
            property_val = self.clean_text(herb.get('property', ''))
            meridian = self.clean_text(herb.get('meridian', ''))
            effects = self.clean_text(herb.get('effects', ''))
            indications = self.clean_text(herb.get('indications', ''))
            
            if name:
                processed.append({
                    'name': name,
                    'category': 'Herb',
                    'alias': alias,
                    'property': property_val,
                    'meridian': meridian,
                    'effects': effects,
                    'indications': indications
                })
        
        # 去重
        processed = self.deduplicate_entities(processed)
        
        # 保存
        output_path = self.output_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 处理完成：{len(processed)} 个药物 -> {output_path}")
    
    def merge_data_sources(self, output_file: str = "merged_tcm_data.json"):
        """
        合并所有数据源
        
        将处理后的各种数据合并成一个完整的数据集
        """
        all_data = {
            'diseases': [],
            'syndromes': [],
            'therapies': [],
            'prescriptions': [],
            'herbs': []
        }
        
        # 加载所有处理后的数据
        for data_type in all_data.keys():
            file_path = self.output_dir / f"processed_{data_type}.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_data[data_type] = json.load(f)
        
        # 保存合并后的数据
        output_path = self.output_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 数据合并完成：{output_path}")
        print(f"   - 疾病：{len(all_data['diseases'])} 条")
        print(f"   - 证候：{len(all_data['syndromes'])} 条")
        print(f"   - 治法：{len(all_data['therapies'])} 条")
        print(f"   - 方剂：{len(all_data['prescriptions'])} 条")
        print(f"   - 药物：{len(all_data['herbs'])} 条")


def main():
    """主函数 - 演示数据处理流程"""
    
    print("=" * 60)
    print("中医知识图谱数据处理器")
    print("=" * 60)
    print()
    
    processor = DataProcessor()
    
    # 加载实体别名字典（如果有的话）
    processor.load_alias_dict("data/raw/aliases.txt")
    print()
    
    # 处理各类数据
    print("📝 开始处理数据...")
    print()
    
    # 处理疾病数据
    processor.process_clinical_diseases(
        "clinical_diseases.json",
        "processed_diseases.json"
    )
    
    # 处理方剂数据
    processor.process_prescriptions(
        "web_prescriptions.json",
        "processed_prescriptions.json"
    )
    
    # 处理药物数据
    processor.process_herbs(
        "web_herbs.json",
        "processed_herbs.json"
    )
    
    print()
    
    # 合并数据
    processor.merge_data_sources()
    
    print()
    print("=" * 60)
    print("数据处理完成！")
    print("=" * 60)
    print()
    print("输出目录：data/processed/")
    print("下一步：运行知识图谱构建脚本")


if __name__ == "__main__":
    main()
