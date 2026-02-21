"""
AbyssAC Main System
AbyssAC主系统 - 整合所有组件的核心系统
"""

import os
import json
from typing import Dict, Optional, Any, List
from datetime import datetime

from config.system_config import get_config, init_config
from core.nng_manager import get_nng_manager
from core.memory_manager import get_memory_manager
from core.llm_interface import get_llm_interface, PromptBuilder
from core.sandbox import get_sandbox
from core.dmn_system import get_dmn_system, DMNTaskType
from core.quick_thinking import get_quick_system
from core.ai_dev_space import get_dev_space, get_sandbox as get_code_sandbox


class AbyssACSystem:
    """
    AbyssAC主系统
    
    整合所有组件，提供统一的交互接口
    """
    
    def __init__(self, base_path: str = "."):
        """初始化系统"""
        print("[AbyssAC] 初始化系统...")
        
        # 初始化配置
        self.config = init_config(base_path)
        
        # 初始化各组件
        self.nng_manager = get_nng_manager()
        self.memory_manager = get_memory_manager()
        self.llm = get_llm_interface()
        self.sandbox = get_sandbox()
        self.dmn_system = get_dmn_system()
        self.quick_system = get_quick_system()
        self.dev_space = get_dev_space()
        self.code_sandbox = get_code_sandbox()
        
        # 系统状态
        self.conversation_history = []
        self.last_response = None
        
        print("[AbyssAC] 系统初始化完成")
    
    def process_input(self, user_input: str, use_sandbox: bool = True) -> Dict[str, Any]:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入
            use_sandbox: 是否使用三层沙盒（慢思考）
        
        Returns:
            处理结果
        """
        result = {
            "success": False,
            "response": "",
            "used_quick": False,
            "used_sandbox": False,
            "memory_id": None,
            "error": ""
        }
        
        try:
            # 1. 检查是否使用快思考
            if not use_sandbox:
                quick_answer = self.quick_system.query(user_input)
                if quick_answer:
                    result["success"] = True
                    result["response"] = quick_answer
                    result["used_quick"] = True
                    
                    # 保存到工作记忆
                    memory_id = self.memory_manager.create_memory(
                        user_input=user_input,
                        ai_response=quick_answer,
                        memory_type="工作记忆",
                        confidence=0.7
                    )
                    result["memory_id"] = memory_id
                    
                    return result
            
            # 2. 使用三层沙盒（慢思考）
            print("[AbyssAC] 启动三层沙盒处理...")
            result["used_sandbox"] = True
            
            sandbox_result = self.sandbox.execute(user_input)
            
            if not sandbox_result["success"]:
                result["error"] = sandbox_result.get("error", "沙盒执行失败")
                return result
            
            context_package = sandbox_result["context_package"]
            
            # 3. 生成最终回复
            print("[AbyssAC] 生成最终回复...")
            final_prompt = PromptBuilder.build_user_response_prompt(
                user_input=user_input,
                context_package=context_package
            )
            
            messages = [{"role": "user", "content": final_prompt}]
            llm_response = self.llm.chat(messages)
            
            if not llm_response.success:
                result["error"] = f"生成回复失败: {llm_response.error}"
                return result
            
            response_text = llm_response.content
            result["success"] = True
            result["response"] = response_text
            
            # 4. 保存到工作记忆
            memory_id = self.memory_manager.create_memory(
                user_input=user_input,
                ai_response=response_text,
                memory_type="工作记忆",
                confidence=0.6
            )
            result["memory_id"] = memory_id
            
            # 5. 添加到历史
            self.conversation_history.append({
                "user": user_input,
                "ai": response_text,
                "timestamp": datetime.now().isoformat()
            })
            
            self.last_response = response_text
            
        except Exception as e:
            result["error"] = f"处理异常: {str(e)}"
        
        return result
    
    def chat(self, user_input: str, use_slow_thinking: bool = False) -> str:
        """
        简化版聊天接口
        
        Args:
            user_input: 用户输入
            use_slow_thinking: 是否强制使用慢思考
        
        Returns:
            AI回复
        """
        result = self.process_input(user_input, use_sandbox=use_slow_thinking)
        
        if result["success"]:
            return result["response"]
        else:
            return f"处理失败: {result['error']}"
    
    def save_important_memory(self, memory_id: str, memory_type: str = "分类记忆",
                              value_level: str = "中价值") -> bool:
        """
        将工作记忆保存为重要记忆
        
        Args:
            memory_id: 记忆ID
            memory_type: 记忆类型
            value_level: 价值层级
        
        Returns:
            是否成功
        """
        try:
            # 读取工作记忆
            memory = self.memory_manager.read_memory(memory_id, "工作记忆")
            if not memory:
                return False
            
            # 创建新记忆
            new_id = self.memory_manager.create_memory(
                user_input=memory.user_input,
                ai_response=memory.ai_response,
                memory_type=memory_type,
                value_level=value_level,
                confidence=memory.confidence
            )
            
            if new_id:
                # 删除原工作记忆
                self.memory_manager.delete_memory(memory_id)
                return True
            
            return False
        except Exception as e:
            print(f"保存重要记忆失败: {e}")
            return False
    
    def run_dmn_maintenance(self) -> List[Dict[str, Any]]:
        """运行DMN维护"""
        print("[AbyssAC] 运行DMN维护...")
        return self.dmn_system.run_maintenance()
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "memory_counter": self.config.counters.memory_counter,
            "nav_fail_count": self.config.counters.nav_fail_counter,
            "nng_nodes": len(self.nng_manager.list_all_nodes()),
            "work_memories": len(self.memory_manager.get_work_memories()),
            "conversation_count": len(self.conversation_history),
            "llm_connected": self.llm.check_connection()
        }
    
    def create_nng_node(self, node_id: str, content: str,
                        parent_id: str = None) -> bool:
        """创建NNG节点"""
        return self.nng_manager.create_node(
            node_id=node_id,
            content=content,
            parent_id=parent_id
        )
    
    def link_memory_to_nng(self, memory_id: str, nng_node_id: str,
                           summary: str) -> bool:
        """将记忆关联到NNG节点"""
        # 查找记忆
        memory = self.memory_manager.read_memory(memory_id)
        if not memory:
            return False
        
        # 构建记忆路径
        year, month, day = self.config.time.get_current_date_path()
        memory_path = f"Y层记忆库/{memory.memory_type}/{memory.value_level}/{year}/{month}/{day}/{memory_id}.txt"
        
        # 添加到NNG节点
        return self.nng_manager.add_memory_summary(
            node_id=nng_node_id,
            memory_id=memory_id,
            memory_path=memory_path,
            summary=summary,
            memory_type=memory.memory_type,
            value_level=memory.value_level,
            confidence=memory.confidence
        )
    
    def export_memory(self, memory_id: str, filepath: str) -> bool:
        """导出记忆到文件"""
        try:
            memory = self.memory_manager.read_memory(memory_id)
            if not memory:
                return False
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(memory.to_text())
            
            return True
        except Exception as e:
            print(f"导出记忆失败: {e}")
            return False
    
    def clear_work_memories(self) -> bool:
        """清空工作记忆"""
        return self.memory_manager.clear_work_memories()


# 全局系统实例
_system_instance = None


def get_system() -> AbyssACSystem:
    """获取全局系统实例"""
    global _system_instance
    if _system_instance is None:
        _system_instance = AbyssACSystem()
    return _system_instance


def init_system(base_path: str = ".") -> AbyssACSystem:
    """初始化系统"""
    global _system_instance
    _system_instance = AbyssACSystem(base_path)
    return _system_instance
