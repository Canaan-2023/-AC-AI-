"""
DMN动态维护网络 - 五个子智能体
"""
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .llm_client import LLMClient, LLMResponse
from .nng_manager import NNGManager, NNGNode
from .memory_manager import MemoryManager, MemoryType, ValueLevel


class DMNTaskType(Enum):
    """DMN任务类型"""
    MEMORY_INTEGRATION = "记忆整合"
    ASSOCIATION_DISCOVERY = "关联发现"
    BIAS_REVIEW = "偏差审查"
    STRATEGY_REHEARSAL = "策略预演"
    CONCEPT_RECOMBINATION = "概念重组"


class Agent1_QuestionOutput:
    """子智能体一：问题输出agent"""
    
    def __init__(self, llm: LLMClient):
        self.llm = llm
    
    def execute(self, working_memories: List[Dict], task_type: DMNTaskType) -> Tuple[bool, List[str], str]:
        """
        根据工作记忆识别需要维护的问题
        
        Returns:
            (success, questions, logs)
        """
        logs = ["=== Agent1: 问题输出 ==="]
        
        prompt = f"""请分析以下工作记忆，识别需要维护的认知问题。

【任务类型】{task_type.value}

【工作记忆】
"""
        for mem in working_memories:
            prompt += f"\n[ID{mem.get('memory_id', '?')}] {mem.get('content', '')[:200]}...\n"
        
        prompt += """
【输出格式】
请列出需要处理的问题（每条一行，以"问题:"开头）:
问题: xxxxxx
问题: xxxxxx
...

请分析问题:"""
        
        messages = [
            {"role": "system", "content": "你是DMN的问题识别模块，负责从工作记忆中发现需要维护的问题。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            logs.append(f"❌ LLM调用失败: {response.error}")
            return False, [], "\n".join(logs)
        
        logs.append(f"📝 识别到问题")
        
        # 解析问题列表
        questions = self._parse_questions(response.content)
        logs.append(f"✅ 提取 {len(questions)} 个问题")
        
        return True, questions, "\n".join(logs)
    
    def _parse_questions(self, content: str) -> List[str]:
        """解析问题列表"""
        questions = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('问题:') or line.startswith('问题：'):
                q = line[3:].strip()
                if q:
                    questions.append(q)
            elif line and ('?' in line or '？' in line):
                questions.append(line)
        return questions


class Agent2_ProblemAnalysis:
    """子智能体二：问题分析agent"""
    
    def __init__(self, llm: LLMClient):
        self.llm = llm
    
    def execute(self, questions: List[str], working_memories: List[Dict],
               task_type: DMNTaskType) -> Tuple[bool, Dict, str]:
        """
        分析问题并给出建议方案
        
        Returns:
            (success, analysis_result, logs)
        """
        logs = ["=== Agent2: 问题分析 ==="]
        
        prompt = f"""请分析以下问题，给出详细的分析结果和建议方案。

【任务类型】{task_type.value}

【待分析问题】
"""
        for i, q in enumerate(questions, 1):
            prompt += f"{i}. {q}\n"
        
        prompt += f"""
【参考工作记忆】
"""
        for mem in working_memories:
            prompt += f"\n[ID{mem.get('memory_id', '?')}] {mem.get('content', '')[:150]}...\n"
        
        prompt += """
【输出格式】
请以JSON格式输出分析结果:
{
    "问题分析": [
        {"问题": "xxx", "分析": "xxx", "建议方案": "xxx"}
    ],
    "需要新建的记忆": ["内容1", "内容2"],
    "需要关联的NNG": ["1.2", "3.1"],
    "建议的价值层级": "高/中/低"
}

请输出分析结果:"""
        
        messages = [
            {"role": "system", "content": "你是DMN的问题分析模块，负责深入分析问题并给出建议方案。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            logs.append(f"❌ LLM调用失败: {response.error}")
            return False, {}, "\n".join(logs)
        
        # 解析JSON
        result = self.llm.parse_json_response(response.content)
        
        if not result:
            logs.append("⚠️ 无法解析JSON响应")
            return False, {"raw": response.content}, "\n".join(logs)
        
        logs.append("✅ 分析完成")
        return True, result, "\n".join(logs)


class Agent3_Review:
    """子智能体三：审查agent"""
    
    def __init__(self, llm: LLMClient):
        self.llm = llm
    
    def execute(self, analysis_result: Dict, task_type: DMNTaskType) -> Tuple[bool, bool, str]:
        """
        审查分析结果
        
        Returns:
            (success, is_valid, logs)
        """
        logs = ["=== Agent3: 审查 ==="]
        
        prompt = f"""请审查以下分析结果是否完整、逻辑是否正确。

【任务类型】{task_type.value}

【分析结果】
{json.dumps(analysis_result, ensure_ascii=False, indent=2)}

【审查标准】
1. 分析是否针对问题本身
2. 建议方案是否具体可行
3. 是否有明确的记忆/NNG操作建议
4. 逻辑是否自洽

【输出格式】
请输出: 通过 或 不通过
如果不通过，请说明原因:
原因: xxxxxx

请审查:"""
        
        messages = [
            {"role": "system", "content": "你是DMN的审查模块，负责检查分析结果的质量。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            logs.append(f"❌ LLM调用失败: {response.error}")
            return False, False, "\n".join(logs)
        
        content = response.content.lower()
        is_valid = "通过" in response.content and "不通过" not in content
        
        if is_valid:
            logs.append("✅ 审查通过")
        else:
            logs.append(f"❌ 审查不通过: {response.content[:100]}")
        
        return True, is_valid, "\n".join(logs)


class Agent4_Organize:
    """子智能体四：整理agent"""
    
    def __init__(self, llm: LLMClient, memory: MemoryManager, nng: NNGManager):
        self.llm = llm
        self.memory = memory
        self.nng = nng
    
    def execute(self, analysis_result: Dict, task_type: DMNTaskType) -> Tuple[bool, Dict, str]:
        """
        整理为标准化的记忆和NNG格式
        
        Returns:
            (success, organized_data, logs)
        """
        logs = ["=== Agent4: 整理 ==="]
        
        # 获取当前NNG结构用于参考
        nng_structure = self.nng.get_structure()
        
        prompt = f"""请将分析结果整理为标准化的记忆和NNG格式。

【任务类型】{task_type.value}

【分析结果】
{json.dumps(analysis_result, ensure_ascii=False, indent=2)}

【当前NNG结构】
{json.dumps(nng_structure, ensure_ascii=False, indent=2)}

【输出格式】
请以JSON格式输出:
{
    "记忆列表": [
        {
            "内容": "记忆内容",
            "类型": "元认知/高阶整合/分类/工作",
            "价值层级": "高/中/低",
            "关联NNG": "建议关联的NNG节点"
        }
    ],
    "NNG节点列表": [
        {
            "定位": "如1.2.3 (新节点用?表示，如1.?)",
            "内容": "节点描述",
            "置信度": 80,
            "关联记忆索引": [0, 1]
        }
    ],
    "需要更新的NNG": [
        {
            "定位": "1",
            "新增子节点": "1.x"
        }
    ]
}

请整理输出:"""
        
        messages = [
            {"role": "system", "content": "你是DMN的整理模块，负责将分析结果转换为标准格式。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            logs.append(f"❌ LLM调用失败: {response.error}")
            return False, {}, "\n".join(logs)
        
        result = self.llm.parse_json_response(response.content)
        
        if not result:
            logs.append("⚠️ 无法解析JSON响应")
            return False, {"raw": response.content}, "\n".join(logs)
        
        logs.append("✅ 整理完成")
        logs.append(f"   - 记忆: {len(result.get('记忆列表', []))} 条")
        logs.append(f"   - NNG节点: {len(result.get('NNG节点列表', []))} 个")
        
        return True, result, "\n".join(logs)


class Agent5_FormatReview:
    """子智能体五：格式位置审查agent"""
    
    def __init__(self, llm: LLMClient):
        self.llm = llm
    
    def execute(self, organized_data: Dict, task_type: DMNTaskType) -> Tuple[bool, bool, str]:
        """
        验证格式和位置是否正确
        
        Returns:
            (success, is_valid, logs)
        """
        logs = ["=== Agent5: 格式位置审查 ==="]
        
        prompt = f"""请审查以下整理结果的格式是否符合规范。

【任务类型】{task_type.value}

【整理结果】
{json.dumps(organized_data, ensure_ascii=False, indent=2)}

【格式规范】
1. 记忆必须包含: 内容、类型
2. NNG节点必须包含: 定位、内容、置信度(0-100)
3. 类型必须是: 元认知/高阶整合/分类/工作 之一
4. 价值层级必须是: 高/中/低 之一（分类记忆需要）

【输出格式】
请输出: 通过 或 不通过
如果不通过，请说明原因:
原因: xxxxxx

请审查:"""
        
        messages = [
            {"role": "system", "content": "你是DMN的格式审查模块，负责验证输出格式是否符合规范。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            logs.append(f"❌ LLM调用失败: {response.error}")
            return False, False, "\n".join(logs)
        
        content = response.content.lower()
        is_valid = "通过" in response.content and "不通过" not in content
        
        if is_valid:
            logs.append("✅ 格式审查通过")
        else:
            logs.append(f"❌ 格式审查不通过: {response.content[:100]}")
        
        return True, is_valid, "\n".join(logs)


class DMNController:
    """DMN控制器"""
    
    def __init__(self, llm: LLMClient, memory: MemoryManager, nng: NNGManager):
        self.llm = llm
        self.memory = memory
        self.nng = nng
        
        self.agent1 = Agent1_QuestionOutput(llm)
        self.agent2 = Agent2_ProblemAnalysis(llm)
        self.agent3 = Agent3_Review(llm)
        self.agent4 = Agent4_Organize(llm, memory, nng)
        self.agent5 = Agent5_FormatReview(llm)
    
    def execute(self, working_memories: List[Dict], 
                task_type: DMNTaskType = DMNTaskType.MEMORY_INTEGRATION,
                max_retries: int = 2) -> Tuple[bool, str]:
        """
        执行完整的DMN五智能体流程
        
        Returns:
            (success, logs)
        """
        all_logs = [f"=== DMN执行: {task_type.value} ==="]
        
        # Agent 1: 问题输出
        success, questions, logs1 = self.agent1.execute(working_memories, task_type)
        all_logs.append(logs1)
        
        if not success or not questions:
            all_logs.append("⚠️ 未识别到问题，DMN结束")
            return False, "\n".join(all_logs)
        
        retries = 0
        while retries <= max_retries:
            # Agent 2: 问题分析
            success2, analysis, logs2 = self.agent2.execute(questions, working_memories, task_type)
            all_logs.append(logs2)
            
            if not success2:
                retries += 1
                continue
            
            # Agent 3: 审查
            success3, is_valid3, logs3 = self.agent3.execute(analysis, task_type)
            all_logs.append(logs3)
            
            if not is_valid3:
                retries += 1
                continue
            
            # Agent 4: 整理
            success4, organized, logs4 = self.agent4.execute(analysis, task_type)
            all_logs.append(logs4)
            
            if not success4:
                retries += 1
                continue
            
            # Agent 5: 格式审查
            success5, is_valid5, logs5 = self.agent5.execute(organized, task_type)
            all_logs.append(logs5)
            
            if is_valid5:
                # 执行实际存储操作
                store_success, store_logs = self._store_results(organized)
                all_logs.append(store_logs)
                return store_success, "\n".join(all_logs)
            
            retries += 1
        
        all_logs.append("❌ DMN执行失败，超过最大重试次数")
        return False, "\n".join(all_logs)
    
    def _store_results(self, organized_data: Dict) -> Tuple[bool, str]:
        """存储整理结果到系统"""
        logs = ["=== 存储执行结果 ==="]
        
        # 存储记忆
        memories = organized_data.get("记忆列表", [])
        memory_id_map = {}  # 用于后续NNG关联
        
        for i, mem_data in enumerate(memories):
            content = mem_data.get("内容", "")
            mem_type_str = mem_data.get("类型", "工作")
            value_str = mem_data.get("价值层级", "中")
            
            # 转换类型
            mem_type_map = {
                "元认知": MemoryType.META_COGNITION,
                "高阶整合": MemoryType.HIGH_LEVEL,
                "分类": MemoryType.CLASSIFIED,
                "工作": MemoryType.WORKING
            }
            mem_type = mem_type_map.get(mem_type_str, MemoryType.WORKING)
            
            # 转换价值层级
            value_map = {
                "高": ValueLevel.HIGH,
                "中": ValueLevel.MEDIUM,
                "低": ValueLevel.LOW
            }
            value_level = value_map.get(value_str, ValueLevel.MEDIUM)
            
            info = self.memory.save_memory(content, mem_type, value_level)
            memory_id_map[i] = info.memory_id
            logs.append(f"✅ 保存记忆 ID{info.memory_id}: {content[:30]}...")
        
        # 存储NNG节点
        nng_nodes = organized_data.get("NNG节点列表", [])
        for node_data in nng_nodes:
            node_id = node_data.get("定位", "")
            content = node_data.get("内容", "")
            confidence = node_data.get("置信度", 80)
            
            # 处理关联记忆
            related_indices = node_data.get("关联记忆索引", [])
            related_memories = []
            for idx in related_indices:
                if idx in memory_id_map:
                    mem_id = memory_id_map[idx]
                    mem_info = self.memory.get_memory(mem_id)
                    if mem_info:
                        related_memories.append({
                            "记忆ID": mem_id,
                            "摘要": mem_info.content[:100] + "..." if len(mem_info.content) > 100 else mem_info.content,
                            "记忆类型": mem_info.memory_type,
                            "价值层级": mem_info.value_level
                        })
            
            # 创建或更新NNG节点
            if "?" in node_id:
                # 新节点，需要找到合适的父节点
                parent = node_id.split(".")[0] if "." in node_id else "root"
                new_id = self.nng.get_next_child_id(parent if parent != "root" else "root")
                if new_id:
                    if parent != "root":
                        node_id = f"{parent}.{new_id}"
                    else:
                        node_id = new_id
            
            if node_id:
                success = self.nng.create_node(node_id, content, confidence, related_memories)
                if success:
                    logs.append(f"✅ 创建NNG节点 {node_id}: {content[:30]}...")
                else:
                    logs.append(f"⚠️ 创建NNG节点失败 {node_id}")
        
        logs.append("✅ 存储完成")
        return True, "\n".join(logs)
    
    def should_trigger(self, working_memory_count: int, 
                      navigation_failures: int,
                      idle_seconds: int = 0) -> Tuple[bool, Optional[DMNTaskType]]:
        """
        判断是否应该触发DMN
        
        Returns:
            (should_trigger, task_type)
        """
        from ..config import DMN_TRIGGER
        
        # 工作记忆超过阈值
        if working_memory_count >= DMN_TRIGGER["working_memory_threshold"]:
            return True, DMNTaskType.MEMORY_INTEGRATION
        
        # 导航失败超过阈值
        if navigation_failures >= DMN_TRIGGER["navigation_failure_threshold"]:
            return True, DMNTaskType.ASSOCIATION_DISCOVERY
        
        # 系统空闲超过阈值
        if idle_seconds >= DMN_TRIGGER["idle_time_seconds"]:
            return True, DMNTaskType.BIAS_REVIEW
        
        return False, None
