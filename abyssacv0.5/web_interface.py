#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渊协议 v5.0 - Web界面简化版
包含基本的聊天功能
"""

import json
from datetime import datetime
from typing import Dict, List, Any

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False

# Ollama相关导入
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from core import logger, config
import threading
from collections import deque


# =============================================================================
# Ollama客户端
# =============================================================================

class OllamaClient:
    """Ollama客户端 - 直接调用本地模型"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.get('modes.ollama.ollama_url', 'http://localhost:11434')
        self.models = []
        self.current_model = None
        self.chat_history = deque(maxlen=50)
        self.history_lock = threading.Lock()
        
        self.available = self._check_ollama_available()
        
        if self.available:
            self._load_models()
            logger.info(f"Ollama客户端初始化完成 | 模型数: {len(self.models)}")
        else:
            logger.warning("Ollama不可用")
    
    def _check_ollama_available(self) -> bool:
        if not REQUESTS_AVAILABLE:
            return False
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def _load_models(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                self.models = [model['name'] for model in data.get('models', [])]
                if self.models:
                    llama_models = [m for m in self.models if 'llama' in m.lower()]
                    if llama_models:
                        self.current_model = llama_models[0]
                    else:
                        self.current_model = self.models[0]
        except Exception as e:
            logger.error(f"加载模型列表失败: {e}")
    
    def generate(self, prompt: str, model: str = None, stream: bool = False, 
                 temperature: float = 0.7, max_tokens: int = 1000) -> str:
        if not self.available:
            return "Ollama服务不可用"
        
        model = model or self.current_model
        if not model:
            return "没有可用的模型"
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                return f"生成失败: HTTP {response.status_code}"
        
        except Exception as e:
            logger.error(f"Ollama生成失败: {e}")
            return f"生成失败: {str(e)}"
    
    def chat(self, message: str, system_prompt: str = None, model: str = None,
             temperature: float = 0.7) -> str:
        if not self.available:
            return "Ollama服务不可用"
        
        model = model or self.current_model
        if not model:
            return "没有可用的模型"
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            with self.history_lock:
                for hist_msg in self.chat_history:
                    messages.append(hist_msg)
            
            messages.append({"role": "user", "content": message})
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result.get('message', {}).get('content', '')
                
                with self.history_lock:
                    self.chat_history.append({"role": "user", "content": message})
                    self.chat_history.append({"role": "assistant", "content": assistant_message})
                
                return assistant_message
            else:
                return f"对话失败: HTTP {response.status_code}"
        
        except Exception as e:
            logger.error(f"Ollama对话失败: {e}")
            return f"对话失败: {str(e)}"
    
    def get_models(self) -> List[str]:
        return self.models.copy()
    
    def clear_history(self):
        with self.history_lock:
            self.chat_history.clear()


class SimpleWebInterface:
    """简化版Web界面"""
    
    def __init__(self, protocol_instance, host: str = "127.0.0.1", port: int = 5000):
        if not WEB_AVAILABLE:
            raise RuntimeError("Flask未安装")
        
        self.protocol = protocol_instance
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.app.secret_key = 'abyss-protocol-secret-key'
        
        CORS(self.app)
        self._register_routes()
        
        logger.info(f"简化Web界面初始化完成 | 地址: http://{host}:{port}")
    
    def _register_routes(self):
        """注册路由"""
        
        @self.app.route('/')
        def index():
            return self._render_simple_html()
        
        @self.app.route('/api/chat', methods=['POST'])
        def api_chat():
            """聊天API"""
            try:
                data = request.get_json()
                message = data.get('message', '')
                
                if not message:
                    return jsonify({'error': '消息不能为空'}), 400
                
                result = self.protocol.chat(message, use_ollama=True, include_context=True)
                return jsonify(result)
            
            except Exception as e:
                logger.error(f"聊天API失败: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/status')
        def api_status():
            """获取状态"""
            try:
                status = {
                    'protocol_stats': self.protocol.get_stats(),
                    'timestamp': datetime.now().isoformat(),
                }
                return jsonify(status)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _render_simple_html(self) -> str:
        """渲染简单HTML"""
        return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>渊协议 v5.0 - AI聊天系统</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #0d1117;
            color: #c9d1d9;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            color: #58a6ff;
            text-align: center;
        }
        .chat-container {
            background-color: #161b22;
            border-radius: 8px;
            border: 1px solid #30363d;
            padding: 20px;
            margin-top: 20px;
        }
        .chat-messages {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #30363d;
            border-radius: 4px;
            padding: 10px;
            margin-bottom: 20px;
        }
        .message {
            margin-bottom: 10px;
            padding: 8px;
            border-radius: 4px;
        }
        .message.user {
            background-color: #21262d;
            text-align: right;
        }
        .message.ai {
            background-color: #1f2937;
        }
        .input-container {
            display: flex;
            gap: 10px;
        }
        #message-input {
            flex: 1;
            padding: 10px;
            background-color: #21262d;
            border: 1px solid #30363d;
            border-radius: 4px;
            color: #c9d1d9;
        }
        #send-button {
            padding: 10px 20px;
            background-color: #58a6ff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        #send-button:hover {
            background-color: #4096d6;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>渊协议 v5.0 - AI聊天系统</h1>
        <div class="chat-container">
            <div class="chat-messages" id="chat-messages">
                <div class="message ai">
                    <strong>AI助手:</strong> 你好！我是基于渊协议认知系统的AI助手。我已经准备好与你进行深度对话，并将自动记录和整合我们的交流内容。
                </div>
            </div>
            <div class="input-container">
                <input type="text" id="message-input" placeholder="输入你的消息..." />
                <button id="send-button">发送</button>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('send-button').addEventListener('click', sendMessage);
        document.getElementById('message-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage(message, 'user');
            input.value = '';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    addMessage('错误: ' + data.error, 'ai');
                } else {
                    addMessage(data.ai_response, 'ai');
                }
            } catch (error) {
                addMessage('错误: ' + error.message, 'ai');
            }
        }
        
        function addMessage(content, type) {
            const messagesContainer = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + type;
            
            const prefix = type === 'user' ? '<strong>你:</strong> ' : '<strong>AI助手:</strong> ';
            messageDiv.innerHTML = prefix + content;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    </script>
</body>
</html>
        '''
    
    def run(self, debug: bool = False):
        """运行Web服务器"""
        try:
            self.app.run(host=self.host, port=self.port, debug=debug)
        except Exception as e:
            logger.error(f"Web服务器运行失败: {e}")
            raise
