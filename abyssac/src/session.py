"""
AbyssAC 会话管理模块
处理多会话支持和状态管理
"""

import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from storage import StorageManager


@dataclass
class Session:
    """会话对象"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    history: List[Dict[str, str]] = field(default_factory=list)
    sandbox_state: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str):
        """添加消息到历史"""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.last_activity = datetime.now()
    
    def get_recent_history(self, count: int = 10) -> List[Dict[str, str]]:
        """获取最近的对话历史"""
        return self.history[-count:] if len(self.history) > count else self.history
    
    def is_expired(self, timeout_seconds: int = 3600) -> bool:
        """检查会话是否过期"""
        idle_time = datetime.now() - self.last_activity
        return idle_time > timedelta(seconds=timeout_seconds)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": len(self.history),
            "metadata": self.metadata
        }


class SessionManager:
    """会话管理器"""
    
    def __init__(self, timeout_seconds: int = 3600):
        self.sessions: Dict[str, Session] = {}
        self.lock = threading.Lock()
        self.timeout_seconds = timeout_seconds
    
    def create_session(self, session_id: Optional[str] = None) -> Session:
        """
        创建新会话
        
        Args:
            session_id: 可选的会话ID，不提供则自动生成
        
        Returns:
            新创建的会话
        """
        with self.lock:
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            session = Session(session_id=session_id)
            self.sessions[session_id] = session
            
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        获取会话
        
        Args:
            session_id: 会话ID
        
        Returns:
            会话对象，不存在则返回None
        """
        with self.lock:
            session = self.sessions.get(session_id)
            
            if session and session.is_expired(self.timeout_seconds):
                # 会话已过期，清理
                del self.sessions[session_id]
                return None
            
            return session
    
    def get_or_create_session(self, session_id: str) -> Session:
        """
        获取或创建会话
        
        Args:
            session_id: 会话ID
        
        Returns:
            会话对象
        """
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id)
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
        
        Returns:
            是否成功删除
        """
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        列出所有会话
        
        Returns:
            会话列表
        """
        with self.lock:
            # 清理过期会话
            expired = [
                sid for sid, s in self.sessions.items() 
                if s.is_expired(self.timeout_seconds)
            ]
            for sid in expired:
                del self.sessions[sid]
            
            return [s.to_dict() for s in self.sessions.values()]
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        添加消息到会话
        
        Args:
            session_id: 会话ID
            role: 角色（user/assistant/system）
            content: 消息内容
        
        Returns:
            是否成功添加
        """
        session = self.get_session(session_id)
        if session is None:
            return False
        
        session.add_message(role, content)
        
        # 同时保存为工作记忆
        self._save_working_memory(session_id, role, content)
        
        return True
    
    def _save_working_memory(self, session_id: str, role: str, content: str):
        """保存工作记忆"""
        memory_id = StorageManager.allocate_memory_id()
        
        memory_content = f"""【记忆层级】: 工作记忆
【记忆ID】: {memory_id}
【记忆时间】: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
【会话ID】: {session_id}
【置信度】: 50
【核心内容】:
角色: {role}
内容: {content}
"""
        
        StorageManager.write_memory(
            memory_id, 
            memory_content, 
            "工作记忆",
            None
        )
    
    def get_history(self, session_id: str, count: int = 10) -> List[Dict[str, str]]:
        """
        获取会话历史
        
        Args:
            session_id: 会话ID
            count: 返回消息数量
        
        Returns:
            消息列表
        """
        session = self.get_session(session_id)
        if session is None:
            return []
        
        return session.get_recent_history(count)
    
    def update_sandbox_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        """
        更新会话的沙盒状态
        
        Args:
            session_id: 会话ID
            state: 沙盒状态
        
        Returns:
            是否成功更新
        """
        session = self.get_session(session_id)
        if session is None:
            return False
        
        session.sandbox_state = state
        return True
    
    def get_sandbox_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话的沙盒状态
        
        Args:
            session_id: 会话ID
        
        Returns:
            沙盒状态
        """
        session = self.get_session(session_id)
        if session is None:
            return None
        
        return session.sandbox_state
    
    def get_stats(self) -> Dict[str, Any]:
        """获取会话统计"""
        with self.lock:
            return {
                "total_sessions": len(self.sessions),
                "active_sessions": len([
                    s for s in self.sessions.values() 
                    if not s.is_expired(self.timeout_seconds)
                ])
            }


# 全局会话管理器实例
session_manager = SessionManager()
