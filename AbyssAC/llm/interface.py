"""AbyssAC LLM接口模块

提供统一的LLM调用接口，支持多种LLM后端（Ollama、OpenAI等），
包含重试机制、格式验证和降级处理。
"""

import json
import re
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
import requests

from utils.logger import get_logger


logger = get_logger()


@dataclass
class LLMResponse:
    """LLM响应结构"""
    content: str
    raw_response: Any
    latency: float
    success: bool
    error: Optional[str] = None


class LLMInterface:
    """LLM接口管理器"""
    
    def __init__(
        self,
        api_type: str = "ollama",
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:latest",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 30,
        retry_count: int = 3
    ):
        """
        初始化LLM接口
        
        Args:
            api_type: API类型 (ollama, openai, etc.)
            base_url: API基础URL
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 超时时间（秒）
            retry_count: 重试次数
        """
        self.api_type = api_type.lower()
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.retry_count = retry_count
        
        # 性能统计
        self.total_calls = 0
        self.failed_calls = 0
        self.total_latency = 0.0
    
    def _call_ollama(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> LLMResponse:
        """
        调用Ollama API
        
        Args:
            messages: 消息列表
            stream: 是否流式输出
        
        Returns:
            LLM响应
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                # 流式处理
                content_parts = []
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if 'message' in data and 'content' in data['message']:
                                content_parts.append(data['message']['content'])
                        except:
                            pass
                content = ''.join(content_parts)
            else:
                data = response.json()
                content = data.get('message', {}).get('content', '')
            
            latency = time.time() - start_time
            
            return LLMResponse(
                content=content,
                raw_response=response,
                latency=latency,
                success=True
            )
        
        except requests.Timeout:
            return LLMResponse(
                content="",
                raw_response=None,
                latency=time.time() - start_time,
                success=False,
                error="请求超时"
            )
        
        except requests.RequestException as e:
            return LLMResponse(
                content="",
                raw_response=None,
                latency=time.time() - start_time,
                success=False,
                error=f"请求错误: {str(e)}"
            )
    
    def _call_openai(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> LLMResponse:
        """
        调用OpenAI兼容API
        
        Args:
            messages: 消息列表
            stream: 是否流式输出
        
        Returns:
            LLM响应
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
                stream=stream
            )
            response.raise_for_status()
            
            data = response.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            latency = time.time() - start_time
            
            return LLMResponse(
                content=content,
                raw_response=response,
                latency=latency,
                success=True
            )
        
        except requests.Timeout:
            return LLMResponse(
                content="",
                raw_response=None,
                latency=time.time() - start_time,
                success=False,
                error="请求超时"
            )
        
        except requests.RequestException as e:
            return LLMResponse(
                content="",
                raw_response=None,
                latency=time.time() - start_time,
                success=False,
                error=f"请求错误: {str(e)}"
            )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        validate_format: Optional[Callable[[str], bool]] = None
    ) -> LLMResponse:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表，格式 [{"role": "user/system/assistant", "content": "..."}]
            stream: 是否流式输出
            validate_format: 格式验证函数
        
        Returns:
            LLM响应
        """
        self.total_calls += 1
        
        for attempt in range(self.retry_count):
            logger.debug(f"LLM调用尝试 {attempt + 1}/{self.retry_count}")
            
            # 调用对应API
            if self.api_type == "ollama":
                response = self._call_ollama(messages, stream)
            elif self.api_type in ["openai", "vllm", "llamacpp"]:
                response = self._call_openai(messages, stream)
            else:
                return LLMResponse(
                    content="",
                    raw_response=None,
                    latency=0,
                    success=False,
                    error=f"不支持的API类型: {self.api_type}"
                )
            
            if response.success:
                self.total_latency += response.latency
                
                # 格式验证
                if validate_format and not validate_format(response.content):
                    logger.warning(f"格式验证失败，重试...")
                    if attempt < self.retry_count - 1:
                        time.sleep(0.5 * (attempt + 1))  # 递增延迟
                        continue
                    else:
                        logger.error("格式验证失败，已达到最大重试次数")
                        self.failed_calls += 1
                        return LLMResponse(
                            content=response.content,
                            raw_response=response.raw_response,
                            latency=response.latency,
                            success=False,
                            error="格式验证失败，已达到最大重试次数"
                        )
                
                return response
            
            else:
                logger.warning(f"LLM调用失败: {response.error}")
                if attempt < self.retry_count - 1:
                    time.sleep(0.5 * (attempt + 1))
        
        # 所有重试都失败
        self.failed_calls += 1
        return LLMResponse(
            content="",
            raw_response=None,
            latency=0,
            success=False,
            error="已达到最大重试次数"
        )
    
    def simple_chat(self, prompt: str, system_prompt: str = "") -> str:
        """
        简化版聊天接口
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
        
        Returns:
            AI回复内容
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.chat(messages)
        
        if response.success:
            return response.content
        else:
            logger.error(f"LLM调用失败: {response.error}")
            return f"[系统错误: {response.error}]"
    
    def extract_json(self, content: str) -> Optional[Dict]:
        """
        从LLM响应中提取JSON
        
        Args:
            content: LLM响应内容
        
        Returns:
            解析后的JSON，失败返回None
        """
        # 尝试直接解析
        try:
            return json.loads(content)
        except:
            pass
        
        # 尝试提取JSON代码块
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{.*\}',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue
        
        return None
    
    def validate_navigation_response(self, content: str) -> bool:
        """
        验证导航响应格式
        
        Args:
            content: LLM响应内容
        
        Returns:
            是否有效
        """
        # 允许的指令模式
        valid_patterns = [
            r'^GOTO\([\d.]+\)$',
            r'^STAY$',
            r'^BACK$',
            r'^ROOT$',
            r'^NNG[\d.]+(,")*STAY$',
            r'^记忆\d+(,")*STAY$',
        ]
        
        content = content.strip()
        
        for pattern in valid_patterns:
            if re.match(pattern, content):
                return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取调用统计
        
        Returns:
            统计信息
        """
        avg_latency = 0
        if self.total_calls > 0:
            avg_latency = round(self.total_latency / self.total_calls, 3)
        
        return {
            "total_calls": self.total_calls,
            "failed_calls": self.failed_calls,
            "success_rate": round(
                (self.total_calls - self.failed_calls) / max(self.total_calls, 1) * 100, 2
            ),
            "avg_latency": avg_latency,
            "api_type": self.api_type,
            "model": self.model
        }
