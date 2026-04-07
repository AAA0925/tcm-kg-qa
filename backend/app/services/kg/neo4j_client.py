from neo4j import GraphDatabase
from app.core.config import settings
from loguru import logger
from typing import List, Dict
import os

class Neo4jClient:
    def __init__(self):
        self.driver = None
        self.connected = False
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            self.verify_connectivity()
            self.connected = True
            logger.info("Neo4j 客户端初始化成功")
        except Exception as e:
            logger.warning(f"Neo4j 未连接：{e}，系统将以简化模式运行")
            self.driver = None
            self.connected = False
    
    def verify_connectivity(self):
        if self.driver:
            self.driver.verify_connectivity()
            logger.info("Neo4j 连接验证成功")
    
    def create_entity(self, entity_name: str, category: str, properties: Dict = {}):
        with self.driver.session() as session:
            cypher = f"""
            MERGE (e:{category} {{name: $name}})
            SET e.category = $category, e += $properties
            RETURN e
            """
            session.run(cypher, name=entity_name, category=category, properties=properties)
    
    def create_relation(self, source_entity: str, target_entity: str, 
                       relation_type: str, properties: Dict = {}):
        with self.driver.session() as session:
            cypher = f"""
            MATCH (a {{name: $source}})
            MATCH (b {{name: $target}})
            MERGE (a)-[r:{relation_type}]->(b)
            SET r += $properties
            RETURN r
            """
            session.run(cypher, source=source_entity, target=target_entity, properties=properties)
    
    def query_by_entity(self, entity_name: str, enable_fuzzy: bool = False) -> List[Dict]:
        if not self.connected:
            logger.warning("Neo4j 未连接，无法查询")
            return []
        with self.driver.session() as session:
            # 第一步：查询有关系的记录
            cypher = """
            MATCH (n {name: $name})-[r]-(m)
            RETURN n, r, m
            """
            result = session.run(cypher, name=entity_name)
            
            results = []
            for record in result:
                node_n = record['n']
                node_m = record['m']
                rel_r = record['r']
                
                # 明确使用 is not None 判断
                if node_n is not None and node_m is not None and rel_r is not None:
                    labels_n = list(node_n.labels)
                    labels_m = list(node_m.labels)
                    
                    results.append({
                        'n': {
                            'name': node_n.get('name'),
                            'category': labels_n[0] if labels_n else 'Concept'
                        },
                        'm': {
                            'name': node_m.get('name'),
                            'category': labels_m[0] if labels_m else 'Concept'
                        },
                        'r': {
                            'type': rel_r.type
                        }
                    })
            
            # 第二步：模糊匹配逻辑
            should_do_fuzzy = (not results) or enable_fuzzy
            
            if should_do_fuzzy:
                if enable_fuzzy and results:
                    logger.info(f"实体 '{entity_name}' 启用了模糊搜索，进行扩展匹配...")
                else:
                    logger.info(f"实体 '{entity_name}' 没有直接关系，尝试模糊匹配...")
                
                # 先添加节点自身（如果还没有）
                if not results:
                    self_cypher = """
                    MATCH (n {name: $name})
                    RETURN n
                    """
                    self_result = session.run(self_cypher, name=entity_name)
                    self_record = self_result.single()
                    
                    if self_record:
                        node_n = self_record['n']
                        labels_n = list(node_n.labels)
                        n_data = {
                            'name': node_n.get('name'),
                            'category': labels_n[0] if labels_n else 'Concept'
                        }
                        results.append({'n': n_data, 'm': None, 'r': None})
                
                # 模糊匹配：找到名称相关的节点
                try:
                    fuzzy_cypher = """
                    MATCH (n {name: $name})
                    MATCH (m)
                    WHERE (m.name CONTAINS $keyword OR $name CONTAINS m.name)
                    AND m <> n
                    RETURN n, m
                    LIMIT 20
                    """
                    fuzzy_result = session.run(fuzzy_cypher, name=entity_name, keyword=entity_name[:2])
                    
                    for record in fuzzy_result:
                        node_n = record['n']
                        node_m = record['m']
                        
                        if node_n is not None and node_m is not None:
                            labels_n = list(node_n.labels)
                            labels_m = list(node_m.labels)
                            
                            results.append({
                                'n': {
                                    'name': node_n.get('name'),
                                    'category': labels_n[0] if labels_n else 'Concept'
                                },
                                'm': {
                                    'name': node_m.get('name'),
                                    'category': labels_m[0] if labels_m else 'Concept'
                                },
                                'r': {
                                    'type': 'RELATED'
                                }
                            })
                    
                    logger.info(f"模糊匹配成功，共找到 {len(results)} 个相关节点")
                except Exception as e:
                    logger.warning(f"模糊匹配失败：{e}")
            
            logger.info(f"查询实体 '{entity_name}' 返回 {len(results)} 条记录")
            return results
    
    def expand_entity(self, entity_name: str, depth: int = 1, limit: int = 50) -> List[Dict]:
        """展开实体的关联节点"""
        if not self.connected:
            logger.warning("Neo4j 未连接，无法展开")
            return []
        with self.driver.session() as session:
            # 根据 depth 查询不同深度的关联
            if depth == 1:
                cypher = """
                MATCH (n {name: $name})-[r]-(m)
                RETURN n, r, m
                LIMIT $limit
                """
            else:
                cypher = """
                MATCH path = (n {name: $name})-[*1..$depth]-(m)
                WITH n, m, relationships(path) as rels
                UNWIND rels as r
                RETURN n, r, m
                LIMIT $limit
                """
            
            logger.info(f"展开实体: {entity_name}, depth={depth}")
            result = session.run(cypher, name=entity_name, depth=depth, limit=limit)
            
            results = []
            seen = set()
            for record in result:
                node_n = record['n']
                node_m = record['m']
                rel_r = record['r']
                
                # 使用 is not None 判断
                if node_n is not None and node_m is not None and rel_r is not None:
                    labels_n = list(node_n.labels)
                    labels_m = list(node_m.labels)
                    
                    edge_key = f"{node_n.get('name')}->{node_m.get('name')}:{rel_r.type}"
                    if edge_key not in seen:
                        seen.add(edge_key)
                        results.append({
                            'n': {
                                'name': node_n.get('name'),
                                'category': labels_n[0] if labels_n else 'Concept'
                            },
                            'm': {
                                'name': node_m.get('name'),
                                'category': labels_m[0] if labels_m else 'Concept'
                            },
                            'r': {
                                'type': rel_r.type
                            }
                        })
            
            logger.info(f"展开实体 '{entity_name}' 返回 {len(results)} 条记录")
            return results
    
    def delete_entity(self, entity_name: str) -> bool:
        """删除实体及其相关关系"""
        if not self.connected:
            logger.warning("Neo4j 未连接，无法删除实体")
            return False
        with self.driver.session() as session:
            cypher = """
            MATCH (n {name: $name})
            DETACH DELETE n
            """
            result = session.run(cypher, name=entity_name)
            summary = result.consume()
            deleted = summary.counters.nodes_deleted
            logger.info(f"删除实体 '{entity_name}'，影响节点数: {deleted}")
            return deleted > 0
    
    def update_entity(self, entity_name: str, category: str = None, properties: Dict = {}) -> bool:
        """更新实体属性"""
        if not self.connected:
            logger.warning("Neo4j 未连接，无法更新实体")
            return False
        with self.driver.session() as session:
            # 构建 SET 子句
            set_clauses = []
            params = {'name': entity_name}
            
            if category:
                set_clauses.append("e.category = $category")
                params['category'] = category
            
            # 添加自定义属性
            for key, value in properties.items():
                set_clauses.append(f"e.{key} = ${key}")
                params[key] = value
            
            if not set_clauses:
                logger.warning("没有提供要更新的属性")
                return False
            
            cypher = f"""
            MATCH (e {{name: $name}})
            SET {', '.join(set_clauses)}
            RETURN e
            """
            result = session.run(cypher, **params)
            return result.single() is not None
    
    def list_entities(self, category: str = None, limit: int = 100, offset: int = 0) -> Dict:
        """查询实体列表"""
        if not self.connected:
            logger.warning("Neo4j 未连接，无法查询实体列表")
            return {"entities": [], "total": 0}
        
        with self.driver.session() as session:
            # 统计总数
            if category:
                count_cypher = f"MATCH (n:{category}) RETURN count(n) as count"
            else:
                count_cypher = "MATCH (n) RETURN count(n) as count"
            total = session.run(count_cypher).single()["count"]
            
            # 分页查询
            if category:
                cypher = f"""
                MATCH (n:{category})
                RETURN n.name as name, labels(n) as categories, n
                ORDER BY n.name
                SKIP $offset LIMIT $limit
                """
            else:
                cypher = """
                MATCH (n)
                RETURN n.name as name, labels(n) as categories, n
                ORDER BY n.name
                SKIP $offset LIMIT $limit
                """
            
            result = session.run(cypher, offset=offset, limit=limit)
            entities = []
            for record in result:
                node = record['n']
                entity = {
                    'name': record['name'],
                    'category': record['categories'][0] if record['categories'] else 'Unknown',
                    'categories': record['categories']
                }
                for key, value in dict(node).items():
                    if key != 'name' and key != 'category':
                        entity[key] = value
                entities.append(entity)
            
            return {"entities": entities, "total": total}
    
    def list_relations(self, source_entity: str = None, target_entity: str = None, 
                      relation_type: str = None, limit: int = 100, offset: int = 0) -> Dict:
        """查询关系列表"""
        if not self.connected:
            logger.warning("Neo4j 未连接，无法查询关系列表")
            return {"relations": [], "total": 0}
        
        with self.driver.session() as session:
            conditions = []
            params = {'limit': limit, 'offset': offset}
            
            if source_entity:
                conditions.append("a.name = $source")
                params['source'] = source_entity
            if target_entity:
                conditions.append("b.name = $target")
                params['target'] = target_entity
            
            where_clause = f'WHERE {" AND ".join(conditions)}' if conditions else ''
            rel_filter = f':{relation_type}' if relation_type else ''
            
            # 统计总数
            count_cypher = f"""
            MATCH (a)-[r{rel_filter}]->(b)
            {where_clause}
            RETURN count(r) as count
            """
            total = session.run(count_cypher, **params).single()["count"]
            
            # 分页查询
            cypher = f"""
            MATCH (a)-[r{rel_filter}]->(b)
            {where_clause}
            RETURN a.name as source, labels(a) as source_labels, 
                   type(r) as relation_type, 
                   b.name as target, labels(b) as target_labels
            ORDER BY a.name, b.name
            SKIP $offset LIMIT $limit
            """
            
            result = session.run(cypher, **params)
            relations = []
            for record in result:
                relations.append({
                    'source_entity': record['source'],
                    'source_type': record['source_labels'][0] if record['source_labels'] else 'Unknown',
                    'relation_type': record['relation_type'],
                    'target_entity': record['target'],
                    'target_type': record['target_labels'][0] if record['target_labels'] else 'Unknown'
                })
            
            return {"relations": relations, "total": total}
    
    def delete_relation(self, source_entity: str, target_entity: str, relation_type: str) -> bool:
        """删除关系"""
        if not self.connected:
            logger.warning("Neo4j 未连接，无法删除关系")
            return False
        with self.driver.session() as session:
            cypher = f"""
            MATCH (a {{name: $source}})-[r:{relation_type}]->(b {{name: $target}})
            DELETE r
            """
            result = session.run(cypher, source=source_entity, target=target_entity)
            summary = result.consume()
            deleted = summary.counters.relationships_deleted
            logger.info(f"删除关系 {source_entity}-[{relation_type}]->{target_entity}，影响关系数: {deleted}")
            return deleted > 0
    
    def update_relation(self, source_entity: str, target_entity: str, 
                       old_relation_type: str, new_relation_type: str = None,
                       properties: Dict = {}) -> bool:
        """更新关系"""
        if not self.connected:
            logger.warning("Neo4j 未连接，无法更新关系")
            return False
        with self.driver.session() as session:
            if new_relation_type:
                # 需要创建新关系并删除旧关系
                cypher = f"""
                MATCH (a {{name: $source}})-[r:{old_relation_type}]->(b {{name: $target}})
                CREATE (a)-[new_r:{new_relation_type}]->(b)
                SET new_r += $properties
                DELETE r
                RETURN new_r
                """
            else:
                # 只更新属性
                set_clauses = []
                params = {'source': source_entity, 'target': target_entity}
                for key, value in properties.items():
                    set_clauses.append(f"r.{key} = ${key}")
                    params[key] = value
                
                if not set_clauses:
                    return False
                
                cypher = f"""
                MATCH (a {{name: $source}})-[r:{old_relation_type}]->(b {{name: $target}})
                SET {', '.join(set_clauses)}
                RETURN r
                """
                params['properties'] = properties
            
            result = session.run(cypher, **params)
            return result.single() is not None
    
    def get_entity_types(self) -> List[str]:
        """获取所有实体类型"""
        if not self.connected:
            return []
        try:
            with self.driver.session() as session:
                result = session.run("CALL db.labels()")
                return [record[0] for record in result]
        except Exception as e:
            logger.error(f"获取实体类型失败：{e}")
            return []
    
    def get_relation_types(self) -> List[str]:
        """获取所有关系类型"""
        if not self.connected:
            return []
        try:
            with self.driver.session() as session:
                result = session.run("CALL db.relationshipTypes()")
                return [record[0] for record in result]
        except Exception as e:
            logger.error(f"获取关系类型失败：{e}")
            return []
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.connected or not self.driver:
            return {"entity_count": 0, "relation_count": 0}
        try:
            with self.driver.session() as session:
                entity_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
                relation_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
                return {"entity_count": entity_count, "relation_count": relation_count}
        except Exception as e:
            logger.error(f"获取统计信息失败：{e}")
            return {"entity_count": 0, "relation_count": 0}
    
    def close(self):
        self.driver.close()

kg_client = Neo4jClient()
