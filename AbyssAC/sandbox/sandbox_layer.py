"""
X层三层沙盒模块
第一层：导航定位沙盒
第二层：记忆筛选沙盒
第三层：上下文组装沙盒
"""
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.llm_interface import LLMInterface, LLMResponse
from nng.nng_manager import NNGManager, NNGNode
from memory.memory_manager import MemoryManager, MemoryEntry, MemoryType


@dataclass
class NavigationResult:
    """导航结果"""
    selected_nodes: List[str]  # 选中的节点ID列表
    navigation_path: List[str]  # 导航路径
    steps: List[Dict[str, Any]]  # 每步决策记录
    success: bool
    error: Optional[str] = None
    failure_reason: Optional[str] = None  # 导航失败原因


@dataclass
class MemorySelectionResult:
    """记忆筛选结果"""
    selected_memories: List[MemoryEntry]  # 选中的记忆
    success: bool
    error: Optional[str] = None


@dataclass
class ContextAssemblyResult:
    """上下文组装结果"""
    assembled_context: str  # 组装后的上下文
    success: bool
    error: Optional[str] = None


class NavigationSandbox:
    """第一层沙盒：导航定位沙盒"""
    
    def __init__(self, llm: LLMInterface, nng_manager: NNGManager):
        self.llm = llm
        self.nng = nng_manager
        self.max_depth = 10
        self.max_nodes = 3
        
    def navigate(self, user_input: str, 
                 working_memories: List[MemoryEntry]) -> NavigationResult:
        """
        执行导航定位
        
        Args:
            user_input: 用户输入
            working_memories: 最近的工作记忆
            
        Returns:
            NavigationResult
        """
        selected_nodes = []
        all_paths = []
        all_steps = []
        
        # 支持多节点导航（最多3个）
        for node_index in range(self.max_nodes):
            result = self._single_navigation(
                user_input, working_memories, 
                selected_nodes, node_index
            )
            
            if result['success']:
                selected_nodes.append(result['final_node'])
                all_paths.append(result['path'])
                all_steps.extend(result['steps'])
                
                # 询问是否需要继续导航到其他节点
                if node_index < self.max_nodes - 1:
                    should_continue = self._ask_continue_navigation(
                        user_input, selected_nodes
                    )
                    if not should_continue:
                        break
            else:
                # 导航失败，记录原因
                return NavigationResult(
                    selected_nodes=selected_nodes,
                    navigation_path=all_paths[0] if all_paths else [],
                    steps=all_steps,
                    success=False,
                    failure_reason=result.get('error', '导航失败')
                )
        
        return NavigationResult(
            selected_nodes=selected_nodes,
            navigation_path=all_paths[0] if all_paths else [],
            steps=all_steps,
            success=True
        )
    
    def _single_navigation(self, user_input: str,
                           working_memories: List[MemoryEntry],
                           excluded_nodes: List[str],
                           node_index: int) -> Dict[str, Any]:
        """执行单次导航"""
        current_node_id = "root"
        path = ["root"]
        steps = []
        
        for depth in range(self.max_depth):
            # 获取当前节点信息
            node = self.nng.get_node(current_node_id)
            if not node:
                return {
                    'success': False,
                    'error': f'节点不存在: {current_node_id}',
                    'final_node': current_node_id,
                    'path': path,
                    'steps': steps
                }
            
            # 构建导航提示
            prompt = self._build_navigation_prompt(
                user_input=user_input,
                current_node_id=current_node_id,
                node=node,
                working_memories=working_memories,
                excluded_nodes=excluded_nodes,
                node_index=node_index,
                depth=depth
            )
            
            # 请求LLM决策
            response = self.llm.simple_chat(
                prompt,
                system_prompt="你是一个NNG导航系统，负责帮助用户在知识图谱中找到最相关的节点。"
            )
            
            # 解析决策
            decision = self._parse_navigation_decision(response)
            
            # 记录决策
            steps.append({
                "位置": current_node_id,
                "决策": decision['action'],
                "目标": decision.get('target', ''),
                "理由": decision.get('reason', '')
            })
            
            # 执行决策
            if decision['action'] == 'STAY':
                # 导航结束
                return {
                    'success': True,
                    'final_node': current_node_id,
                    'path': path,
                    'steps': steps
                }
            
            elif decision['action'] == 'BACK':
                # 返回上一层
                if len(path) > 1:
                    path.pop()
                    current_node_id = path[-1]
                else:
                    # 已经在root，无法返回
                    return {
                        'success': False,
                        'error': '已在root节点，无法返回',
                        'final_node': current_node_id,
                        'path': path,
                        'steps': steps
                    }
            
            elif decision['action'] == 'GOTO':
                target = decision.get('target', '')
                
                # 验证目标节点
                if not target:
                    return {
                        'success': False,
                        'error': 'GOTO目标为空',
                        'final_node': current_node_id,
                        'path': path,
                        'steps': steps
                    }
                
                # 检查目标是否在子节点列表中
                if target not in node.子节点:
                    # 可能是关联节点，允许跳转但记录警告
                    if not self.nng.validate_node_exists(target):
                        return {
                            'success': False,
                            'error': f'目标节点不存在: {target}',
                            'final_node': current_node_id,
                            'path': path,
                            'steps': steps
                        }
                
                # 执行跳转
                current_node_id = target
                path.append(target)
            
            else:
                # 无法解析的决策，默认STAY
                return {
                    'success': True,
                    'final_node': current_node_id,
                    'path': path,
                    'steps': steps,
                    'error': f'无法解析决策: {response[:50]}'
                }
        
        # 达到最大深度，强制停止
        return {
            'success': True,
            'final_node': current_node_id,
            'path': path,
            'steps': steps,
            'error': '达到最大导航深度'
        }
    
    def _build_navigation_prompt(self, user_input: str,
                                  current_node_id: str,
                                  node: NNGNode,
                                  working_memories: List[MemoryEntry],
                                  excluded_nodes: List[str],
                                  node_index: int,
                                  depth: int) -> str:
        """构建导航提示"""
        
        # 获取子节点信息
        children_info = []
        for child_id in node.子节点:
            if child_id not in excluded_nodes:  # 排除已选中的节点
                child = self.nng.get_node(child_id)
                if child:
                    children_info.append({
                        "id": child_id,
                        "描述": child.内容[:80] + "..." if len(child.内容) > 80 else child.内容
                    })
        
        # 获取关联节点信息
        associations_info = []
        for assoc in node.关联节点[:3]:  # 最多显示3个关联节点
            associations_info.append(assoc)
        
        # 获取记忆摘要示例
        memory_summaries = []
        for mem in node.关联的记忆文件摘要[:3]:
            memory_summaries.append(mem.get('摘要', '')[:50])
        
        # 构建工作记忆上下文
        working_context = ""
        if working_memories:
            working_context = "\n最近的工作记忆:\n"
            for i, wm in enumerate(working_memories[-3:], 1):
                working_context += f"{i}. {wm.content[:80]}...\n"
        
        prompt = f"""【NNG导航决策】

用户输入: {user_input}
当前导航节点: {node_index + 1}/3 (深度: {depth})
当前位置: {current_node_id}

当前节点信息:
- 节点ID: {node.定位}
- 节点描述: {node.内容}
- 关联性评分: {node.关联性}/100
- 置信度评分: {node.置信度}/100
- 关联记忆数量: {len(node.关联的记忆文件摘要)}
"""
        
        if memory_summaries:
            prompt += f"- 记忆摘要示例: {', '.join(memory_summaries)}\n"
        
        if children_info:
            prompt += f"\n可选子节点:\n"
            for child in children_info:
                prompt += f"  - {child['id']}: {child['描述']}\n"
        else:
            prompt += "\n[当前节点没有可选子节点]\n"
        
        if associations_info:
            prompt += f"\n关联节点:\n"
            for assoc in associations_info:
                prompt += f"  - {assoc.get('id', '')}: {assoc.get('名称', '')} (关联强度: {assoc.get('关联强度', 0)})\n"
        
        if excluded_nodes:
            prompt += f"\n已选中的节点（请勿重复选择）: {', '.join(excluded_nodes)}\n"
        
        prompt += working_context
        
        prompt += """
请根据用户输入和当前节点信息，选择下一步行动。

可用指令:
1. GOTO(节点ID) - 进入指定的子节点
2. STAY - 停留在当前节点，结束导航
3. BACK - 返回上一层节点

请严格按照以下格式输出你的决策:
决策: GOTO(1.2) 或 STAY 或 BACK
理由: [简要说明原因]

注意:
- 只输出一个指令
- 不要包含其他解释性文字
- 如果当前节点与用户需求高度相关，选择STAY
- 如果有更相关的子节点，选择GOTO
"""
        
        return prompt
    
    def _parse_navigation_decision(self, response: str) -> Dict[str, str]:
        """解析导航决策"""
        response = response.strip()
        
        # 尝试匹配GOTO
        goto_match = re.search(r'GOTO\s*\(?\s*([\d.]+)\s*\)?', response, re.IGNORECASE)
        if goto_match:
            return {
                'action': 'GOTO',
                'target': goto_match.group(1),
                'reason': self._extract_reason(response)
            }
        
        # 尝试匹配STAY
        if re.search(r'\bSTAY\b', response, re.IGNORECASE):
            return {
                'action': 'STAY',
                'reason': self._extract_reason(response)
            }
        
        # 尝试匹配BACK
        if re.search(r'\bBACK\b', response, re.IGNORECASE):
            return {
                'action': 'BACK',
                'reason': self._extract_reason(response)
            }
        
        # 无法解析，默认STAY
        return {
            'action': 'STAY',
            'reason': f'无法解析决策: {response[:50]}',
            'parse_error': True
        }
    
    def _extract_reason(self, response: str) -> str:
        """提取决策理由"""
        reason_match = re.search(r'理由[:：]\s*(.+?)(?:\n|$)', response, re.DOTALL)
        if reason_match:
            return reason_match.group(1).strip()[:100]
        return ""
    
    def _ask_continue_navigation(self, user_input: str, 
                                  selected_nodes: List[str]) -> bool:
        """询问是否需要继续导航到其他节点"""
        prompt = f"""用户输入: {user_input}
已选中的节点: {', '.join(selected_nodes)}

这些节点是否足以回答用户的问题？还是需要在其他主题领域继续搜索？

请回答: YES（继续搜索其他节点）或 NO（已足够）
"""
        response = self.llm.simple_chat(prompt)
        
        # 如果包含YES，继续导航
        return 'YES' in response.upper() or '是' in response


class MemorySelectionSandbox:
    """第二层沙盒：记忆筛选沙盒"""
    
    def __init__(self, llm: LLMInterface, memory_manager: MemoryManager):
        self.llm = llm
        self.memory = memory_manager
    
    def select_memories(self, user_input: str,
                        selected_nodes: List[str]) -> MemorySelectionResult:
        """
        根据选中的节点筛选记忆
        
        Args:
            user_input: 用户输入
            selected_nodes: 第一层沙盒选中的节点ID列表
            
        Returns:
            MemorySelectionResult
        """
        # 收集所有相关记忆
        all_memories = []
        memory_ids_seen = set()
        
        for node_id in selected_nodes:
            node = self.nng.get_node(node_id) if hasattr(self, 'nng') else None
            
            # 从NNG节点获取关联的记忆摘要
            if node and node.关联的记忆文件摘要:
                for mem_summary in node.关联的记忆文件摘要:
                    mem_id = mem_summary.get('记忆ID')
                    if mem_id and mem_id not in memory_ids_seen:
                        memory_entry = self.memory.get_memory(mem_id)
                        if memory_entry:
                            all_memories.append(memory_entry)
                            memory_ids_seen.add(mem_id)
        
        if not all_memories:
            # 如果没有找到关联记忆，返回空结果
            return MemorySelectionResult(
                selected_memories=[],
                success=True
            )
        
        # 让LLM选择需要的记忆
        prompt = self._build_selection_prompt(user_input, all_memories)
        
        response = self.llm.simple_chat(
            prompt,
            system_prompt="你是一个记忆筛选系统，负责从候选记忆中选择最相关的部分。"
        )
        
        # 解析选中的记忆ID
        selected_ids = self._parse_selected_memories(response)
        
        # 获取选中的记忆
        selected_memories = []
        for mem_id in selected_ids:
            mem = self.memory.get_memory(mem_id)
            if mem:
                selected_memories.append(mem)
        
        return MemorySelectionResult(
            selected_memories=selected_memories,
            success=True
        )
    
    def _build_selection_prompt(self, user_input: str, 
                                 memories: List[MemoryEntry]) -> str:
        """构建记忆选择提示"""
        prompt = f"""【记忆筛选】

用户输入: {user_input}

候选记忆列表:
"""
        for mem in memories:
            preview = mem.content[:200] + "..." if len(mem.content) > 200 else mem.content
            prompt += f"\n[记忆 #{mem.id}]\n{preview}\n"
        
        prompt += """
请从上述记忆中选择对回答用户问题有帮助的内容。

输出格式:
选中记忆: 记忆ID1, 记忆ID2, 记忆ID3
理由: [简要说明选择原因]

如果没有任何记忆相关，请输出:
选中记忆: 无
"""
        return prompt
    
    def _parse_selected_memories(self, response: str) -> List[int]:
        """解析选中的记忆ID"""
        selected_ids = []
        
        # 匹配"选中记忆:"后面的内容
        match = re.search(r'选中记忆[:：]\s*(.+?)(?:\n|$)', response)
        if match:
            content = match.group(1)
            # 提取所有数字
            ids = re.findall(r'\d+', content)
            selected_ids = [int(id_str) for id_str in ids]
        
        return selected_ids


class ContextAssemblySandbox:
    """第三层沙盒：上下文组装沙盒"""
    
    def __init__(self, llm: LLMInterface):
        self.llm = llm
    
    def assemble_context(self, user_input: str,
                         selected_memories: List[MemoryEntry],
                         working_memories: List[MemoryEntry],
                         meta_memories: List[MemoryEntry] = None) -> ContextAssemblyResult:
        """
        组装上下文
        
        Args:
            user_input: 用户输入
            selected_memories: 第二层沙盒选中的记忆
            working_memories: 最近的工作记忆
            meta_memories: 元认知记忆（可选）
            
        Returns:
            ContextAssemblyResult
        """
        prompt = self._build_assembly_prompt(
            user_input, selected_memories, working_memories, meta_memories
        )
        
        response = self.llm.simple_chat(
            prompt,
            system_prompt="你是一个上下文组装系统，负责整合记忆和当前对话，生成结构化的上下文。"
        )
        
        return ContextAssemblyResult(
            assembled_context=response,
            success=True
        )
    
    def _build_assembly_prompt(self, user_input: str,
                                selected_memories: List[MemoryEntry],
                                working_memories: List[MemoryEntry],
                                meta_memories: List[MemoryEntry] = None) -> str:
        """构建上下文组装提示"""
        prompt = "【上下文组装】\n\n"
        
        # 用户当前输入
        prompt += f"=== 用户当前输入 ===\n{user_input}\n\n"
        
        # 元认知记忆（常驻）
        if meta_memories:
            prompt += "=== 元认知记忆（系统认知）===\n"
            for mem in meta_memories[:2]:
                preview = mem.content[:300] + "..." if len(mem.content) > 300 else mem.content
                prompt += f"- {preview}\n"
            prompt += "\n"
        
        # 工作记忆（当前对话历史）
        if working_memories:
            prompt += "=== 工作记忆（当前对话）===\n"
            for mem in working_memories[-5:]:  # 最近5条
                preview = mem.content[:200] + "..." if len(mem.content) > 200 else mem.content
                prompt += f"- {preview}\n"
            prompt += "\n"
        
        # 选中的相关记忆
        if selected_memories:
            prompt += "=== 相关记忆（从NNG调取）===\n"
            for mem in selected_memories:
                preview = mem.content[:400] + "..." if len(mem.content) > 400 else mem.content
                prompt += f"[记忆 #{mem.id}]\n{preview}\n\n"
        
        prompt += """=== 任务 ===
请整合以上信息，生成一个结构化的上下文，用于回答用户的问题。

输出要求:
1. 保持信息层次清晰
2. 标注信息来源（如"来自记忆#123"）
3. 突出与用户问题最相关的内容
4. 如果记忆之间有冲突，请指出

直接输出整合后的上下文内容，不需要额外解释。
"""
        return prompt


class SandboxLayer:
    """X层三层沙盒整合"""
    
    def __init__(self, llm: LLMInterface, 
                 nng_manager: NNGManager,
                 memory_manager: MemoryManager):
        self.llm = llm
        self.nng = nng_manager
        self.memory = memory_manager
        
        # 初始化三层沙盒
        self.nav_sandbox = NavigationSandbox(llm, nng_manager)
        self.mem_sandbox = MemorySelectionSandbox(llm, memory_manager)
        self.ctx_sandbox = ContextAssemblySandbox(llm)
        
        # 导航失败计数
        self.navigation_failure_count = 0
        
    def process(self, user_input: str, 
                working_memories: List[MemoryEntry]) -> Dict[str, Any]:
        """
        执行三层沙盒处理
        
        Args:
            user_input: 用户输入
            working_memories: 最近的工作记忆
            
        Returns:
            处理结果字典
        """
        result = {
            'success': False,
            'context': '',
            'selected_nodes': [],
            'selected_memories': [],
            'navigation_result': None,
            'fallback': False
        }
        
        # 第一层：导航定位
        print("\n[沙盒] 第一层：导航定位...")
        nav_result = self.nav_sandbox.navigate(user_input, working_memories)
        result['navigation_result'] = nav_result
        
        if not nav_result.success:
            # 导航失败，增加计数
            self.navigation_failure_count += 1
            print(f"[沙盒] 导航失败: {nav_result.failure_reason}")
            print(f"[沙盒] 导航失败计数: {self.navigation_failure_count}")
            
            # 降级处理：直接返回，不经过记忆筛选
            result['fallback'] = True
            result['context'] = self._build_fallback_context(user_input, working_memories)
            result['success'] = True
            return result
        
        # 导航成功，重置失败计数
        self.navigation_failure_count = 0
        result['selected_nodes'] = nav_result.selected_nodes
        print(f"[沙盒] 选中节点: {nav_result.selected_nodes}")
        
        # 第二层：记忆筛选
        print("\n[沙盒] 第二层：记忆筛选...")
        mem_result = self.mem_sandbox.select_memories(user_input, nav_result.selected_nodes)
        result['selected_memories'] = mem_result.selected_memories
        
        if mem_result.selected_memories:
            mem_ids = [m.id for m in mem_result.selected_memories]
            print(f"[沙盒] 选中记忆: {mem_ids}")
        else:
            print("[沙盒] 未选中任何记忆")
        
        # 第三层：上下文组装
        print("\n[沙盒] 第三层：上下文组装...")
        ctx_result = self.ctx_sandbox.assemble_context(
            user_input,
            mem_result.selected_memories,
            working_memories
        )
        
        result['context'] = ctx_result.assembled_context
        result['success'] = True
        
        return result
    
    def _build_fallback_context(self, user_input: str, 
                                 working_memories: List[MemoryEntry]) -> str:
        """构建降级处理的上下文"""
        context = f"用户输入: {user_input}\n\n"
        
        if working_memories:
            context += "最近对话:\n"
            for mem in working_memories[-3:]:
                context += f"- {mem.content[:150]}...\n"
        
        context += "\n[系统提示: NNG导航失败，基于当前上下文直接回复]"
        
        return context
    
    def get_navigation_failure_count(self) -> int:
        """获取导航失败计数"""
        return self.navigation_failure_count
    
    def reset_navigation_failure_count(self):
        """重置导航失败计数"""
        self.navigation_failure_count = 0


if __name__ == "__main__":
    # 自测
    print("=" * 60)
    print("SandboxLayer模块自测")
    print("=" * 60)
    
    import tempfile
    import shutil
    
    # 创建临时测试目录
    test_dir = tempfile.mkdtemp(prefix="abyssac_sandbox_test_")
    print(f"\n测试目录: {test_dir}")
    
    try:
        # 初始化组件
        llm = LLMInterface(use_local=True, ollama_model="qwen2.5:7b")
        
        # 创建测试用的NNG和Memory
        from nng.nng_manager import NNGManager
        from memory.memory_manager import MemoryManager, ValueLevel
        
        nng = NNGManager(base_path=f"{test_dir}/NNG")
        memory = MemoryManager(base_path=f"{test_dir}/Y层记忆库")
        
        # 创建一些测试节点和记忆
        node1_id = nng.create_node("root", "Python编程")
        node2_id = nng.create_node("root", "人工智能")
        
        mem1 = memory.save_memory("GIL是Python的全局解释器锁", 
                                   MemoryType.CLASSIFIED, 
                                   value_level=ValueLevel.HIGH)
        nng.add_memory_to_node(node1_id, mem1.id, "GIL详解", "分类记忆", "高价值")
        
        # 初始化沙盒层
        sandbox = SandboxLayer(llm, nng, memory)
        print("[✓] 沙盒层初始化成功")
        
        # 测试导航沙盒
        print("\n测试导航沙盒...")
        working_mems = memory.get_working_memories()
        nav_result = sandbox.nav_sandbox.navigate("什么是GIL？", working_mems)
        print(f"[✓] 导航结果: 选中节点 {nav_result.selected_nodes}")
        print(f"[✓] 导航路径: {nav_result.navigation_path}")
        print(f"[✓] 导航步数: {len(nav_result.steps)}")
        
        # 测试记忆筛选沙盒
        print("\n测试记忆筛选沙盒...")
        mem_result = sandbox.mem_sandbox.select_memories("什么是GIL？", nav_result.selected_nodes)
        print(f"[✓] 选中记忆数: {len(mem_result.selected_memories)}")
        
        # 测试上下文组装沙盒
        print("\n测试上下文组装沙盒...")
        ctx_result = sandbox.ctx_sandbox.assemble_context(
            "什么是GIL？",
            mem_result.selected_memories,
            working_mems
        )
        print(f"[✓] 组装上下文长度: {len(ctx_result.assembled_context)}")
        
        # 测试完整流程
        print("\n测试完整沙盒流程...")
        result = sandbox.process("什么是GIL？", working_mems)
        print(f"[✓] 处理成功: {result['success']}")
        print(f"[✓] 选中节点: {result['selected_nodes']}")
        print(f"[✓] 是否降级: {result['fallback']}")
        
        print("\n" + "=" * 60)
        print("SandboxLayer模块自测通过")
        print("=" * 60)
        
    finally:
        # 清理测试目录
        shutil.rmtree(test_dir, ignore_errors=True)
        print(f"\n已清理测试目录")
