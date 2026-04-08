import torch
import torch.nn as nn
from transformers import BertModel
from loguru import logger

# 定义你的关系类型 (根据你的 Neo4j 设计调整)
RELATION_TYPES = ["O", "HAS_SYMPTOM", "TREATS", "IS_A"] 
REL2ID = {r: i for i, r in enumerate(RELATION_TYPES)}

class BertRelationExtractor(nn.Module):
    """基于 BERT 的中医关系抽取模型"""
    
    def __init__(self, model_name='models/albert-base-chinese', num_relations=len(RELATION_TYPES)):
        super(BertRelationExtractor, self).__init__()
        self.bert = BertModel.from_pretrained(model_name)
        hidden_size = self.bert.config.hidden_size
        
        # 分类层：将 [CLS] 的输出映射到关系类别
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size // 2, num_relations)
        )
        
    def forward(self, input_ids, attention_mask, token_type_ids=None):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids)
        cls_output = outputs.last_hidden_state[:, 0, :]  # 取 [CLS] 标记的输出
        logits = self.classifier(cls_output)
        return logits
