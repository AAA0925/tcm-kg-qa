import torch
from transformers import BertTokenizer
from models.net.net_model import AlbertBiLSTMCRF
from loguru import logger

TAG2ID = {"O": 0, "B-DIS": 1, "I-DIS": 2, "B-SYM": 3, "I-SYM": 4, "B-HERB": 5, "I-HERB": 6}
ID2TAG = {v: k for k, v in TAG2ID.items()}

class NERInference:
    def __init__(self, model_path='models/ner_model.pth', device='cpu'):
        self.device = torch.device(device)
        self.tokenizer = BertTokenizer.from_pretrained('models/albert-base-chinese')
        
        self.model = AlbertBiLSTMCRF(num_tags=len(TAG2ID))
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"NER 模型已从 {model_path} 加载")

    def predict(self, text):
        """对单句文本进行实体识别"""
        # ALBERT/BERT  tokenizer 会自动处理中文，不需要 list(text)
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
            emissions = self.model(input_ids, attention_mask)
            predictions = torch.argmax(emissions, dim=-1)
        
        tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0])
        pred_labels = [ID2TAG.get(p.item(), 'O') for p in predictions[0]]
        
        logger.debug(f"Tokens: {tokens}")
        logger.debug(f"Labels: {pred_labels}")
        
        # 提取实体 (BIO 解码)
        entities = []
        current_entity = ""
        current_type = ""
        
        # 同时遍历，跳过特殊标记
        for token, label in zip(tokens, pred_labels):
            if token in ['[CLS]', '[SEP]', '[PAD]']: continue
            
            # 如果是 B- 标签，开启新实体
            if label.startswith('B-'):
                if current_entity:
                    entities.append({"text": current_entity, "type": current_type})
                current_entity = token
                current_type = label[2:]
            # 如果是 I- 标签，且当前有正在进行的同类型实体，则拼接
            elif label.startswith('I-') and current_type == label[2:]:
                current_entity += token
            # 如果当前是 I- 但没有对应的 B-（比如模型预测偏移），尝试当作 B- 处理
            elif label.startswith('I-') and not current_entity:
                current_entity = token
                current_type = label[2:]
            else:
                # 遇到 O 或类型不匹配，结束当前实体
                if current_entity:
                    entities.append({"text": current_entity, "type": current_type})
                current_entity = ""
                current_type = ""
                
        if current_entity:
            entities.append({"text": current_entity, "type": current_type})
            
        logger.info(f"NER 识别结果: {entities}")
        return entities

# 全局实例
ner_infer = NERInference()
