#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API控制器 - RESTful API接口

提供完整的RESTful API接口，支持所有核心功能。
"""

import json
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.parse

from ..core.config_manager import config
from ..core.logger import AbyssLogger
from ..core.memory_monitor import memory_monitor
from ..core.event_system import event_system, SystemEvents
# from ..models.abyss_kernel import AbyssKernel  # 避免循环导入


class APIRequest:
    """API请求对象"""
    
    def __init__(self, method: str, path: str, headers: Dict[str, str], 
                 query_params: Dict[str, List[str]], body: bytes = b''):
        self.method = method
        self.path = path
        self.headers = headers
        self.query_params = query_params
        self.body = body
        self.timestamp = time.time()


class APIResponse:
    """API响应对象"""
    
    def __init__(self, status_code: int = 200, headers: Optional[Dict[str, str]] = None, 
                 body: Optional[bytes] = None):
        self.status_code = status_code
        self.headers = headers or {}
        self.body = body or b''
        
        # 默认响应头
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'application/json'
        if 'Access-Control-Allow-Origin' not in self.headers:
            self.headers['Access-Control-Allow-Origin'] = '*'


class RateLimiter:
    """API限流器"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, client_ip: str) -> bool:
        """检查是否允许请求"""
        with self.lock:
            now = time.time()
            minute_ago = now - 60
            
            # 清理旧请求
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > minute_ago
            ]
            
            # 检查限制
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                return False
            
            # 记录请求
            self.requests[client_ip].append(now)
            return True


class APIHandler(BaseHTTPRequestHandler):
    """API请求处理器"""
    
    def __init__(self, *args, api_controller=None, **kwargs):
        self.api_controller = api_controller
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        self._handle_request('GET')
    
    def do_POST(self):
        """处理POST请求"""
        self._handle_request('POST')
    
    def do_PUT(self):
        """处理PUT请求"""
        self._handle_request('PUT')
    
    def do_DELETE(self):
        """处理DELETE请求"""
        self._handle_request('DELETE')
    
    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def _handle_request(self, method: str):
        """处理请求"""
        try:
            # 解析请求
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b''
            
            # 创建请求对象
            request = APIRequest(
                method=method,
                path=path,
                headers=dict(self.headers),
                query_params=query_params,
                body=body
            )
            
            # 检查限流
            if self.api_controller.rate_limiter:
                client_ip = self.client_address[0]
                if not self.api_controller.rate_limiter.is_allowed(client_ip):
                    self._send_error(429, "Too Many Requests")
                    return
            
            # 处理请求
            response = self.api_controller.handle_request(request)
            
            # 发送响应
            self.send_response(response.status_code)
            for header, value in response.headers.items():
                self.send_header(header, value)
            self.end_headers()
            self.wfile.write(response.body)
            
        except Exception as e:
            self._send_error(500, f"Internal Server Error: {str(e)}")
    
    def _send_error(self, status_code: int, message: str):
        """发送错误响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        error_response = {
            'error': message,
            'status_code': status_code
        }
        self.wfile.write(json.dumps(error_response).encode())
    
    def log_message(self, format, *args):
        """重写日志方法，使用自定义日志"""
        pass  # 使用APIController的日志记录


class APIController:
    """
    API控制器 - 统一管理所有API接口
    
    提供以下功能：
    - 文本处理
    - 记忆管理
    - 字典管理
    - 系统状态查询
    - 健康检查
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.logger = AbyssLogger("APIController")
        
        # 限流器
        rate_limit_config = config.get('api.rate_limit', {})
        if rate_limit_config.get('enabled', True):
            self.rate_limiter = RateLimiter(rate_limit_config.get('requests_per_minute', 60))
        else:
            self.rate_limiter = None
        
        # 注册路由
        self.routes = self._register_routes()
        
        # 启动状态
        self.start_time = time.time()
        self.request_count = 0
        self._request_lock = threading.Lock()
        
        self.logger.info("API控制器初始化完成")
    
    def _register_routes(self) -> Dict[str, Dict[str, Callable]]:
        """注册API路由"""
        return {
            '/api/process': {
                'POST': self._handle_process
            },
            '/api/memory': {
                'GET': self._handle_get_memories,
                'POST': self._handle_create_memory
            },
            '/api/memory/search': {
                'GET': self._handle_search_memories
            },
            '/api/dictionary': {
                'GET': self._handle_get_dictionaries,
                'POST': self._handle_add_word
            },
            '/api/dictionary/search': {
                'GET': self._handle_search_words
            },
            '/api/stats': {
                'GET': self._handle_get_stats
            },
            '/api/health': {
                'GET': self._handle_health_check
            },
            '/api/fission': {
                'POST': self._handle_trigger_fission
            },
            '/api/fuse': {
                'POST': self._handle_fuse_memories
            },
            '/api/system': {
                'GET': self._handle_system_info
            }
        }
    
    def handle_request(self, request: APIRequest) -> APIResponse:
        """处理API请求"""
        start_time = time.time()
        
        # 更新请求计数
        with self._request_lock:
            self.request_count += 1
        
        # 记录请求
        self.logger.info(f"API请求: {request.method} {request.path}", extra={
            'client_ip': 'unknown',  # 需要从handler获取
            'method': request.method,
            'path': request.path
        })
        
        # 触发事件
        event_system.emit(SystemEvents.API_REQUEST, {
            'method': request.method,
            'path': request.path,
            'timestamp': request.timestamp
        })
        
        # 查找路由
        route_key = request.path
        if route_key not in self.routes or request.method not in self.routes[route_key]:
            return self._not_found_response()
        
        # 执行处理器
        handler = self.routes[route_key][request.method]
        
        try:
            response = handler(request)
            
            # 记录响应
            duration = time.time() - start_time
            self.logger.info(f"API响应: {request.method} {request.path} - {response.status_code} ({duration:.3f}s)")
            
            # 触发事件
            event_system.emit(SystemEvents.API_RESPONSE, {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration': duration
            })
            
            return response
            
        except Exception as e:
            self.logger.error(f"API处理失败: {request.method} {request.path} - {str(e)}")
            return self._error_response(500, str(e))
    
    def _handle_process(self, request: APIRequest) -> APIResponse:
        """处理文本"""
        try:
            data = json.loads(request.body.decode())
            text = data.get('text', '')
            return_metadata = data.get('return_metadata', False)
            
            if not text:
                return self._error_response(400, "Missing 'text' field")
            
            result = self.kernel.process(text, return_metadata=return_metadata)
            
            return self._json_response(result)
            
        except json.JSONDecodeError:
            return self._error_response(400, "Invalid JSON")
        except Exception as e:
            return self._error_response(500, str(e))
    
    def _handle_get_memories(self, request: APIRequest) -> APIResponse:
        """获取记忆列表"""
        layer = request.query_params.get('layer', [None])[0]
        category = request.query_params.get('category', [None])[0]
        limit = int(request.query_params.get('limit', ['100'])[0])
        
        memories = self.kernel.memory.retrieve_memory(
            query="", layer=layer, category=category, limit=limit
        )
        
        result = {
            'memories': [
                {
                    'id': mem.id,
                    'content': mem.content[:100],  # 截断内容
                    'layer': mem.layer.name,
                    'category': mem.category,
                    'timestamp': mem.timestamp,
                    'importance_score': mem.importance_score
                }
                for mem in memories
            ],
            'total': len(memories)
        }
        
        return self._json_response(result)
    
    def _handle_create_memory(self, request: APIRequest) -> APIResponse:
        """创建记忆"""
        try:
            data = json.loads(request.body.decode())
            content = data.get('content', '')
            layer = data.get('layer', 'CATEGORICAL')
            category = data.get('category', '未分类')
            metadata = data.get('metadata', {})
            
            if not content:
                return self._error_response(400, "Missing 'content' field")
            
            # 转换层枚举
            from ..models.memory_system import MemoryLayer
            layer_enum = getattr(MemoryLayer, layer, MemoryLayer.CATEGORICAL)
            
            memory_id = self.kernel.memory.create_memory(
                content, layer=layer_enum, category=category, metadata=metadata
            )
            
            return self._json_response({'memory_id': memory_id})
            
        except json.JSONDecodeError:
            return self._error_response(400, "Invalid JSON")
        except Exception as e:
            return self._error_response(500, str(e))
    
    def _handle_search_memories(self, request: APIRequest) -> APIResponse:
        """搜索记忆"""
        query = request.query_params.get('query', [''])[0]
        layer = request.query_params.get('layer', [None])[0]
        category = request.query_params.get('category', [None])[0]
        limit = int(request.query_params.get('limit', ['10'])[0])
        
        if not query:
            return self._error_response(400, "Missing 'query' parameter")
        
        # 转换层枚举
        from ..models.memory_system import MemoryLayer
        layer_enum = None
        if layer:
            layer_enum = getattr(MemoryLayer, layer, None)
        
        memories = self.kernel.memory.retrieve_memory(
            query=query, layer=layer_enum, category=category, limit=limit
        )
        
        result = {
            'query': query,
            'results': [
                {
                    'id': mem.id,
                    'content': mem.content[:200],  # 截断内容
                    'layer': mem.layer.name,
                    'category': mem.category,
                    'timestamp': mem.timestamp,
                    'importance_score': mem.importance_score,
                    'activation_count': mem.activation_count
                }
                for mem in memories
            ],
            'total': len(memories)
        }
        
        return self._json_response(result)
    
    def _handle_get_dictionaries(self, request: APIRequest) -> APIResponse:
        """获取字典列表"""
        stats = self.kernel.dict_manager.get_stats()
        return self._json_response(stats)
    
    def _handle_add_word(self, request: APIRequest) -> APIResponse:
        """添加词到字典"""
        try:
            data = json.loads(request.body.decode())
            word = data.get('word', '')
            
            if not word:
                return self._error_response(400, "Missing 'word' field")
            
            dict_id = self.kernel.dict_manager.add_word(word)
            
            return self._json_response({
                'word': word,
                'dictionary_id': dict_id
            })
            
        except json.JSONDecodeError:
            return self._error_response(400, "Invalid JSON")
        except Exception as e:
            return self._error_response(500, str(e))
    
    def _handle_search_words(self, request: APIRequest) -> APIResponse:
        """搜索词"""
        prefix = request.query_params.get('prefix', [''])[0]
        limit = int(request.query_params.get('limit', ['10'])[0])
        
        if not prefix:
            return self._error_response(400, "Missing 'prefix' parameter")
        
        words = self.kernel.dict_manager.search_words(prefix, limit)
        
        return self._json_response({
            'prefix': prefix,
            'words': words,
            'count': len(words)
        })
    
    def _handle_get_stats(self, request: APIRequest) -> APIResponse:
        """获取系统统计"""
        stats = {
            'kernel': self.kernel.get_stats(),
            'memory': self.kernel.memory.get_stats() if self.kernel.memory else {},
            'dictionary': self.kernel.dict_manager.get_stats() if self.kernel.dict_manager else {},
            'api': {
                'uptime': time.time() - self.start_time,
                'request_count': self.request_count,
                'memory_usage': memory_monitor.get_current_memory_usage()
            }
        }
        
        return self._json_response(stats)
    
    def _handle_health_check(self, request: APIRequest) -> APIResponse:
        """健康检查"""
        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'uptime': time.time() - self.start_time,
            'memory_usage': memory_monitor.get_current_memory_usage(),
            'request_count': self.request_count,
            'components': {
                'kernel': self.kernel is not None,
                'dictionary': self.kernel.dict_manager is not None,
                'memory': self.kernel.memory is not None
            }
        }
        
        return self._json_response(health_status)
    
    def _handle_trigger_fission(self, request: APIRequest) -> APIResponse:
        """触发裂变"""
        try:
            result = self.kernel.dict_manager.check_and_perform_fission()
            return self._json_response({
                'fission_performed': result
            })
        except Exception as e:
            return self._error_response(500, str(e))
    
    def _handle_fuse_memories(self, request: APIRequest) -> APIResponse:
        """融合记忆"""
        try:
            data = json.loads(request.body.decode())
            category = data.get('category', '未分类')
            
            fused_ids = self.kernel.memory.fuse_related_memories(category)
            
            return self._json_response({
                'fused_memories': fused_ids,
                'count': len(fused_ids)
            })
            
        except json.JSONDecodeError:
            return self._error_response(400, "Invalid JSON")
        except Exception as e:
            return self._error_response(500, str(e))
    
    def _handle_system_info(self, request: APIRequest) -> APIResponse:
        """获取系统信息"""
        info = {
            'name': 'AbyssMCP',
            'version': '4.0.0',
            'description': '渊协议 MCP 插件系统',
            'features': [
                'Model-Controller-Plugin架构',
                '反向索引增强',
                '无外部依赖',
                'RESTful API',
                '插件系统',
                '内存监控'
            ],
            'endpoints': list(self.routes.keys())
        }
        
        return self._json_response(info)
    
    def _json_response(self, data: Any, status_code: int = 200) -> APIResponse:
        """创建JSON响应"""
        body = json.dumps(data, ensure_ascii=False, indent=2).encode()
        
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
        
        return APIResponse(status_code=status_code, headers=headers, body=body)
    
    def _error_response(self, status_code: int, message: str) -> APIResponse:
        """创建错误响应"""
        error_data = {
            'error': message,
            'status_code': status_code
        }
        return self._json_response(error_data, status_code)
    
    def _not_found_response(self) -> APIResponse:
        """创建404响应"""
        return self._error_response(404, "Not Found")
    
    def start_server(self, host: str = None, port: int = None):
        """启动API服务器"""
        host = host or config.get('api.host', '127.0.0.1')
        port = port or config.get('api.port', 8080)
        
        # 创建处理器工厂
        def handler_factory(*args, **kwargs):
            return APIHandler(*args, api_controller=self, **kwargs)
        
        # 启动服务器
        self.server = HTTPServer((host, port), handler_factory)
        
        self.logger.info(f"API服务器启动: http://{host}:{port}")
        
        # 在单独线程中运行服务器
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
    
    def stop_server(self):
        """停止API服务器"""
        if hasattr(self, 'server'):
            self.server.shutdown()
            self.server.server_close()
            self.logger.info("API服务器已停止")
    
    def make_request(self, method: str, path: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """内部API请求（用于测试）"""
        url = f"http://127.0.0.1:{config.get('api.port', 8080)}{path}"
        
        if data:
            json_data = json.dumps(data).encode()
            req = urllib.request.Request(url, data=json_data, method=method)
            req.add_header('Content-Type', 'application/json')
        else:
            req = urllib.request.Request(url, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                response_data = response.read().decode()
                return json.loads(response_data)
        except Exception as e:
            return {'error': str(e)}