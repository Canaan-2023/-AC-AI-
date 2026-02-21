"""
LLM Interface Module
LLM调用接口 - 支持本地模型API（如Ollama）
"""

import requests
import json
import time
from typing import Optional, Dict, Any, List, Generator
from dataclasses import dataclass

from config.system_config import get_config


@dataclass
class LLMResponse:
    """LLM响应数据结构"""
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    success: bool = True
    error: str = ""


class LLMInterface:
    """LLM接口类"""
    
    def __init__(self):
        self.config = get_config()
        self.api_base = self.config.llm.api_base
        self.model = self.config.llm.model_name
        self.temperature = self.config.llm.temperature
        self.max_tokens = self.config.llm.max_tokens
        self.timeout = self.config.llm.timeout
    
    def _get_api_url(self, endpoint: str) -> str:
        """获取完整API URL"""
        base = self.api_base.rstrip('/')
        return f"{base}/{endpoint}"
    
    def chat(self, messages: List[Dict[str, str]], 
             temperature: float = None,
             max_tokens: int = None,
             stream: bool = False) -> LLMResponse:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}, ...]
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
        
        Returns:
            LLMResponse对象
        """
        try:
            url = self._get_api_url("api/chat")
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": stream,
                "options": {
                    "temperature": temperature or self.temperature,
                    "num_predict": max_tokens or self.max_tokens
                }
            }
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                return self._handle_stream_response(response)
            else:
                return self._handle_normal_response(response)
                
        except requests.exceptions.RequestException as e:
            return LLMResponse(
                content="",
                model=self.model,
                success=False,
                error=f"请求失败: {str(e)}"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                success=False,
                error=f"未知错误: {str(e)}"
            )
    
    def _handle_normal_response(self, response: requests.Response) -> LLMResponse:
        """处理普通响应"""
        try:
            data = response.json()
            message = data.get("message", {})
            content = message.get("content", "")
            
            return LLMResponse(
                content=content,
                model=self.model,
                success=True
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                success=False,
                error=f"解析响应失败: {str(e)}"
            )
    
    def _handle_stream_response(self, response: requests.Response) -> LLMResponse:
        """处理流式响应"""
        content_parts = []
        
        try:
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        message = data.get("message", {})
                        content = message.get("content", "")
                        content_parts.append(content)
                        
                        # 检查是否完成
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
            
            return LLMResponse(
                content="".join(content_parts),
                model=self.model,
                success=True
            )
        except Exception as e:
            return LLMResponse(
                content="".join(content_parts),
                model=self.model,
                success=False,
                error=f"流式处理错误: {str(e)}"
            )
    
    def generate(self, prompt: str, 
                 system_prompt: str = None,
                 temperature: float = None,
                 max_tokens: int = None) -> LLMResponse:
        """
        生成文本（非聊天模式）
        
        Args:
            prompt: 提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数
        
        Returns:
            LLMResponse对象
        """
        try:
            url = self._get_api_url("api/generate")
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature or self.temperature,
                    "num_predict": max_tokens or self.max_tokens
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            content = data.get("response", "")
            
            return LLMResponse(
                content=content,
                model=self.model,
                success=True
            )
            
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                success=False,
                error=f"生成失败: {str(e)}"
            )
    
    def list_models(self) -> List[str]:
        """列出可用模型"""
        try:
            url = self._get_api_url("api/tags")
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            models = data.get("models", [])
            return [m.get("name", "") for m in models]
            
        except Exception as e:
            print(f"获取模型列表失败: {e}")
            return []
    
    def check_connection(self) -> bool:
        """检查LLM服务连接"""
        try:
            url = self._get_api_url("api/tags")
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def set_model(self, model_name: str):
        """设置当前模型"""
        self.model = model_name
        self.config.llm.model_name = model_name


class PromptBuilder:
    """提示词构建器"""
    
    @staticmethod
    def build_nng_nav_prompt(user_input: str, collected_nng: str) -> str:
        """构建NNG导航提示词"""
        return f"""你是AbyssAC系统的NNG导航模块。在NNG树中定位与用户问题相关的概念节点。

【输出格式】
nng/{{node_id}}.json
...
笔记：{{选择理由和下一步计划}}

【规则】
- 每行一个路径，nng/开头
- 可批量输出，并行读取
- 路径不存在会收到系统提示
- 无路径输出则进入第二层
- 禁止输出解释性文字

【输入】
用户问题：{user_input}
已收集NNG：{collected_nng}"""
    
    @staticmethod
    def build_memory_filter_prompt(user_input: str, nng_content: str, 
                                   collected_memories: str) -> str:
        """构建记忆筛选提示词"""
        return f"""你是AbyssAC系统的记忆筛选模块。基于NNG中的记忆摘要，选择需要读取的完整记忆文件。

【输出格式】
Y层记忆库/{{memory_type}}/{{value_level}}/{{year}}/{{month}}/{{day}}/{{memory_id}}.txt
...
笔记：{{选择理由和关联分析}}

【规则】
- 基于NNG中的"关联的记忆文件摘要"选择
- 优先高置信度、高价值、直接相关的记忆
- 注意记忆间的互补和冲突关系
- 无路径输出则进入第三层

【输入】
用户问题：{user_input}
NNG内容（含记忆摘要）：{nng_content}
已读取记忆：{collected_memories}"""
    
    @staticmethod
    def build_context_assembly_prompt(user_input: str, nng_content: str,
                                      memory_content: str) -> str:
        """构建上下文组装提示词"""
        return f"""你是AbyssAC系统的上下文组装模块。将分散的NNG节点和记忆片段整合为连贯、有逻辑结构的认知上下文。

【核心原则】
- 构建"思维路径"而非罗列信息
- 识别记忆间的逻辑关系（因果、对比、递进、冲突）
- 评估信息充分性，标记知识缺口
- 为最终回复LLM提供"思考框架"

【输出格式】
【问题解析】
- 核心意图：{{用户真正想问的是什么}}
- 关键概念：{{涉及的核心术语}}
- 隐含需求：{{用户没明说但需要的背景}}

【认知路径】（按逻辑顺序排列）
1. {{概念A}} → 2. {{概念B}} → 3. {{概念C}}
- 路径说明：{{为什么这样组织}}

【记忆整合】（按逻辑关系分组）
【核心组】直接回答问题的记忆：
- [{{memory_id}}] 置信度{{value}} {{关键内容摘要}}
作用：{{在回答中的角色}}
关联：{{与其他记忆的关系}}

【支撑组】提供背景/证据的记忆：
- [{{memory_id}}] 置信度{{value}} {{关键内容摘要}}
作用：{{补充说明什么}}

【对比组】不同视角/冲突观点：
- [{{memory_id}}] 置信度{{value}} {{关键内容摘要}}
冲突点：{{与哪条记忆矛盾，如何处理}}

【缺失信息】
- 已知但未获取：{{NNG中存在但未选中的相关节点}}
- 疑似存在：{{根据逻辑推断应该存在但未找到}}
- 需要澄清：{{用户问题中模糊的部分}}

【置信度评估】
- 整体置信度：{{高/中/低}}
- 依据：{{为什么这样评估}}
- 风险提示：{{哪些部分可能不准确}}

【回复策略建议】
- 推荐角度：{{从哪个切入点回答}}
- 重点强调：{{必须包含的关键点}}
- 谨慎处理：{{需要限定条件的部分}}
- 可扩展方向：{{如果用户追问，可以深入的方向}}

【输入】
用户问题：{user_input}
NNG导航结果：{nng_content}
记忆筛选结果：{memory_content}"""
    
    @staticmethod
    def build_user_response_prompt(user_input: str, context_package: str) -> str:
        """构建用户回复提示词"""
        return f"""你是AbyssAC系统的用户交互界面。基于用户问题和系统组装的上下文包，生成高质量回复。

【核心原则】
- 基于上下文包中的记忆和NNG信息回答
- 保持自然对话风格，但确保信息准确可追溯
- 不确定时说明"根据已有记忆..."而非编造
- 可主动建议深入探索方向

【输入】
用户问题：{user_input}
上下文包：{context_package}

【输出要求】
- 直接回答用户问题
- 可适当引用记忆来源（如"根据之前的讨论..."）
- 信息不足时诚实说明，并建议"需要我查找XX方面的信息吗？"
- 不暴露系统内部路径和机制"""


# 全局LLM接口实例
_llm_interface = None


def get_llm_interface() -> LLMInterface:
    """获取全局LLM接口"""
    global _llm_interface
    if _llm_interface is None:
        _llm_interface = LLMInterface()
    return _llm_interface
