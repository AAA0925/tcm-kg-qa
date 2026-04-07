"""
中医知识图谱构建脚本
基于 medical_new_2.json 数据集构建 Neo4j 知识图谱
"""

import json
import argparse
from neo4j import GraphDatabase
from loguru import logger
from typing import List, Dict, Any
from pathlib import Path


class KnowledgeGraphBuilder:
    """知识图谱构建器"""
    
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        """
        初始化 Neo4j 连接
        
        Args:
            uri: Neo4j 地址，如 http://localhost:7474
            user: 用户名，如 neo4j
            password: 密码
            database: 数据库名称
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        logger.info(f"已连接到 Neo4j 数据库：{uri}")
        
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            logger.info("数据库连接已关闭")
    
    def create_constraints(self):
        """创建唯一性约束"""
        constraints = [
            "CREATE CONSTRAINT disease_name IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT symptom_name IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT herb_name IF NOT EXISTS FOR (h:Herb) REQUIRE h.name IS UNIQUE",
            "CREATE CONSTRAINT prescription_name IF NOT EXISTS FOR (p:Prescription) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT drug_name IF NOT EXISTS FOR (d:Drug) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT food_name IF NOT EXISTS FOR (f:Food) REQUIRE f.name IS UNIQUE",
            "CREATE CONSTRAINT check_name IF NOT EXISTS FOR (c:Check) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT department_name IF NOT EXISTS FOR (d:Department) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT producer_name IF NOT EXISTS FOR (p:Producer) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT cure_name IF NOT EXISTS FOR (c:Cure) REQUIRE c.name IS UNIQUE",
        ]
        
        with self.driver.session(database=self.database) as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"创建约束成功：{constraint.split('FOR')[0].strip()}")
                except Exception as e:
                    logger.warning(f"创建约束失败或已存在：{e}")
    
    def create_indexes(self):
        """创建索引加速查询"""
        indexes = [
            "CREATE INDEX disease_description IF NOT EXISTS FOR (d:Disease) ON (d.description)",
            "CREATE INDEX disease_cause IF NOT EXISTS FOR (d:Disease) ON (d.cause)",
            "CREATE INDEX herb_effects IF NOT EXISTS FOR (h:Herb) ON (h.effects)",
            "CREATE INDEX prescription_functions IF NOT EXISTS FOR (p:Prescription) ON (p.functions)",
        ]
        
        with self.driver.session(database=self.database) as session:
            for index in indexes:
                try:
                    session.run(index)
                    logger.info(f"创建索引成功：{index.split('ON')[0].strip()}")
                except Exception as e:
                    logger.warning(f"创建索引失败或已存在：{e}")
    
    def load_data(self, data_path: str) -> List[Dict[str, Any]]:
        """
        加载 JSON 数组格式数据（MongoDB 导出格式）
        
        Args:
            data_path: 数据文件路径
            
        Returns:
            数据列表
        """
        logger.info(f"正在加载数据文件：{data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            # 读取全部内容并构造成 JSON 数组格式
            content = f.read()
            # MongoDB 导出格式每行以 }, 结尾，需要构造成数组
            if not content.strip().startswith('['):
                content = '[' + content.replace('},\n', '},').rstrip(',') + ']'
            
            data = json.loads(content)
        
        logger.info(f"数据加载成功，共 {len(data)} 条记录")
        return data
    
    def create_disease_entity(self, disease: Dict[str, Any]):
        """创建疾病实体"""
        query = """
        MERGE (d:Disease {name: $name})
        SET d.desc = COALESCE($desc, d.desc),
            d.cause = COALESCE($cause, d.cause),
            d.prevent = COALESCE($prevent, d.prevent),
            d.cure_lasttime = COALESCE($cure_lasttime, d.cure_lasttime),
            d.cured_prob = COALESCE($cured_prob, d.cured_prob),
            d.easy_get = COALESCE($easy_get, d.easy_get)
        RETURN d
        """
        
        with self.driver.session(database=self.database) as session:
            session.run(query, 
                       name=disease.get('name'),
                       desc=disease.get('desc'),
                       cause=disease.get('cause'),
                       prevent=disease.get('prevent'),
                       cure_lasttime=disease.get('cure_lasttime'),
                       cured_prob=disease.get('cured_prob'),
                       easy_get=disease.get('easy_get'))
    
    def create_generic_entity(self, entity_type: str, entities: List[str]):
        """
        创建通用实体（药品、食物、检查等）
        
        Args:
            entity_type: 实体类型标签
            entities: 实体名称列表
        """
        label_map = {
            'Drug': 'Drug',
            'Food': 'Food',
            'Check': 'Check',
            'Department': 'Department',
            'Producer': 'Producer',
            'Symptom': 'Symptom',
            'Cure': 'Cure'
        }
        
        label = label_map.get(entity_type, entity_type)
        
        query = f"""
        UNWIND $entities AS name
        MERGE (e:{label} {{name: name}})
        """
        
        with self.driver.session(database=self.database) as session:
            # 分批处理，每批 1000 个
            batch_size = 1000
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]
                session.run(query, entities=batch)
            
            logger.info(f"创建 {len(entities)} 个 {label} 实体完成")
    
    def create_relation(self, head: str, relation: str, tail: str, 
                       head_type: str = None, tail_type: str = None):
        """
        创建关系
        
        Args:
            head: 头实体名称
            relation: 关系类型
            tail: 尾实体名称
            head_type: 头实体类型（可选）
            tail_type: 尾实体类型（可选）
        """
        # 关系类型映射到 Neo4j 标签
        relation_map = {
            'belongs_to': 'BELONGS_TO',
            'common_drug': 'COMMON_DRUG',
            'do_eat': 'DO_EAT',
            'drugs_of': 'DRUGS_OF',
            'need_check': 'NEED_CHECK',
            'no_eat': 'NO_EAT',
            'recommand_drug': 'RECOMMAND_DRUG',
            'recommand_eat': 'RECOMMAND_EAT',
            'has_symptom': 'HAS_SYMPTOM',
            'acompany_with': 'ACOMPANY_WITH',
            'cure_way': 'CURE_WAY'
        }
        
        rel_type = relation_map.get(relation, relation.upper())
        
        # 默认实体类型
        if not head_type:
            head_type = 'Disease' if relation in ['has_symptom', 'common_drug', 'need_check', 
                                                   'do_eat', 'no_eat', 'recommand_drug', 
                                                   'recommand_eat', 'acompany_with', 'cure_way'] else 'Entity'
        
        if not tail_type:
            if relation in ['belongs_to']:
                tail_type = 'Department'
            elif relation in ['common_drug', 'recommand_drug']:
                tail_type = 'Drug'
            elif relation in ['do_eat', 'recommand_eat']:
                tail_type = 'Food'
            elif relation in ['need_check']:
                tail_type = 'Check'
            elif relation in ['has_symptom']:
                tail_type = 'Symptom'
            elif relation in ['acompany_with']:
                tail_type = 'Disease'
            elif relation in ['cure_way']:
                tail_type = 'Cure'
            else:
                tail_type = 'Entity'
        
        query = f"""
        MATCH (h:{head_type} {{name: $head}})
        MATCH (t:{tail_type} {{name: $tail}})
        MERGE (h)-[r:{rel_type}]->(t)
        RETURN r
        """
        
        with self.driver.session(database=self.database) as session:
            try:
                session.run(query, head=head, tail=tail)
            except Exception as e:
                logger.debug(f"创建关系失败：{head}-[{relation}]->{tail}, 错误：{e}")
    
    def build_graph(self, data: List[Dict[str, Any]]):
        """
        构建完整知识图谱
        
        Args:
            data: 疾病数据列表
        """
        logger.info("开始构建知识图谱...")
        
        # Step 1: 创建所有疾病实体
        logger.info("Step 1: 创建疾病实体...")
        for disease in data:
            self.create_disease_entity(disease)
        
        # Step 2: 收集所有其他实体
        logger.info("Step 2: 收集其他类型实体...")
        all_entities = {
            'Drug': set(),
            'Food': set(),
            'Check': set(),
            'Department': set(),
            'Producer': set(),
            'Symptom': set(),
            'Cure': set()
        }
        
        all_relations = []
        
        def parse_field(value):
            """解析字段值，支持字符串和列表两种格式"""
            if not value:
                return []
            if isinstance(value, list):
                # 如果已经是列表，直接返回
                return [str(item).strip() for item in value if str(item).strip()]
            elif isinstance(value, str):
                # 如果是字符串，按逗号分割
                return [item.strip() for item in value.split('，') if item.strip()]
            return []
        
        for disease in data:
            disease_name = disease['name']
            
            # 收集症状
            symptoms = parse_field(disease.get('symptoms'))
            for symptom in symptoms:
                all_entities['Symptom'].add(symptom)
                all_relations.append((disease_name, 'has_symptom', symptom))
            
            # 收集药品
            common_drugs = parse_field(disease.get('common_drug'))
            for drug in common_drugs:
                all_entities['Drug'].add(drug)
                all_relations.append((disease_name, 'common_drug', drug))
            
            recommand_drugs = parse_field(disease.get('recommand_drug'))
            for drug in recommand_drugs:
                all_entities['Drug'].add(drug)
                all_relations.append((disease_name, 'recommand_drug', drug))
            
            # 收集食物
            do_eat = parse_field(disease.get('do_eat'))
            for food in do_eat:
                all_entities['Food'].add(food)
                all_relations.append((disease_name, 'do_eat', food))
            
            no_eat = parse_field(disease.get('no_eat'))
            for food in no_eat:
                all_entities['Food'].add(food)
                all_relations.append((disease_name, 'no_eat', food))
            
            recommand_eat = parse_field(disease.get('recommand_eat'))
            for food in recommand_eat:
                all_entities['Food'].add(food)
                all_relations.append((disease_name, 'recommand_eat', food))
            
            # 收集检查项目
            need_check = parse_field(disease.get('need_check'))
            for check in need_check:
                all_entities['Check'].add(check)
                all_relations.append((disease_name, 'need_check', check))
            
            # 收集治疗方法
            cure_way = parse_field(disease.get('cure_way'))
            for cure in cure_way:
                all_entities['Cure'].add(cure)
                all_relations.append((disease_name, 'cure_way', cure))
            
            # 收集并发疾病
            acompany_with = parse_field(disease.get('acompany_with'))
            for dis in acompany_with:
                all_relations.append((disease_name, 'acompany_with', dis))
            
            # 收集所属科室
            department = parse_field(disease.get('department'))
            for dept in department:
                all_entities['Department'].add(dept)
                all_relations.append((disease_name, 'belongs_to', dept))
        
        # Step 3: 创建所有其他实体
        logger.info("Step 3: 创建其他类型实体...")
        for entity_type, entities in all_entities.items():
            if entities:
                self.create_generic_entity(entity_type, list(entities))
        
        # Step 4: 创建所有关系
        logger.info(f"Step 4: 创建 {len(all_relations)} 个关系...")
        for i, (head, rel, tail) in enumerate(all_relations):
            self.create_relation(head, rel, tail)
            if (i + 1) % 10000 == 0:
                logger.info(f"已创建 {i + 1}/{len(all_relations)} 个关系")
        
        logger.info("知识图谱构建完成!")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        stats_query = """
        MATCH (n)
        RETURN count(n) as node_count
        """
        
        rel_query = """
        MATCH ()-[r]->()
        RETURN count(r) as relation_count
        """
        
        with self.driver.session(database=self.database) as session:
            node_result = session.run(stats_query)
            rel_result = session.run(rel_query)
            
            return {
                'node_count': node_result.single()['node_count'] if node_result else 0,
                'relation_count': rel_result.single()['relation_count'] if rel_result else 0
            }
    
    def export_entities_and_relations(self, output_dir: str = "data"):
        """
        导出实体和关系到文件
        
        Args:
            output_dir: 输出目录
        """
        logger.info("正在导出实体和关系...")
        
        output_path = Path(output_dir)
        ent_dir = output_path / "ent_aug"
        ent_dir.mkdir(parents=True, exist_ok=True)
        
        # 导出实体
        entity_types = ['Disease', 'Drug', 'Food', 'Check', 'Department', 
                       'Producer', 'Symptom', 'Cure']
        
        for entity_type in entity_types:
            query = f"MATCH (n:{entity_type}) RETURN n.name as name"
            
            with self.driver.session(database=self.database) as session:
                result = session.run(query)
                entities = [record['name'] for record in result if record['name']]
                
                # 写入文件
                output_file = ent_dir / f"{entity_type.lower()}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    for entity in entities:
                        f.write(f"{entity}\n")
                
                logger.info(f"导出 {len(entities)} 个 {entity_type} 实体到 {output_file}")
        
        # 导出关系
        relations_query = """
        MATCH (n)-[r]->(m)
        RETURN labels(n)[0] as head_type, n.name as head, 
               type(r) as relation, 
               labels(m)[0] as tail_type, m.name as tail
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(relations_query)
            
            output_file = output_path / "rel_aug.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                for record in result:
                    line = f"{record['head']}\t{record['relation']}\t{record['tail']}\n"
                    f.write(line)
            
            logger.info(f"导出关系到 {output_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='构建中医知识图谱')
    parser.add_argument('--website', type=str, required=True, 
                       help='Neo4j bolt 地址，如 bolt://localhost:7687')
    parser.add_argument('--user', type=str, default='neo4j',
                       help='Neo4j 用户名')
    parser.add_argument('--password', type=str, required=True,
                       help='Neo4j 密码')
    parser.add_argument('--dbname', type=str, default='neo4j',
                       help='Neo4j 数据库名')
    parser.add_argument('--data', type=str, default='data/medical_new_2.json',
                       help='数据文件路径')
    parser.add_argument('--export-dir', type=str, default='data',
                       help='导出文件目录')
    
    args = parser.parse_args()
    
    # 初始化构建器
    builder = KnowledgeGraphBuilder(
        uri=args.website,
        user=args.user,
        password=args.password,
        database=args.dbname
    )
    
    try:
        # 创建约束和索引
        logger.info("创建数据库约束和索引...")
        builder.create_constraints()
        builder.create_indexes()
        
        # 加载数据
        data = builder.load_data(args.data)
        
        # 构建图谱
        builder.build_graph(data)
        
        # 获取统计信息
        stats = builder.get_statistics()
        logger.info(f"图谱统计信息：节点数={stats['node_count']}, 关系数={stats['relation_count']}")
        
        # 导出实体和关系
        builder.export_entities_and_relations(args.export_dir)
        
        logger.success("✅ 知识图谱构建完成!")
        
    except Exception as e:
        logger.error(f"❌ 构建过程中发生错误：{e}")
        raise
    finally:
        builder.close()


if __name__ == "__main__":
    main()
