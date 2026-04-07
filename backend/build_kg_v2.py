"""
中医知识图谱构建脚本 v2.0
修复：正确过滤书名，只保留真正的中医实体

策略：
1. 排除所有带《》的书名
2. 基于更精确的关键词分类
3. 将字面量转换为实体（症状、证候、功效）
"""

from rdflib import Graph, RDF, RDFS, OWL
from neo4j import GraphDatabase
import re
from collections import defaultdict, Counter
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TCMKGBuilderV2:
    """中医知识图谱构建器 v2.0"""
    
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
        
        # 实体分类规则（更精确）
        self.entity_categories = {
            'Disease': ['病', '症', '疾'],
            'Syndrome': ['证', '候'],
            'Prescription': ['汤', '丸', '散', '膏', '丹', '饮', '剂'],
            'Herb': ['人参', '当归', '白术', '茯苓', '甘草', '柴胡', '黄芩', '半夏', '陈皮', 
                     '砂仁', '木香', '黄芪', '枸杞', '菊花', '金银花'],
            'Symptom': ['痛', '咳', '喘', '晕', '胀', '闷', '烦', '渴', '呕', '泻', 
                       '失眠', '食欲不振', '面色', '乏力', '头晕'],
            'Therapy': ['法', '疗法', '灸', '针', '推拿', '按摩', '针刺', '艾灸'],
            'WellnessMethod': ['养生', '调护', '保健', '食疗', '锻炼', '导引'],
            'Meridian': ['心经', '肝经', '脾经', '肺经', '肾经', '胃经', '胆经', '膀胱经', 
                        '任脉', '督脉', '冲脉', '带脉'],
            'Classic': [],  # 专门处理书名
            'Effect': ['健脾', '化痰', '清热', '解毒', '利水', '消肿', '补气', '养血']
        }
    
    def is_book_title(self, label: str) -> bool:
        """判断是否为书名"""
        return '《' in label or '》' in label
    
    def classify_entity(self, label: str) -> str:
        """分类实体类型"""
        # 首先检查是否为书名
        if self.is_book_title(label):
            return 'Classic'
        
        # 其他实体类型
        for entity_type, keywords in self.entity_categories.items():
            if entity_type == 'Classic':
                continue
            if any(kw in label for kw in keywords):
                return entity_type
        
        # 关键修改：对于无法分类但有意义的中文标签，归类为 Concept
        # 这样可以保留“下位词/上位词”关系
        if len(label) >= 2 and any('\u4e00' <= c <= '\u9fff' for c in label):
            return 'Concept'
        
        return 'Other'
    
    def clean_label(self, label: str) -> str:
        """清理标签"""
        if not label:
            return ""
        label = label.strip()
        label = re.sub(r'\s+', ' ', label)
        return label
    
    def extract_data(self):
        """提取实体和关系"""
        logger.info("正在提取数据...")
        
        entities = {}  # name -> type
        relations = []
        
        individuals = list(self.g.subjects(RDF.type, OWL.NamedIndividual))
        
        # 第一遍：收集所有实体
        for ind in individuals:
            label = self.g.value(ind, RDFS.label)
            if not label:
                continue
            
            label_str = self.clean_label(str(label))
            if not label_str or len(label_str) > 100:
                continue
            
            entity_type = self.classify_entity(label_str)
            
            # 跳过无法分类的
            if entity_type == 'Other':
                continue
            
            entities[label_str] = entity_type
        
        logger.info(f"实体总数: {len(entities)}")
        
        # 统计各类型数量
        type_counter = Counter(entities.values())
        for etype, count in type_counter.most_common():
            logger.info(f"  {etype}: {count}")
        
        # 第二遍：提取关系
        literal_to_entity_count = 0
        
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
                
                # 关系映射
                rel_mapping = {
                    '治疗': 'TREATS',
                    '由...组成': 'COMPOSED_OF',
                    '归...经': 'BELONGS_TO_MERIDIAN',
                    '具有性味': 'HAS_PROPERTY',
                    '上位词': 'SUBCLASS_OF',  # A 的上位词是 B => A SUBCLASS_OF B
                    '下位词': 'SUPERCLASS_OF',  # A 的下位词是 B => A SUPERCLASS_OF B (B是A的子类)
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
                    '被包含': 'CONTAINED_IN',
                    '产生': 'GENERATES',
                    '被产生': 'GENERATED_BY',
                    '有的概念部分': 'HAS_PART',
                    '的概念部分': 'PART_OF',
                    '与相互作用': 'INTERACTS_WITH',
                    '被…使用': 'USED_BY',
                    '被…治疗': 'TREATED_BY',
                    '被…分析': 'ANALYZED_BY',
                    '之中的焦点问题': 'FOCUS_ISSUE',
                }
                
                neo4j_rel_type = rel_mapping.get(rel_label_str)
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
                            if obj_name not in entities:
                                entities[obj_name] = obj_type
                            
                            relations.append({
                                'source': subj_name,
                                'relation': neo4j_rel_type,
                                'target': obj_name
                            })
                else:
                    # 客体是字面量 - 对特定关系类型转换为实体
                    obj_value = str(o).strip()
                    
                    if not obj_value or len(obj_value) > 200:
                        continue
                    
                    # 需要转换为实体的关系
                    literal_to_entity_rules = {
                        '有症状': 'Symptom',
                        '对应证候': 'Syndrome',
                        '功效': 'Effect',
                        '作用': 'Effect',
                        '来源': 'Classic',  # 新增：将书名转换为典籍节点
                        '出自': 'Classic',
                    }
                    
                    if rel_label_str in literal_to_entity_rules:
                        target_type = literal_to_entity_rules[rel_label_str]
                        
                        # 分割多个值
                        items = [item.strip() for item in re.split(r'[，,;；$]', obj_value) if item.strip()]
                        
                        for item in items:
                            if item and len(item) < 100:
                                # 对于 Classic 类型，保留书名号
                                if target_type == 'Classic' and '《' not in item:
                                    item = f'《{item}》'
                                
                                if item not in entities:
                                    entities[item] = target_type
                                    literal_to_entity_count += 1
                                
                                relations.append({
                                    'source': subj_name,
                                    'relation': neo4j_rel_type,
                                    'target': item
                                })
        
        logger.info(f"从字面量创建的实体: {literal_to_entity_count}")
        logger.info(f"关系总数: {len(relations)}")
        
        return entities, relations
    
    def build(self):
        """执行构建"""
        logger.info("=" * 80)
        logger.info("开始构建中医知识图谱 v2.0")
        logger.info("=" * 80)
        
        try:
            # 1. 提取数据
            logger.info("\n步骤 1/4: 提取数据...")
            entities, relations = self.extract_data()
            
            # 2. 清空数据库
            logger.info("\n步骤 2/4: 清空数据库...")
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
                # 删除所有约束
                result = session.run("SHOW CONSTRAINTS")
                for record in result:
                    constraint_name = record['name']
                    try:
                        session.run(f"DROP CONSTRAINT {constraint_name} IF EXISTS")
                    except:
                        pass
            logger.info("数据库已清空")
            
            # 3. 导入实体
            logger.info("\n步骤 3/4: 导入实体...")
            entities_by_type = defaultdict(list)
            for name, etype in entities.items():
                entities_by_type[etype].append(name)
            
            with self.driver.session() as session:
                for entity_type, names in entities_by_type.items():
                    # 创建约束
                    try:
                        session.run(f"""
                            CREATE CONSTRAINT unique_{entity_type.lower()}_name
                            FOR (n:{entity_type})
                            REQUIRE n.name IS UNIQUE
                        """)
                    except Exception as e:
                        logger.warning(f"约束创建失败 {entity_type}: {e}")
                    
                    # 批量导入
                    batch_size = 100
                    for i in range(0, len(names), batch_size):
                        batch = names[i:i+batch_size]
                        cypher = f"""
                            UNWIND $batch AS name
                            MERGE (n:{entity_type} {{name: name}})
                        """
                        session.run(cypher, batch=batch)
                    
                    logger.info(f"  {entity_type}: {len(names)} 个")
            
            # 4. 导入关系
            logger.info("\n步骤 4/4: 导入关系...")
            success = 0
            failed = 0
            
            with self.driver.session() as session:
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
            
            logger.info(f"  成功: {success}, 失败: {failed}")
            
            # 验证
            logger.info("\n验证结果...")
            with self.driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = result.single()['count']
                
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = result.single()['count']
                
                logger.info(f"节点数: {node_count}")
                logger.info(f"关系数: {rel_count}")
                
                # 显示每个类型的数量
                result = session.run("""
                    MATCH (n)
                    UNWIND labels(n) AS label
                    RETURN label, count(*) AS count
                    ORDER BY count DESC
                """)
                
                logger.info("\n实体分布:")
                for record in result:
                    logger.info(f"  {record['label']}: {record['count']}")
            
            logger.info("\n✅ 构建完成！")
            
        except Exception as e:
            logger.error(f"❌ 构建失败: {e}", exc_info=True)
            raise
        finally:
            self.driver.close()


def main():
    builder = TCMKGBuilderV2(
        owl_file="data/health-sample.owl",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password"
    )
    builder.build()


if __name__ == "__main__":
    main()
