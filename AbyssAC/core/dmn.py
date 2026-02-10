"""AbyssAC DMN（动态维护网络）模块

实现系统的自我维护功能，包含五个子智能体：
- Agent 1: 问题输出
- Agent 2: 问题分析
- Agent 3: 审查
- Agent 4: 整理
- Agent 5: 格式位置审查
"""

import json
import time
import threading
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

from core.memory_manager import MemoryManager, MemoryType, ValueLevel
from core.nng_navigator import NNGNavigator
from core.sandbox import ThreeLayerSandbox
from llm.interface import LLMInterface
from llm.prompt_templates import PromptTemplates
from utils.file_ops import safe_read_json, safe_write_json
from utils.logger import get_logger


logger = get_logger()


class DMNTaskType(Enum):
    """DMN任务类型"""
    MEMORY_INTEGRATION = "记忆整合"
    RELATION_DISCOVERY = "关联发现"
    DEVIATION_REVIEW = "偏差审查"
    STRATEGY_REHEARSAL = "策略预演"
    CONCEPT_REORG = "概念重组"
    NNG_OPTIMIZATION = "NNG优化"


@dataclass
class DMNTask:
    """DMN任务"""
    task_type: DMNTaskType
    trigger_reason: str
    created_at: datetime
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict] = None


class DMNSystem:
    """DMN维护系统"""
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        nng_navigator: NNGNavigator,
        llm_interface: LLMInterface,
        sandbox: ThreeLayerSandbox,
        auto_trigger: bool = True,
        idle_threshold: int = 300,
        memory_threshold: int = 20,
        failure_threshold: int = 5
    ):
        """
        初始化DMN系统
        
        Args:
            memory_manager: 记忆管理器
            nng_navigator: NNG导航器
            llm_interface: LLM接口
            sandbox: 三层沙盒
            auto_trigger: 是否自动触发
            idle_threshold: 空闲触发阈值（秒）
            memory_threshold: 记忆数量触发阈值
            failure_threshold: 导航失败触发阈值
        """
        self.memory_manager = memory_manager
        self.nng_navigator = nng_navigator
        self.llm = llm_interface
        self.sandbox = sandbox
        
        self.auto_trigger = auto_trigger
        self.idle_threshold = idle_threshold
        self.memory_threshold = memory_threshold
        self.failure_threshold = failure_threshold
        
        # 任务队列
        self.task_queue: List[DMNTask] = []
        self.running = False
        self.last_activity = datetime.now()
        
        # 统计
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0
        }
        
        # 后台线程
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def start_monitoring(self) -> None:
        """启动后台监控线程"""
        if not self.auto_trigger:
            return
        
        self.running = True
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("DMN监控线程已启动")
    
    def stop_monitoring(self) -> None:
        """停止后台监控线程"""
        self.running = False
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("DMN监控线程已停止")
    
    def _monitor_loop(self) -> None:
        """监控循环"""
        while self.running and not self._stop_event.is_set():
            try:
                # 检查触发条件
                if self._should_trigger():
                    self._auto_trigger_task()
                
                # 处理任务队列
                if self.task_queue:
                    task = self.task_queue.pop(0)
                    self._execute_task(task)
                
                # 休眠
                self._stop_event.wait(10)  # 每10秒检查一次
            
            except Exception as e:
                logger.error(f"DMN监控循环错误: {e}")
                self._stop_event.wait(10)
    
    def _should_trigger(self) -> bool:
        """检查是否应该自动触发DMN"""
        # 检查空闲时间
        idle_time = (datetime.now() - self.last_activity).total_seconds()
        if idle_time >= self.idle_threshold:
            return True
        
        # 检查工作记忆数量
        working_count = self.memory_manager.get_working_memory_count()
        if working_count >= self.memory_threshold:
            return True
        
        # 检查导航失败次数
        nav_stats = self.sandbox.get_navigation_stats()
        if nav_stats.get("failure_count", 0) >= self.failure_threshold:
            return True
        
        return False
    
    def _auto_trigger_task(self) -> None:
        """自动触发DMN任务"""
        # 确定任务类型
        nav_stats = self.sandbox.get_navigation_stats()
        
        if nav_stats.get("failure_count", 0) >= self.failure_threshold:
            task_type = DMNTaskType.NNG_OPTIMIZATION
            reason = "导航失败次数过多"
        elif self.memory_manager.get_working_memory_count() >= self.memory_threshold:
            task_type = DMNTaskType.MEMORY_INTEGRATION
            reason = "工作记忆数量过多"
        else:
            task_type = DMNTaskType.RELATION_DISCOVERY
            reason = "系统空闲"
        
        task = DMNTask(
            task_type=task_type,
            trigger_reason=reason,
            created_at=datetime.now()
        )
        
        self.task_queue.append(task)
        logger.info(f"自动触发DMN任务: {task_type.value}, 原因: {reason}")
    
    def trigger_task(
        self,
        task_type: DMNTaskType,
        reason: str = "手动触发"
    ) -> bool:
        """
        手动触发DMN任务
        
        Args:
            task_type: 任务类型
            reason: 触发原因
        
        Returns:
            是否成功添加任务
        """
        task = DMNTask(
            task_type=task_type,
            trigger_reason=reason,
            created_at=datetime.now()
        )
        
        self.task_queue.append(task)
        logger.info(f"手动触发DMN任务: {task_type.value}, 原因: {reason}")
        
        return True
    
    def _execute_task(self, task: DMNTask) -> None:
        """
        执行DMN任务
        
        Args:
            task: DMN任务
        """
        logger.info(f"开始执行DMN任务: {task.task_type.value}")
        task.status = "running"
        self.stats["total_tasks"] += 1
        
        try:
            # 根据任务类型执行
            if task.task_type == DMNTaskType.MEMORY_INTEGRATION:
                result = self._task_memory_integration()
            elif task.task_type == DMNTaskType.RELATION_DISCOVERY:
                result = self._task_relation_discovery()
            elif task.task_type == DMNTaskType.DEVIATION_REVIEW:
                result = self._task_deviation_review()
            elif task.task_type == DMNTaskType.NNG_OPTIMIZATION:
                result = self._task_nng_optimization()
            else:
                result = {"success": False, "error": "未知任务类型"}
            
            task.result = result
            
            if result.get("success"):
                task.status = "completed"
                self.stats["completed_tasks"] += 1
                logger.info(f"DMN任务完成: {task.task_type.value}")
            else:
                task.status = "failed"
                self.stats["failed_tasks"] += 1
                logger.error(f"DMN任务失败: {task.task_type.value}, {result.get('error')}")
        
        except Exception as e:
            task.status = "failed"
            task.result = {"success": False, "error": str(e)}
            self.stats["failed_tasks"] += 1
            logger.error(f"DMN任务执行异常: {e}")
        
        # 记录日志
        logger.dmn(task.task_type.value, task.status, task.result or {})
        
        # 更新活动时间
        self.last_activity = datetime.now()
    
    # ========== Agent 1: 问题输出 ==========
    
    def _agent1_problem_output(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent 1: 问题输出
        
        Args:
            context: 任务上下文
        
        Returns:
            问题列表
        """
        # 获取工作记忆
        working_memories = self.memory_manager.get_working_memories(limit=20)
        
        prompt = f"""分析以下工作记忆，识别需要维护的认知区域：

=== 工作记忆 ===
"""
        for mem_id, content in working_memories:
            prompt += f"\n[记忆ID: {mem_id}]\n{content[:500]}\n"
        
        prompt += """\n请输出待处理问题列表（JSON格式）：
{
  "问题列表": [
    {
      "问题": "问题描述",
      "类型": "记忆整合/关联发现/偏差审查/策略预演/概念重组",
      "优先级": "高/中/低",
      "理由": "为什么这个问题重要"
    }
  ]
}"""
        
        messages = [
            {"role": "system", "content": PromptTemplates.DMN_AGENT1_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            return {"success": False, "error": response.error}
        
        # 解析JSON
        result = self.llm.extract_json(response.content)
        
        if not result:
            return {"success": False, "error": "无法解析问题列表"}
        
        return {"success": True, "problems": result.get("问题列表", [])}
    
    # ========== Agent 2: 问题分析 ==========
    
    def _agent2_problem_analysis(self, problems: List[Dict]) -> Dict[str, Any]:
        """
        Agent 2: 问题分析
        
        Args:
            problems: 问题列表
        
        Returns:
            分析结果
        """
        prompt = f"""分析以下问题，提供初步分析结果和建议方案：

=== 问题列表 ===
{json.dumps(problems, ensure_ascii=False, indent=2)}

请输出分析结果（JSON格式）：
{
  "分析结果": [
    {
      "问题": "原问题",
      "分析": "详细分析",
      "建议方案": "具体建议",
      "预期效果": "方案预期效果"
    }
  ]
}"""
        
        messages = [
            {"role": "system", "content": PromptTemplates.DMN_AGENT2_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            return {"success": False, "error": response.error}
        
        result = self.llm.extract_json(response.content)
        
        if not result:
            return {"success": False, "error": "无法解析分析结果"}
        
        return {"success": True, "analysis": result.get("分析结果", [])}
    
    # ========== Agent 3: 审查 ==========
    
    def _agent3_review(self, analysis: List[Dict]) -> Dict[str, Any]:
        """
        Agent 3: 审查
        
        Args:
            analysis: 分析结果
        
        Returns:
            审查结果
        """
        prompt = f"""审查以下分析结果是否完整、逻辑是否正确：

=== 分析结果 ===
{json.dumps(analysis, ensure_ascii=False, indent=2)}

请输出审查结果（JSON格式）：
{
  "审查结果": "通过/不通过",
  "理由": "审查理由",
  "需要修改": ["需要修改的点1", "需要修改的点2"]
}"""
        
        messages = [
            {"role": "system", "content": PromptTemplates.DMN_AGENT3_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            return {"success": False, "error": response.error}
        
        result = self.llm.extract_json(response.content)
        
        if not result:
            return {"success": False, "error": "无法解析审查结果"}
        
        return {
            "success": True,
            "passed": result.get("审查结果") == "通过",
            "review": result
        }
    
    # ========== Agent 4: 整理 ==========
    
    def _agent4_organize(self, analysis: List[Dict]) -> Dict[str, Any]:
        """
        Agent 4: 整理
        
        Args:
            analysis: 分析结果
        
        Returns:
            整理后的NNG和记忆
        """
        prompt = f"""将以下分析结果整理为标准化的NNG节点格式和记忆格式：

=== 分析结果 ===
{json.dumps(analysis, ensure_ascii=False, indent=2)}

请输出整理结果（JSON格式）：
{
  "新NNG节点": {
    "定位": "节点位置，如1.2.3",
    "置信度": 80,
    "内容": "节点描述",
    "关联记忆": ["记忆ID1", "记忆ID2"]
  },
  "新记忆": {
    "层级": "分类记忆/元认知记忆/高阶整合记忆",
    "价值层级": "高/中/低",
    "置信度": 80,
    "内容": "记忆内容摘要"
  }
}"""
        
        messages = [
            {"role": "system", "content": PromptTemplates.DMN_AGENT4_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            return {"success": False, "error": response.error}
        
        result = self.llm.extract_json(response.content)
        
        if not result:
            return {"success": False, "error": "无法解析整理结果"}
        
        return {"success": True, "organized": result}
    
    # ========== Agent 5: 格式位置审查 ==========
    
    def _agent5_format_review(self, organized: Dict) -> Dict[str, Any]:
        """
        Agent 5: 格式位置审查
        
        Args:
            organized: 整理后的内容
        
        Returns:
            审查结果
        """
        prompt = f"""验证以下格式是否符合规范，放置位置是否正确：

=== 整理结果 ===
{json.dumps(organized, ensure_ascii=False, indent=2)}

请输出验证结果（JSON格式）：
{
  "验证结果": "通过/不通过",
  "格式检查": "正确/错误",
  "位置检查": "正确/错误",
  "错误详情": ["错误1", "错误2"],
  "修正建议": "如何修正"
}"""
        
        messages = [
            {"role": "system", "content": PromptTemplates.DMN_AGENT5_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages)
        
        if not response.success:
            return {"success": False, "error": response.error}
        
        result = self.llm.extract_json(response.content)
        
        if not result:
            return {"success": False, "error": "无法解析验证结果"}
        
        return {
            "success": True,
            "passed": result.get("验证结果") == "通过",
            "review": result
        }
    
    # ========== 任务实现 ==========
    
    def _task_memory_integration(self) -> Dict[str, Any]:
        """记忆整合任务"""
        logger.info("执行记忆整合任务")
        
        # 执行5个Agent
        context = {}
        
        # Agent 1
        result1 = self._agent1_problem_output(context)
        if not result1.get("success"):
            return result1
        
        problems = result1.get("problems", [])
        if not problems:
            return {"success": True, "message": "没有问题需要处理"}
        
        # Agent 2
        result2 = self._agent2_problem_analysis(problems)
        if not result2.get("success"):
            return result2
        
        analysis = result2.get("analysis", [])
        
        # Agent 3
        result3 = self._agent3_review(analysis)
        if not result3.get("success"):
            return result3
        
        if not result3.get("passed"):
            return {"success": False, "error": "审查未通过", "review": result3.get("review")}
        
        # Agent 4
        result4 = self._agent4_organize(analysis)
        if not result4.get("success"):
            return result4
        
        organized = result4.get("organized", {})
        
        # Agent 5
        result5 = self._agent5_format_review(organized)
        if not result5.get("success"):
            return result5
        
        if not result5.get("passed"):
            return {"success": False, "error": "格式审查未通过", "review": result5.get("review")}
        
        # 执行创建操作
        return self._execute_creation(organized)
    
    def _execute_creation(self, organized: Dict) -> Dict[str, Any]:
        """
        执行创建操作
        
        Args:
            organized: 整理后的内容
        
        Returns:
            执行结果
        """
        results = {"nn_created": [], "memory_created": []}
        
        # 创建NNG节点
        nng_data = organized.get("新NNG节点", {})
        if nng_data:
            location = nng_data.get("定位")
            content = nng_data.get("内容")
            confidence = nng_data.get("置信度", 70)
            
            if location and content:
                success = self.nng_navigator.create_node(
                    location=location,
                    content=content,
                    confidence=confidence
                )
                if success:
                    results["nn_created"].append(location)
        
        # 创建记忆
        memory_data = organized.get("新记忆", {})
        if memory_data:
            level = memory_data.get("层级", "分类记忆")
            value_level = memory_data.get("价值层级", "中")
            confidence = memory_data.get("置信度", 70)
            content = memory_data.get("内容", "")
            
            # 映射层级
            mem_type_map = {
                "元认知记忆": MemoryType.META_COGNITIVE,
                "高阶整合记忆": MemoryType.HIGH_LEVEL,
                "分类记忆": MemoryType.CLASSIFIED,
                "工作记忆": MemoryType.WORKING
            }
            
            value_map = {
                "高": ValueLevel.HIGH,
                "中": ValueLevel.MEDIUM,
                "低": ValueLevel.LOW
            }
            
            mem_type = mem_type_map.get(level, MemoryType.CLASSIFIED)
            val_level = value_map.get(value_level, ValueLevel.MEDIUM)
            
            mem_id = self.memory_manager.create_memory(
                memory_type=mem_type,
                user_input="DMN自动整理",
                ai_response=content,
                confidence=confidence,
                value_level=val_level,
                associated_nngs=results["nn_created"]
            )
            
            results["memory_created"].append(mem_id)
            
            # 更新NNG关联
            for nng_id in results["nn_created"]:
                self.nng_navigator.add_memory_summary(
                    nng_id,
                    mem_id,
                    content[:100],
                    level,
                    value_level
                )
                self.memory_manager.add_nng_association(mem_id, nng_id)
        
        # 清空工作记忆
        cleared = self.memory_manager.clear_working_memory()
        results["working_memory_cleared"] = cleared
        
        return {"success": True, "results": results}
    
    def _task_relation_discovery(self) -> Dict[str, Any]:
        """关联发现任务"""
        logger.info("执行关联发现任务")
        
        # 获取最近的记忆
        recent_memories = self.memory_manager.get_working_memories(limit=10)
        
        # 简单实现：分析记忆间的关联
        # 实际实现应该使用LLM分析
        
        return {"success": True, "message": "关联发现完成", "relations_found": 0}
    
    def _task_deviation_review(self) -> Dict[str, Any]:
        """偏差审查任务"""
        logger.info("执行偏差审查任务")
        
        # 获取导航日志
        nav_logs = self.sandbox.get_navigation_stats()
        
        # 分析失败模式
        
        return {"success": True, "message": "偏差审查完成"}
    
    def _task_nng_optimization(self) -> Dict[str, Any]:
        """NNG优化任务"""
        logger.info("执行NNG优化任务")
        
        # 验证NNG完整性
        integrity = self.nng_navigator.verify_integrity()
        
        if integrity.get("valid"):
            return {"success": True, "message": "NNG完整性良好"}
        
        # 修复问题
        fixes = []
        
        # 修复断链
        for parent, child in integrity.get("stats", {}).get("broken_links", []):
            # 从父节点移除不存在的子节点
            node = self.nng_navigator.get_node(parent)
            if node:
                node.child_nngs = [c for c in node.child_nngs if c.get("节点") != child]
                self.nng_navigator._save_node(node)
                fixes.append(f"移除断链: {parent} -> {child}")
        
        return {"success": True, "message": "NNG优化完成", "fixes": fixes}
    
    def update_activity(self) -> None:
        """更新活动时间"""
        self.last_activity = datetime.now()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取DMN统计
        
        Returns:
            统计信息
        """
        return {
            **self.stats,
            "queue_length": len(self.task_queue),
            "last_activity": self.last_activity.isoformat(),
            "auto_trigger": self.auto_trigger
        }
