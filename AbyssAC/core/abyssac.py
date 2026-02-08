"""
AbyssAC 主控制器
整合所有模块，提供统一接口
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import threading

from core.config import get_config, SystemConfig
from llm.llm_interface import LLMInterface, ContextManager
from memory.memory_manager import MemoryManager, MemoryType, ValueLevel
from nng.nng_manager import NNGManager
from sandbox.sandbox_layer import SandboxLayer
from dmn.dmn_agents import DMNController, DMNTaskType


class AbyssAC:
    """
    AbyssAC主控制器
    整合X层沙盒、Y层记忆、NNG导航、DMN维护
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        """
        初始化AbyssAC系统
        
        Args:
            config: 系统配置，如果为None则加载默认配置
        """
        print("=" * 60)
        print("AbyssAC 系统初始化")
        print("=" * 60)
        
        # 加载配置
        self.config = config or get_config()
        
        # 初始化LLM接口
        print("\n[初始化] LLM接口...")
        self.llm = LLMInterface(
            use_local=self.config.llm.use_local,
            ollama_base_url=self.config.llm.ollama_base_url,
            ollama_model=self.config.llm.ollama_model,
            api_base_url=self.config.llm.api_base_url,
            api_key=self.config.llm.api_key,
            api_model=self.config.llm.api_model,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
            timeout=self.config.llm.timeout
        )
        
        # 初始化记忆管理器
        print("[初始化] Y层记忆库...")
        self.memory = MemoryManager(
            base_path=self.config.memory.base_path,
            id_counter_file=self.config.memory.id_counter_file
        )
        
        # 初始化NNG管理器
        print("[初始化] NNG导航图...")
        self.nng = NNGManager(
            base_path=self.config.nng.base_path,
            root_file=self.config.nng.root_file
        )
        
        # 初始化沙盒层
        print("[初始化] X层沙盒...")
        self.sandbox = SandboxLayer(self.llm, self.nng, self.memory)
        
        # 初始化DMN控制器
        print("[初始化] DMN维护网络...")
        self.dmn = DMNController(self.llm, self.nng, self.memory)
        
        # 上下文管理器
        self.context = ContextManager(max_history=10)
        
        # 系统状态
        self.system_state = {
            'initialized': True,
            'bootstrap_stage': self._determine_bootstrap_stage(),
            'total_conversations': 0,
            'last_dmn_time': None,
            'navigation_failures': 0
        }
        
        # 导航日志目录
        self.nav_logs_dir = Path(self.config.dmn.navigation_logs_dir)
        self.nav_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # DMN触发锁
        self.dmn_lock = threading.Lock()
        self.dmn_running = False
        
        print("\n" + "=" * 60)
        print(f"AbyssAC 初始化完成")
        print(f"  - Bootstrap阶段: {self.system_state['bootstrap_stage']}")
        print(f"  - NNG为空: {self.nng.is_nng_empty()}")
        print(f"  - 工作记忆数: {self.memory.count_working_memories()}")
        print("=" * 60)
    
    def _determine_bootstrap_stage(self) -> str:
        """确定当前Bootstrap阶段"""
        if self.nng.is_nng_empty():
            return "阶段1_NNG为空"
        elif self.memory.count_working_memories() < self.config.dmn.working_memory_threshold:
            return "阶段2_初始化中"
        else:
            return "阶段3_正常运行"
    
    def chat(self, user_input: str) -> str:
        """
        用户聊天接口
        
        Args:
            user_input: 用户输入
            
        Returns:
            AI回复
        """
        print(f"\n{'='*60}")
        print(f"[对话] 用户: {user_input[:50]}...")
        print(f"{'='*60}")
        
        # 更新系统状态
        self.system_state['total_conversations'] += 1
        
        # 获取当前工作记忆
        working_memories = self.memory.get_working_memories(limit=10)
        
        # 根据Bootstrap阶段决定处理流程
        stage = self.system_state['bootstrap_stage']
        
        if stage == "阶段1_NNG为空":
            # Bootstrap阶段1：NNG为空，跳过沙盒，直接回复
            response = self._stage1_process(user_input, working_memories)
        else:
            # Bootstrap阶段2/3：使用X层三层沙盒
            response = self._stage3_process(user_input, working_memories)
        
        # 保存对话到工作记忆
        self._save_conversation(user_input, response)
        
        # 更新Bootstrap阶段
        self.system_state['bootstrap_stage'] = self._determine_bootstrap_stage()
        
        # 检查DMN触发条件
        self._check_dmn_triggers()
        
        return response
    
    def _stage1_process(self, user_input: str, 
                        working_memories: List) -> str:
        """
        Bootstrap阶段1处理：NNG为空，直接回复
        """
        print("\n[Bootstrap] 阶段1：NNG为空，跳过沙盒直接回复")
        
        # 构建简单提示
        context = ""
        if working_memories:
            context = "最近的对话:\n"
            for mem in working_memories[-3:]:
                context += f"- {mem.content[:100]}...\n"
        
        prompt = f"""{context}

用户: {user_input}

请回复用户的问题。
"""
        
        response = self.llm.simple_chat(
            prompt,
            system_prompt="你是一个有帮助的AI助手。"
        )
        
        return response
    
    def _stage3_process(self, user_input: str,
                        working_memories: List) -> str:
        """
        Bootstrap阶段3处理：使用X层三层沙盒
        """
        print("\n[Bootstrap] 阶段3：使用X层三层沙盒")
        
        # 执行三层沙盒
        sandbox_result = self.sandbox.process(user_input, working_memories)
        
        # 记录导航日志
        if sandbox_result.get('navigation_result'):
            self._log_navigation(user_input, sandbox_result['navigation_result'])
        
        # 更新导航失败计数
        nav_failures = self.sandbox.get_navigation_failure_count()
        self.system_state['navigation_failures'] = nav_failures
        
        # 构建最终提示
        context = sandbox_result.get('context', '')
        
        prompt = f"""{context}

基于以上上下文，请回答用户的问题:
{user_input}
"""
        
        response = self.llm.simple_chat(
            prompt,
            system_prompt="你是一个智能助手，基于提供的上下文回答用户问题。"
        )
        
        return response
    
    def _save_conversation(self, user_input: str, response: str):
        """保存对话到工作记忆"""
        # 保存用户输入
        self.memory.save_memory(
            content=f"用户: {user_input}",
            memory_type=MemoryType.WORKING
        )
        
        # 保存AI回复
        self.memory.save_memory(
            content=f"AI: {response}",
            memory_type=MemoryType.WORKING
        )
        
        # 更新上下文管理器
        self.context.add_message("user", user_input)
        self.context.add_message("assistant", response)
        
        print(f"[记忆] 对话已保存到工作记忆")
    
    def _log_navigation(self, user_input: str, nav_result):
        """记录导航日志"""
        log_entry = {
            "时间戳": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "用户输入": user_input[:100],
            "导航路径": nav_result.navigation_path,
            "最终节点": nav_result.selected_nodes,
            "导航步数": len(nav_result.steps),
            "每步决策": nav_result.steps,
            "成功": nav_result.success,
            "失败原因": nav_result.failure_reason
        }
        
        log_file = self.nav_logs_dir / f"nav_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def _check_dmn_triggers(self):
        """检查DMN触发条件"""
        with self.dmn_lock:
            if self.dmn_running:
                return
            
            should_trigger = False
            trigger_reason = ""
            task_type = DMNTaskType.MEMORY_INTEGRATION
            
            # 条件1：工作记忆数量超过阈值
            working_count = self.memory.count_working_memories()
            if working_count >= self.config.dmn.working_memory_threshold:
                should_trigger = True
                trigger_reason = f"工作记忆数量({working_count})超过阈值"
            
            # 条件2：导航失败次数超过阈值
            nav_failures = self.system_state['navigation_failures']
            if nav_failures >= self.config.dmn.navigation_failure_threshold:
                should_trigger = True
                trigger_reason = f"导航失败次数({nav_failures})超过阈值"
                task_type = DMNTaskType.NNG_OPTIMIZATION
            
            if should_trigger:
                print(f"\n[DMN] 触发条件满足: {trigger_reason}")
                self.dmn_running = True
                
                # 在后台线程执行DMN
                threading.Thread(
                    target=self._run_dmn,
                    args=(task_type,),
                    daemon=True
                ).start()
    
    def _run_dmn(self, task_type: DMNTaskType):
        """运行DMN任务"""
        try:
            print(f"\n[DMN] 启动任务: {task_type.value}")
            
            # 获取工作记忆
            working_memories = self.memory.get_working_memories(limit=20)
            
            # 获取导航日志（如果是优化任务）
            navigation_logs = []
            if task_type == DMNTaskType.NNG_OPTIMIZATION:
                navigation_logs = self._load_recent_navigation_logs(10)
            
            # 构建系统状态
            system_state = {
                'working_memory_count': len(working_memories),
                'nng_node_count': len(self.nng.get_all_node_ids()),
                'navigation_failures': self.system_state['navigation_failures']
            }
            
            # 执行DMN
            if task_type == DMNTaskType.NNG_OPTIMIZATION:
                result = self.dmn.optimize_nng_structure(
                    navigation_logs,
                    self.system_state['navigation_failures']
                )
            else:
                result = self.dmn.execute(
                    task_type=task_type,
                    working_memories=working_memories,
                    system_state=system_state
                )
            
            # 处理结果
            if result.success:
                print(f"[DMN] 任务完成:")
                print(f"  - 新记忆: {len(result.new_memories)}条")
                print(f"  - 新NNG节点: {len(result.new_nng_nodes)}个")
                
                # 重置导航失败计数
                if task_type == DMNTaskType.NNG_OPTIMIZATION:
                    self.sandbox.reset_navigation_failure_count()
                    self.system_state['navigation_failures'] = 0
                
                # 更新Bootstrap阶段
                self.system_state['bootstrap_stage'] = self._determine_bootstrap_stage()
            else:
                print(f"[DMN] 任务失败: {result.error}")
            
            self.system_state['last_dmn_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        except Exception as e:
            print(f"[DMN] 任务异常: {e}")
        finally:
            self.dmn_running = False
    
    def _load_recent_navigation_logs(self, limit: int = 10) -> List[Dict]:
        """加载最近的导航日志"""
        logs = []
        
        # 获取最近的日志文件
        log_files = sorted(self.nav_logs_dir.glob("nav_*.jsonl"), reverse=True)
        
        for log_file in log_files[:3]:  # 最多读3个文件
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        logs.append(json.loads(line.strip()))
                        if len(logs) >= limit:
                            break
            except Exception as e:
                print(f"[日志] 读取失败 {log_file}: {e}")
        
        return logs[-limit:] if len(logs) > limit else logs
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'bootstrap_stage': self.system_state['bootstrap_stage'],
            'total_conversations': self.system_state['total_conversations'],
            'working_memory_count': self.memory.count_working_memories(),
            'nng_node_count': len(self.nng.get_all_node_ids()),
            'navigation_failures': self.system_state['navigation_failures'],
            'last_dmn_time': self.system_state['last_dmn_time'],
            'dmn_running': self.dmn_running,
            'llm_provider': self.llm.provider.value,
            'llm_model': self.llm.ollama_model if self.llm.use_local else self.llm.api_model
        }
    
    def manual_trigger_dmn(self, task_type: str = "memory_integration") -> str:
        """
        手动触发DMN任务
        
        Args:
            task_type: 任务类型
            
        Returns:
            执行结果消息
        """
        task_map = {
            'memory_integration': DMNTaskType.MEMORY_INTEGRATION,
            'association_discovery': DMNTaskType.ASSOCIATION_DISCOVERY,
            'bias_review': DMNTaskType.BIAS_REVIEW,
            'strategy_rehearsal': DMNTaskType.STRATEGY_REHEARSAL,
            'concept_recombination': DMNTaskType.CONCEPT_RECOMBINATION,
            'nng_optimization': DMNTaskType.NNG_OPTIMIZATION
        }
        
        task = task_map.get(task_type, DMNTaskType.MEMORY_INTEGRATION)
        
        with self.dmn_lock:
            if self.dmn_running:
                return "DMN任务正在运行中，请稍后再试"
            
            self.dmn_running = True
        
        # 同步执行DMN
        try:
            working_memories = self.memory.get_working_memories(limit=20)
            system_state = {
                'working_memory_count': len(working_memories),
                'nng_node_count': len(self.nng.get_all_node_ids()),
                'navigation_failures': self.system_state['navigation_failures']
            }
            
            result = self.dmn.execute(task, working_memories, system_state)
            
            if result.success:
                return f"DMN任务完成: 新建{len(result.new_memories)}条记忆, {len(result.new_nng_nodes)}个NNG节点"
            else:
                return f"DMN任务失败: {result.error}"
                
        except Exception as e:
            return f"DMN任务异常: {e}"
        finally:
            self.dmn_running = False
    
    def clear_working_memory(self) -> str:
        """清空工作记忆"""
        # 获取所有工作记忆ID
        working_ids = self.memory.get_all_memory_ids()
        
        # 删除工作记忆（简化实现，实际应该只删除工作记忆类型）
        # 这里仅返回提示
        return f"工作记忆清空功能需要谨慎实现，当前工作记忆数量: {self.memory.count_working_memories()}"


if __name__ == "__main__":
    # 自测
    print("=" * 60)
    print("AbyssAC主控制器自测")
    print("=" * 60)
    
    import tempfile
    import shutil
    
    test_dir = tempfile.mkdtemp(prefix="abyssac_main_test_")
    print(f"\n测试目录: {test_dir}")
    
    try:
        # 创建配置
        from core.config import SystemConfig, LLMConfig, MemoryConfig, NNGConfig, DMNConfig
        
        config = SystemConfig(
            llm=LLMConfig(
                use_local=True,
                ollama_model="qwen2.5:7b"
            ),
            memory=MemoryConfig(
                base_path=f"{test_dir}/Y层记忆库"
            ),
            nng=NNGConfig(
                base_path=f"{test_dir}/NNG"
            ),
            dmn=DMNConfig(
                working_memory_threshold=5  # 降低阈值以便测试
            )
        )
        
        # 初始化AbyssAC
        print("\n初始化AbyssAC系统...")
        ac = AbyssAC(config)
        
        print(f"\n[✓] 系统状态: {ac.get_system_status()}")
        
        # 测试对话
        print("\n测试对话...")
        response = ac.chat("你好，请介绍一下自己")
        print(f"[✓] 回复: {response[:100]}...")
        
        # 测试多轮对话
        for i in range(3):
            response = ac.chat(f"测试消息 {i+1}")
            print(f"[✓] 对话 {i+2} 完成")
        
        # 检查系统状态
        status = ac.get_system_status()
        print(f"\n[✓] 最终状态:")
        print(f"  - 对话总数: {status['total_conversations']}")
        print(f"  - 工作记忆: {status['working_memory_count']}")
        print(f"  - NNG节点: {status['nng_node_count']}")
        print(f"  - 当前阶段: {status['bootstrap_stage']}")
        
        print("\n" + "=" * 60)
        print("AbyssAC主控制器自测通过")
        print("=" * 60)
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
        print(f"\n已清理测试目录")
