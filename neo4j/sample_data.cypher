// 示例病症数据
CREATE (d1:Disease {name: '感冒', description: '外感风邪引起的常见疾病', category: '外感病'})
CREATE (d2:Disease {name: '咳嗽', description: '肺气上逆导致的病症', category: '肺系病'})
CREATE (d3:Disease {name: '胃痛', description: '胃部疼痛不适', category: '脾胃病'})

// 示例症状数据
CREATE (s1:Symptom {name: '发热', description: '体温升高'})
CREATE (s2:Symptom {name: '头痛', description: '头部疼痛'})
CREATE (s3:Symptom {name: '鼻塞', description: '鼻腔阻塞'})
CREATE (s4:Symptom {name: '流涕', description: '鼻涕流出'})
CREATE (s5:Symptom {name: '咳嗽', description: '咳嗽症状'})

// 示例中药数据
CREATE (h1:Herb {name: '金银花', effects: '清热解毒，疏散风热', nature: '寒', flavor: '甘'})
CREATE (h2:Herb {name: '连翘', effects: '清热解毒，消肿散结', nature: '微寒', flavor: '苦'})
CREATE (h3:Herb {name: '薄荷', effects: '疏散风热，清利头目', nature: '凉', flavor: '辛'})
CREATE (h4:Herb {name: '甘草', effects: '补脾益气，清热解毒', nature: '平', flavor: '甘'})
CREATE (h5:Herb {name: '陈皮', effects: '理气健脾，燥湿化痰', nature: '温', flavor: '辛'})

// 示例处方数据
CREATE (p1:Prescription {name: '银翘散', source: '《温病条辨》', effects: '辛凉透表，清热解毒'})
CREATE (p2:Prescription {name: '麻黄汤', source: '《伤寒论》', effects: '发汗解表，宣肺平喘'})
CREATE (p3:Prescription {name: '桂枝汤', source: '《伤寒论》', effects: '解肌发表，调和营卫'})

// 创建病症 - 症状关系
MATCH (d:Disease {name: '感冒'}), (s:Symptom) 
WHERE s.name IN ['发热', '头痛', '鼻塞', '流涕']
CREATE (d)-[:HAS_SYMPTOM {severity: 'common'}]->(s)

MATCH (d:Disease {name: '咳嗽'}), (s:Symptom {name: '咳嗽'})
CREATE (d)-[:HAS_SYMPTOM {severity: 'main'}]->(s)

// 创建病症 - 中药关系（推荐用药）
MATCH (d:Disease {name: '感冒'}), (h:Herb) 
WHERE h.name IN ['金银花', '连翘', '薄荷', '甘草']
CREATE (d)-[:RECOMMEND_HERB]->(h)

MATCH (d:Disease {name: '咳嗽'}), (h:Herb) 
WHERE h.name IN ['甘草', '陈皮']
CREATE (d)-[:RECOMMEND_HERB]->(h)

// 创建病症 - 处方关系
MATCH (d:Disease {name: '感冒'}), (p:Prescription {name: '银翘散'})
CREATE (d)-[:TREATED_BY]->(p)

MATCH (d:Disease {name: '感冒'}), (p:Prescription {name: '桂枝汤'})
CREATE (d)-[:TREATED_BY]->(p)

// 创建处方 - 中药关系（处方组成）
MATCH (p:Prescription {name: '银翘散'}), (h:Herb) 
WHERE h.name IN ['金银花', '连翘', '薄荷', '甘草']
CREATE (p)-[:CONTAINS_HERB {amount: '9g'}]->(h)

// 创建中药功效关系
MATCH (h1:Herb {name: '金银花'}), (h2:Herb {name: '连翘'})
CREATE (h1)-[:OFTEN_USED_WITH]->(h2)

MATCH (h1:Herb {name: '薄荷'}), (h2:Herb {name: '甘草'})
CREATE (h1)-[:OFTEN_USED_WITH]->(h2)
