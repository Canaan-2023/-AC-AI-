"""
AbyssAC DMN（默认模式网络）模块
实现5个子智能体和任务管理
"""

import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field

from storage import StorageManager
from llm_client import LLMClient, PromptLoader, InstructionParser


class DMNTaskType(Enum):
    """DMN任务类型"""
    MEMORY_INTEGRATION = "memory"      # 记忆整合任务
    ASSOCIATION_DISCOVERY = "assoc"    # 关联发现任务
    BIAS_REVIEW = "bias"               # 偏差审查任务
    STRATEGY_REHEARSAL = "strategy"    # 策略预演任务
    CONCEPT_RECOMBINATION = "concept"  # 概念重组任务


@dataclass
class DMNTask:
    """DMN任务"""
    task_type: DMNTaskType
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed
    progress: int = 0  # 0-100
    current_agent: int = 0  # 当前执行的agent (1-5)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DMNAgent:
    """DMN子智能体基类"""
    
    def __init__(self, llm_client: LLMClient, agent_number: int):
        self.llm = llm_client
        self.agent_number = agent_number
    
    async def execute(self, task: DMNTask, 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """执行agent任务"""
        raise NotImplementedError


class Agent1ProblemOutput(DMNAgent):
    """子智能体一：问题输出agent"""
    
    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, 1)
    
    async def execute(self, task: DMNTask, 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """识别需要维护的认知区域"""
        
        # 获取工作记忆
        work_memories = context.get("work_memories", [])
        work_memories_formatted = "\n".join([
            f"- ID: {m.get('id')}, 内容: {m.get('content', '')[:100]}..."
            for m in work_memories[:10]  # 最多10条
        ]) if work_memories else "（无工作记忆）"
        
        prompt = PromptLoader.load_prompt(
            "dmn_agent1",
            task_type=task.task_type.value,
            working_memory_count=len(work_memories),
            navigation_failures=context.get("navigation_failures", 0),
            work_memories=work_memories_formatted
        )
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm.chat(messages)
        
        # 解析问题列表
        questions = [q.strip() for q in response.split('\n') if q.strip()]
        
        return {
            "questions": questions,
            "raw_response": response
        }


class Agent2ProblemAnalysis(DMNAgent):
    """子智能体二：问题分析agent"""
    
    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, 2)
    
    async def execute(self, task: DMNTask, 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """分析问题并给出建议"""
        
        agent1_result = context.get("agent1_result", {})
        questions = agent1_result.get("questions", [])
        
        work_memories = context.get("work_memories", [])
        work_memories_formatted = "\n".join([
            f"- {m.get('content', '')[:150]}..."
            for m in work_memories[:5]
        ]) if work_memories else "（无工作记忆）"
        
        prompt = PromptLoader.load_prompt(
            "dmn_agent2",
            task_type=task.task_type.value,
            questions="\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)]),
            work_memories=work_memories_formatted
        )
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm.chat(messages)
        
        return {
            "analysis": response,
            "questions": questions
        }


class Agent3Review(DMNAgent):
    """子智能体三：审查agent"""
    
    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, 3)
    
    async def execute(self, task: DMNTask, 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """审查分析结果"""
        
        agent2_result = context.get("agent2_result", {})
        analysis = agent2_result.get("analysis", "")
        
        prompt = PromptLoader.load_prompt(
            "dmn_agent3",
            task_type=task.task_type.value,
            analysis_result=analysis
        )
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm.chat(messages)
        
        approved = "APPROVED" in response.upper()
        
        return {
            "approved": approved,
            "review_result": response,
            "needs_revision": not approved
        }


class Agent4Organize(DMNAgent):
    """子智能体四：整理agent"""
    
    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, 4)
    
    async def execute(self, task: DMNTask, 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """整理为标准格式"""
        
        agent2_result = context.get("agent2_result", {})
        analysis = agent2_result.get("analysis", "")
        
        prompt = PromptLoader.load_prompt(
            "dmn_agent4",
            task_type=task.task_type.value,
            analysis_result=analysis
        )
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm.chat(messages)
        
        # 解析指令
        instructions = InstructionParser.parse_dmn_instruction(response)
        
        return {
            "formatted_output": response,
            "instructions": instructions
        }


class Agent5FormatVerify(DMNAgent):
    """子智能体五：格式位置审查agent"""
    
    def __init__(self, llm_client: LLMClient):
        super().__init__(llm_client, 5)
    
    async def execute(self, task: DMNTask, 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """验证格式和位置"""
        
        agent4_result = context.get("agent4_result", {})
        formatted = agent4_result.get("formatted_output", "")
        
        prompt = PromptLoader.load_prompt(
            "dmn_agent5",
            task_type=task.task_type.value,
            formatted_output=formatted
        )
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm.chat(messages)
        
        verified = "VERIFIED" in response.upper()
        
        return {
            "verified": verified,
            "verification_result": response
        }


class DMN:
    """DMN管理器"""
    
    def __init__(self):
        self.llm = LLMClient()
        self.is_running = False
        self.current_task: Optional[DMNTask] = None
        self.lock = threading.Lock()
        
        # 初始化agents
        self.agents = {
            1: Agent1ProblemOutput(self.llm),
            2: Agent2ProblemAnalysis(self.llm),
            3: Agent3Review(self.llm),
            4: Agent4Organize(self.llm),
            5: Agent5FormatVerify(self.llm)
        }
        
        # 任务循环索引（用于空闲时的循环任务）
        self._cycle_index = 0
        self._cycle_tasks = [
            DMNTaskType.ASSOCIATION_DISCOVERY,
            DMNTaskType.CONCEPT_RECOMBINATION,
            DMNTaskType.STRATEGY_REHEARSAL
        ]
    
    def run_task(self, task_type: DMNTaskType, 
                 context: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行DMN任务（同步接口）
        
        Args:
            task_type: 任务类型
            context: 任务上下文
        
        Returns:
            任务结果
        """
        with self.lock:
            if self.is_running:
                return {"error": "DMN正在执行任务，请稍后", "status": "busy"}
            
            self.is_running = True
            self.current_task = DMNTask(task_type=task_type)
        
        try:
            result = asyncio.run(self._execute_agents(task_type, context))
            
            with self.lock:
                self.current_task.status = "completed"
                self.current_task.completed_at = datetime.now()
                self.current_task.result = result
            
            # 记录日志
            StorageManager.write_dmn_log(
                task_type.value,
                {
                    "task_type": task_type.value,
                    "started_at": self.current_task.started_at.isoformat() if self.current_task.started_at else None,
                    "completed_at": self.current_task.completed_at.isoformat(),
                    "result": result
                }
            )
            
            return result
        
        except Exception as e:
            with self.lock:
                self.current_task.status = "failed"
                self.current_task.error = str(e)
            
            StorageManager.write_error_log({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "DMN_TASK_FAILED",
                "task_type": task_type.value,
                "error": str(e)
            })
            
            return {"error": str(e), "status": "failed"}
        
        finally:
            with self.lock:
                self.is_running = False
    
    async def _execute_agents(self, task_type: DMNTaskType,
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """执行5个agent流程"""
        
        agent_context = context.copy()
        max_retries = 2
        
        # Agent 1: 问题输出
        self.current_task.started_at = datetime.now()
        self.current_task.current_agent = 1
        self.current_task.progress = 10
        
        agent1_result = await self.agents[1].execute(self.current_task, agent_context)
        agent_context["agent1_result"] = agent1_result
        
        # Agent 2: 问题分析
        self.current_task.current_agent = 2
        self.current_task.progress = 30
        
        agent2_result = await self.agents[2].execute(self.current_task, agent_context)
        agent_context["agent2_result"] = agent2_result
        
        # Agent 3: 审查（可能重试）
        for attempt in range(max_retries):
            self.current_task.current_agent = 3
            self.current_task.progress = 50
            
            agent3_result = await self.agents[3].execute(self.current_task, agent_context)
            
            if agent3_result.get("approved", False):
                break
            
            # 需要修改，重新执行agent 1或2
            if attempt < max_retries - 1:
                # 简化处理：重新执行agent 2
                agent2_result = await self.agents[2].execute(self.current_task, agent_context)
                agent_context["agent2_result"] = agent2_result
        
        agent_context["agent3_result"] = agent3_result
        
        # Agent 4: 整理
        self.current_task.current_agent = 4
        self.current_task.progress = 70
        
        agent4_result = await self.agents[4].execute(self.current_task, agent_context)
        agent_context["agent4_result"] = agent4_result
        
        # Agent 5: 格式验证（可能重试）
        for attempt in range(max_retries):
            self.current_task.current_agent = 5
            self.current_task.progress = 90
            
            agent5_result = await self.agents[5].execute(self.current_task, agent_context)
            
            if agent5_result.get("verified", False):
                break
            
            # 需要重新整理
            if attempt < max_retries - 1:
                agent4_result = await self.agents[4].execute(self.current_task, agent_context)
                agent_context["agent4_result"] = agent4_result
        
        agent_context["agent5_result"] = agent5_result
        
        # 执行实际操作
        if agent5_result.get("verified", False):
            await self._execute_instructions(agent4_result.get("instructions", []))
        
        self.current_task.progress = 100
        
        return {
            "task_type": task_type.value,
            "status": "completed",
            "agent_results": {
                "agent1": agent1_result,
                "agent2": agent2_result,
                "agent3": agent3_result,
                "agent4": agent4_result,
                "agent5": agent5_result
            }
        }
    
    async def _execute_instructions(self, instructions: List[Dict[str, Any]]):
        """执行DMN生成的指令"""
        import json
        
        for instr in instructions:
            action = instr.get("action")
            
            if action == "ADD_NNG":
                nng_id = instr.get("nng_id")
                content = instr.get("content", "")
                
                try:
                    nng_data = json.loads(content)
                    StorageManager.write_nng(nng_id, nng_data)
                    
                    # 更新父节点
                    parent_id = StorageManager.get_parent_nng_id(nng_id)
                    if parent_id and parent_id != "root":
                        parent_data = StorageManager.read_nng(parent_id)
                        if parent_data:
                            if "下级关联NNG" not in parent_data:
                                parent_data["下级关联NNG"] = []
                            parent_data["下级关联NNG"].append({
                                "名称": nng_id,
                                "摘要": nng_data.get("内容", "")[:50],
                                "关联记忆": [m.get("记忆ID") for m in nng_data.get("关联的记忆文件摘要", [])],
                                "关联程度": 80
                            })
                            StorageManager.write_nng(parent_id, parent_data)
                    
                    # 更新root.json
                    if '.' not in nng_id:
                        root_data = StorageManager.read_nng("root")
                        if nng_id not in root_data.get("一级节点", []):
                            root_data["一级节点"].append(nng_id)
                            root_data["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            StorageManager.write_nng("root", root_data)
                
                except Exception as e:
                    print(f"新增NNG失败: {e}")
            
            elif action == "MODIFY_NNG":
                nng_id = instr.get("nng_id")
                content = instr.get("content", "")
                
                try:
                    nng_data = json.loads(content)
                    StorageManager.write_nng(nng_id, nng_data)
                except Exception as e:
                    print(f"修改NNG失败: {e}")
            
            elif action == "DELETE_NNG":
                nng_id = instr.get("nng_id")
                StorageManager.delete_nng(nng_id)
            
            elif action == "ADD_MEMORY":
                memory_type = instr.get("memory_type", "分类记忆")
                value_tier = instr.get("value_tier")
                content = instr.get("content", "")
                
                memory_id = StorageManager.allocate_memory_id()
                StorageManager.write_memory(memory_id, content, memory_type, value_tier)
    
    def get_status(self) -> Dict[str, Any]:
        """获取DMN状态"""
        with self.lock:
            if not self.current_task:
                return {
                    "is_running": False,
                    "current_task": None,
                    "progress": 0
                }
            
            return {
                "is_running": self.is_running,
                "current_task": {
                    "type": self.current_task.task_type.value,
                    "status": self.current_task.status,
                    "progress": self.current_task.progress,
                    "current_agent": self.current_task.current_agent
                }
            }
    
    def check_auto_trigger(self, working_memory_count: int,
                           navigation_failures: int,
                           last_activity: datetime) -> Optional[DMNTaskType]:
        """
        检查是否应该自动触发DMN任务
        
        Returns:
            应该执行的任务类型，或None
        """
        # 未处理工作记忆 > 20条
        if working_memory_count > 20:
            return DMNTaskType.MEMORY_INTEGRATION
        
        # 近期导航失败次数 > 5次
        if navigation_failures > 5:
            return DMNTaskType.BIAS_REVIEW
        
        # 系统空闲时间 > 5分钟
        idle_time = datetime.now() - last_activity
        if idle_time > timedelta(seconds=300):
            if working_memory_count > 0:
                return DMNTaskType.MEMORY_INTEGRATION
            elif navigation_failures > 0:
                return DMNTaskType.BIAS_REVIEW
            else:
                # 循环执行其他任务
                task = self._cycle_tasks[self._cycle_index]
                self._cycle_index = (self._cycle_index + 1) % len(self._cycle_tasks)
                return task
        
        return None
