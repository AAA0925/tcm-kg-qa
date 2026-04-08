import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import json
from loguru import logger
from app.services.kg import kg_client
from models.net.relation_extractor import REL2ID

def generate_re_dataset():
    """利用 Neo4j 现有关系进行远程监督，生成 RE 训练数据"""
    logger.info("开始从 Neo4j 提取关系对并构建 RE 数据集...")
    
    dataset = []
    # 定义要抽取的关系类型和对应的 Cypher 查询
    relations_config = [
        {"rel": "HAS_SYMPTOM", "h_label": "Disease", "t_label": "Symptom"},
        {"rel": "TREATS", "h_label": "Prescription", "t_label": "Disease"}
    ]
    
    try:
        with kg_client.driver.session() as session:
            for config in relations_config:
                rel_type = config["rel"]
                h_label = config["h_label"]
                t_label = config["t_label"]
                
                # 查询所有该类型的关系
                query = f"MATCH (h:{h_label})-[r:{rel_type}]->(t:{t_label}) RETURN h.name AS head, t.name AS tail LIMIT 500"
                results = session.run(query)
                
                for record in results:
                    head_ent = record["head"]
                    tail_ent = record["tail"]
                    
                    if not head_ent or not tail_ent: continue
                    
                    # 构造正样本句子 (模拟语境，实际可替换为爬取的原始文本)
                    if rel_type == "HAS_SYMPTOM":
                        sentence = f"{head_ent}的常见临床表现包括{tail_ent}。"
                    elif rel_type == "TREATS":
                        sentence = f"{head_ent}在临床上主要用于治疗{tail_ent}。"
                    
                    dataset.append({
                        "text": sentence,
                        "head": head_ent,
                        "tail": tail_ent,
                        "relation": rel_type
                    })
                    
                    # 构造负样本 (随机组合不相关的实体) - 简单演示
                    # 实际项目中应从语料库中随机抽取
                    
    except Exception as e:
        logger.error(f"RE 数据生成失败: {e}")
        return

    # 保存数据
    output_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 're_train_data.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
        
    logger.success(f"RE 训练数据生成完毕！共 {len(dataset)} 条，已保存至 {output_path}")

if __name__ == "__main__":
    generate_re_dataset()
