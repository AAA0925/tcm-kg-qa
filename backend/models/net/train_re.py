import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer
from models.net.relation_extractor import BertRelationExtractor, REL2ID
from loguru import logger
import json

class REDataset(Dataset):
    def __init__(self, data_path, tokenizer):
        with open(data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        # 构造输入格式：[CLS] 句子 [SEP] 头实体 [SEP] 尾实体 [SEP]
        text = f"{item['text']} [SEP] {item['head']} [SEP] {item['tail']}"
        
        encodings = self.tokenizer(
            text, 
            padding='max_length', 
            truncation=True, 
            max_length=128, 
            return_tensors='pt'
        )
        
        label_id = REL2ID.get(item['relation'], 0)
        
        return {
            'input_ids': encodings['input_ids'].squeeze(),
            'attention_mask': encodings['attention_mask'].squeeze(),
            'labels': torch.tensor(label_id, dtype=torch.long)
        }

def train_re():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"使用设备: {device}")
    
    # 1. 准备数据
    tokenizer = BertTokenizer.from_pretrained('models/albert-base-chinese')
    dataset = REDataset('data/re_train_data.json', tokenizer)
    dataloader = DataLoader(dataset, batch_size=16, shuffle=True)
    
    # 2. 初始化模型
    model = BertRelationExtractor().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    criterion = nn.CrossEntropyLoss()
    
    logger.info("开始训练 RE 模型...")
    epochs = 3
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch in dataloader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            optimizer.zero_grad()
            logits = model(input_ids, attention_mask)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(dataloader)
        logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
    
    # 3. 保存模型
    save_path = 'models/re_model.pth'
    torch.save(model.state_dict(), save_path)
    logger.success(f"RE 模型训练完成并保存至 {save_path}")

if __name__ == "__main__":
    train_re()
