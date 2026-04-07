"""调试 Neo4j 查询结果"""
from app.services.kg.neo4j_client import kg_client

print("查询心阴虚的关系...")

with kg_client.driver.session() as session:
    # 测试查询
    cypher = """
    MATCH (n {name: '心阴虚'})-[r]-(m)
    RETURN n, r, m
    LIMIT 3
    """
    result = session.run(cypher)
    
    print("\n查询结果:")
    for i, record in enumerate(result, 1):
        print(f"\n记录 {i}:")
        print(f"  n = {record['n']}")
        print(f"  n.get('name') = {record['n'].get('name')}")
        print(f"  r = {record['r']}")
        print(f"  r type = {type(record['r'])}")
        print(f"  m = {record['m']}")
        print(f"  m.get('name') = {record['m'].get('name')}")
        
        if record['r']:
            print(f"  r.type = {record['r'].type}")
