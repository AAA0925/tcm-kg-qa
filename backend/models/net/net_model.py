import torch
import torch.nn as nn
try:
    from modelscope import AutoModel as MSModel, AutoTokenizer as MSTokenizer
    USE_MODELSCOPE = True
except ImportError:
    from transformers import AlbertModel, AlbertTokenizer
    USE_MODELSCOPE = False

class AlbertBiLSTMCRF(nn.Module):
    """基于 ALBERT-BiLSTM-CRF 的中医实体识别模型"""
    
    def __init__(self, albert_model_name='models/albert-base-chinese', num_tags=7, lstm_hidden=256):
        super(AlbertBiLSTMCRF, self).__init__()
        
        # 1. ALBERT 预训练模型 (Embedding 层)
        if USE_MODELSCOPE:
            self.albert = MSModel.from_pretrained(albert_model_name)
            hidden_size = self.albert.config.hidden_size
        else:
            self.albert = AlbertModel.from_pretrained('albert-base-chinese')
            hidden_size = self.albert.config.hidden_size
        
        # 2. BiLSTM 层 (捕捉序列特征)
        self.bilstm = nn.LSTM(
            input_size=hidden_size,
            hidden_size=lstm_hidden,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        
        # 3. 线性映射层 (将 LSTM 输出映射到标签空间)
        self.hidden2tag = nn.Linear(lstm_hidden * 2, num_tags)
        
        # 4. CRF 层 (学习标签转移约束)
        self.crf = None # 实际使用时建议引入 torchcrf 库
        
    def forward(self, input_ids, attention_mask, tags=None):
        # 获取 ALBERT 输出
        outputs = self.albert(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state  # [batch, seq_len, hidden]
        
        # 通过 BiLSTM
        lstm_out, _ = self.bilstm(sequence_output)
        
        # 映射到标签得分 (emissions)
        emissions = self.hidden2tag(lstm_out)
        
        if tags is not None:
            # 训练模式：计算损失
            # 这里简化处理，实际应调用 crf.forward(emissions, tags, attention_mask)
            return self._compute_loss(emissions, tags, attention_mask)
        else:
            # 预测模式：返回得分矩阵，后续用 Viterbi 算法解码
            return emissions
            
    def _compute_loss(self, emissions, tags, mask):
        # 简化的交叉熵损失作为替代，毕设中请替换为 CRF Loss
        loss_fct = nn.CrossEntropyLoss()
        active_loss = mask.view(-1) == 1
        active_logits = emissions.view(-1, emissions.shape[-1])[active_loss]
        active_labels = tags.view(-1)[active_loss]
        return loss_fct(active_logits, active_labels)
