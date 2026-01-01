#!/usr/bin/env python3
"""
数据验证和校验模块
"""

import re
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import yaml

class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_config(config_data: Dict) -> List[str]:
        """验证配置数据的完整性"""
        errors = []
        
        # 必需字段检查
        required_sections = ['system', 'kernel', 'memory', 'ai']
        for section in required_sections:
            if section not in config_data:
                errors.append(f"缺少必需配置段: {section}")
        
        # 类型检查
        if 'kernel' in config_data:
            kernel = config_data['kernel']
            if not isinstance(kernel.get('top_k_nodes', 0), int):
                errors.append("kernel.top_k_nodes 必须是整数")
            if kernel.get('top_k_nodes', 0) <= 0:
                errors.append("kernel.top_k_nodes 必须大于0")
        
        if 'memory' in config_data:
            memory = config_data['memory']
            if not isinstance(memory.get('default_limit', 0), int):
                errors.append("memory.default_limit 必须是整数")
        
        return errors
    
    @staticmethod
    def validate_path(path_str: str, must_exist: bool = False) -> bool:
        """验证路径有效性"""
        try:
            path = Path(path_str)
            if must_exist and not path.exists():
                return False
            # 检查路径是否可写（父目录存在）
            parent = path.parent
            return parent.exists() and parent.is_dir()
        except Exception:
            return False

class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_memory_content(content: str, max_length: int = 10000) -> bool:
        """验证记忆内容"""
        if not content or not isinstance(content, str):
            return False
        if len(content.strip()) == 0:
            return False
        if len(content) > max_length:
            return False
        return True
    
    @staticmethod
    def validate_memory_id(memory_id: str) -> bool:
        """验证记忆ID格式"""
        pattern = r'^M[0-3]_\d{17}_[a-f0-9]{6}$'
        return bool(re.match(pattern, memory_id))
    
    @staticmethod
    def validate_layer(layer: int) -> bool:
        """验证记忆层级"""
        return layer in [0, 1, 2, 3]
    
    @staticmethod
    def validate_category(category: str, valid_categories: List[str]) -> bool:
        """验证分类"""
        return category in valid_categories
    
    @staticmethod
    def validate_tags(tags: List[str]) -> bool:
        """验证标签"""
        if not isinstance(tags, list):
            return False
        for tag in tags:
            if not isinstance(tag, str) or len(tag.strip()) == 0:
                return False
        return True

class JSONValidator:
    """JSON格式验证器"""
    
    @staticmethod
    def is_valid_json(text: str) -> bool:
        """检查是否为有效JSON"""
        try:
            json.loads(text)
            return True
        except json.JSONDecodeError:
            return False
    
    @staticmethod
    def validate_json_structure(json_data: Dict, schema: Dict) -> List[str]:
        """验证JSON结构"""
        errors = []
        
        def _validate(data, schema, path=""):
            if "type" in schema:
                expected_type = schema["type"]
                actual_type = type(data).__name__
                
                if expected_type == "dict" and not isinstance(data, dict):
                    errors.append(f"{path}: 应为字典，得到{actual_type}")
                elif expected_type == "list" and not isinstance(data, list):
                    errors.append(f"{path}: 应为列表，得到{actual_type}")
                elif expected_type == "str" and not isinstance(data, str):
                    errors.append(f"{path}: 应为字符串，得到{actual_type}")
                elif expected_type == "int" and not isinstance(data, int):
                    errors.append(f"{path}: 应为整数，得到{actual_type}")
                elif expected_type == "float" and not isinstance(data, (int, float)):
                    errors.append(f"{path}: 应为数字，得到{actual_type}")
                elif expected_type == "bool" and not isinstance(data, bool):
                    errors.append(f"{path}: 应为布尔值，得到{actual_type}")
            
            if "required" in schema and isinstance(data, dict):
                for field in schema["required"]:
                    if field not in data:
                        errors.append(f"{path}.{field}: 必需字段缺失")
            
            if "fields" in schema and isinstance(data, dict):
                for field_name, field_schema in schema["fields"].items():
                    if field_name in data:
                        new_path = f"{path}.{field_name}" if path else field_name
                        _validate(data[field_name], field_schema, new_path)
        
        _validate(json_data, schema, "")
        return errors
    
    @staticmethod
    def get_command_schema() -> Dict:
        """获取AI命令JSON的验证模式"""
        return {
            "type": "dict",
            "required": ["action"],
            "fields": {
                "action": {"type": "str"},
                "params": {
                    "type": "dict",
                    "required": [],
                    "fields": {}
                }
            }
        }

class FileValidator:
    """文件验证器"""
    
    @staticmethod
    def validate_file_size(file_path: str, max_size_mb: int = 10) -> bool:
        """验证文件大小"""
        try:
            size = Path(file_path).stat().st_size
            return size <= max_size_mb * 1024 * 1024
        except Exception:
            return False
    
    @staticmethod
    def validate_file_extension(file_path: str, allowed_extensions: List[str]) -> bool:
        """验证文件扩展名"""
        ext = Path(file_path).suffix.lower()
        return ext in allowed_extensions
    
    @staticmethod
    def validate_directory_structure(dir_path: str) -> List[str]:
        """验证目录结构完整性"""
        required_dirs = [
            "元认知记忆",
            "高阶整合记忆", 
            "分类记忆",
            "工作记忆",
            "系统日志",
            "AC100评估记录",
            "备份"
        ]
        
        missing = []
        for dir_name in required_dirs:
            if not (Path(dir_path) / dir_name).exists():
                missing.append(dir_name)
        
        return missing

class TextValidator:
    """文本验证器"""
    
    @staticmethod
    def contains_sensitive_content(text: str, sensitive_patterns: List[str] = None) -> bool:
        """检查是否包含敏感内容"""
        if sensitive_patterns is None:
            sensitive_patterns = []
        
        text_lower = text.lower()
        for pattern in sensitive_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        # 检查常见敏感词
        sensitive_words = [
            r'密码', r'密钥', r'api[_-]?key', r'secret', 
            r'token', r'credential', r'password', r'私密'
        ]
        
        for word in sensitive_words:
            if re.search(word, text, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def validate_text_length(text: str, min_length: int = 1, max_length: int = 10000) -> bool:
        """验证文本长度"""
        length = len(text.strip())
        return min_length <= length <= max_length
    
    @staticmethod
    def is_valid_chinese_text(text: str, min_ratio: float = 0.5) -> bool:
        """验证是否为有效中文文本"""
        if not text:
            return False
        
        # 计算中文字符比例
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text)
        
        if total_chars == 0:
            return False
        
        return chinese_chars / total_chars >= min_ratio

# 全局验证器实例
validator = DataValidator()
json_validator = JSONValidator()
config_validator = ConfigValidator()
file_validator = FileValidator()
text_validator = TextValidator()