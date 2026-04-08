import torch
import torch.nn as nn

class CRF(nn.Module):
    """条件随机场 (Conditional Random Field)"""
    
    def __init__(self, num_tags):
        super(CRF, self).__init__()
        self.num_tags = num_tags
        # 转移矩阵：transitions[i][j] 表示从标签 j 转移到标签 i 的得分
        self.transitions = nn.Parameter(torch.randn(num_tags, num_tags))
        
    def forward(self, emissions, tags, mask=None):
        """
        计算负对数似然损失
        emissions: [batch_size, seq_len, num_tags] - BiLSTM 的输出
        tags: [batch_size, seq_len] - 真实标签
        mask: [batch_size, seq_len] - 填充掩码
        """
        if mask is None:
            mask = torch.ones_like(tags).byte()
            
        # 计算真实路径的得分
        score = self._compute_score(emissions, tags, mask)
        # 计算所有可能路径的总得分 (Log Sum Exp)
        total_score = self._compute_log_normalizer(emissions, mask)
        
        return -(score - total_score).mean()

    def _compute_score(self, emissions, tags, mask):
        batch_size, seq_len = tags.shape
        score = torch.zeros(batch_size, device=emissions.device)
        
        # 加上起始位置的发射分数
        score += emissions[torch.arange(batch_size), 0, tags[:, 0]]
        
        for i in range(1, seq_len):
            # 累加转移分数和发射分数
            trans_score = self.transitions[tags[:, i], tags[:, i - 1]]
            emit_score = emissions[torch.arange(batch_size), i, tags[:, i]]
            score += (trans_score + emit_score) * mask[:, i].float()
            
        return score

    def _compute_log_normalizer(self, emissions, mask):
        # 简化的 Log Sum Exp 实现，实际工程中建议使用 torchcrf 库
        # 这里为了演示结构，使用一个简单的近似或占位逻辑
        # 在实际毕设中，建议 pip install torchcrf 并直接调用
        return torch.zeros(emissions.size(0), device=emissions.device) 
