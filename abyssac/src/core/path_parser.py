"""路径解析器模块"""

import re
from typing import List, Dict, Optional

class PathParser:
    """路径解析器类"""
    
    def __init__(self):
        """初始化路径解析器"""
        self.nng_pattern = re.compile(r'nng/[0-9.]+\.json', re.IGNORECASE)
        self.memory_pattern = re.compile(r'Y层记忆库/[^ \t\n]+\.json', re.IGNORECASE)
    
    def parse_paths(self, text: str) -> List[str]:
        """解析文本中的文件路径"""
        if not text:
            return []
        
        paths = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            if line.startswith('笔记') or line.startswith('完成') or line.startswith('无'):
                continue
            
            if line.startswith('-') or line.startswith('*') or line.startswith('#'):
                continue
            
            if '：' in line and not line.startswith('nng') and not line.startswith('Y层记忆库'):
                continue
            
            extracted = self._extract_path(line)
            if extracted:
                paths.append(extracted)
        
        return paths
    
    def _extract_path(self, line: str) -> Optional[str]:
        """从一行文本中提取路径"""
        nng_match = self.nng_pattern.search(line)
        if nng_match:
            return nng_match.group(0)
        
        memory_match = self.memory_pattern.search(line)
        if memory_match:
            return memory_match.group(0)
        
        if line.startswith('nng/') and '.json' in line:
            path = line.split()[0]
            if path.endswith('.json'):
                return path
        
        if line.startswith('Y层记忆库/'):
            path = line.split()[0]
            if path.endswith('.json'):
                return path
        
        return None
    
    def _is_valid_path(self, path: str) -> bool:
        """验证路径是否有效"""
        if not path:
            return False
        
        if path.startswith('nng/') and path.endswith('.json'):
            return True
        
        if path.startswith('Y层记忆库/') and path.endswith('.json'):
            return True
        
        return False
    
    def get_path_type(self, path: str) -> Optional[str]:
        """获取路径类型"""
        if path.startswith('nng/'):
            return 'nng'
        if path.startswith('Y层记忆库/'):
            return 'memory'
        return None
    
    def extract_notes(self, text: str) -> str:
        """提取文本中的笔记"""
        if not text:
            return ''
        
        lines = text.strip().split('\n')
        notes = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('笔记：') or line.startswith('笔记:'):
                note_content = line[3:].strip() if '：' in line else line[3:].strip()
                if note_content:
                    notes.append(note_content)
        
        return ' '.join(notes)
    
    def split_paths_and_notes(self, text: str) -> Dict[str, any]:
        """分离路径和笔记"""
        paths = self.parse_paths(text)
        notes = self.extract_notes(text)
        
        return {
            'paths': paths,
            'notes': notes
        }
    
    def normalize_path(self, path: str) -> str:
        """标准化路径"""
        if not path:
            return ''
        
        path = path.replace('\\', '/')
        path = re.sub(r'/+', '/', path)
        
        if path.endswith('/'):
            path = path[:-1]
        
        return path
    
    def validate_path_structure(self, path: str) -> bool:
        """验证路径结构"""
        normalized_path = self.normalize_path(path)
        path_type = self.get_path_type(normalized_path)
        
        if not path_type:
            return False
        
        if path_type == 'nng':
            parts = normalized_path.split('/')
            if len(parts) < 2:
                return False
            if not parts[-1].endswith('.json'):
                return False
        
        elif path_type == 'memory':
            parts = normalized_path.split('/')
            if len(parts) < 2:
                return False
            if not parts[-1].endswith('.json'):
                return False
        
        return True
