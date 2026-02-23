"""工作记忆管理器模块"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class WorkingMemoryManager:
    """工作记忆管理器类"""
    
    def __init__(self, storage_dir: str = 'storage/working_memory'):
        """初始化工作记忆管理器
        
        Args:
            storage_dir: 存储目录
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        self.current_session: Dict[str, Any] = {}
        self.sandbox_contexts: Dict[str, Dict[str, Any]] = {}
    
    def start_session(self, user_input: str):
        """开始新会话
        
        Args:
            user_input: 用户输入
        """
        self.current_session = {
            'session_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'user_input': user_input,
            'start_time': datetime.now().isoformat(),
            'sandbox_contexts': {},
            'conversation_history': [],
            'errors': []
        }
    
    def record_sandbox_context(self, sandbox_type: str, context: Dict[str, Any]):
        """记录沙盒上下文
        
        Args:
            sandbox_type: 沙盒类型（nng_navigation/memory_filtering/context_assembly）
            context: 上下文内容
        """
        if not self.current_session:
            return
        
        self.current_session['sandbox_contexts'][sandbox_type] = {
            'timestamp': datetime.now().isoformat(),
            'context': context
        }
    
    def record_conversation(self, role: str, content: str):
        """记录对话
        
        Args:
            role: 角色（user/assistant）
            content: 内容
        """
        if not self.current_session:
            return
        
        self.current_session['conversation_history'].append({
            'timestamp': datetime.now().isoformat(),
            'role': role,
            'content': content
        })
    
    def record_error(self, error_type: str, error_message: str):
        """记录错误
        
        Args:
            error_type: 错误类型
            error_message: 错误信息
        """
        if not self.current_session:
            return
        
        self.current_session['errors'].append({
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': error_message
        })
    
    def end_session(self) -> Dict[str, Any]:
        """结束会话
        
        Returns:
            会话数据
        """
        if not self.current_session:
            return {}
        
        self.current_session['end_time'] = datetime.now().isoformat()
        
        session_data = self.current_session.copy()
        
        self._save_session(session_data)
        
        self.current_session = {}
        
        return session_data
    
    def _save_session(self, session_data: Dict[str, Any]):
        """保存会话数据"""
        try:
            session_id = session_data.get('session_id', 'unknown')
            filename = f"session_{session_id}.json"
            filepath = os.path.join(self.storage_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def get_session_for_dmn(self) -> Dict[str, Any]:
        """获取供DMN处理的会话数据
        
        Returns:
            会话数据（不包含DMN运行的三层沙盒上下文）
        """
        if not self.current_session:
            return {}
        
        return {
            'session_id': self.current_session.get('session_id'),
            'user_input': self.current_session.get('user_input'),
            'conversation_history': self.current_session.get('conversation_history', []),
            'errors': self.current_session.get('errors', [])
        }
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的会话
        
        Args:
            limit: 数量限制
            
        Returns:
            会话列表
        """
        sessions = []
        
        try:
            files = sorted(
                [f for f in os.listdir(self.storage_dir) if f.startswith('session_')],
                reverse=True
            )[:limit]
            
            for filename in files:
                filepath = os.path.join(self.storage_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    sessions.append(json.load(f))
        except Exception:
            pass
        
        return sessions
    
    def clear_old_sessions(self, days: int = 7):
        """清理旧会话
        
        Args:
            days: 保留天数
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        try:
            for filename in os.listdir(self.storage_dir):
                if not filename.startswith('session_'):
                    continue
                
                filepath = os.path.join(self.storage_dir, filename)
                if os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)
        except Exception:
            pass
