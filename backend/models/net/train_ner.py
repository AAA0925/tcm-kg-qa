import sys
import os
# 确保能导入 backend 根目录下的 models 模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer
from models.net.net_model import AlbertBiLSTMCRF
from loguru import logger
import json

# 标签映射 (根据你的毕设需求可以扩展)
TAG2ID = {"O": 0, "B-DIS": 1, "I-DIS": 2, "B-SYM": 3, "I-SYM": 4, "B-HERB": 5, "I-HERB": 6}
ID2TAG = {v: k for k, v in TAG2ID.items()}

class TCMDataset(Dataset):
    def __init__(self, data_path, tokenizer, max_len=128):
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.examples = self._load_and_tag_data(data_path)

    def _load_and_tag_data(self, path):
        """从 JSON 文件加载数据并进行远程监督标注"""
        examples = []
        # 这里假设你已经通过脚本生成了包含 'text' 和 'entities' 的 JSON
        if not os.path.exists(path):
            logger.warning(f"数据文件不存在: {path}，使用模拟数据")
            return [{"input_ids": [101, 2345, 2346, 102], "attention_mask": [1, 1, 1, 1], "labels": [0, 1, 2, 0]}]
            
        with open(path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        for item in raw_data:
            text = item['text']
            entities = item.get('entities', []) # [{'start': 0, 'end': 2, 'type': 'DIS'}]
            
            # 1. 初始化全 O 标签
            labels = ['O'] * len(text)
            
            # 2. 填充实体标签
            for ent in entities:
                start, end, etype = ent['start'], ent['end'], ent['type']
                if end <= len(text):
                    labels[start] = f'B-{etype}'
                    for i in range(start + 1, end):
                        labels[i] = f'I-{etype}'
            
            # 3. Tokenize
            encoding = self.tokenizer(
                list(text), 
                is_split_into_words=True, 
                padding='max_length', 
                truncation=True, 
                max_length=self.max_len,
                return_tensors='pt'
            )
            
            # 4. 对齐标签 (简化处理：直接按字符索引映射)
            label_ids = [TAG2ID.get(l, 0) for l in labels]
            # 补齐 padding
            label_ids += [0] * (self.max_len - len(label_ids))
            
            examples.append({
                'input_ids': encoding['input_ids'].squeeze(),
                'attention_mask': encoding['attention_mask'].squeeze(),
                'labels': torch.tensor(label_ids[:self.max_len])
            })
            
        return examples

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]

def train():
    logger.info("正在初始化 ALBERT-BiLSTM-CRF 模型...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    model = AlbertBiLSTMCRF(num_tags=len(TAG2ID)).to(device)
    tokenizer = BertTokenizer.from_pretrained('models/albert-base-chinese')
    
    # 准备数据集
    dataset = TCMDataset('data/ner_train_data.json', tokenizer)
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=2e-5)
    
    logger.info(f"模型已加载到: {device}，开始训练...")
    model.train()
    
    for epoch in range(3): # 示例：训练 3 轮
        total_loss = 0
        for batch in dataloader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            loss = model(input_ids, attention_mask, labels)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        logger.info(f"Epoch {epoch+1}, Loss: {total_loss / len(dataloader):.4f}")
        
    # 保存模型
    torch.save(model.state_dict(), 'models/ner_model.pth')
    logger.success("模型训练完成并保存至 models/ner_model.pth")

if __name__ == "__main__":
    train()
