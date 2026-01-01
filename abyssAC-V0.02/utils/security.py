# utils/security.py
#!/usr/bin/env python3
"""
安全模块
"""

import re
import hashlib
import secrets
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import jwt

class SecurityManager:
    """安全管理器"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or self._generate_secret_key()
        self.token_expiry_hours = 24
        self.sensitive_patterns = [
            r'password\s*[:=]', r'api[_-]?key\s*[:=]', r'secret\s*[:=]',
            r'token\s*[:=]', r'credential\s*[:=]', r'private[_-]?key\s*[:=]'
        ]
    
    def _generate_secret_key(self) -> str:
        """生成秘密密钥"""
        return secrets.token_urlsafe(32)
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return f"{salt}:{hash_obj.hex()}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            salt, stored_hash = hashed_password.split(':')
            hash_obj = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            return hash_obj.hex() == stored_hash
        except Exception:
            return False
    
    def generate_token(self, user_id: str, data: Dict = None) -> str:
        """生成JWT令牌"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow(),
        }
        
        if data:
            payload.update(data)
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def sanitize_input(self, text: str) -> str:
        """清理输入，防止注入攻击"""
        if not text:
            return text
        
        # 移除潜在的脚本标签
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除特殊字符
        text = re.sub(r'[<>"\']', '', text)
        
        # 限制长度
        if len(text) > 10000:
            text = text[:10000]
        
        return text.strip()
    
    def detect_sensitive_data(self, text: str) -> List[str]:
        """检测敏感数据"""
        detected = []
        
        for pattern in self.sensitive_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                detected.extend(matches)
        
        # 检查可能的API密钥格式
        api_key_patterns = [
            r'sk-[a-zA-Z0-9]{32,}',  # OpenAI格式
            r'[a-f0-9]{32,}',         # 十六进制格式
            r'[A-Za-z0-9+/]{40,}',    # Base64格式
        ]
        
        for pattern in api_key_patterns:
            matches = re.findall(pattern, text)
            if matches:
                detected.extend(matches)
        
        return list(set(detected))
    
    def mask_sensitive_data(self, text: str) -> str:
        """掩码敏感数据"""
        masked_text = text
        
        # 掩码API密钥
        api_key_patterns = [
            (r'sk-[a-zA-Z0-9]{32,}', r'sk-*******************************'),
            (r'[a-f0-9]{32,}', r'********************************'),
            (r'[A-Za-z0-9+/]{40,}', r'****************************************')
        ]
        
        for pattern, replacement in api_key_patterns:
            masked_text = re.sub(pattern, replacement, masked_text)
        
        return masked_text
    
    def validate_api_key(self, api_key: str, expected_prefix: str = None) -> bool:
        """验证API密钥格式"""
        if not api_key or len(api_key) < 20:
            return False
        
        if expected_prefix and not api_key.startswith(expected_prefix):
            return False
        
        # 基本格式检查
        if re.match(r'^[a-zA-Z0-9_-]+$', api_key):
            return True
        
        return False
    
    def encrypt_sensitive_config(self, config_data: Dict) -> Dict:
        """加密敏感配置"""
        encrypted_config = config_data.copy()
        
        sensitive_fields = ['api_key', 'password', 'secret', 'token']
        
        for field in sensitive_fields:
            if field in encrypted_config:
                value = encrypted_config[field]
                if value and isinstance(value, str):
                    # 简单加密（实际应用中应使用更安全的加密方式）
                    encrypted = self._simple_encrypt(value)
                    encrypted_config[field] = encrypted
        
        return encrypted_config
    
    def _simple_encrypt(self, text: str) -> str:
        """简单加密（仅用于演示，实际应用应使用更安全的加密）"""
        import base64
        encoded = base64.b64encode(text.encode()).decode()
        return f"encrypted:{encoded}"
    
    def _simple_decrypt(self, encrypted_text: str) -> Optional[str]:
        """简单解密"""
        if encrypted_text.startswith("encrypted:"):
            import base64
            try:
                encoded = encrypted_text.split(":", 1)[1]
                decoded = base64.b64decode(encoded).decode()
                return decoded
            except Exception:
                return None
        return encrypted_text

class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # user_id -> [timestamp1, timestamp2, ...]
    
    def check_rate_limit(self, user_id: str) -> Dict:
        """检查速率限制"""
        current_time = datetime.now().timestamp()
        
        # 清理过期的请求记录
        if user_id in self.requests:
            self.requests[user_id] = [
                t for t in self.requests[user_id]
                if current_time - t <= self.window_seconds
            ]
        
        # 获取当前请求记录
        user_requests = self.requests.get(user_id, [])
        
        # 检查是否超过限制
        if len(user_requests) >= self.max_requests:
            oldest_request = min(user_requests)
            reset_time = oldest_request + self.window_seconds
            wait_seconds = reset_time - current_time
            
            return {
                "allowed": False,
                "limit": self.max_requests,
                "remaining": 0,
                "reset_in_seconds": wait_seconds,
                "reset_time": datetime.fromtimestamp(reset_time).isoformat()
            }
        
        # 添加新请求
        user_requests.append(current_time)
        self.requests[user_id] = user_requests
        
        return {
            "allowed": True,
            "limit": self.max_requests,
            "remaining": self.max_requests - len(user_requests),
            "reset_in_seconds": self.window_seconds,
            "reset_time": datetime.fromtimestamp(current_time + self.window_seconds).isoformat()
        }

# 全局安全管理器实例
security_manager = SecurityManager()
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)