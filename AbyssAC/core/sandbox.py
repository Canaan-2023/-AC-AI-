"""AbyssAC 三层沙盒模块

实现X层AI操作系统的三层沙盒工作流程：
- 第一层：导航定位沙盒
- 第二层：记忆筛选沙盒
- 第三层：上下文组装沙盒
"""

import json
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from core.memory_manager import MemoryManager, MemoryType
from core.nng_navigator import NNGNavigator
from llm.interface import LLMInterface
from llm.prompt_templates import PromptTemplates
from utils.logger import get_logger


logger = get_logger()


@dataclass
class NavigationResult:
    """导航结果"""
    success: bool
    selected_nodes: List[str]
    path: List[str]
    steps: int
    decisions: List[Dict[str, str]]
    error: Optional[str] = None


@dataclass
class MemoryFilterResult:
    """记忆筛选结果"""
    success: bool
    selected_memory_ids: List[int]
    selected_memories: List[str]
    error: Optional[str] = None


@dataclass
class ContextAssemblyResult:
    """上下文组装结果"""
    success: bool
    assembled_context: str
    error: Optional[str] = None


class ThreeLayerSandbox:
    """三层沙盒管理器"""
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        nng_navigator: NNGNavigator,
        llm_interface: LLMInterface,
        max_depth: int = 10,
        navigation_timeout: int = 30
    ):
        """
        初始化三层沙盒
        
        Args:
            memory_manager: 记忆管理器
            nng_navigator: NNG导航器
            llm_interface: LLM接口
            max_depth: 最大导航深度
            navigation_timeout: 导航超时时间（秒）
        """
        self.memory_manager = memory_manager
        self.nng_navigator = nng_navigator
        self.llm = llm_interface
        self.max_depth = max_depth
        self.navigation_timeout = navigation_timeout
        
        # 导航失败计数
        self.navigation_failures = 0
        
        # 导航日志
        self.navigation_logs: List[Dict] = []
    
    # ========== 第一层沙盒：导航定位 ==========
    
    def layer1_navigation(
        self,
        user_input: str,
        allow_multiple: bool = True
    ) -> NavigationResult:
        """
        第一层沙盒：导航定位
        
        Args:
            user_input: 用户输入
            allow_multiple: 是否允许多节点导航
        
        Returns:
            导航结果
        """
        logger.info(f"第一层沙盒开始: 用户输入='{user_input[:50]}...'")
        
        selected_nodes: List[str] = []
        all_paths: List[List[str]] = []
        all_decisions: List[Dict[str, str]] = []
        total_steps = 0
        
        start_time = time.time()
        
        while True:
            # 单次导航
            result = self._single_navigation(
                user_input,
                selected_nodes
            )
            
            if not result.success:
                self.navigation_failures += 1
                logger.warning(f"导航失败: {result.error}")
                return result
            
            selected_nodes.extend(result.selected_nodes)
            all_paths.append(result.path)
            all_decisions.extend(result.decisions)
            total_steps += result.steps
            
            # 检查超时
            if time.time() - start_time > self.navigation_timeout:
                logger.warning("导航超时")
                self.navigation_failures += 1
                return NavigationResult(
                    success=False,
                    selected_nodes=selected_nodes,
                    path=[],
                    steps=total_steps,
                    decisions=all_decisions,
                    error="导航超时"
                )
            
            # 如果不允许多节点，直接返回
            if not allow_multiple:
                break
            
            # 询问是否需要继续导航
            if not self._ask_continue_navigation(user_input, selected_nodes):
                break
        
        # 记录导航日志
        self._log_navigation(user_input, selected_nodes, all_paths, total_steps, all_decisions)
        
        logger.info(f"第一层沙盒完成: 选中节点={selected_nodes}")
        
        return NavigationResult(
            success=True,
            selected_nodes=list(set(selected_nodes)),  # 去重
            path=all_paths[0] if all_paths else [],
            steps=total_steps,
            decisions=all_decisions
        )
    
    def _single_navigation(
        self,
        user_input: str,
        already_selected: List[str]
    ) -> NavigationResult:
        """
        执行单次导航
        
        Args:
            user_input: 用户输入
            already_selected: 已选中的节点
        
        Returns:
            导航结果
        """
        current = "root"
        path = [current]
        decisions: List[Dict[str, str]] = []
        steps = 0
        visited: set = {current}  # 循环检测
        
        while steps < self.max_depth:
            # 获取当前节点信息
            if current == "root":
                node_data = self.nng_navigator.get_root()
                node_data["定位"] = "root"
                node_data["置信度"] = 100
                node_data["内容"] = "根节点"
                node_data["关联的记忆文件摘要"] = []
                node_data["下级关联NNG"] = [
                    {"节点": n.split("（")[0], "摘要": n.split("（")[1].rstrip("）") if "（" in n else ""}
                    for n in node_data.get("一级节点", [])
                ]
                node_data["上级关联NNG"] = None
            else:
                node = self.nng_navigator.get_node(current)
                if not node:
                    logger.error(f"节点不存在: {current}")
                    return NavigationResult(
                        success=False,
                        selected_nodes=[],
                        path=path,
                        steps=steps,
                        decisions=decisions,
                        error=f"节点不存在: {current}"
                    )
                
                node_data = {
                    "定位": node.location,
                    "置信度": node.confidence,
                    "内容": node.content,
                    "关联的记忆文件摘要": node.memory_summaries,
                    "下级关联NNG": node.child_nngs,
                    "上级关联NNG": node.parent_nng
                }
            
            # 构建提示词
            prompt = PromptTemplates.navigation_context(
                user_input=user_input,
                current_node=node_data,
                current_path=path,
                selected_nodes=already_selected
            )
            
            # 调用LLM
            messages = [
                {"role": "system", "content": PromptTemplates.NAVIGATION_SYSTEM},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm.chat(
                messages,
                validate_format=self.llm.validate_navigation_response
            )
            
            if not response.success:
                logger.error(f"LLM导航响应失败: {response.error}")
                return NavigationResult(
                    success=False,
                    selected_nodes=[],
                    path=path,
                    steps=steps,
                    decisions=decisions,
                    error=f"LLM响应失败: {response.error}"
                )
            
            action = response.content.strip()
            logger.debug(f"导航决策: {current} -> {action}")
            
            # 解析指令
            decision = {"位置": current, "决策": action, "理由": "LLM决策"}
            
            # 处理直接NNG指令
            if action.startswith("NNG") and "STAY" in action:
                # 提取所有NNG
                nng_matches = re.findall(r'NNG([\d.]+)', action)
                return NavigationResult(
                    success=True,
                    selected_nodes=nng_matches,
                    path=path,
                    steps=steps + 1,
                    decisions=decisions + [decision]
                )
            
            # 处理GOTO
            goto_match = re.match(r'GOTO\(([\d.]+)\)', action)
            if goto_match:
                target = goto_match.group(1)
                
                # 循环检测
                if target in visited:
                    logger.warning(f"检测到循环: {target}")
                    return NavigationResult(
                        success=False,
                        selected_nodes=[],
                        path=path,
                        steps=steps,
                        decisions=decisions,
                        error=f"检测到导航循环: {target}"
                    )
                
                new_current, success = self.nng_navigator.navigate(current, "GOTO", target)
                if not success:
                    logger.warning(f"GOTO失败: {target}")
                    return NavigationResult(
                        success=False,
                        selected_nodes=[],
                        path=path,
                        steps=steps,
                        decisions=decisions,
                        error=f"GOTO目标不存在: {target}"
                    )
                
                current = new_current
                path.append(current)
                visited.add(current)
                decisions.append(decision)
                steps += 1
                continue
            
            # 处理BACK
            if action == "BACK":
                new_current, _ = self.nng_navigator.navigate(current, "BACK")
                current = new_current
                path.append(current)
                decisions.append(decision)
                steps += 1
                continue
            
            # 处理ROOT
            if action == "ROOT":
                current = "root"
                path.append(current)
                visited.add(current)
                decisions.append(decision)
                steps += 1
                continue
            
            # 处理STAY
            if action == "STAY":
                decisions.append(decision)
                return NavigationResult(
                    success=True,
                    selected_nodes=[current] if current != "root" else [],
                    path=path,
                    steps=steps + 1,
                    decisions=decisions
                )
            
            # 未知指令
            logger.warning(f"未知导航指令: {action}")
            decisions.append({"位置": current, "决策": "UNKNOWN", "理由": f"未知指令: {action}"})
        
        # 达到最大深度
        logger.warning("达到最大导航深度")
        return NavigationResult(
            success=False,
            selected_nodes=[],
            path=path,
            steps=steps,
            decisions=decisions,
            error="达到最大导航深度"
        )
    
    def _ask_continue_navigation(self, user_input: str, selected_nodes: List[str]) -> bool:
        """
        询问是否需要继续导航到其他节点
        
        Args:
            user_input: 用户输入
            selected_nodes: 已选中的节点
        
        Returns:
            是否继续
        """
        prompt = f"""用户输入: {user_input}
已选中节点: {', '.join(selected_nodes)}

是否需要导航到其他主题节点？请回答：是/否"""
        
        messages = [
            {"role": "system", "content": "你是导航决策助手。判断是否需要继续导航到其他相关节点。只回答'是'或'否'。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if response.success:
            return "是" in response.content or "yes" in response.content.lower()
        
        return False
    
    def _log_navigation(
        self,
        user_input: str,
        selected_nodes: List[str],
        paths: List[List[str]],
        steps: int,
        decisions: List[Dict[str, str]]
    ) -> None:
        """记录导航日志"""
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "user_input": user_input,
            "navigation_path": paths,
            "final_nodes": selected_nodes,
            "navigation_steps": steps,
            "step_decisions": decisions
        }
        
        self.navigation_logs.append(log_entry)
        
        # 同时记录到文件
        logger.navigation(user_input, paths[0] if paths else [], 
                         ', '.join(selected_nodes), steps, decisions)
    
    # ========== 第二层沙盒：记忆筛选 ==========
    
    def layer2_memory_filter(
        self,
        user_input: str,
        selected_nodes: List[str],
        confidence_threshold: int = 30
    ) -> MemoryFilterResult:
        """
        第二层沙盒：记忆筛选
        
        Args:
            user_input: 用户输入
            selected_nodes: 选中的NNG节点列表
            confidence_threshold: 置信度阈值
        
        Returns:
            记忆筛选结果
        """
        logger.info(f"第二层沙盒开始: 节点={selected_nodes}")
        
        # 收集所有相关记忆
        all_memories: List[Dict] = []
        
        for node_id in selected_nodes:
            if node_id == "root":
                continue
            
            node = self.nng_navigator.get_node(node_id)
            if not node:
                continue
            
            for mem_summary in node.memory_summaries:
                mem_id_str = mem_summary.get("记忆ID", "")
                if not mem_id_str.isdigit():
                    continue
                
                mem_id = int(mem_id_str)
                
                # 获取记忆元数据
                meta = self.memory_manager.get_memory_metadata(mem_id)
                if not meta or meta.is_deleted:
                    continue
                
                # 置信度筛选
                if meta.confidence < confidence_threshold:
                    continue
                
                # 获取记忆内容
                content = self.memory_manager.get_memory(mem_id)
                if not content:
                    continue
                
                all_memories.append({
                    "id": mem_id,
                    "type": meta.memory_type,
                    "value_level": meta.value_level,
                    "confidence": meta.confidence,
                    "content": content,
                    "summary": mem_summary.get("摘要", ""),
                    "nng": node_id
                })
        
        # 按置信度排序
        all_memories.sort(key=lambda x: x["confidence"], reverse=True)
        
        if not all_memories:
            logger.info("第二层沙盒: 无相关记忆")
            return MemoryFilterResult(
                success=True,
                selected_memory_ids=[],
                selected_memories=[]
            )
        
        # 构建提示词
        prompt = PromptTemplates.memory_filter_context(user_input, all_memories)
        
        messages = [
            {"role": "system", "content": PromptTemplates.MEMORY_FILTER_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            logger.error(f"记忆筛选LLM调用失败: {response.error}")
            return MemoryFilterResult(
                success=False,
                selected_memory_ids=[],
                selected_memories=[],
                error=f"LLM调用失败: {response.error}"
            )
        
        # 解析选中的记忆
        action = response.content.strip()
        selected_ids: List[int] = []
        
        # 提取记忆ID
        mem_matches = re.findall(r'记忆(\d+)', action)
        selected_ids = [int(m) for m in mem_matches]
        
        # 获取选中的记忆内容
        selected_memories: List[str] = []
        for mem_id in selected_ids:
            content = self.memory_manager.get_memory(mem_id)
            if content:
                selected_memories.append(content)
        
        logger.info(f"第二层沙盒完成: 选中{len(selected_ids)}条记忆")
        
        return MemoryFilterResult(
            success=True,
            selected_memory_ids=selected_ids,
            selected_memories=selected_memories
        )
    
    # ========== 第三层沙盒：上下文组装 ==========
    
    def layer3_context_assembly(
        self,
        user_input: str,
        selected_memories: List[str]
    ) -> ContextAssemblyResult:
        """
        第三层沙盒：上下文组装
        
        Args:
            user_input: 用户输入
            selected_memories: 选中的记忆内容列表
        
        Returns:
            上下文组装结果
        """
        logger.info(f"第三层沙盒开始: {len(selected_memories)}条记忆")
        
        # 获取元认知记忆
        meta_memories = self.memory_manager.get_memories_by_confidence(
            min_confidence=50,
            memory_type=MemoryType.META_COGNITIVE
        )
        
        meta_contents: List[str] = []
        for mem_id in meta_memories[:3]:  # 最多3条元认知记忆
            content = self.memory_manager.get_memory(mem_id)
            if content:
                meta_contents.append(content)
        
        # 构建提示词
        prompt = PromptTemplates.context_assembly_prompt(
            user_input=user_input,
            selected_memories=selected_memories,
            meta_cognitive_memories=meta_contents
        )
        
        messages = [
            {"role": "system", "content": PromptTemplates.CONTEXT_ASSEMBLY_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            logger.error(f"上下文组装LLM调用失败: {response.error}")
            # 降级处理：直接拼接记忆
            assembled = f"用户问题: {user_input}\n\n相关记忆:\n"
            for i, mem in enumerate(selected_memories, 1):
                assembled += f"\n[记忆{i}]\n{mem[:500]}\n"
            
            return ContextAssemblyResult(
                success=True,
                assembled_context=assembled
            )
        
        logger.info("第三层沙盒完成")
        
        return ContextAssemblyResult(
            success=True,
            assembled_context=response.content
        )
    
    # ========== 完整沙盒流程 ==========
    
    def run_full_sandbox(
        self,
        user_input: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        运行完整的三层沙盒流程
        
        Args:
            user_input: 用户输入
        
        Returns:
            (是否成功, 组装好的上下文, 错误信息)
        """
        logger.info(f"=== 启动三层沙盒流程 ===")
        
        # 第一层：导航
        nav_result = self.layer1_navigation(user_input)
        
        if not nav_result.success:
            logger.warning(f"导航失败: {nav_result.error}")
            return False, "", nav_result.error
        
        if not nav_result.selected_nodes:
            logger.info("未选中任何节点，无需调取记忆")
            return True, f"用户问题: {user_input}\n（无相关记忆）", None
        
        # 第二层：记忆筛选
        filter_result = self.layer2_memory_filter(
            user_input,
            nav_result.selected_nodes
        )
        
        if not filter_result.success:
            logger.warning(f"记忆筛选失败: {filter_result.error}")
            return False, "", filter_result.error
        
        if not filter_result.selected_memories:
            logger.info("未选中任何记忆")
            return True, f"用户问题: {user_input}\n（无相关记忆）", None
        
        # 第三层：上下文组装
        assembly_result = self.layer3_context_assembly(
            user_input,
            filter_result.selected_memories
        )
        
        if not assembly_result.success:
            logger.warning(f"上下文组装失败: {assembly_result.error}")
            return False, "", assembly_result.error
        
        logger.info("=== 三层沙盒流程完成 ===")
        
        return True, assembly_result.assembled_context, None
    
    def get_navigation_stats(self) -> Dict[str, Any]:
        """
        获取导航统计
        
        Returns:
            统计信息
        """
        return {
            "total_logs": len(self.navigation_logs),
            "failure_count": self.navigation_failures,
            "recent_logs": self.navigation_logs[-5:] if self.navigation_logs else []
        }
