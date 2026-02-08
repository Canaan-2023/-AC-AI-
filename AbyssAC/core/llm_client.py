"""
LLM客户端 - 支持Ollama/LM Studio/API
"""
import json
import re
import requests
from typing import Dict, List, Optional, Generator
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """LLM响应封装"""
    content: str
    success: bool
    error: str = ""
    raw_response: Optional[Dict] = None


class LLMClient:
    """统一LLM客户端"""
    
    def __init__(self, config: Dict):
        self.provider = config.get("provider", "ollama")
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.model = config.get("model", "qwen2.5")
        self.api_key = config.get("api_key", "")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4096)
    
    def chat(self, messages: List[Dict], stream: bool = False, json_mode: bool = False) -> LLMResponse:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表 [{"role": "system/user/assistant", "content": "..."}]
            stream: 是否流式输出
            json_mode: 是否要求JSON格式输出
        
        Returns:
            LLMResponse对象
        """
        try:
            if self.provider == "ollama":
                return self._call_ollama(messages, stream, json_mode)
            elif self.provider == "lmstudio":
                return self._call_lmstudio(messages, stream, json_mode)
            elif self.provider == "openai":
                return self._call_openai(messages, stream, json_mode)
            else:
                return LLMResponse("", False, f"不支持的provider: {self.provider}")
        except Exception as e:
            return LLMResponse("", False, str(e))
    
    def _call_ollama(self, messages: List[Dict], stream: bool, json_mode: bool) -> LLMResponse:
        """调用Ollama"""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
            }
        }
        
        if json_mode:
            payload["format"] = "json"
        
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        if stream:
            return self._handle_stream(response)
        
        data = response.json()
        content = data.get("message", {}).get("content", "")
        return LLMResponse(content, True, raw_response=data)
    
    def _call_lmstudio(self, messages: List[Dict], stream: bool, json_mode: bool) -> LLMResponse:
        """调用LM Studio (OpenAI兼容格式)"""
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        if stream:
            return self._handle_stream(response)
        
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return LLMResponse(content, True, raw_response=data)
    
    def _call_openai(self, messages: List[Dict], stream: bool, json_mode: bool) -> LLMResponse:
        """调用OpenAI API"""
        url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        if stream:
            return self._handle_stream(response)
        
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return LLMResponse(content, True, raw_response=data)
    
    def _handle_stream(self, response) -> LLMResponse:
        """处理流式响应"""
        content_parts = []
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if self.provider == "ollama":
                        part = data.get("message", {}).get("content", "")
                    else:
                        part = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    content_parts.append(part)
                except:
                    pass
        return LLMResponse("".join(content_parts), True)
    
    def parse_json_response(self, content: str) -> Optional[Dict]:
        """
        安全解析JSON响应
        
        尝试多种方式提取JSON:
        1. 直接解析
        2. 从markdown代码块提取
        3. 从文本中提取第一个JSON对象
        """
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 尝试从markdown代码块提取
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    pass
        
        # 尝试从文本中提取第一个JSON对象
        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return None
    
    def test_connection(self) -> bool:
        """测试LLM连接"""
        messages = [{"role": "user", "content": "Hi"}]
        response = self.chat(messages)
        return response.success


# 全局LLM客户端实例
_llm_client: Optional[LLMClient] = None


def init_llm(config: Dict) -> LLMClient:
    """初始化LLM客户端"""
    global _llm_client
    _llm_client = LLMClient(config)
    return _llm_client


def get_llm() -> Optional[LLMClient]:
    """获取LLM客户端实例"""
    return _llm_client
