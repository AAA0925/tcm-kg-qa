import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from models.net.inference import ner_infer
from models.net.re_inference import re_infer, RELATION_TYPES
from app.services.kg import kg_client
from loguru import logger

def extract_and_store(text):
    """从非结构化文本中抽取三元组并导入 Neo4j"""
    logger.info(f"开始处理文本: {text[:50]}...")
    
    # 1. 实体识别 (NER)
    entities = ner_infer.predict(text)
    if len(entities) < 2:
        logger.warning("实体数量不足，无法构建关系")
        return []

    triples = []
    
    # 2. 关系抽取 (RE) - 两两配对尝试
    for i in range(len(entities)):
        for j in range(len(entities)):
            if i == j: continue
            
            head = entities[i]
            tail = entities[j]
            
            # 使用训练好的 RE 模型进行关系判断
            if re_infer and re_infer.model:
                relation = re_infer.predict(text, head['text'], tail['text'])
            else:
                logger.warning("RE 模型未加载，跳过关系判断")
                continue
            
            if relation != "O":
                triples.append((head['text'], relation, tail['text']))
                logger.success(f"抽取到三元组: ({head['text']}, {relation}, {tail['text']})")
                
                # 3. 导入 Neo4j
                try:
                    with kg_client.driver.session() as session:
                        # 确保节点存在
                        session.run(
                            "MERGE (a:Disease {name: $h}) MERGE (b:Symptom {name: $t}) "
                            "MERGE (a)-[:HAS_SYMPTOM]->(b)",
                            h=head['text'], t=tail['text']
                        )
                except Exception as e:
                    logger.error(f"导入 Neo4j 失败: {e}")

    return triples

if __name__ == "__main__":
    test_text = "心阴虚的症状通常包括心悸、失眠和盗汗。"
    extract_and_store(test_text)
