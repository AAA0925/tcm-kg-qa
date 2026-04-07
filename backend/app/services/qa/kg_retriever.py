from typing import List, Dict
from loguru import logger
from app.services.kg import kg_client

class KGRetriever:
    """知识图谱检索器 - 根据实体查询图谱"""
    
    def __init__(self):
        self.kg_client = kg_client
    
    def retrieve_by_entities(self, entities: List[str], top_k: int = 20) -> List[Dict]:
        """
        根据实体列表检索知识图谱
        
        Args:
            entities: 实体名称列表
            top_k: 每个实体返回的关系数量（默认20，确保获取完整信息）
            
        Returns:
            检索结果列表，格式: [
                {
                    "entity": "实体名称",
                    "relations": [
                        {"source": "A", "relation": "关系", "target": "B"},
                        ...
                    ]
                }
            ]
        """
        results = []
        
        for entity_name in entities:
            try:
                # 调用Neo4j客户端查询实体关系
                entity_relations = self.kg_client.query_by_entity(entity_name, enable_fuzzy=False)
                
                if entity_relations:
                    # 限制返回的关系数量
                    limited_relations = entity_relations[:top_k]
                    
                    results.append({
                        "entity": entity_name,
                        "relations": limited_relations
                    })
                    logger.info(f"实体 '{entity_name}' 检索到 {len(limited_relations)} 条关系")
                else:
                    logger.warning(f"实体 '{entity_name}' 未找到相关关系")
                    
            except Exception as e:
                logger.error(f"检索实体 '{entity_name}' 失败: {e}")
        
        logger.info(f"知识图谱检索完成，共检索 {len(results)} 个实体")
        return results
    
    def format_context(self, retrieve_results: List[Dict]) -> str:
        """
        将检索结果格式化为自然语言文本
        
        Args:
            retrieve_results: 检索结果列表
            
        Returns:
            格式化后的上下文文本
        """
        if not retrieve_results:
            return "未找到相关知识图谱信息。"
        
        context_parts = []
        
        # 关系类型中文映射
        relation_map = {
            'HAS_SYMPTOM': '有症状',
            'TREATS': '治疗',
            'TREATED_BY_PRESCRIPTION': '治疗方剂',
            'CONTAINS_HERB': '包含草药',
            'HAS_EFFECT': '具有功效',
            'BELONGS_TO_MERIDIAN': '归经',
            'USED_FOR': '用于治疗',
            'PART_OF': '属于',
            'CAUSES': '导致',
            'RELATED': '相关',
            'SUBCLASS_OF': '子类',
            'FROM_CLASSIC': '出自经典',
            'HAS_PROPERTY': '具有属性',
            'DO_EAT': '宜吃',
            'NO_EAT': '忌吃',
            'COMMON_DRUG': '常用药',
            'GENERATES': '生成',
            'CONTAINED_IN': '包含于'
        }
        
        for result in retrieve_results:
            entity = result["entity"]
            relations = result["relations"]
            
            if relations:
                # 按关系类型分组
                relation_groups = {}
                for rel in relations:
                    rel_type = rel["r"]["type"]
                    source = rel["n"]["name"]
                    target = rel["m"]["name"]
                    rel_cn = relation_map.get(rel_type, rel_type)
                    
                    if rel_type not in relation_groups:
                        relation_groups[rel_type] = []
                    relation_groups[rel_type].append(f"{target}（{rel_cn}）")
                
                # 格式化输出
                relation_texts = []
                for rel_type, targets in relation_groups.items():
                    rel_cn = relation_map.get(rel_type, rel_type)
                    relation_texts.append(f"  - {rel_cn}：{', '.join(targets)}")
                
                context_parts.append(f"【{entity}】的相关知识：\n" + "\n".join(relation_texts))
        
        context = "\n\n".join(context_parts)
        logger.info(f"上下文格式化完成，共 {len(context_parts)} 个实体的信息")
        return context
