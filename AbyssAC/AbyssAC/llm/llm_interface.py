"""
LLM接口层模块
支持Ollama本地模型和API调用
"""
import json
import time
import requests
from typing import Optional, List, Dict, Any, Generator
from dataclasses import dataclass
from enum import Enum


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    success: bool
    error: Optional[str] = None
    tokens_used: int = 0
    latency_ms: float = 0.0


class LLMProvider(Enum):
    """LLM提供商"""
    OLLAMA = "ollama"
    OPENAI_COMPATIBLE = "openai_compatible"


class LLMInterface:
    """LLM接口"""
    
    def __init__(self, 
                 use_local: bool = True,
                 ollama_base_url: str = "http://localhost:11434",
                 ollama_model: str = "qwen2.5:7b",
                 api_base_url: str = "",
                 api_key: str = "",
                 api_model: str = "",
                 temperature: float = 0.7,
                 max_tokens: int = 4096,
                 timeout: int = 60):
        """
        初始化LLM接口
        
        Args:
            use_local: 是否使用本地模型(Ollama)
            ollama_base_url: Ollama服务地址
            ollama_model: Ollama模型名称
            api_base_url: API基础URL
            api_key: API密钥
            api_model: API模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 超时时间(秒)
        """
        self.use_local = use_local
        self.ollama_base_url = ollama_base_url.rstrip('/')
        self.ollama_model = ollama_model
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.api_model = api_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # 检测可用的提供商
        self.provider = self._detect_provider()
        
    def _detect_provider(self) -> LLMProvider:
        """检测可用的LLM提供商"""
        if self.use_local:
            # 检测Ollama是否可用
            if self._check_ollama():
                print(f"[LLM] 使用Ollama: {self.ollama_model}")
                return LLMProvider.OLLAMA
            else:
                print("[LLM] Ollama不可用，尝试使用API")
                if self.api_base_url and self.api_key:
                    return LLMProvider.OPENAI_COMPATIBLE
        else:
            if self.api_base_url and self.api_key:
                return LLMProvider.OPENAI_COMPATIBLE
        
        # 默认返回Ollama，即使检测失败
        print("[LLM] 警告: 未检测到可用的LLM服务，将尝试Ollama")
        return LLMProvider.OLLAMA
    
    def _check_ollama(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            response = requests.get(
                f"{self.ollama_base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                models = [m.get('name', '') for m in data.get('models', [])]
                print(f"[LLM] Ollama可用，已安装模型: {models}")
                
                # 检查指定模型是否可用
                if self.ollama_model not in models:
                    # 尝试找到相似的模型
                    for m in models:
                        if self.ollama_model.split(':')[0] in m:
                            print(f"[LLM] 使用相似模型: {m}")
                            self.ollama_model = m
                            break
                return True
        except Exception as e:
            print(f"[LLM] Ollama检测失败: {e}")
        return False
    
    def chat(self, messages: List[Dict[str, str]], 
             system_prompt: Optional[str] = None,
             stream: bool = False) -> LLMResponse:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}, ...]
            system_prompt: 系统提示词
            stream: 是否流式输出
            
        Returns:
            LLMResponse
        """
        start_time = time.time()
        
        try:
            if self.provider == LLMProvider.OLLAMA:
                return self._chat_ollama(messages, system_prompt, stream)
            else:
                return self._chat_api(messages, system_prompt, stream)
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return LLMResponse(
                content="",
                success=False,
                error=str(e),
                latency_ms=latency
            )
    
    def _chat_ollama(self, messages: List[Dict[str, str]], 
                     system_prompt: Optional[str] = None,
                     stream: bool = False) -> LLMResponse:
        """使用Ollama进行聊天"""
        start_time = time.time()
        
        # 构建请求体
        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                # 流式输出处理
                content = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if 'message' in data and 'content' in data['message']:
                                content += data['message']['content']
                        except:
                            pass
            else:
                data = response.json()
                content = data.get('message', {}).get('content', '')
            
            latency = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=content,
                success=True,
                tokens_used=data.get('eval_count', 0) if not stream else 0,
                latency_ms=latency
            )
            
        except requests.exceptions.Timeout:
            latency = (time.time() - start_time) * 1000
            return LLMResponse(
                content="",
                success=False,
                error="请求超时",
                latency_ms=latency
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return LLMResponse(
                content="",
                success=False,
                error=f"Ollama请求失败: {str(e)}",
                latency_ms=latency
            )
    
    def _chat_api(self, messages: List[Dict[str, str]], 
                  system_prompt: Optional[str] = None,
                  stream: bool = False) -> LLMResponse:
        """使用API进行聊天（OpenAI兼容格式）"""
        start_time = time.time()
        
        # 添加系统提示词
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        payload = {
            "model": self.api_model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                content = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content += delta['content']
                            except:
                                pass
                
                latency = (time.time() - start_time) * 1000
                return LLMResponse(
                    content=content,
                    success=True,
                    latency_ms=latency
                )
            else:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                tokens = data.get('usage', {}).get('total_tokens', 0)
                
                latency = (time.time() - start_time) * 1000
                return LLMResponse(
                    content=content,
                    success=True,
                    tokens_used=tokens,
                    latency_ms=latency
                )
                
        except requests.exceptions.Timeout:
            latency = (time.time() - start_time) * 1000
            return LLMResponse(
                content="",
                success=False,
                error="API请求超时",
                latency_ms=latency
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return LLMResponse(
                content="",
                success=False,
                error=f"API请求失败: {str(e)}",
                latency_ms=latency
            )
    
    def simple_chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        简单聊天接口，只返回内容字符串
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            
        Returns:
            回复内容
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.chat(messages, system_prompt)
        
        if response.success:
            return response.content
        else:
            return f"[错误] {response.error}"
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        if self.provider == LLMProvider.OLLAMA:
            try:
                response = requests.get(
                    f"{self.ollama_base_url}/api/tags",
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    return [m.get('name', '') for m in data.get('models', [])]
            except:
                pass
        return []


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, max_history: int = 10):
        """
        初始化上下文管理器
        
        Args:
            max_history: 最大历史消息数
        """
        self.max_history = max_history
        self.history: List[Dict[str, str]] = []
    
    def add_message(self, role: str, content: str):
        """添加消息到历史"""
        self.history.append({"role": role, "content": content})
        
        # 保持历史记录在限制范围内
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_context(self, include_system: bool = True) -> List[Dict[str, str]]:
        """获取当前上下文"""
        return self.history.copy()
    
    def clear_context(self):
        """清空上下文"""
        self.history = []
    
    def get_recent_messages(self, n: int = 3) -> List[Dict[str, str]]:
        """获取最近的n条消息"""
        return self.history[-n:] if len(self.history) >= n else self.history.copy()


if __name__ == "__main__":
    # 自测
    print("=" * 60)
    print("LLMInterface模块自测")
    print("=" * 60)
    
    # 初始化LLM接口
    llm = LLMInterface(
        use_local=True,
        ollama_model="qwen2.5:7b",
        temperature=0.7
    )
    
    print(f"\n[✓] LLM接口初始化成功")
    print(f"  - 提供商: {llm.provider.value}")
    print(f"  - 模型: {llm.ollama_model if llm.provider == LLMProvider.OLLAMA else llm.api_model}")
    
    # 获取可用模型
    models = llm.get_available_models()
    print(f"\n[✓] 可用模型: {models}")
    
    # 测试简单聊天（如果Ollama可用）
    if llm.provider == LLMProvider.OLLAMA:
        print("\n测试聊天功能...")
        response = llm.simple_chat("你好，请用一句话介绍自己", 
                                   system_prompt="你是一个有帮助的AI助手")
        print(f"[✓] 回复: {response[:100]}...")
        
        # 测试上下文管理器
        print("\n测试上下文管理器...")
        ctx = ContextManager(max_history=5)
        ctx.add_message("user", "你好")
        ctx.add_message("assistant", "你好！有什么可以帮助你的？")
        ctx.add_message("user", "Python是什么？")
        
        context = ctx.get_context()
        print(f"[✓] 上下文消息数: {len(context)}")
        
        recent = ctx.get_recent_messages(2)
        print(f"[✓] 最近2条消息: {recent}")
    else:
        print("\n[!] Ollama不可用，跳过聊天测试")
    
    print("\n" + "=" * 60)
    print("LLMInterface模块自测完成")
    print("=" * 60)
