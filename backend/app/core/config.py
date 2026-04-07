from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "中医知识图谱问答系统"
    DEBUG: bool = True
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    BERT_MODEL_PATH: str = "./models/bert-base-chinese"
    ALBERT_MODEL_PATH: str = "./models/albert-base-chinese"
    DATA_DIR: str = "./data"
    LOG_DIR: str = "./logs"
    
    # 大模型配置
    DASHSCOPE_API_KEY: str = ""
    LLM_MODEL: str = "qwen-plus"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
