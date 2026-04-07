// 创建中医知识图谱约束和索引
CREATE CONSTRAINT disease_name IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE;
CREATE CONSTRAINT symptom_name IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT herb_name IF NOT EXISTS FOR (h:Herb) REQUIRE h.name IS UNIQUE;
CREATE CONSTRAINT prescription_name IF NOT EXISTS FOR (p:Prescription) REQUIRE p.name IS UNIQUE;

// 创建索引加速查询
CREATE INDEX disease_description IF NOT EXISTS FOR (d:Disease) ON (d.description);
CREATE INDEX herb_effects IF NOT EXISTS FOR (h:Herb) ON (h.effects);
