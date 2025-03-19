from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class AgentConfig:
    """Agent配置数据模型"""
    name: str
    description: str
    color: str

@dataclass
class ApiConfig:
    """API配置数据模型"""
    deepseek_key: str
    deepseek_base_url: str
    model: str

@dataclass
class Config:
    """系统配置数据模型"""
    api: ApiConfig
    agents: List[AgentConfig]
    max_rounds: int
    mechanical_words: List[str]

@dataclass
class AgentResponse:
    """Agent回应数据模型"""
    agent_name: str
    agent_color: str
    content: str

@dataclass
class RoundResult:
    """对话轮次结果数据模型"""
    round: int
    responses: List[AgentResponse]

@dataclass
class ConversationHistory:
    """对话历史数据模型"""
    rounds: List[RoundResult] = field(default_factory=list)

@dataclass
class ReferenceDoc:
    """参考文档数据模型"""
    content: str
    style_analysis: str

@dataclass
class PolishingResult:
    """润色结果数据模型"""
    original_text: str
    final_text: str
    history: ConversationHistory
    reference_docs: ReferenceDoc

@dataclass
class ProcessResult:
    """处理结果通用数据模型"""
    success: bool
    message: str
    data: Optional[Any] = None 