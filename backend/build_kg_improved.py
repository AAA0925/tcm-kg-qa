"""
改进版中医知识图谱构建脚本
策略：将字面量转换为实体节点，增加关系密度

@author: TCM-KG-QA Team
@date: 2026-04
"""

from rdflib import Graph, RDF, RDFS, OWL
from neo4j import GraphDatabase
import re
from collections import defaultdict, Counter
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImprovedTCMKGBuilder:
    """改进版中医知识图谱构建器"""
    
    def __init__(self, owl_file: str, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.owl_file = owl_file
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        
        logger.info("正在加载 OWL 文件...")
        self.g = Graph()
        self.g.parse(owl_file, format='xml')
        logger.info(f"OWL 文件加载完成，共 {len(self.g)} 个三元组")
        
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # 实体分类规则
        self.entity_categories = {
            'Disease': ['病', '症', '疾'],
            'Syndrome': ['证', '候'],
            'Prescription': ['汤', '丸', '散', '膏', '丹', '饮', '剂'],
            'Herb': ['草', '参', '苓', '术', '归', '芍', '芩', '连', '花', '叶', '根', '皮'],
            'Symptom': ['痛', '咳', '喘', '晕', '胀', '闷', '烦', '渴', '呕', '泻'],
            'Therapy': ['法', '疗法', '灸', '针', '推拿', '按摩'],
            'WellnessMethod': ['养生', '调护', '保健', '食疗', '锻炼'],
            'Meridian': ['经', '络', '脉', '穴'],
            'Classic': ['《', '》', '论', '经', '本草', '医籍'],
            'Effect': ['功效', '作用']  # 新增：功效作为独立实体
        }
        
        # 关系映射
        self.relation_mapping = {
            '治疗': 'TREATS',
            '由...组成': 'COMPOSED_OF',
            '归...经': 'BELONGS_TO_MERIDIAN',
            '具有性味': 'HAS_PROPERTY',
            '上位词': 'SUBCLASS_OF',
            '下位词': 'SUPERCLASS_OF',
            '有症状': 'HAS_SYMPTOM',
            '对应证候': 'CORRESPONDS_TO_SYNDROME',
            '采用治法': 'TREATED_BY_THERAPY',
            '出自': 'FROM_CLASSIC',
            '来源': 'FROM_CLASSIC',
            '功效': 'HAS_EFFECT',
            '作用': 'HAS_EFFECT',
            '采用方法': 'USES_METHOD',
            '操作方法': 'HAS_OPERATION',
            '使用频次': 'HAS_FREQUENCY',
            '禁忌': 'HAS_CONTRAINT',
            '节气': 'RELATED_TO_SEASON',
            '时间上相关': 'RELATED_TO_TIME',
            '概念上相关': 'CONCEPTUALLY_RELATED',
            '包含': 'CONTAINS',
        }
        
        # 需要转换为实体的字面量关系
        self.literal_to_entity_relations = {
            '有症状': 'Symptom',
            '对应证候': 'Syndrome',
            '功效': 'Effect',
            '作用': 'Effect',
        }
    
    def classify_entity(self, label: str) -> str:
        """分类实体类型"""
        for entity_type, keywords in self.entity_categories.items():
            if any(kw in label for kw in keywords):
                return entity_type
        return 'Other'
    
    def clean_label(self, label: str) -> str:
        """清理标签"""
        if not label:
            return ""
        label = label.strip()
        label = re.sub(r'\s+', ' ', label)
        return label
    
    def extract_all_entities_and_relations(self):
        """
        提取所有实体和关系，包括从字面量创建新实体
        """
        logger.info("正在提取实体和关系...")
        
        entities = {}  # name -> type
        relations = []  # (source, rel_type, target)
        
        individuals = list(self.g.subjects(RDF.type, OWL.NamedIndividual))
        
        # 第一遍：收集所有有标签的个体
        for ind in individuals:
            label = self.g.value(ind, RDFS.label)
            if label:
                label_str = self.clean_label(str(label))
                if label_str and len(label_str) < 100:
                    entity_type = self.classify_entity(label_str)
                    if entity_type != 'Other':
                        entities[label_str] = entity_type
        
        logger.info(f"第一遍扫描：找到 {len(entities)} 个实体")
        
        # 第二遍：提取关系，并将字面量转换为实体
        literal_counter = Counter()
        
        for subj in individuals:
            subj_label = self.g.value(subj, RDFS.label)
            if not subj_label:
                continue
            
            subj_name = self.clean_label(str(subj_label))
            if not subj_name or subj_name not in entities:
                continue
            
            for s, p, o in self.g.triples((subj, None, None)):
                if p in [RDF.type, RDFS.label]:
                    continue
                
                rel_label = self.g.value(p, RDFS.label)
                if not rel_label:
                    continue
                
                rel_label_str = str(rel_label)
                neo4j_rel_type = self.relation_mapping.get(rel_label_str)
                
                if not neo4j_rel_type:
                    continue
                
                # 检查客体
                obj_label = self.g.value(o, RDFS.label)
                
                if obj_label:
                    # 客体是实体
                    obj_name = self.clean_label(str(obj_label))
                    if obj_name and len(obj_name) < 100:
                        obj_type = self.classify_entity(obj_name)
                        if obj_type != 'Other':
                            # 确保目标实体也在列表中
                            if obj_name not in entities:
                                entities[obj_name] = obj_type
                            
                            relations.append({
                                'source': subj_name,
                                'relation': neo4j_rel_type,
                                'target': obj_name
                            })
                else:
                    # 客体是字面量 - 检查是否需要转换为实体
                    obj_value = str(o).strip()
                    
                    if not obj_value or len(obj_value) > 200:
                        continue
                    
                    # 如果这个关系应该转换为实体
                    if rel_label_str in self.literal_to_entity_relations:
                        target_type = self.literal_to_entity_relations[rel_label_str]
                        
                        # 清理值（可能是逗号分隔的列表）
                        items = [item.strip() for item in re.split(r'[，,;；]', obj_value) if item.strip()]
                        
                        for item in items:
                            if item and len(item) < 50:
                                # 添加到实体列表
                                if item not in entities:
                                    entities[item] = target_type
                                    literal_counter[target_type] += 1
                                
                                relations.append({
                                    'source': subj_name,
                                    'relation': neo4j_rel_type,
                                    'target': item
                                })
        
        logger.info(f"实体总数: {len(entities)}")
        logger.info(f"关系总数: {len(relations)}")
        logger.info(f"从字面量创建的实体: {dict(literal_counter)}")
        
        return entities, relations
    
    def build(self):
        """执行构建"""
        logger.info("=" * 80)
        logger.info("开始构建改进版中医知识图谱")
        logger.info("=" * 80)
        
        try:
            # 1. 提取数据
            logger.info("\n步骤 1/4: 提取实体和关系...")
            entities, relations = self.extract_all_entities_and_relations()
            
            # 2. 清空数据库
            logger.info("\n步骤 2/4: 清空现有数据...")
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            logger.info("数据清空完成")
            
            # 3. 创建约束
            logger.info("\n步骤 3/4: 创建约束...")
            with self.driver.session() as session:
                entity_types = set(entities.values())
                for entity_type in entity_types:
                    try:
                        session.run(f"DROP CONSTRAINT unique_{entity_type.lower()}_name IF EXISTS")
                        session.run(f"""
                            CREATE CONSTRAINT unique_{entity_type.lower()}_name
                            FOR (n:{entity_type})
                            REQUIRE n.name IS UNIQUE
                        """)
                    except Exception as e:
                        logger.warning(f"约束创建失败 {entity_type}: {e}")
            
            # 4. 导入数据
            logger.info("\n步骤 4/4: 导入数据...")
            
            # 按类型分组实体
            entities_by_type = defaultdict(list)
            for name, etype in entities.items():
                entities_by_type[etype].append(name)
            
            with self.driver.session() as session:
                # 导入实体
                for entity_type, names in entities_by_type.items():
                    batch_size = 100
                    for i in range(0, len(names), batch_size):
                        batch = names[i:i+batch_size]
                        cypher = f"""
                            UNWIND $batch AS name
                            MERGE (n:{entity_type} {{name: name}})
                        """
                        session.run(cypher, batch=batch)
                    logger.info(f"  导入 {entity_type}: {len(names)} 个")
                
                # 导入关系
                success = 0
                failed = 0
                for rel in relations:
                    try:
                        cypher = f"""
                            MATCH (source {{name: $source}})
                            MATCH (target {{name: $target}})
                            MERGE (source)-[r:{rel['relation']}]->(target)
                        """
                        session.run(cypher, source=rel['source'], target=rel['target'])
                        success += 1
                    except Exception as e:
                        failed += 1
                
                logger.info(f"  关系导入: 成功 {success}, 失败 {failed}")
            
            # 验证
            logger.info("\n验证结果...")
            with self.driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = result.single()['count']
                
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = result.single()['count']
                
                logger.info(f"Neo4j 节点数: {node_count}")
                logger.info(f"Neo4j 关系数: {rel_count}")
            
            logger.info("\n✅ 构建完成！")
            
        except Exception as e:
            logger.error(f"❌ 构建失败: {e}", exc_info=True)
            raise
        finally:
            self.driver.close()


def main():
    builder = ImprovedTCMKGBuilder(
        owl_file="data/health-sample.owl",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password"
    )
    builder.build()


if __name__ == "__main__":
    main()
