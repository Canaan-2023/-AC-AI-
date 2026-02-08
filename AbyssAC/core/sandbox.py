"""
X层AI操作系统 - 三层沙盒流程
"""
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .llm_client import LLMClient, LLMResponse
from .nng_manager import NNGManager
from .memory_manager import MemoryManager


@dataclass
class SandboxResult:
    """沙盒执行结果"""
    success: bool
    context: str  # 组装好的上下文
    selected_memories: List[Dict]  # 选中的记忆
    logs: List[str]  # 执行日志
    error: str = ""


class SandboxLayer1:
    """第一层沙盒：导航定位沙盒"""
    
    def __init__(self, llm: LLMClient, nng: NNGManager):
        self.llm = llm
        self.nng = nng
        self.logs: List[str] = []
    
    def execute(self, user_input: str, working_memories: List[Dict]) -> Tuple[bool, List[str], str]:
        """
        执行第一层沙盒：导航到需要的NNG节点
        
        Returns:
            (success, selected_nng_ids, log_summary)
        """
        self.logs = []
        self.logs.append("=== 第一层沙盒：导航定位 ===")
        
        # 获取NNG结构
        nng_structure = self.nng.get_structure()
        
        # 构建提示词
        prompt = self._build_navigation_prompt(user_input, nng_structure, working_memories)
        
        messages = [
            {"role": "system", "content": "你是AbyssAC系统的导航定位模块。请分析用户输入，选择需要调取的NNG节点。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            self.logs.append(f"❌ LLM调用失败: {response.error}")
            return False, [], "\n".join(self.logs)
        
        self.logs.append(f"📝 LLM响应: {response.content[:200]}...")
        
        # 解析NNG选择
        selected_ids = self._parse_nng_selection(response.content)
        
        if not selected_ids:
            self.logs.append("⚠️ 未选择任何NNG节点")
            return False, [], "\n".join(self.logs)
        
        self.logs.append(f"✅ 选中NNG节点: {selected_ids}")
        return True, selected_ids, "\n".join(self.logs)
    
    def _build_navigation_prompt(self, user_input: str, nng_structure: Dict, 
                                  working_memories: List[Dict]) -> str:
        """构建导航提示词"""
        prompt = f"""请分析以下用户输入，判断需要调取哪些NNG节点的记忆来辅助回复。

【用户输入】
{user_input}

【当前NNG结构】
{json.dumps(nng_structure, ensure_ascii=False, indent=2)}

【最近工作记忆】
"""
        for mem in working_memories[-5:]:
            mem_id = mem.get('memory_id', '?')
            mem_content = mem.get('content', '')[:50]
            prompt += f"- ID{mem_id}: {mem_content}...\n"
        
        prompt += """
【输出格式】
如果需要调取记忆，请输出: NNGx.x.x (可多个，如 NNG1.2 NNG2.1)
如果不需要调取记忆，请输出: 无需调取

请分析并输出:"""
        return prompt
    
    def _parse_nng_selection(self, content: str) -> List[str]:
        """解析NNG选择"""
        selected = []
        
        # 匹配 NNG1.2.3 格式
        pattern = r'NNG(\d+(?:\.\d+)*)'
        matches = re.findall(pattern, content)
        
        for match in matches:
            selected.append(match)
        
        # 也匹配 1.2.3 格式（前面没有NNG）
        if not selected:
            pattern = r'(?:^|\s)(\d+(?:\.\d+)*)(?:\s|$)'
            matches = re.findall(pattern, content)
            for match in matches:
                if '.' in match:  # 确保是层级格式
                    selected.append(match)
        
        return selected


class SandboxLayer2:
    """第二层沙盒：记忆筛选沙盒"""
    
    def __init__(self, llm: LLMClient, nng: NNGManager, memory: MemoryManager):
        self.llm = llm
        self.nng = nng
        self.memory = memory
        self.logs: List[str] = []
    
    def execute(self, user_input: str, nng_ids: List[str]) -> Tuple[bool, List[Dict], str]:
        """
        执行第二层沙盒：筛选需要的记忆
        
        Returns:
            (success, selected_memories, log_summary)
        """
        self.logs = []
        self.logs.append("=== 第二层沙盒：记忆筛选 ===")
        
        # 获取选中NNG节点的关联记忆
        all_related_memories = []
        for nng_id in nng_ids:
            node = self.nng.get_node(nng_id)
            if node and node.关联的记忆文件摘要:
                for mem_summary in node.关联的记忆文件摘要:
                    mem_summary["_来源NNG"] = nng_id
                    all_related_memories.append(mem_summary)
        
        if not all_related_memories:
            self.logs.append("⚠️ 选中的NNG节点没有关联记忆")
            return False, [], "\n".join(self.logs)
        
        self.logs.append(f"📚 找到 {len(all_related_memories)} 条关联记忆")
        
        # 构建提示词让LLM选择需要的记忆
        prompt = self._build_selection_prompt(user_input, all_related_memories)
        
        messages = [
            {"role": "system", "content": "你是AbyssAC系统的记忆筛选模块。请从候选记忆中选择对回复用户最有帮助的内容。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            self.logs.append(f"❌ LLM调用失败: {response.error}")
            return False, [], "\n".join(self.logs)
        
        self.logs.append(f"📝 LLM响应: {response.content[:200]}...")
        
        # 解析记忆选择
        selected_ids = self._parse_memory_selection(response.content)
        
        if not selected_ids:
            self.logs.append("⚠️ 未选择任何记忆")
            return False, [], "\n".join(self.logs)
        
        # 获取完整记忆内容
        selected_memories = []
        for mem_id in selected_ids:
            mem_info = self.memory.get_memory(mem_id)
            if mem_info:
                selected_memories.append({
                    "id": mem_id,
                    "content": mem_info.content,
                    "type": mem_info.memory_type,
                    "timestamp": mem_info.timestamp
                })
        
        self.logs.append(f"✅ 选中 {len(selected_memories)} 条记忆")
        return True, selected_memories, "\n".join(self.logs)
    
    def _build_selection_prompt(self, user_input: str, memories: List[Dict]) -> str:
        """构建记忆选择提示词"""
        prompt = f"""请从以下候选记忆中，选择对回复用户最有帮助的内容。

【用户输入】
{user_input}

【候选记忆】
"""
        for mem in memories:
            mem_id = mem.get("记忆ID", "未知")
            summary = mem.get("摘要", "无摘要")
            mem_type = mem.get("记忆类型", "未知")
            value = mem.get("价值层级", "")
            value_str = f" [{value}价值]" if value else ""
            prompt += f"\n[记忆{mem_id}]{value_str} ({mem_type})\n{summary}\n"
        
        prompt += """
【输出格式】
请输出需要的记忆ID，格式: 记忆xxx (可多个，如 记忆123 记忆456)
如果都不需要，请输出: 无需调取

请分析并输出:"""
        return prompt
    
    def _parse_memory_selection(self, content: str) -> List[int]:
        """解析记忆选择"""
        selected = []
        
        # 匹配 记忆123 或 记忆ID123 格式
        pattern = r'记忆(?:ID)?(\d+)'
        matches = re.findall(pattern, content)
        
        for match in matches:
            try:
                selected.append(int(match))
            except:
                pass
        
        # 也匹配纯数字
        if not selected:
            pattern = r'\b(\d{1,6})\b'
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    num = int(match)
                    if num > 0 and num < 100000:  # 合理的记忆ID范围
                        selected.append(num)
                except:
                    pass
        
        return selected


class SandboxLayer3:
    """第三层沙盒：上下文组装沙盒"""
    
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.logs: List[str] = []
    
    def execute(self, user_input: str, selected_memories: List[Dict],
                working_memories: List[Dict]) -> Tuple[bool, str, str]:
        """
        执行第三层沙盒：组装上下文
        
        Returns:
            (success, assembled_context, log_summary)
        """
        self.logs = []
        self.logs.append("=== 第三层沙盒：上下文组装 ===")
        
        # 构建组装提示词
        prompt = self._build_assembly_prompt(user_input, selected_memories, working_memories)
        
        messages = [
            {"role": "system", "content": "你是AbyssAC系统的上下文组装模块。请整合用户输入、相关记忆和工作记忆，形成结构化的上下文。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            self.logs.append(f"❌ LLM调用失败: {response.error}")
            return False, "", "\n".join(self.logs)
        
        assembled_context = response.content
        self.logs.append(f"✅ 上下文组装完成，长度: {len(assembled_context)}")
        
        return True, assembled_context, "\n".join(self.logs)
    
    def _build_assembly_prompt(self, user_input: str, selected_memories: List[Dict],
                                working_memories: List[Dict]) -> str:
        """构建上下文组装提示词"""
        prompt = f"""请将以下信息整合为结构化的上下文，供回复生成使用。

【用户输入】
{user_input}

【调取的长期记忆】
"""
        for mem in selected_memories:
            prompt += f"\n[记忆{mem.get('id', '?')}] ({mem.get('type', '?')})\n{mem.get('content', '')}\n"
        
        prompt += "\n【相关工作记忆】\n"
        for mem in working_memories[-5:]:
            prompt += f"\n[ID{mem.get('memory_id', '?')}] {mem.get('content', '')[:100]}...\n"
        
        prompt += """
【输出格式】
请输出结构化的上下文，包含:
1. 用户意图分析
2. 相关背景信息（从记忆中提取）
3. 需要关注的关键点
4. 回复建议方向

请输出整合后的上下文:"""
        return prompt


class XLayerSandbox:
    """X层三层沙盒控制器"""
    
    def __init__(self, llm: LLMClient, nng: NNGManager, memory: MemoryManager):
        self.llm = llm
        self.nng = nng
        self.memory = memory
        self.layer1 = SandboxLayer1(llm, nng)
        self.layer2 = SandboxLayer2(llm, nng, memory)
        self.layer3 = SandboxLayer3(llm)
        self.navigation_failures = 0
    
    def execute(self, user_input: str, working_memories: List[Dict]) -> SandboxResult:
        """
        执行完整的三层沙盒流程
        
        Returns:
            SandboxResult对象
        """
        all_logs = []
        
        # 检查NNG是否为空
        if self.nng.is_empty():
            all_logs.append("⚠️ NNG为空，跳过三层沙盒")
            return SandboxResult(
                success=True,
                context=user_input,
                selected_memories=[],
                logs=all_logs
            )
        
        # === 第一层：导航定位 ===
        success1, nng_ids, logs1 = self.layer1.execute(user_input, working_memories)
        all_logs.append(logs1)
        
        if not success1 or not nng_ids:
            self.navigation_failures += 1
            all_logs.append(f"⚠️ 第一层导航失败，失败次数: {self.navigation_failures}")
            return SandboxResult(
                success=False,
                context=user_input,
                selected_memories=[],
                logs=all_logs,
                error="导航失败"
            )
        
        # === 第二层：记忆筛选 ===
        success2, selected_memories, logs2 = self.layer2.execute(user_input, nng_ids)
        all_logs.append(logs2)
        
        if not success2 or not selected_memories:
            all_logs.append("⚠️ 第二层未选中记忆，使用原始输入")
            return SandboxResult(
                success=True,
                context=user_input,
                selected_memories=[],
                logs=all_logs
            )
        
        # === 第三层：上下文组装 ===
        success3, assembled_context, logs3 = self.layer3.execute(
            user_input, selected_memories, working_memories
        )
        all_logs.append(logs3)
        
        return SandboxResult(
            success=success3,
            context=assembled_context if success3 else user_input,
            selected_memories=selected_memories,
            logs=all_logs
        )
    
    def get_navigation_failure_count(self) -> int:
        """获取导航失败次数"""
        return self.navigation_failures
    
    def reset_navigation_failures(self):
        """重置导航失败计数"""
        self.navigation_failures = 0
