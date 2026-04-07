from typing import List, Dict
import dashscope
from dashscope import Generation
from loguru import logger
from app.core.config import settings

class LLMClient:
    """大模型客户端 - 封装大模型API调用"""
    
    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.model = settings.LLM_MODEL
        dashscope.api_key = self.api_key
        logger.info(f"大模型客户端初始化，使用模型: {self.model}")
    
    def generate(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """
        调用大模型生成回答
        
        Args:
            messages: 消息列表，格式: [{"role": "system/user/assistant", "content": "文本"}]
            temperature: 温度参数，控制随机性
            
        Returns:
            生成的文本
        """
        try:
            response = Generation.call(
                model=self.model,
                messages=messages,
                temperature=temperature,
                result_format='message'
            )
            
            if response.status_code == 200:
                result = response.output.choices[0].message.content
                logger.info(f"大模型调用成功，生成 {len(result)} 字符")
                return result
            else:
                logger.error(f"大模型调用失败: {response.code} - {response.message}")
                return f"模型调用失败: {response.message}"
                
        except Exception as e:
            logger.error(f"大模型调用异常: {e}")
            return f"生成答案时出错: {str(e)}"
    
    def test_connection(self) -> bool:
        """测试大模型连接"""
        try:
            result = self.generate([
                {"role": "user", "content": "你好"}
            ])
            return "你好" in result or "你好" in result
        except Exception as e:
            logger.error(f"大模型连接测试失败: {e}")
            return False
