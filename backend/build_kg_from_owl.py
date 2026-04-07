"""
中医知识图谱构建脚本
从 health-sample.owl 提取数据并导入 Neo4j

@author: TCM-KG-QA Team
@date: 2026-04
"""

from rdflib import Graph, RDF, RDFS, OWL, Namespace
from neo4j import GraphDatabase
import re
from collections import defaultdict
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TCMKnowledgeGraphBuilder:
    """中医知识图谱构建器"""
    
    def __init__(self, owl_file: str, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        """
        初始化构建器
        
        Args:
            owl_file: OWL 文件路径
            neo4j_uri: Neo4j 连接 URI
            neo4j_user: Neo4j 用户名
            neo4j_password: Neo4j 密码
        """
        self.owl_file = owl_file
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        
        # 加载 OWL 文件
        logger.info("正在加载 OWL 文件...")
        self.g = Graph()
        self.g.parse(owl_file, format='xml')
        logger.info(f"OWL 文件加载完成，共 {len(self.g)} 个三元组")
        
        # 连接 Neo4j
        self.driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )
        logger.info("Neo4j 连接成功")
        
        # 实体分类映射
        self.entity_categories = {
            'Disease': ['病', '症', '疾'],
            'Syndrome': ['证', '候'],
            'Prescription': ['汤', '丸', '散', '膏', '丹', '饮', '剂'],
            'Herb': ['草', '参', '苓', '术', '归', '芍', '芩', '连', '花', '叶', '根', '皮'],
            'Symptom': ['痛', '咳', '喘', '晕', '胀', '闷', '烦', '渴'],
            'Therapy': ['法', '疗法', '灸', '针', '推拿', '按摩'],
            'WellnessMethod': ['养生', '调护', '保健', '食疗', '锻炼'],
            'Meridian': ['经', '络', '脉', '穴'],
            'Classic': ['《', '》', '论', '经', '本草', '医籍']
        }
        
        # 关系映射（OWL 关系 -> Neo4j 关系）
        self.relation_mapping = {
            '治疗': 'TREATS',
            '由...组成': 'COMPOSED_OF',
            '归...经': 'BELONGS_TO_MERIDIAN',
            '具有性味': 'HAS_PROPERTY',
            '上位词': 'SUBCLASS_OF',
            '下位词': 'SUBCLASS_OF',  # 反向处理
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
            '功能上相关': 'CONCEPTUALLY_RELATED',
            '包含': 'CONTAINS',
            '被包含': 'CONTAINED_IN',
        }
        
        # 统计信息
        self.stats = {
            'entities': defaultdict(int),
            'relations': defaultdict(int),
            'errors': 0
        }
    
    def classify_entity(self, label: str) -> str:
        """
        根据标签分类实体类型
        
        Args:
            label: 实体的中文标签
            
        Returns:
            实体类型字符串
        """
        for entity_type, keywords in self.entity_categories.items():
            if any(kw in label for kw in keywords):
                return entity_type
        
        # 默认返回 Other
        return 'Other'
    
    def clean_label(self, label: str) -> str:
        """
        清理标签文本
        
        Args:
            label: 原始标签
            
        Returns:
            清理后的标签
        """
        if not label:
            return ""
        
        # 去除首尾空格
        label = label.strip()
        
        # 去除多余空格
        label = re.sub(r'\s+', ' ', label)
        
        return label
    
    def extract_entities(self) -> dict:
        """
        提取所有实体
        
        Returns:
            字典，键为实体类型，值为实体列表
        """
        logger.info("正在提取实体...")
        
        entities = defaultdict(list)
        individuals = list(self.g.subjects(RDF.type, OWL.NamedIndividual))
        
        for ind in individuals:
            # 获取实体的中文标签
            label = self.g.value(ind, RDFS.label)
            
            if label:
                label_str = str(label)
                cleaned_label = self.clean_label(label_str)
                
                if not cleaned_label:
                    continue
                
                # 分类实体
                entity_type = self.classify_entity(cleaned_label)
                
                # 如果分类为 Other，跳过
                if entity_type == 'Other':
                    continue
                
                # 添加实体
                entity_data = {
                    'uri': str(ind),
                    'name': cleaned_label,
                    'type': entity_type
                }
                
                # 检查是否已存在（去重）
                existing_names = [e['name'] for e in entities[entity_type]]
                if cleaned_label not in existing_names:
                    entities[entity_type].append(entity_data)
                    self.stats['entities'][entity_type] += 1
        
        total_entities = sum(len(v) for v in entities.values())
        logger.info(f"实体提取完成，共 {total_entities} 个实体")
        
        # 打印统计
        for entity_type, count in sorted(self.stats['entities'].items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {entity_type}: {count}")
        
        return dict(entities)
    
    def extract_relations(self, entities: dict) -> list:
        """
        提取所有关系
        
        Args:
            entities: 实体字典
            
        Returns:
            关系列表
        """
        logger.info("正在提取关系...")
        
        relations = []
        
        # 创建名称到实体类型的映射（包括所有可能的名称变体）
        name_to_type = {}
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                name_to_type[entity['name']] = entity_type
        
        logger.info(f"已建立 {len(name_to_type)} 个实体的索引")
        
        # 遍历所有三元组
        individuals = list(self.g.subjects(RDF.type, OWL.NamedIndividual))
        processed_count = 0
        
        for subj in individuals:
            subj_label = self.g.value(subj, RDFS.label)
            if not subj_label:
                continue
            
            subj_name = self.clean_label(str(subj_label))
            if not subj_name or subj_name not in name_to_type:
                continue
            
            # 获取该主体的所有关系
            for s, p, o in self.g.triples((subj, None, None)):
                # 跳过类型和标签
                if p in [RDF.type, RDFS.label]:
                    continue
                
                # 获取关系的中文标签
                rel_label = self.g.value(p, RDFS.label)
                if not rel_label:
                    continue
                
                rel_label_str = str(rel_label)
                
                # 映射到 Neo4j 关系类型
                neo4j_rel_type = self.relation_mapping.get(rel_label_str)
                if not neo4j_rel_type:
                    continue
                
                # 尝试获取客体
                obj_label = self.g.value(o, RDFS.label)
                
                if obj_label:
                    # 客体是实体
                    obj_name = self.clean_label(str(obj_label))
                    if obj_name and obj_name in name_to_type:
                        relation = {
                            'source': subj_name,
                            'source_type': name_to_type[subj_name],
                            'target': obj_name,
                            'target_type': name_to_type[obj_name],
                            'relation_type': neo4j_rel_type,
                            'original_relation': rel_label_str
                        }
                        relations.append(relation)
                        self.stats['relations'][neo4j_rel_type] += 1
                        processed_count += 1
                else:
                    # 客体是 URI 但没有 label，尝试从 URI 推断
                    if hasattr(o, 'n3'):
                        obj_uri = str(o)
                        # 检查这个 URI 是否在我们的实体列表中
                        for entity_name, entity_type in name_to_type.items():
                            # 简单匹配：如果 URI 包含实体名称
                            import urllib.parse
                            decoded_uri = urllib.parse.unquote(obj_uri)
                            if entity_name in decoded_uri:
                                relation = {
                                    'source': subj_name,
                                    'source_type': name_to_type[subj_name],
                                    'target': entity_name,
                                    'target_type': entity_type,
                                    'relation_type': neo4j_rel_type,
                                    'original_relation': rel_label_str
                                }
                                relations.append(relation)
                                self.stats['relations'][neo4j_rel_type] += 1
                                processed_count += 1
                                break
        
        total_relations = len(relations)
        logger.info(f"关系提取完成，共 {total_relations} 个关系")
        
        # 打印统计
        for rel_type, count in sorted(self.stats['relations'].items(), key=lambda x: x[1], reverse=True)[:15]:
            logger.info(f"  {rel_type}: {count}")
        
        return relations
    
    def create_constraints_and_indexes(self):
        """创建 Neo4j 约束和索引"""
        logger.info("正在创建约束和索引...")
        
        with self.driver.session() as session:
            # 为每种实体类型创建唯一性约束
            entity_types = [
                'Disease', 'Syndrome', 'Prescription', 'Herb',
                'Symptom', 'Therapy', 'WellnessMethod', 'Meridian',
                'Property', 'Classic'
            ]
            
            for entity_type in entity_types:
                try:
                    # Neo4j 5.x 语法：先尝试删除，再创建
                    session.run(f"DROP CONSTRAINT unique_{entity_type.lower()}_name IF EXISTS")
                    
                    # 创建新约束
                    session.run(f"""
                        CREATE CONSTRAINT unique_{entity_type.lower()}_name
                        FOR (n:{entity_type})
                        REQUIRE n.name IS UNIQUE
                    """)
                    logger.info(f"  创建约束: {entity_type}.name")
                except Exception as e:
                    logger.warning(f"  创建约束失败 {entity_type}: {e}")
        
        logger.info("约束和索引创建完成")
    
    def import_entities(self, entities: dict):
        """
        导入实体到 Neo4j
        
        Args:
            entities: 实体字典
        """
        logger.info("正在导入实体...")
        
        with self.driver.session() as session:
            for entity_type, entity_list in entities.items():
                if not entity_list:
                    continue
                
                logger.info(f"  导入 {entity_type}: {len(entity_list)} 个")
                
                # 批量导入
                batch_size = 100
                for i in range(0, len(entity_list), batch_size):
                    batch = entity_list[i:i+batch_size]
                    
                    cypher = f"""
                        UNWIND $batch AS entity
                        MERGE (n:{entity_type} {{name: entity.name}})
                        SET n.uri = entity.uri
                    """
                    
                    try:
                        session.run(cypher, batch=batch)
                    except Exception as e:
                        logger.error(f"  导入 {entity_type} 批次失败: {e}")
                        self.stats['errors'] += 1
        
        logger.info("实体导入完成")
    
    def import_relations(self, relations: list):
        """
        导入关系到 Neo4j
        
        Args:
            relations: 关系列表
        """
        logger.info("正在导入关系...")
        
        with self.driver.session() as session:
            # 逐个导入关系，避免批量语句的变量冲突
            success_count = 0
            error_count = 0
            
            for rel in relations:
                source_type = rel['source_type']
                target_type = rel['target_type']
                rel_type = rel['relation_type']
                source_name = rel['source']
                target_name = rel['target']
                
                cypher = f"""
                    MATCH (source:{source_type} {{name: $source_name}})
                    MATCH (target:{target_type} {{name: $target_name}})
                    MERGE (source)-[r:{rel_type}]->(target)
                """
                
                try:
                    session.run(cypher, source_name=source_name, target_name=target_name)
                    success_count += 1
                except Exception as e:
                    logger.debug(f"  导入关系失败: {source_name}-[{rel_type}]->{target_name}: {e}")
                    error_count += 1
            
            logger.info(f"  成功: {success_count}, 失败: {error_count}")
        
        logger.info("关系导入完成")
    
    def build(self):
        """执行完整的构建流程"""
        logger.info("=" * 80)
        logger.info("开始构建中医知识图谱")
        logger.info("=" * 80)
        
        try:
            # 1. 清空现有数据
            logger.info("\n步骤 1/5: 清空现有数据...")
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            logger.info("数据清空完成")
            
            # 2. 提取实体
            logger.info("\n步骤 2/5: 提取实体...")
            entities = self.extract_entities()
            
            # 3. 提取关系
            logger.info("\n步骤 3/5: 提取关系...")
            relations = self.extract_relations(entities)
            
            # 4. 创建约束和索引
            logger.info("\n步骤 4/5: 创建约束和索引...")
            self.create_constraints_and_indexes()
            
            # 5. 导入数据
            logger.info("\n步骤 5/5: 导入数据到 Neo4j...")
            self.import_entities(entities)
            self.import_relations(relations)
            
            # 打印最终统计
            logger.info("\n" + "=" * 80)
            logger.info("构建完成！统计信息:")
            logger.info("=" * 80)
            
            total_entities = sum(self.stats['entities'].values())
            total_relations = sum(self.stats['relations'].values())
            
            logger.info(f"\n实体总数: {total_entities}")
            for entity_type, count in sorted(self.stats['entities'].items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {entity_type}: {count}")
            
            logger.info(f"\n关系总数: {total_relations}")
            for rel_type, count in sorted(self.stats['relations'].items(), key=lambda x: x[1], reverse=True)[:10]:
                logger.info(f"  {rel_type}: {count}")
            
            logger.info(f"\n错误数: {self.stats['errors']}")
            
            # 验证导入
            logger.info("\n验证导入结果...")
            with self.driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = result.single()['count']
                
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = result.single()['count']
                
                logger.info(f"Neo4j 中节点数: {node_count}")
                logger.info(f"Neo4j 中关系数: {rel_count}")
            
            logger.info("\n✅ 知识图谱构建成功！")
            
        except Exception as e:
            logger.error(f"\n❌ 构建失败: {e}", exc_info=True)
            raise
        finally:
            self.driver.close()
            logger.info("Neo4j 连接已关闭")


def main():
    """主函数"""
    # 配置参数
    OWL_FILE = "data/health-sample.owl"
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "password"  # 根据 docker-compose.yml 中的配置
    
    # 创建构建器并执行
    builder = TCMKnowledgeGraphBuilder(
        owl_file=OWL_FILE,
        neo4j_uri=NEO4J_URI,
        neo4j_user=NEO4J_USER,
        neo4j_password=NEO4J_PASSWORD
    )
    
    builder.build()


if __name__ == "__main__":
    main()
