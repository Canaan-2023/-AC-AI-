#!/usr/bin/env python3
"""
AI模型适配器模块
支持多种AI模型后端
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

import openai
from openai import OpenAI

from config.config_manager import config_manager

class BaseModelAdapter(ABC):
    """模型适配器基类"""
    
    def __init__(self, config):
        self.config = config
        self.name = self.__class__.__name__
        self.request_count = 0
        self.total_tokens = 0
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """对话"""
        pass
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "model": self.name,
            "request_count": self.request_count,
            "total_tokens": self.total_tokens
        }

class OpenAIModelAdapter(BaseModelAdapter):
    """OpenAI模型适配器"""
    
    def __init__(self, config):
        super().__init__(config)
        
        self.client = OpenAI(
            api_key=self.config.ai.openai_api_key,
            base_url=self.config.ai.openai_base_url
        )
        
        self.model = self.config.ai.openai_model
    
    def generate(self, prompt: str, **kwargs) -> str:
        self.request_count += 1
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self.config.ai.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.ai.max_tokens),
                timeout=kwargs.get("timeout", self.config.ai.timeout_seconds)
            )
            
            # 统计tokens
            usage = response.usage
            if usage:
                self.total_tokens += usage.total_tokens
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"❌ OpenAI请求失败: {e}")
            raise
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        self.request_count += 1
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.config.ai.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.ai.max_tokens)
            )
            
            usage = response.usage
            if usage:
                self.total_tokens += usage.total_tokens
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"❌ OpenAI对话失败: {e}")
            raise

class DeepSeekModelAdapter(BaseModelAdapter):
    """深度求索模型适配器"""
    
    def __init__(self, config):
        super().__init__(config)
        
        self.api_key = self.config.ai.deepseek_api_key
        self.base_url = self.config.ai.deepseek_base_url
        self.model = self.config.ai.deepseek_model
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, payload: Dict) -> Dict:
        """发送API请求"""
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=self.config.ai.timeout_seconds
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API错误: {response.status_code}, {response.text}")
        
        except requests.exceptions.Timeout:
            raise Exception("请求超时")
        
        except Exception as e:
            raise Exception(f"API请求失败: {e}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        self.request_count += 1
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.config.ai.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.ai.max_tokens)
        }
        
        result = self._make_request(payload)
        
        # 统计tokens
        if "usage" in result:
            usage = result["usage"]
            self.total_tokens += usage.get("total_tokens", 0)
        
        return result["choices"][0]["message"]["content"]
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        self.request_count += 1
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.ai.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.ai.max_tokens)
        }
        
        result = self._make_request(payload)
        
        if "usage" in result:
            usage = result["usage"]
            self.total_tokens += usage.get("total_tokens", 0)
        
        return result["choices"][0]["message"]["content"]

class OllamaModelAdapter(BaseModelAdapter):
    """Ollama本地模型适配器"""
    
    def __init__(self, config):
        super().__init__(config)
        
        self.base_url = self.config.ai.ollama_base_url
        self.model = self.config.ai.ollama_model
    
    def _make_request(self, endpoint: str, payload: Dict) -> Dict:
        """发送Ollama请求"""
        try:
            url = f"{self.base_url}/api/{endpoint}"
            
            response = requests.post(
                url,
                json=payload,
                timeout=60  # Ollama可能较慢
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Ollama错误: {response.status_code}")
        
        except Exception as e:
            raise Exception(f"Ollama请求失败: {e}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        self.request_count += 1
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.ai.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.ai.max_tokens)
            }
        }
        
        result = self._make_request("generate", payload)
        return result.get("response", "")
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        self.request_count += 1
        
        # 转换消息格式
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.ai.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.ai.max_tokens)
            }
        }
        
        result = self._make_request("chat", payload)
        return result.get("message", {}).get("content", "")

class LocalMockModelAdapter(BaseModelAdapter):
    """本地模拟模型适配器（用于测试）"""
    
    def generate(self, prompt: str, **kwargs) -> str:
        self.request_count += 1
        
        # 模拟AI响应
        responses = [
            '{"action": "store_memory", "params": {"content": "这是测试记忆", "layer": 2, "tags": ["测试"]}}',
            '{"action": "retrieve_memory", "params": {"query": "测试", "limit": 5}}',
            '{"action": "get_status"}',
            '{"action": "get_kernel_status"}'
        ]
        
        import random
        return random.choice(responses)
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        self.request_count += 1
        
        last_message = messages[-1]["content"] if messages else ""
        
        if "存储" in last_message:
            return "记忆已存储"
        elif "查找" in last_message:
            return "找到相关记忆"
        else:
            return "这是一个模拟响应"

class ModelFactory:
    """模型工厂"""
    
    @staticmethod
    def create_model(config) -> BaseModelAdapter:
        """创建模型适配器"""
        model_type = config.ai.model_type
        
        if model_type == "openai":
            return OpenAIModelAdapter(config)
        
        elif model_type == "deepseek":
            return DeepSeekModelAdapter(config)
        
        elif model_type == "ollama":
            return OllamaModelAdapter(config)
        
        elif model_type == "transformers":
            # 本地transformers模型需要额外安装
            try:
                from .local_transformers_adapter import LocalTransformersAdapter
                return LocalTransformersAdapter(config)
            except ImportError:
                print("⚠️  Transformers未安装，使用模拟模式")
                return LocalMockModelAdapter(config)
        
        else:
            # 默认使用模拟模式
            return LocalMockModelAdapter(config)