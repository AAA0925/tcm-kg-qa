from typing import List
from loguru import logger
from app.models.qa import AnswerOutput
from app.services.qa.entity_extractor import EntityExtractor
from app.services.qa.kg_retriever import KGRetriever
from app.services.qa.llm_client import LLMClient
from app.services.qa.prompt_templates import SYSTEM_PROMPT

class QAEngine:
    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.kg_retriever = KGRetriever()
        self.llm_client = LLMClient()
        logger.info("问答引擎初始化完成")
    
    def answer_question(self, question: str, top_k: int = 5) -> AnswerOutput:
        """
        完整问答流程：实体提取 → 知识图谱检索 → 构建上下文 → 大模型生成
        
        Args:
            question: 用户问题
            top_k: 每个实体返回的关系数量
            
        Returns:
            AnswerOutput: 回答结果
        """
        try:
            logger.info(f"="*60)
            logger.info(f"开始处理问题: {question}")
            
            # 步骤1: 提取实体
            entities = self.entity_extractor.extract(question)
            logger.info(f"提取到实体: {entities}")
            
            # 步骤2: 检索知识图谱
            retrieve_results = self.kg_retriever.retrieve_by_entities(entities, top_k=top_k)
            logger.info(f"检索到 {len(retrieve_results)} 个实体的信息")
            
            # 步骤3: 格式化上下文
            context = self.kg_retriever.format_context(retrieve_results)
            logger.info(f"上下文长度: {len(context)} 字符")
            
            # 步骤4: 构建Prompt并调用大模型
            prompt = SYSTEM_PROMPT.format(context=context, question=question)
            messages = [
                {"role": "system", "content": "你是中医知识图谱智能问答助手。"},
                {"role": "user", "content": prompt}
            ]
            
            logger.info("调用大模型生成答案...")
            answer = self.llm_client.generate(messages, temperature=0.7)
            
            # 步骤5: 构建返回结果
            relations = []
            for result in retrieve_results:
                for rel in result.get("relations", []):
                    relations.append(rel["r"]["type"])
            
            result = AnswerOutput(
                answer=answer,
                confidence=0.85,
                entities=entities,
                relations=list(set(relations)),  # 去重
                evidence=f"基于 {len(retrieve_results)} 个实体的知识图谱信息"
            )
            
            logger.info(f"答案生成成功，长度: {len(answer)} 字符")
            logger.info(f"="*60)
            return result
            
        except Exception as e:
            logger.error(f"问答处理失败: {e}", exc_info=True)
            return AnswerOutput(
                answer=f"抱歉，处理问题时出错：{str(e)}",
                confidence=0.0,
                entities=[],
                relations=[],
                evidence=None
            )

qa_engine = QAEngine()
