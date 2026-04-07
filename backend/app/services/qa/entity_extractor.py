from typing import List
from loguru import logger
import re
from app.services.kg import kg_client

class EntityExtractor:
    """实体提取器 - 从用户问题中识别实体"""
    
    def __init__(self):
        self.kg_client = kg_client
    
    def extract(self, question: str) -> List[str]:
        """
        从问题中提取实体
        
        Args:
            question: 用户问题
            
        Returns:
            实体列表
        """
        entities = []
        
        # 方法1：去除问句特征词，提取核心关键词
        # 常见问句模式："XX有什么症状？"、"XX怎么治疗？"、"XX是什么？"
        question_patterns = [
            r'(.+?)有什么症状',
            r'(.+?)怎么治疗',
            r'(.+?)怎么治',
            r'(.+?)怎么办',
            r'(.+?)的症状',
            r'(.+?)的治疗方法',
            r'(.+?)是什么',
            r'(.+?)的功效',
            r'(.+?)的作用',
        ]
        
        for pattern in question_patterns:
            match = re.search(pattern, question)
            if match:
                entity_name = match.group(1).strip()
                if entity_name and len(entity_name) > 0:
                    entities.append(entity_name)
                    logger.info(f"模式匹配到实体: {entity_name}")
                    break  # 找到就停止
        
        # 方法2：如果方法1没找到，尝试用Neo4j模糊匹配
        if not entities:
            # 提取2-5个字符的连续文本
            stop_words = ["的", "了", "吗", "呢", "啊", "什么", "怎么", "如何", "为什么", "有", "是"]
            cleaned = re.sub(r'[？?，。！、；：""''（）【】《》]', '', question)
            
            # 尝试不同长度的词
            for length in [5, 4, 3, 2]:
                words = [cleaned[i:i+length] for i in range(len(cleaned)-length+1)]
                for word in words:
                    if word not in stop_words and len(word) >= 2:
                        # 在Neo4j中模糊搜索
                        try:
                            fuzzy_results = self.kg_client.query_by_entity(word, enable_fuzzy=True)
                            if fuzzy_results:
                                # 取第一个匹配的实体名
                                matched_name = fuzzy_results[0]["n"]["name"]
                                entities.append(matched_name)
                                logger.info(f"模糊匹配到实体: {matched_name} (关键词: {word})")
                                break
                        except:
                            pass
                if entities:
                    break
        
        # 方法3：如果还是没找到，使用整个问题的核心部分
        if not entities:
            # 去除常见问句词
            core = re.sub(r'(有什么|怎么|如何|为什么|的症状|的治疗|怎么办|是什么)', '', question)
            core = core.strip()
            if core:
                entities = [core[:10]]
                logger.warning(f"未提取到实体，使用核心词: {entities[0]}")
        
        # 去重
        entities = list(set(entities))
        
        logger.info(f"实体提取完成，共提取 {len(entities)} 个实体: {entities}")
        return entities
