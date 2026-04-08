from typing import List
from loguru import logger
import sys
import os

# 确保能导入 backend 根目录下的 models 模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

try:
    from models.net.inference import ner_infer
    USE_MODEL = True
except Exception as e:
    USE_MODEL = False
    logger.warning(f"NER 模型加载失败，将使用正则匹配兜底: {e}")

from app.services.kg import kg_client

class EntityExtractor:
    def __init__(self):
        pass
    
    def extract(self, question: str) -> List[str]:
        entities = []
        
        if USE_MODEL:
            try:
                # 1. 使用训练好的 ALBERT-BiLSTM-CRF 模型
                results = ner_infer.predict(question)
                raw_entities = [r['text'] for r in results]
                logger.info(f"模型原始提取结果: {raw_entities}")
                
                # 2. RAG 辅助校验：利用 Neo4j 模糊匹配修正实体
                for ent in raw_entities:
                    # 尝试精确匹配
                    exact_match = kg_client.query_by_entity(ent, enable_fuzzy=False)
                    if exact_match:
                        # 使用图谱中实际存在的实体名
                        entities.append(exact_match[0]["n"]["name"])
                    else:
                        # 如果精确匹配失败，尝试寻找最长匹配子串
                        found = False
                        for length in range(len(ent), 1, -1):
                            for i in range(len(ent) - length + 1):
                                sub_ent = ent[i:i+length]
                                fuzzy_match = kg_client.query_by_entity(sub_ent, enable_fuzzy=True)
                                if fuzzy_match:
                                    # 使用图谱中实际存在的实体名，避免截取错误（如“人”匹配到“人参”）
                                    matched_name = fuzzy_match[0]["n"]["name"]
                                    if matched_name not in entities:
                                        entities.append(matched_name)
                                    found = True
                                    break
                            if found: break
            except Exception as e:
                logger.error(f"模型推理出错: {e}")
        
        # 如果模型没提取到，使用简单的正则兜底
        if not entities:
            import re
            patterns = [r'(.+?)有什么症状', r'(.+?)怎么治疗', r'(.+?)怎么办']
            for pattern in patterns:
                match = re.search(pattern, question)
                if match:
                    entities.append(match.group(1).strip())
                    break
                    
        return list(set(entities))
