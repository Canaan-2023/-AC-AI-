"""LLM集成模块"""

import requests
import json
import time
from typing import Dict, Any, Optional, List

class LLMIntegration:
    """LLM集成类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化LLM集成"""
        self.config = config
        self.model_name = config.get('model_name', 'llama3')
        self.api_endpoint = config.get('api_endpoint', 'http://localhost:11434')
        self.max_tokens = config.get('max_tokens', 4096)
        self.temperature = config.get('temperature', 0.7)
        self.timeout = config.get('timeout', 60)
        self.retry_count = config.get('retry_count', 3)
        
        self._available_models = None
    
    def generate(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """生成文本"""
        if not prompt or not prompt.strip():
            return ''
        
        return self._generate_with_ollama(prompt)
    
    def _generate_with_ollama(self, prompt: str) -> str:
        """使用ollama生成文本"""
        retry = 0
        last_error = None
        
        while retry < self.retry_count:
            try:
                endpoint = f"{self.api_endpoint}/api/generate"
                
                data = {
                    'model': self.model_name,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'num_predict': self.max_tokens,
                        'temperature': self.temperature
                    }
                }
                
                response = requests.post(
                    endpoint,
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get('response', '')
                    if response_text:
                        return response_text.strip()
                else:
                    last_error = f"API返回错误: {response.status_code}"
                    
                    if response.status_code == 404:
                        return self._handle_model_not_found()
            
            except requests.exceptions.Timeout:
                last_error = "请求超时"
            except requests.exceptions.ConnectionError:
                last_error = "无法连接到Ollama服务，请确保Ollama正在运行"
            except Exception as e:
                last_error = f"未知错误: {str(e)}"
            
            retry += 1
            if retry < self.retry_count:
                time.sleep(1)
        
        return f"[LLM错误] {last_error}"
    
    def _handle_model_not_found(self) -> str:
        """处理模型未找到的情况"""
        models = self.list_models()
        if models:
            available = ', '.join(models)
            return f"[错误] 模型 '{self.model_name}' 未找到。可用模型: {available}\n请使用 'ollama pull {self.model_name}' 下载模型，或在config.json中修改model_name。"
        return f"[错误] 模型 '{self.model_name}' 未找到，且无法获取模型列表。请确保Ollama服务正在运行。"
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """聊天模式"""
        try:
            endpoint = f"{self.api_endpoint}/api/chat"
            
            data = {
                'model': self.model_name,
                'messages': messages,
                'stream': False
            }
            
            response = requests.post(
                endpoint,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', {})
                return message.get('content', '')
            
        except Exception as e:
            pass
        
        prompt = ""
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            if role == 'system':
                prompt += f"System: {content}\n\n"
            elif role == 'user':
                prompt += f"User: {content}\n\n"
            elif role == 'assistant':
                prompt += f"Assistant: {content}\n\n"
        
        prompt += "Assistant: "
        return self.generate(prompt)
    
    def embeddings(self, text: str) -> List[float]:
        """生成文本嵌入"""
        try:
            endpoint = f"{self.api_endpoint}/api/embeddings"
            
            data = {
                'model': self.model_name,
                'prompt': text
            }
            
            response = requests.post(
                endpoint,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('embedding', [])
        
        except Exception:
            pass
        
        return []
    
    def list_models(self) -> List[str]:
        """列出可用模型"""
        try:
            endpoint = f"{self.api_endpoint}/api/tags"
            
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                models = result.get('models', [])
                return [m.get('name', '') for m in models if m.get('name')]
        
        except Exception:
            pass
        
        return []
    
    def set_model(self, model_name: str):
        """设置模型"""
        self.model_name = model_name
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        try:
            endpoint = f"{self.api_endpoint}/api/tags"
            response = requests.get(endpoint, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        status = {
            'available': False,
            'endpoint': self.api_endpoint,
            'model': self.model_name,
            'models': []
        }
        
        try:
            status['available'] = self.is_available()
            if status['available']:
                status['models'] = self.list_models()
        except Exception:
            pass
        
        return status
