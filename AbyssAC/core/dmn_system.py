"""
DMN Maintenance System
DMN维护系统 - 默认模式网络，执行空闲时的自我审查与结构优化
"""

import os
import json
from typing import List, Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass

from config.system_config import get_config
from core.nng_manager import get_nng_manager
from core.memory_manager import get_memory_manager
from core.llm_interface import get_llm_interface
from core.sandbox import ThreeLayerSandbox


class DMNTaskType(Enum):
    """DMN任务类型"""
    MEMORY_INTEGRATION = "记忆整合"
    ASSOCIATION_DISCOVERY = "关联发现"
    DEVIATION_REVIEW = "偏差审查"
    STRATEGY_REHEARSAL = "策略预演"
    CONCEPT_REORG = "概念重组"


@dataclass
class DMNTask:
    """DMN任务"""
    task_id: int
    task_type: DMNTaskType
    priority: int
    description: str
    status: str = "pending"  # pending, running, completed, failed


class DMNQuestionAgent:
    """DMN问题输出Agent"""
    
    def __init__(self):
        self.config = get_config()
        self.llm = get_llm_interface()
    
    def execute(self, task_type: DMNTaskType, work_memories: List[Dict],
                nav_fail_count: int, unprocessed_count: int,
                idle_time: int) -> Dict[str, Any]:
        """
        分析问题，输出需要审查的资源路径
        
        Returns:
            {"paths": [...], "notes": "..."}
        """
        prompt = f"""你是DMN的问题输出Agent。分析工作记忆和系统状态，识别需要维护的认知区域。

【任务类型】{task_type.value}

【输出格式】
{{path1}}
{{path2}}
...
笔记：{{为什么这些资源需要审查，预期发现什么问题}}

【规则】
- 优先选择高价值、高冲突、长时间未访问的资源
- 记忆整合：选积压的工作记忆
- 关联发现：选主题相近但未联结的NNG/记忆
- 偏差审查：选导航失败相关的NNG节点
- 策略预演：选需要推演的目标场景
- 概念重组：选跨界可融合的概念节点

【输入】
工作记忆：{json.dumps(work_memories, ensure_ascii=False)}
系统状态：
- 导航失败次数：{nav_fail_count}
- 未处理工作记忆：{unprocessed_count}
- 空闲时间：{idle_time}秒"""
        
        messages = [{"role": "user", "content": prompt}]
        response = self.llm.chat(messages)
        
        if not response.success:
            return {"paths": [], "notes": f"执行失败: {response.error}"}
        
        # 解析路径
        paths = []
        notes = ""
        for line in response.content.split('\n'):
            line = line.strip()
            if line.startswith('nng/') or line.startswith('Y层记忆库/'):
                paths.append(line)
            elif line.startswith('笔记：') or line.startswith('笔记:'):
                notes = line.replace('笔记：', '').replace('笔记:', '').strip()
        
        return {"paths": paths, "notes": notes}


class DMNAnalysisAgent:
    """DMN问题分析Agent"""
    
    def __init__(self):
        self.llm = get_llm_interface()
    
    def execute(self, paths: List[str], path_contents: Dict[str, str]) -> str:
        """
        基于资源路径深入分析问题
        
        Returns:
            分析结果文本
        """
        prompt = f"""你是DMN的问题分析Agent。基于指定的资源路径，深入分析问题并生成解决方案。

【输出格式】
【资源分析】（对每个审查的资源）
- {{path}}：{{内容摘要}} → {{发现的问题/价值点}}

【问题归纳】
- 核心问题：{{最根本的问题是什么}}
- 表现形式：{{具体症状}}
- 根本原因：{{深层原因分析}}

【解决方案】
- 方案1：{{具体操作}}，预期效果{{value}}，风险{{risk}}
- 方案2：{{具体操作}}，预期效果{{value}}，风险{{risk}}

【建议优先级】
- 立即执行：{{最紧急的操作}}
- 后续优化：{{可延后的改进}}
- 长期观察：{{需要持续跟踪的点}}

【输入】
待审查路径：{json.dumps(paths, ensure_ascii=False)}
路径内容：{json.dumps(path_contents, ensure_ascii=False)}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = self.llm.chat(messages)
        
        return response.content if response.success else f"分析失败: {response.error}"


class DMNReviewAgent:
    """DMN审查Agent"""
    
    def __init__(self):
        self.llm = get_llm_interface()
    
    def execute(self, analysis_result: str, original_resources: Dict[str, str]) -> Dict[str, Any]:
        """
        验证分析结果
        
        Returns:
            {"passed": bool, "feedback": "...", "defects": [...]}
        """
        prompt = f"""你是DMN的审查Agent。验证问题分析Agent的输出是否完整、逻辑正确。

【审查维度】
- 完整性：是否覆盖了所有待审查资源？
- 逻辑性：推理过程是否有漏洞？
- 可行性：方案是否可落地执行？
- 一致性：与系统现有结构是否冲突？

【输出格式】
审查结论：{{通过 / 不通过}}
缺陷分级：
- 致命缺陷：{{有无}}，{{描述}} → 不通过，返回问题分析Agent
- 重大遗漏：{{有无}}，{{描述}} → 不通过，返回问题输出Agent补充资源
- minor问题：{{有无}}，{{描述}} → 通过，备注待修正

【输入】
分析结果：{analysis_result}
原始资源：{json.dumps(original_resources, ensure_ascii=False)}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = self.llm.chat(messages)
        
        if not response.success:
            return {"passed": False, "feedback": response.error, "defects": ["调用失败"]}
        
        # 解析审查结论
        content = response.content
        passed = "通过" in content and "不通过" not in content.split("审查结论：")[-1].split('\n')[0]
        
        return {
            "passed": passed,
            "feedback": content,
            "defects": []
        }


class DMNOrganizeAgent:
    """DMN整理Agent"""
    
    def __init__(self):
        self.config = get_config()
        self.llm = get_llm_interface()
        self.nng_manager = get_nng_manager()
        self.memory_manager = get_memory_manager()
    
    def execute(self, approved_analysis: str, existing_structure: Dict) -> Dict[str, Any]:
        """
        将审查通过的方案转化为标准化的NNG节点和记忆文件
        
        Returns:
            {"nngs": [...], "memories": [...], "parent_updates": [...]}
        """
        memory_counter = self.config.counters.memory_counter
        
        prompt = f"""你是DMN的整理Agent。将审查通过的方案转化为标准化的NNG节点和记忆文件。

【当前计数器】
- 下一个记忆ID：{memory_counter}

【输出格式】
【新增/修改NNG】
路径：nng/{{new_node_id}}.json
内容：
{{
"定位": "{{new_node_id}}",
"置信度": {{confidence_value}},
"时间": "{{current_timestamp}}",
"内容": "{{概念摘要}}",
"关联的记忆文件摘要": [
{{
"记忆ID": "{{memory_id}}",
"路径": "Y层记忆库/{{type}}/{{level}}/{{year}}/{{month}}/{{day}}/{{memory_id}}.txt",
"摘要": "{{summary}}",
"记忆类型": "{{type}}",
"价值层级": "{{level}}",
"置信度": {{confidence_value}}
}}
],
"上级关联NNG": [
{{
"节点ID": "{{parent_id}}",
"路径": "nng/{{parent_path}}/{{parent_id}}.json",
"关联程度": {{association_value}}
}}
],
"下级关联NNG": [
{{
"节点ID": "{{child_id}}",
"路径": "nng/{{new_node_id}}/{{child_id}}.json",
"关联程度": {{association_value}}
}}
]
}}

【新增/修改记忆】
路径：Y层记忆库/{{type}}/{{level}}/{{year}}/{{month}}/{{day}}/{{memory_id}}.txt
内容：
【记忆层级】：{{type}}
【记忆ID】：{{memory_id}}
【记忆时间】：{{timestamp}}
【置信度】：{{confidence_value}}
【核心内容】：
用户输入：{{content}}
AI响应：{{content}}
{{额外分析（高阶整合/元认知可添加）}}

【父节点更新】（如新增子节点）
路径：nng/{{parent_id}}.json
更新内容：在"下级关联NNG"中添加新节点

【输入】
审查通过的方案：{approved_analysis}
现有系统结构：{json.dumps(existing_structure, ensure_ascii=False)}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = self.llm.chat(messages)
        
        if not response.success:
            return {"nngs": [], "memories": [], "parent_updates": [], "error": response.error}
        
        # 解析输出（简化处理，实际应该更复杂的解析）
        return self._parse_organize_output(response.content)
    
    def _parse_organize_output(self, content: str) -> Dict[str, Any]:
        """解析整理Agent的输出"""
        # 这里简化处理，实际应该解析JSON
        return {
            "nngs": [],
            "memories": [],
            "parent_updates": [],
            "raw_output": content
        }


class DMNFormatReviewAgent:
    """DMN格式位置审查Agent"""
    
    def __init__(self):
        self.llm = get_llm_interface()
    
    def execute(self, organizer_output: Dict, existing_structure: Dict) -> Dict[str, Any]:
        """
        验证整理Agent的输出是否符合规范
        
        Returns:
            {"passed": bool, "final_action": "...", "fixes": [...]}
        """
        prompt = f"""你是DMN的格式位置审查Agent。验证整理Agent的输出是否符合规范。

【验证清单】
- [ ] NNG JSON格式正确（字段完整、类型正确）
- [ ] 路径符合层级规则（如1.2.3必须在1/1.2/1.2.3/下）
- [ ] 记忆ID唯一且正确（未与现有冲突）
- [ ] 时间戳格式正确（YYYY-MM-DD HH:MM:SS）
- [ ] 父节点已同步更新（新增子节点时）
- [ ] 关联路径可解析（无死链、无循环）
- [ ] 置信度范围合法（0-100）
- [ ] 文件命名符合规范（{{memory_id}}.txt、{{node_id}}.json）

【输出格式】
审查结论：{{通过 / 不通过}}
检查结果：
- 通过项：{{list}}
- 失败项：{{list}}，{{具体错误}}
修复建议：{{如何修改}}
最终操作：{{存入系统 / 替换文件 / 返回整理Agent}}

【输入】
待审查输出：{json.dumps(organizer_output, ensure_ascii=False)}
系统现有结构：{json.dumps(existing_structure, ensure_ascii=False)}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = self.llm.chat(messages)
        
        if not response.success:
            return {"passed": False, "final_action": "返回整理Agent", "fixes": [response.error]}
        
        content = response.content
        passed = "通过" in content and "不通过" not in content.split("审查结论：")[-1].split('\n')[0]
        
        return {
            "passed": passed,
            "final_action": "存入系统" if passed else "返回整理Agent",
            "fixes": [],
            "feedback": content
        }


class DMNSystem:
    """DMN维护系统主类"""
    
    def __init__(self):
        self.config = get_config()
        self.nng_manager = get_nng_manager()
        self.memory_manager = get_memory_manager()
        self.question_agent = DMNQuestionAgent()
        self.analysis_agent = DMNAnalysisAgent()
        self.review_agent = DMNReviewAgent()
        self.organize_agent = DMNOrganizeAgent()
        self.format_review_agent = DMNFormatReviewAgent()
        self.sandbox = ThreeLayerSandbox()
        self.task_counter = 0
    
    def create_task(self, task_type: DMNTaskType, priority: int = 1,
                   description: str = "") -> DMNTask:
        """创建DMN任务"""
        self.task_counter += 1
        return DMNTask(
            task_id=self.task_counter,
            task_type=task_type,
            priority=priority,
            description=description
        )
    
    def execute_task(self, task: DMNTask) -> Dict[str, Any]:
        """
        执行DMN任务（完整流程）
        
        所有子智能体的回复和输出必须经过X层三层沙盒走完全流程
        """
        task.status = "running"
        result = {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "success": False,
            "steps": []
        }
        
        try:
            # 1. 问题输出Agent
            print(f"[DMN] 任务{task.task_id}: 问题输出Agent执行中...")
            work_memories = self.memory_manager.get_work_memories()
            work_memories_dict = [
                {"id": m.memory_id, "content": m.user_input[:50]} 
                for m in work_memories[:5]
            ]
            
            question_result = self.question_agent.execute(
                task_type=task.task_type,
                work_memories=work_memories_dict,
                nav_fail_count=self.config.counters.nav_fail_counter,
                unprocessed_count=len(work_memories),
                idle_time=300
            )
            result["steps"].append({"agent": "question", "output": question_result})
            
            # 2. 读取路径内容
            path_contents = {}
            for path in question_result.get("paths", []):
                if path.startswith("nng/"):
                    node_id = path.replace("nng/", "").replace(".json", "")
                    content = self.nng_manager.read_node_raw(node_id)
                    if content:
                        path_contents[path] = content
                elif path.startswith("Y层记忆库/"):
                    content = self.memory_manager.read_memory_by_path(path)
                    if content:
                        path_contents[path] = content
            
            # 3. 问题分析Agent
            print(f"[DMN] 任务{task.task_id}: 问题分析Agent执行中...")
            analysis_result = self.analysis_agent.execute(
                paths=question_result.get("paths", []),
                path_contents=path_contents
            )
            result["steps"].append({"agent": "analysis", "output": analysis_result})
            
            # 4. 审查Agent
            print(f"[DMN] 任务{task.task_id}: 审查Agent执行中...")
            review_result = self.review_agent.execute(
                analysis_result=analysis_result,
                original_resources=path_contents
            )
            result["steps"].append({"agent": "review", "output": review_result})
            
            if not review_result.get("passed", False):
                result["success"] = False
                result["error"] = "审查未通过"
                task.status = "failed"
                return result
            
            # 5. 整理Agent
            print(f"[DMN] 任务{task.task_id}: 整理Agent执行中...")
            existing_structure = {
                "nng_nodes": self.nng_manager.list_all_nodes()[:10],
                "memory_count": len(self.memory_manager.list_memories(limit=1))
            }
            organize_result = self.organize_agent.execute(
                approved_analysis=analysis_result,
                existing_structure=existing_structure
            )
            result["steps"].append({"agent": "organize", "output": organize_result})
            
            # 6. 格式位置审查Agent
            print(f"[DMN] 任务{task.task_id}: 格式位置审查Agent执行中...")
            format_result = self.format_review_agent.execute(
                organizer_output=organize_result,
                existing_structure=existing_structure
            )
            result["steps"].append({"agent": "format_review", "output": format_result})
            
            result["success"] = format_result.get("passed", False)
            task.status = "completed" if result["success"] else "failed"
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            task.status = "failed"
        
        return result
    
    def run_maintenance(self) -> List[Dict[str, Any]]:
        """运行维护任务"""
        results = []
        
        # 检查工作记忆数量
        work_memories = self.memory_manager.get_work_memories()
        if len(work_memories) >= self.config.runtime.work_memory_threshold:
            task = self.create_task(
                DMNTaskType.MEMORY_INTEGRATION,
                priority=1,
                description="工作记忆数量超过阈值，执行记忆整合"
            )
            results.append(self.execute_task(task))
        
        # 检查导航失败次数
        if self.config.counters.nav_fail_counter >= self.config.runtime.fail_count_threshold:
            task = self.create_task(
                DMNTaskType.DEVIATION_REVIEW,
                priority=2,
                description="导航失败次数过多，执行偏差审查"
            )
            results.append(self.execute_task(task))
        
        return results


# 全局DMN系统实例
_dmn_system = None


def get_dmn_system() -> DMNSystem:
    """获取全局DMN系统"""
    global _dmn_system
    if _dmn_system is None:
        _dmn_system = DMNSystem()
    return _dmn_system
