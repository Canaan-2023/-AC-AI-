"""AbyssAC 主程序入口

系统启动、初始化和主交互循环。
"""

import json
import os
import sys
import time
import signal
from datetime import datetime
from typing import Dict, Any, Optional

from config import get_config
from utils.logger import get_logger
from utils.file_ops import safe_read_json, safe_write_json
from core.memory_manager import MemoryManager, MemoryType, ValueLevel
from core.nng_navigator import NNGNavigator
from core.sandbox import ThreeLayerSandbox
from core.dmn import DMNSystem, DMNTaskType
from llm.interface import LLMInterface
from llm.prompt_templates import PromptTemplates


logger = get_logger()


class AbyssACSystem:
    """AbyssAC主系统"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化AbyssAC系统
        
        Args:
            config_path: 配置文件路径
        """
        self.config = get_config(config_path)
        self.config.ensure_directories()
        
        # 初始化组件
        self.memory_manager: Optional[MemoryManager] = None
        self.nng_navigator: Optional[NNGNavigator] = None
        self.llm_interface: Optional[LLMInterface] = None
        self.sandbox: Optional[ThreeLayerSandbox] = None
        self.dmn: Optional[DMNSystem] = None
        
        # 运行状态
        self.running = False
        self.conversation_count = 0
        
        # 信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理"""
        logger.info(f"收到信号 {signum}，正在关闭系统...")
        self.shutdown()
        sys.exit(0)
    
    def initialize(self) -> bool:
        """
        初始化系统
        
        Returns:
            是否初始化成功
        """
        logger.info("=" * 50)
        logger.info("AbyssAC 系统初始化")
        logger.info("=" * 50)
        
        # 系统检查
        if not self._system_init_check():
            logger.error("系统初始化检查失败")
            return False
        
        try:
            # 初始化记忆管理器
            logger.info("初始化记忆管理器...")
            self.memory_manager = MemoryManager(
                base_path=os.path.join(self.config.paths.base, "storage")
            )
            
            # 初始化NNG导航器
            logger.info("初始化NNG导航器...")
            self.nng_navigator = NNGNavigator(
                base_path=os.path.join(self.config.paths.base, self.config.paths.nng)
            )
            
            # 初始化LLM接口
            logger.info("初始化LLM接口...")
            self.llm_interface = LLMInterface(
                api_type=self.config.llm.api_type,
                base_url=self.config.llm.base_url,
                model=self.config.llm.model,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                timeout=self.config.llm.timeout,
                retry_count=self.config.llm.retry_count
            )
            
            # 初始化三层沙盒
            logger.info("初始化三层沙盒...")
            self.sandbox = ThreeLayerSandbox(
                memory_manager=self.memory_manager,
                nng_navigator=self.nng_navigator,
                llm_interface=self.llm_interface,
                max_depth=self.config.system.max_navigation_depth,
                navigation_timeout=self.config.system.navigation_timeout
            )
            
            # 初始化DMN系统
            logger.info("初始化DMN系统...")
            self.dmn = DMNSystem(
                memory_manager=self.memory_manager,
                nng_navigator=self.nng_navigator,
                llm_interface=self.llm_interface,
                sandbox=self.sandbox,
                auto_trigger=self.config.system.dmn_auto_trigger,
                idle_threshold=self.config.system.dmn_idle_threshold,
                memory_threshold=self.config.system.dmn_memory_threshold,
                failure_threshold=self.config.system.dmn_failure_threshold
            )
            
            # 启动DMN监控
            if self.config.system.dmn_auto_trigger:
                self.dmn.start_monitoring()
            
            logger.info("=" * 50)
            logger.info("AbyssAC 系统初始化完成")
            logger.info("=" * 50)
            
            return True
        
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            return False
    
    def _system_init_check(self) -> bool:
        """
        系统初始化检查
        
        Returns:
            检查是否通过
        """
        logger.info("执行系统初始化检查...")
        
        checks = []
        
        # 1. 检查目录结构
        try:
            self.config.ensure_directories()
            checks.append(("目录结构", True, ""))
        except Exception as e:
            checks.append(("目录结构", False, str(e)))
        
        # 2. 检查root.json
        root_file = os.path.join(
            self.config.paths.base,
            self.config.paths.nng,
            "root.json"
        )
        try:
            if not os.path.exists(root_file):
                safe_write_json(root_file, {
                    "一级节点": [],
                    "更新时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                data = safe_read_json(root_file)
                if "一级节点" not in data:
                    raise ValueError("root.json格式错误")
            checks.append(("root.json", True, ""))
        except Exception as e:
            checks.append(("root.json", False, str(e)))
        
        # 3. 检查memory_counter.txt
        counter_file = os.path.join(
            self.config.paths.base,
            self.config.paths.system,
            "memory_counter.txt"
        )
        try:
            if not os.path.exists(counter_file):
                os.makedirs(os.path.dirname(counter_file), exist_ok=True)
                with open(counter_file, 'w') as f:
                    f.write("0")
            checks.append(("memory_counter.txt", True, ""))
        except Exception as e:
            checks.append(("memory_counter.txt", False, str(e)))
        
        # 4. 检查memory_metadata.json
        metadata_file = os.path.join(
            self.config.paths.base,
            self.config.paths.system,
            "memory_metadata.json"
        )
        try:
            if not os.path.exists(metadata_file):
                safe_write_json(metadata_file, {})
            checks.append(("memory_metadata.json", True, ""))
        except Exception as e:
            checks.append(("memory_metadata.json", False, str(e)))
        
        # 5. 构建内存索引
        try:
            if self.memory_manager:
                self.memory_manager.build_memory_index()
            checks.append(("内存索引", True, ""))
        except Exception as e:
            checks.append(("内存索引", False, str(e)))
        
        # 6. 验证NNG完整性
        try:
            if self.nng_navigator:
                integrity = self.nng_navigator.verify_integrity()
                if not integrity.get("valid"):
                    logger.warning(f"NNG完整性警告: {integrity.get('warnings', [])}")
            checks.append(("NNG完整性", True, ""))
        except Exception as e:
            checks.append(("NNG完整性", False, str(e)))
        
        # 输出检查结果
        all_passed = True
        for name, passed, error in checks:
            status = "✓" if passed else "✗"
            logger.info(f"  [{status}] {name}")
            if error:
                logger.error(f"      错误: {error}")
                all_passed = False
        
        return all_passed
    
    def _needs_memory(self, user_input: str) -> bool:
        """
        判断是否需要调用记忆
        
        Args:
            user_input: 用户输入
        
        Returns:
            是否需要记忆
        """
        prompt = PromptTemplates.needs_memory_judgment(user_input)
        
        messages = [
            {"role": "system", "content": "你是记忆需求判断助手。判断用户输入是否需要调用记忆系统。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm_interface.chat(messages)
        
        if response.success:
            content = response.content.lower()
            return "是" in content or "yes" in content or "true" in content
        
        # 默认需要记忆
        return True
    
    def _generate_response(self, user_input: str, context: str) -> str:
        """
        生成最终回复
        
        Args:
            user_input: 用户输入
            context: 组装好的上下文
        
        Returns:
            AI回复
        """
        prompt = PromptTemplates.final_response_prompt(user_input, context)
        
        messages = [
            {"role": "system", "content": PromptTemplates.USER_INTERACTION_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm_interface.chat(messages)
        
        if response.success:
            return response.content
        else:
            return f"[系统错误: {response.error}]"
    
    def process_input(self, user_input: str) -> str:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入
        
        Returns:
            AI回复
        """
        logger.info(f"处理用户输入: {user_input[:50]}...")
        
        # 更新DMN活动时间
        if self.dmn:
            self.dmn.update_activity()
        
        # 判断是否需要记忆
        if not self._needs_memory(user_input):
            logger.info("判断不需要记忆，直接生成回复")
            response = self.llm_interface.simple_chat(
                user_input,
                PromptTemplates.USER_INTERACTION_SYSTEM
            )
            
            # 保存到工作记忆
            self._save_to_working_memory(user_input, response)
            
            return response
        
        # 执行三层沙盒
        success, context, error = self.sandbox.run_full_sandbox(user_input)
        
        if not success:
            logger.warning(f"沙盒执行失败: {error}")
            # 降级处理：直接回复
            response = self.llm_interface.simple_chat(
                user_input,
                PromptTemplates.USER_INTERACTION_SYSTEM
            )
        else:
            # 生成回复
            response = self._generate_response(user_input, context)
        
        # 保存到工作记忆
        self._save_to_working_memory(user_input, response)
        
        self.conversation_count += 1
        
        return response
    
    def _save_to_working_memory(self, user_input: str, ai_response: str) -> int:
        """
        保存到工作记忆
        
        Args:
            user_input: 用户输入
            ai_response: AI响应
        
        Returns:
            记忆ID
        """
        mem_id = self.memory_manager.create_memory(
            memory_type=MemoryType.WORKING,
            user_input=user_input,
            ai_response=ai_response,
            confidence=70
        )
        
        logger.debug(f"保存到工作记忆: ID={mem_id}")
        
        return mem_id
    
    def interactive_mode(self) -> None:
        """交互模式"""
        print("\n" + "=" * 50)
        print("AbyssAC 人工意识系统")
        print("输入 'exit' 或 'quit' 退出")
        print("输入 'stats' 查看统计")
        print("输入 'dmn' 手动触发DMN")
        print("=" * 50 + "\n")
        
        self.running = True
        
        while self.running:
            try:
                user_input = input("\n[用户] ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', '退出']:
                    break
                
                if user_input.lower() == 'stats':
                    self._print_stats()
                    continue
                
                if user_input.lower() == 'dmn':
                    self._trigger_dmn()
                    continue
                
                # 处理输入
                start_time = time.time()
                response = self.process_input(user_input)
                elapsed = time.time() - start_time
                
                print(f"\n[AI] {response}")
                print(f"\n[系统] 处理耗时: {elapsed:.2f}秒")
            
            except KeyboardInterrupt:
                print("\n\n收到中断信号，正在退出...")
                break
            except Exception as e:
                logger.error(f"处理输入时出错: {e}")
                print(f"[错误] {e}")
        
        self.shutdown()
    
    def _print_stats(self) -> None:
        """打印系统统计"""
        print("\n" + "=" * 50)
        print("系统统计")
        print("=" * 50)
        
        # 记忆统计
        mem_stats = self.memory_manager.get_statistics()
        print(f"\n记忆统计:")
        print(f"  总记忆数: {mem_stats['total']}")
        print(f"  按类型: {mem_stats['by_type']}")
        print(f"  工作记忆: {mem_stats['working_memory']}")
        print(f"  平均置信度: {mem_stats['avg_confidence']}")
        
        # NNG统计
        nng_stats = self.nng_navigator.get_statistics()
        print(f"\nNNG统计:")
        print(f"  总节点数: {nng_stats['total_nodes']}")
        print(f"  最大深度: {nng_stats['max_depth']}")
        print(f"  平均置信度: {nng_stats['avg_confidence']}")
        
        # LLM统计
        llm_stats = self.llm_interface.get_stats()
        print(f"\nLLM统计:")
        print(f"  总调用: {llm_stats['total_calls']}")
        print(f"  失败: {llm_stats['failed_calls']}")
        print(f"  成功率: {llm_stats['success_rate']}%")
        print(f"  平均延迟: {llm_stats['avg_latency']}s")
        
        # DMN统计
        if self.dmn:
            dmn_stats = self.dmn.get_stats()
            print(f"\nDMN统计:")
            print(f"  总任务: {dmn_stats['total_tasks']}")
            print(f"  已完成: {dmn_stats['completed_tasks']}")
            print(f"  失败: {dmn_stats['failed_tasks']}")
        
        # 导航统计
        nav_stats = self.sandbox.get_navigation_stats()
        print(f"\n导航统计:")
        print(f"  导航次数: {nav_stats['total_logs']}")
        print(f"  失败次数: {nav_stats['failure_count']}")
        
        print("=" * 50)
    
    def _trigger_dmn(self) -> None:
        """手动触发DMN"""
        print("\n触发DMN任务...")
        
        if self.dmn:
            self.dmn.trigger_task(DMNTaskType.MEMORY_INTEGRATION, "手动触发")
            print("DMN任务已添加到队列")
        else:
            print("DMN系统未初始化")
    
    def shutdown(self) -> None:
        """关闭系统"""
        logger.info("正在关闭AbyssAC系统...")
        
        self.running = False
        
        # 停止DMN监控
        if self.dmn:
            self.dmn.stop_monitoring()
        
        logger.info("AbyssAC系统已关闭")
    
    def runtime_monitor(self) -> Dict[str, Any]:
        """
        运行时监控
        
        Returns:
            监控数据
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "conversation_count": self.conversation_count,
            "llm_stats": self.llm_interface.get_stats() if self.llm_interface else {},
            "dmn_stats": self.dmn.get_stats() if self.dmn else {},
            "sandbox_stats": self.sandbox.get_navigation_stats() if self.sandbox else {}
        }


def main():
    """主函数"""
    # 获取配置文件路径
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    # 创建系统实例
    system = AbyssACSystem(config_path)
    
    # 初始化
    if not system.initialize():
        print("系统初始化失败，请检查配置和日志")
        sys.exit(1)
    
    # 启动交互模式
    system.interactive_mode()


if __name__ == "__main__":
    main()
