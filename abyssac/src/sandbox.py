"""
AbyssAC 三层沙盒模块
实现导航、筛选、组装三层沙盒
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from storage import StorageManager
from llm_client import LLMClient, PromptLoader, InstructionParser


@dataclass
class SandboxState:
    """沙盒状态"""
    session_id: str
    current_position: str = "root"
    navigation_path: List[str] = field(default_factory=lambda: ["root"])
    depth: int = 0
    selected_nngs: List[str] = field(default_factory=list)
    selected_memories: List[Dict[str, Any]] = field(default_factory=list)
    layer: int = 1
    completed: bool = False
    error: Optional[str] = None
    log: Dict[str, Any] = field(default_factory=dict)


class Layer1Sandbox:
    """第一层沙盒：导航定位"""
    
    MAX_DEPTH = 10
    NAVIGATION_TIMEOUT = 30
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.navigation_failures = 0
    
    async def navigate(self, user_input: str, state: SandboxState) -> SandboxState:
        """
        执行导航流程
        
        Args:
            user_input: 用户输入
            state: 当前沙盒状态
        
        Returns:
            更新后的沙盒状态
        """
        state.layer = 1
        state.log = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_input": user_input,
            "navigation_path": ["root"],
            "final_nodes": [],
            "steps": [],
            "session_id": state.session_id
        }
        
        current_nng_id = "root"
        navigation_path = ["root"]
        
        try:
            while state.depth < self.MAX_DEPTH:
                # 读取当前NNG
                nng_data = StorageManager.read_nng(current_nng_id)
                if not nng_data:
                    # 节点不存在，记录错误
                    state.error = f"NNG节点 {current_nng_id} 不存在"
                    self._log_navigation_error(state, "NODE_NOT_FOUND")
                    break
                
                # 构建提示词
                prompt = PromptLoader.load_prompt(
                    "sandbox_layer1",
                    user_input=user_input,
                    current_position=current_nng_id,
                    navigation_path=" → ".join(navigation_path),
                    depth=state.depth + 1,
                    nng_content=json.dumps(nng_data, ensure_ascii=False, indent=2)
                )
                
                # 调用LLM
                messages = [{"role": "user", "content": prompt}]
                response = await asyncio.wait_for(
                    self.llm.chat(messages),
                    timeout=self.NAVIGATION_TIMEOUT
                )
                
                # 检查错误
                if response.startswith("ERROR:"):
                    state.error = f"LLM调用失败: {response}"
                    self._log_navigation_error(state, "LLM_ERROR")
                    break
                
                # 解析指令
                instruction = InstructionParser.parse_layer1_instruction(response)
                
                # 记录决策
                step_log = {
                    "position": current_nng_id,
                    "decision": response.strip(),
                    "parsed": instruction
                }
                state.log["steps"].append(step_log)
                
                # 执行指令
                if instruction["type"] == "STAY":
                    # 停留在当前节点
                    state.selected_nngs.append(current_nng_id)
                    state.log["final_nodes"].append(current_nng_id)
                    break
                
                elif instruction["type"] == "DIRECT":
                    # 直接定位到指定节点
                    if "multiple" in instruction:
                        state.selected_nngs.extend(instruction["multiple"])
                        state.log["final_nodes"].extend(instruction["multiple"])
                    else:
                        state.selected_nngs.append(instruction["target"])
                        state.log["final_nodes"].append(instruction["target"])
                    break
                
                elif instruction["type"] == "GOTO":
                    target = instruction["target"]
                    # 检查目标是否存在
                    target_data = StorageManager.read_nng(target)
                    if not target_data:
                        # 目标不存在，记录错误
                        state.error = f"导航目标 {target} 不存在"
                        self._log_navigation_error(state, "TARGET_NOT_FOUND")
                        break
                    
                    current_nng_id = target
                    navigation_path.append(target)
                    state.depth += 1
                    state.navigation_path = navigation_path
                
                elif instruction["type"] == "BACK":
                    # 返回上一层
                    if len(navigation_path) > 1:
                        navigation_path.pop()
                        current_nng_id = navigation_path[-1]
                        state.depth = max(0, state.depth - 1)
                        state.navigation_path = navigation_path
                
                elif instruction["type"] == "ROOT":
                    # 回到根目录
                    current_nng_id = "root"
                    navigation_path = ["root"]
                    state.depth = 0
                    state.navigation_path = navigation_path
            
            else:
                # 达到最大深度
                state.error = "达到最大导航深度"
                self._log_navigation_error(state, "MAX_DEPTH_REACHED")
            
            # 保存导航日志
            state.log["navigation_path"] = navigation_path
            StorageManager.write_navigation_log(state.log)
            
        except asyncio.TimeoutError:
            state.error = "导航超时"
            self._log_navigation_error(state, "TIMEOUT")
            self.navigation_failures += 1
        
        except Exception as e:
            state.error = f"导航异常: {str(e)}"
            self._log_navigation_error(state, "EXCEPTION")
            self.navigation_failures += 1
        
        return state
    
    def _log_navigation_error(self, state: SandboxState, error_type: str):
        """记录导航错误"""
        state.log["error"] = {
            "type": error_type,
            "message": state.error,
            "depth": state.depth
        }
        StorageManager.write_navigation_log(state.log)
        StorageManager.write_error_log({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": f"NAVIGATION_{error_type}",
            "session_id": state.session_id,
            "layer": 1,
            "error": state.error,
            "context": state.log
        })
        self.navigation_failures += 1


class Layer2Sandbox:
    """第二层沙盒：记忆筛选"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    async def filter_memories(self, user_input: str, state: SandboxState) -> SandboxState:
        """
        执行记忆筛选
        
        Args:
            user_input: 用户输入
            state: 当前沙盒状态（包含选中的NNG）
        
        Returns:
            更新后的沙盒状态
        """
        state.layer = 2
        
        try:
            # 收集所有候选记忆
            all_memories = []
            memory_map = {}  # memory_id -> memory_info
            
            for nng_id in state.selected_nngs:
                nng_data = StorageManager.read_nng(nng_id)
                if not nng_data:
                    continue
                
                for mem_summary in nng_data.get("关联的记忆文件摘要", []):
                    mem_id = mem_summary.get("记忆ID")
                    if mem_id and mem_id not in memory_map:
                        memory_map[mem_id] = mem_summary
                        all_memories.append({
                            "id": mem_id,
                            "summary": mem_summary.get("摘要", ""),
                            "type": mem_summary.get("记忆类型", ""),
                            "value": mem_summary.get("价值层级", ""),
                            "file_path": mem_summary.get("文件路径", "")
                        })
            
            if not all_memories:
                # 没有候选记忆，直接进入下一层
                state.layer = 3
                return state
            
            # 格式化记忆列表
            memories_formatted = "\n".join([
                f"- 记忆ID: {m['id']}, 摘要: {m['summary']}, "
                f"类型: {m['type']}({m['value']}), 文件: {m['file_path']}"
                for m in all_memories
            ])
            
            # 构建提示词
            prompt = PromptLoader.load_prompt(
                "sandbox_layer2",
                user_input=user_input,
                current_nng=", ".join(state.selected_nngs),
                memories_list=memories_formatted
            )
            
            # 调用LLM
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.chat(messages)
            
            # 检查错误
            if response.startswith("ERROR:"):
                state.error = f"LLM调用失败: {response}"
                return state
            
            # 解析指令
            instruction = InstructionParser.parse_layer2_instruction(response)
            
            # 读取选中的记忆内容
            if instruction["type"] == "SELECT" and instruction["memory_ids"]:
                for mem_id in instruction["memory_ids"]:
                    mem_info = memory_map.get(mem_id)
                    if mem_info:
                        content = StorageManager.read_memory(
                            mem_id, 
                            mem_info.get("文件路径")
                        )
                        if content:
                            state.selected_memories.append({
                                "id": mem_id,
                                "type": mem_info.get("记忆类型"),
                                "content": content
                            })
            
        except Exception as e:
            state.error = f"记忆筛选异常: {str(e)}"
        
        return state


class Layer3Sandbox:
    """第三层沙盒：上下文组装"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    async def assemble_context(self, user_input: str, state: SandboxState,
                               context_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        执行上下文组装
        
        Args:
            user_input: 用户输入
            state: 当前沙盒状态（包含选中的记忆）
            context_history: 对话历史
        
        Returns:
            组装后的上下文
        """
        state.layer = 3
        
        try:
            # 格式化选中的记忆
            memories_formatted = ""
            if state.selected_memories:
                memories_parts = []
                for mem in state.selected_memories:
                    memories_parts.append(
                        f"--- 记忆ID: {mem['id']} ({mem['type']}) ---\n{mem['content']}"
                    )
                memories_formatted = "\n\n".join(memories_parts)
            else:
                memories_formatted = "（无选中记忆）"
            
            # 格式化对话历史
            history_formatted = ""
            if context_history:
                history_parts = []
                for msg in context_history[-5:]:  # 最近5条
                    role = "用户" if msg["role"] == "user" else "AI"
                    history_parts.append(f"{role}: {msg['content']}")
                history_formatted = "\n".join(history_parts)
            else:
                history_formatted = "（无历史对话）"
            
            # 构建提示词
            prompt = PromptLoader.load_prompt(
                "sandbox_layer3",
                user_input=user_input,
                selected_memories=memories_formatted,
                context_history=history_formatted
            )
            
            # 调用LLM
            messages = [{"role": "user", "content": prompt}]
            assembled_context = await self.llm.chat(messages)
            
            # 检查错误
            if assembled_context.startswith("ERROR:"):
                # 使用简化上下文
                assembled_context = self._build_simple_context(
                    user_input, state.selected_memories, context_history
                )
            
            state.completed = True
            
            return {
                "user_input": user_input,
                "assembled_context": assembled_context,
                "selected_memories": state.selected_memories,
                "selected_nngs": state.selected_nngs,
                "navigation_path": state.navigation_path,
                "completed": True
            }
        
        except Exception as e:
            state.error = f"上下文组装异常: {str(e)}"
            return {
                "user_input": user_input,
                "assembled_context": self._build_simple_context(
                    user_input, state.selected_memories, context_history
                ),
                "error": str(e),
                "completed": False
            }
    
    def _build_simple_context(self, user_input: str, 
                              memories: List[Dict], 
                              history: List[Dict[str, str]]) -> str:
        """构建简化上下文（LLM失败时回退）"""
        parts = ["【用户输入】", user_input]
        
        if memories:
            parts.extend(["\n【相关记忆】"])
            for mem in memories:
                parts.append(f"\n--- 记忆 {mem['id']} ---")
                parts.append(mem['content'][:500] + "..." if len(mem['content']) > 500 else mem['content'])
        
        if history:
            parts.extend(["\n【对话历史】"])
            for msg in history[-3:]:
                role = "用户" if msg["role"] == "user" else "AI"
                parts.append(f"{role}: {msg['content'][:200]}...")
        
        return "\n".join(parts)


class SandboxOrchestrator:
    """沙盒编排器"""
    
    def __init__(self):
        self.llm = LLMClient()
        self.layer1 = Layer1Sandbox(self.llm)
        self.layer2 = Layer2Sandbox(self.llm)
        self.layer3 = Layer3Sandbox(self.llm)
    
    async def process(self, user_input: str, session_id: str,
                      context_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        执行完整的三层沙盒流程
        
        Args:
            user_input: 用户输入
            session_id: 会话ID
            context_history: 对话历史
        
        Returns:
            处理结果
        """
        # 初始化状态
        state = SandboxState(session_id=session_id)
        
        # 第一层：导航
        state = await self.layer1.navigate(user_input, state)
        
        # 如果有错误且没有选中NNG，直接返回
        if state.error and not state.selected_nngs:
            return {
                "error": state.error,
                "user_input": user_input,
                "final_response": await self._generate_fallback_response(user_input, context_history)
            }
        
        # 第二层：记忆筛选
        state = await self.layer2.filter_memories(user_input, state)
        
        # 第三层：上下文组装
        result = await self.layer3.assemble_context(user_input, state, context_history)
        
        # 生成最终回复
        final_response = await self._generate_final_response(
            result["assembled_context"], context_history
        )
        
        result["final_response"] = final_response
        
        return result
    
    async def _generate_fallback_response(self, user_input: str,
                                          context_history: List[Dict[str, str]]) -> str:
        """生成回退回复（导航失败时）"""
        messages = context_history + [{"role": "user", "content": user_input}]
        return await self.llm.chat(messages)
    
    async def _generate_final_response(self, assembled_context: str,
                                       context_history: List[Dict[str, str]]) -> str:
        """生成最终回复"""
        system_prompt = """你是AbyssAC系统的回复生成智能体。
请根据提供的上下文生成自然、连贯的回复。
上下文包含用户输入、相关记忆和对话历史。
请确保回复准确、有帮助，并自然地融入记忆中的信息。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"【上下文】\n{assembled_context}\n\n请生成回复："}
        ]
        
        return await self.llm.chat(messages)


# 导入json用于类型提示
import json
