// Simple TCM Knowledge Graph Sample Data
CREATE (d1:Disease {name: 'GanMao', description: 'Common cold', category: 'External disease'})
CREATE (d2:Disease {name: 'KeSou', description: 'Cough', category: 'Lung disease'})
CREATE (s1:Symptom {name: 'FaRe', description: 'Fever'})
CREATE (s2:Symptom {name: 'TouTong', description: 'Headache'})
CREATE (h1:Herb {name: 'JinYinHua', effects: 'Clear heat and detoxify', nature: 'Cold'})
CREATE (h2:Herb {name: 'LianQiao', effects: 'Clear heat and reduce inflammation', nature: 'Cool'})
CREATE (p1:Prescription {name: 'YinQiaoSan', source: 'Wen Bing Tiao Bian', effects: 'Clear heat and resolve toxins'})

MATCH (d:Disease {name: 'GanMao'}), (s:Symptom) 
WHERE s.name IN ['FaRe', 'TouTong']
CREATE (d)-[:HAS_SYMPTOM]->(s)

MATCH (d:Disease {name: 'GanMao'}), (h:Herb) 
WHERE h.name IN ['JinYinHua', 'LianQiao']
CREATE (d)-[:RECOMMEND_HERB]->(h)

MATCH (p:Prescription {name: 'YinQiaoSan'}), (h:Herb) 
WHERE h.name IN ['JinYinHua', 'LianQiao']
CREATE (p)-[:CONTAINS_HERB]->(h)
