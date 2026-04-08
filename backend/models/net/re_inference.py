import torch
from transformers import BertTokenizer
from models.net.relation_extractor import BertRelationExtractor, RELATION_TYPES, REL2ID
from loguru import logger

class REInference:
    def __init__(self, model_path=None, device='cpu'):
        self.device = torch.device(device)
        self.tokenizer = BertTokenizer.from_pretrained('models/albert-base-chinese')
        
        self.model = BertRelationExtractor()
        if model_path:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            logger.info(f"关系抽取模型已加载: {model_path}")
        else:
            logger.warning("未提供关系抽取模型路径，将使用规则兜底")
            
        self.model.to(self.device)
        self.model.eval()

    def predict(self, sentence, head_entity, tail_entity):
        """预测两个实体在句子中的关系"""
        # 构造输入：[CLS] 句子 [SEP] 头实体 [SEP] 尾实体 [SEP]
        text = f"{sentence} [SEP] {head_entity} [SEP] {tail_entity}"
        inputs = self.tokenizer(
            text, 
            return_tensors='pt', 
            padding=True, 
            truncation=True, 
            max_length=128
        )
        
        input_ids = inputs['input_ids'].to(self.device)
        attention_mask = inputs['attention_mask'].to(self.device)
        
        with torch.no_grad():
            logits = self.model(input_ids, attention_mask)
            pred_id = torch.argmax(logits, dim=-1).item()
            
        relation = RELATION_TYPES[pred_id]
        return relation

# 全局实例
try:
    re_infer = REInference(model_path='models/re_model.pth')
except Exception as e:
    logger.error(f"RE 模型加载失败: {e}")
    re_infer = None
