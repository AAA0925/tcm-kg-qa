import sys
import os
# 确保能导入 backend 根目录下的 app 模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import json
from loguru import logger
from app.services.kg import kg_client

def generate_ner_dataset():
    """利用知识图谱进行远程监督，自动生成 NER 训练数据"""
    logger.info("开始从 Neo4j 导出实体并生成标注数据...")
    
    # 1. 从 Neo4j 获取各类实体 (根据你的实际 Label 调整这里的键值对)
    # 格式: "图谱中的Label": "NER模型中的标签类型"
    label_mapping = {
        "Disease": "DIS",
        "Symptom": "SYM",
        "Herb": "HERB",
        "Prescription": "HERB" 
    }
    
    entities_map = {etype: [] for etype in label_mapping.values()}
    
    try:
        with kg_client.driver.session() as session:
            for label, etype in label_mapping.items():
                # 检查该 Label 是否存在，避免报错
                result = session.run(f"MATCH (n:{label}) RETURN n.name AS name LIMIT 1")
                if result.single():
                    # 如果存在，则获取全部
                    all_res = session.run(f"MATCH (n:{label}) RETURN n.name AS name")
                    entities_map[etype] = [record["name"] for record in all_res if record["name"]]
                    logger.info(f"成功导出 {label} -> {etype}: {len(entities_map[etype])} 个")
                else:
                    logger.warning(f"图谱中未找到 Label: {label}，已跳过")
    except Exception as e:
        logger.error(f"Neo4j 查询失败: {e}")
        return

    # 2. 准备原始文本 (从图谱关系中提取句子，确保能匹配到实体)
    texts = []
    raw_data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw_crawled_data.json')
    
    if os.path.exists(raw_data_path):
        try:
            with open(raw_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                texts = [item.get('content', '') for item in data if item.get('content')]
            logger.info(f"从爬取文件中加载了 {len(texts)} 条文本")
        except Exception as e:
            logger.warning(f"读取爬取文件失败: {e}")

    # 如果文本不足，则从 Neo4j 补充
    if len(texts) < 10:
        logger.info("正在从 Neo4j 关系中提取训练文本...")
        try:
            with kg_client.driver.session() as session:
                # 提取“疾病-有症状-症状”的句子
                res1 = session.run("MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom) RETURN d.name AS d_name, s.name AS s_name LIMIT 500")
                for r in res1:
                    if r["d_name"] and r["s_name"]:
                        texts.append(f"{r['d_name']}的常见症状包括{r['s_name']}。")
                
                # 提取“方剂-治疗-疾病”的句子
                res2 = session.run("MATCH (p:Prescription)-[:TREATS]->(d:Disease) RETURN p.name AS p_name, d.name AS d_name LIMIT 500")
                for r in res2:
                    if r["p_name"] and r["d_name"]:
                        texts.append(f"{r['p_name']}主要用于治疗{r['d_name']}。")
                
                logger.info(f"从图谱关系中构建了 {len(texts)} 条训练文本")
        except Exception as e:
            logger.error(f"提取图谱文本失败: {e}")
            texts = ["胃痛是一种常见的消化系统疾病，常伴有腹胀痛。", "人参具有大补元气的功效。"]

    # 3. 匹配并生成标注
    ner_dataset = []
    for text in texts:
        if not text or len(text) < 5: continue
        
        found_entities = []
        # 简单的字符串匹配（毕设中可优化为 AC 自动机或 Trie 树以提高效率）
        for etype, names in entities_map.items():
            for name in names:
                if not name or len(name) < 2: continue # 跳过太短的词
                start = 0
                while True:
                    idx = text.find(name, start)
                    if idx == -1: break
                    found_entities.append({"start": idx, "end": idx + len(name), "type": etype})
                    start = idx + 1
        
        if found_entities:
            ner_dataset.append({
                "text": text[:128], # 限制长度
                "entities": found_entities
            })

    # 4. 保存
    output_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ner_train_data.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ner_dataset, f, ensure_ascii=False, indent=2)
        
    logger.success(f"标注数据生成完毕！共 {len(ner_dataset)} 条，已保存至 {output_path}")

if __name__ == "__main__":
    generate_ner_dataset()
