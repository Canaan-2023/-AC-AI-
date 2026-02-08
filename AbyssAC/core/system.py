"""
AbyssAC 系统主控制器
"""
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config, LLM_CONFIG
from core.llm_client import init_llm, get_llm, LLMClient
from core.memory_manager import init_memory_manager, get_memory_manager, MemoryManager, MemoryType
from core.nng_manager import init_nng_manager, get_nng_manager, NNGManager
from core.sandbox import XLayerSandbox, SandboxResult
from core.dmn import DMNController, DMNTaskType


@dataclass
class ChatResponse:
    """聊天响应"""
    content: str
    used_memories: List[Dict]
    sandbox_logs: str
    dmn_triggered: bool
    dmn_logs: str


class AbyssACSystem:
    """AbyssAC系统主控制器"""
    
    def __init__(self):
        self.config = load_config()
        self.llm: Optional[LLMClient] = None
        self.memory: Optional[MemoryManager] = None
        self.nng: Optional[NNGManager] = None
        self.sandbox: Optional[XLayerSandbox] = None
        self.dmn: Optional[DMNController] = None
        
        self.last_activity_time = time.time()
        self.is_initialized = False
    
    def initialize(self, llm_config: Optional[Dict] = None) -> bool:
        """
        初始化系统
        
        Args:
            llm_config: 可选的LLM配置，覆盖默认配置
        """
        try:
            config = self.config
            
            # 使用自定义LLM配置
            if llm_config:
                config["llm"].update(llm_config)
            
            # 初始化各模块
            self.llm = init_llm(config["llm"])
            self.memory = init_memory_manager(config)
            self.nng = init_nng_manager(config)
            
            # 初始化沙盒和DMN
            self.sandbox = XLayerSandbox(self.llm, self.nng, self.memory)
            self.dmn = DMNController(self.llm, self.memory, self.nng)
            
            self.is_initialized = True
            print("✅ AbyssAC系统初始化完成")
            return True
        except Exception as e:
            print(f"❌ 系统初始化失败: {e}")
            return False
    
    def test_llm_connection(self) -> bool:
        """测试LLM连接"""
        if not self.llm:
            return False
        return self.llm.test_connection()
    
    def chat(self, user_input: str, enable_sandbox: bool = True) -> ChatResponse:
        """
        处理用户输入并生成回复
        
        Args:
            user_input: 用户输入
            enable_sandbox: 是否启用三层沙盒
        
        Returns:
            ChatResponse对象
        """
        if not self.is_initialized:
            return ChatResponse(
                content="系统未初始化，请先调用initialize()",
                used_memories=[],
                sandbox_logs="",
                dmn_triggered=False,
                dmn_logs=""
            )
        
        self.last_activity_time = time.time()
        
        # 保存用户输入到工作记忆
        user_mem = self.memory.save_memory(
            f"用户: {user_input}",
            MemoryType.WORKING
        )
        
        # 获取当前工作记忆
        working_memories = [
            {"memory_id": m.memory_id, "content": m.content, "timestamp": m.timestamp}
            for m in self.memory.get_working_memories(limit=20)
        ]
        
        sandbox_logs = []
        selected_memories = []
        context = user_input
        
        # === 阶段1: Bootstrap - NNG为空时跳过沙盒 ===
        if self.nng.is_empty():
            sandbox_logs.append("=== Bootstrap阶段: NNG为空，跳过三层沙盒 ===")
            context = user_input
        elif enable_sandbox:
            # === X层三层沙盒 ===
            result = self.sandbox.execute(user_input, working_memories)
            sandbox_logs.append("\n".join(result.logs))
            context = result.context
            selected_memories = result.selected_memories
        
        # === 生成回复 ===
        messages = self._build_chat_messages(context, working_memories)
        response = self.llm.chat(messages)
        
        if not response.success:
            return ChatResponse(
                content=f"生成回复失败: {response.error}",
                used_memories=selected_memories,
                sandbox_logs="\n".join(sandbox_logs),
                dmn_triggered=False,
                dmn_logs=""
            )
        
        reply = response.content
        
        # 保存AI回复到工作记忆
        self.memory.save_memory(
            f"AI: {reply}",
            MemoryType.WORKING
        )
        
        # === 检查DMN触发 ===
        dmn_triggered = False
        dmn_logs = ""
        
        working_count = self.memory.count_working_memories()
        nav_failures = self.sandbox.get_navigation_failure_count() if self.sandbox else 0
        idle_time = time.time() - self.last_activity_time
        
        should_trigger, task_type = self.dmn.should_trigger(
            working_count, nav_failures, int(idle_time)
        )
        
        if should_trigger and task_type:
            dmn_triggered = True
            success, logs = self.dmn.execute(working_memories, task_type)
            dmn_logs = logs
            
            # 重置导航失败计数
            if self.sandbox:
                self.sandbox.reset_navigation_failures()
        
        return ChatResponse(
            content=reply,
            used_memories=selected_memories,
            sandbox_logs="\n".join(sandbox_logs),
            dmn_triggered=dmn_triggered,
            dmn_logs=dmn_logs
        )
    
    def _build_chat_messages(self, context: str, working_memories: List[Dict]) -> List[Dict]:
        """构建聊天消息列表"""
        # 构建系统提示
        system_prompt = """你是AbyssAC系统的AI助手，一个基于NNG导航和Y层记忆的智能系统。

你的特点:
1. 能够理解并利用长期记忆来提供个性化回复
2. 会参考相关的历史对话和知识
3. 回复简洁、准确、有帮助

当前上下文已整合了相关记忆信息，请基于此生成回复。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # 添加上下文
        messages.append({"role": "user", "content": f"【整合后的上下文】\n{context}\n\n请基于以上信息回复:"})
        
        return messages
    
    def manual_dmn(self, task_type: str = "记忆整合") -> Tuple[bool, str]:
        """
        手动触发DMN
        
        Args:
            task_type: 任务类型 (记忆整合/关联发现/偏差审查/策略预演/概念重组)
        """
        if not self.is_initialized:
            return False, "系统未初始化"
        
        task_map = {
            "记忆整合": DMNTaskType.MEMORY_INTEGRATION,
            "关联发现": DMNTaskType.ASSOCIATION_DISCOVERY,
            "偏差审查": DMNTaskType.BIAS_REVIEW,
            "策略预演": DMNTaskType.STRATEGY_REHEARSAL,
            "概念重组": DMNTaskType.CONCEPT_RECOMBINATION
        }
        
        task = task_map.get(task_type, DMNTaskType.MEMORY_INTEGRATION)
        
        working_memories = [
            {"memory_id": m.memory_id, "content": m.content, "timestamp": m.timestamp}
            for m in self.memory.get_working_memories(limit=20)
        ]
        
        success, logs = self.dmn.execute(working_memories, task)
        return success, logs
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        if not self.is_initialized:
            return {"status": "未初始化"}
        
        return {
            "status": "运行中",
            "nng_empty": self.nng.is_empty(),
            "working_memory_count": self.memory.count_working_memories(),
            "navigation_failures": self.sandbox.get_navigation_failure_count() if self.sandbox else 0,
            "llm_provider": self.config["llm"]["provider"],
            "llm_model": self.config["llm"]["model"]
        }
    
    def get_nng_structure(self) -> Dict:
        """获取NNG结构"""
        if not self.nng:
            return {}
        return self.nng.get_structure()
    
    def get_working_memory_list(self, limit: int = 20) -> List[Dict]:
        """获取工作记忆列表"""
        if not self.memory:
            return []
        
        memories = self.memory.get_working_memories(limit=limit)
        return [
            {
                "id": m.memory_id,
                "content": m.content[:100] + "..." if len(m.content) > 100 else m.content,
                "timestamp": m.timestamp
            }
            for m in memories
        ]
    
    def clear_working_memory(self) -> bool:
        """清空工作记忆"""
        if not self.memory:
            return False
        
        # 获取所有工作记忆并删除
        memories = self.memory.get_working_memories()
        for mem in memories:
            self.memory.delete_memory(mem.memory_id)
        
        return True


# 全局系统实例
_system: Optional[AbyssACSystem] = None


def get_system() -> AbyssACSystem:
    """获取系统实例（单例）"""
    global _system
    if _system is None:
        _system = AbyssACSystem()
    return _system
