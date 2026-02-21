"""
Three-Layer Sandbox System
三层沙盒系统 - NNG导航、记忆筛选、上下文组装
"""

import re
import os
from typing import List, Dict, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from config.system_config import get_config
from core.nng_manager import get_nng_manager
from core.memory_manager import get_memory_manager
from core.llm_interface import get_llm_interface, PromptBuilder


@dataclass
class SandboxResult:
    """沙盒执行结果"""
    success: bool
    collected_paths: List[str] = field(default_factory=list)
    collected_content: str = ""
    notes: str = ""
    error: str = ""


class PathParser:
    """路径解析器"""
    
    NNG_PREFIX = "nng/"
    MEMORY_PREFIX = "Y层记忆库/"
    
    @classmethod
    def parse_paths(cls, text: str) -> Tuple[List[str], str]:
        """
        解析LLM输出，提取路径和笔记
        
        Returns:
            (路径列表, 笔记)
        """
        paths = []
        notes = []
        
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是笔记行
            if line.startswith("笔记：") or line.startswith("笔记:"):
                notes.append(line.replace("笔记：", "").replace("笔记:", "").strip())
            # 检查是否是路径
            elif line.startswith(cls.NNG_PREFIX) or line.startswith(cls.MEMORY_PREFIX):
                paths.append(line)
        
        return paths, '\n'.join(notes)
    
    @classmethod
    def extract_node_id(cls, path: str) -> Optional[str]:
        """从NNG路径提取节点ID"""
        if path.startswith(cls.NNG_PREFIX):
            # nng/{node_id}.json 或 nng/{parent}/{node_id}.json
            parts = path.replace(cls.NNG_PREFIX, "").replace('.json', '').split('/')
            return parts[-1]
        return None
    
    @classmethod
    def is_nng_path(cls, path: str) -> bool:
        """检查是否是NNG路径"""
        return path.startswith(cls.NNG_PREFIX)
    
    @classmethod
    def is_memory_path(cls, path: str) -> bool:
        """检查是否是记忆路径"""
        return path.startswith(cls.MEMORY_PREFIX)


class Layer1NNGNavigator:
    """第一层：NNG导航沙盒"""
    
    def __init__(self):
        self.config = get_config()
        self.nng_manager = get_nng_manager()
        self.llm = get_llm_interface()
        self.parser = PathParser()
    
    def execute(self, user_input: str, max_rounds: int = 5) -> SandboxResult:
        """
        执行NNG导航
        
        Args:
            user_input: 用户输入
            max_rounds: 最大轮数
        
        Returns:
            SandboxResult
        """
        collected_nng = []
        collected_content = [self.nng_manager.get_root_content()]
        all_notes = []
        
        for round_num in range(max_rounds):
            # 构建提示词
            prompt = PromptBuilder.build_nng_nav_prompt(
                user_input=user_input,
                collected_nng='\n\n'.join(collected_content)
            )
            
            # 调用LLM
            messages = [{"role": "user", "content": prompt}]
            response = self.llm.chat(messages)
            
            if not response.success:
                return SandboxResult(
                    success=False,
                    error=f"LLM调用失败: {response.error}"
                )
            
            # 解析路径
            paths, notes = self.parser.parse_paths(response.content)
            
            if notes:
                all_notes.append(notes)
            
            # 如果没有路径，结束导航
            if not paths:
                break
            
            # 并行读取NNG文件
            new_contents = []
            for path in paths:
                node_id = self.parser.extract_node_id(path)
                if node_id and node_id not in collected_nng:
                    content = self.nng_manager.read_node_raw(node_id)
                    if content:
                        collected_nng.append(node_id)
                        new_contents.append(f"=== {path} ===\n{content}")
                    else:
                        new_contents.append(f"【系统提示】路径不存在: {path}")
            
            if not new_contents:
                break
            
            collected_content.extend(new_contents)
        
        return SandboxResult(
            success=True,
            collected_paths=[f"nng/{n}.json" for n in collected_nng],
            collected_content='\n\n'.join(collected_content),
            notes='\n'.join(all_notes)
        )


class Layer2MemoryFilter:
    """第二层：记忆筛选沙盒"""
    
    def __init__(self):
        self.config = get_config()
        self.memory_manager = get_memory_manager()
        self.llm = get_llm_interface()
        self.parser = PathParser()
    
    def execute(self, user_input: str, nng_result: SandboxResult,
                max_rounds: int = 3) -> SandboxResult:
        """
        执行记忆筛选
        
        Args:
            user_input: 用户输入
            nng_result: 第一层NNG导航结果
            max_rounds: 最大轮数
        
        Returns:
            SandboxResult
        """
        collected_memories = []
        collected_content = []
        all_notes = []
        
        for round_num in range(max_rounds):
            # 构建提示词
            prompt = PromptBuilder.build_memory_filter_prompt(
                user_input=user_input,
                nng_content=nng_result.collected_content,
                collected_memories='\n\n'.join(collected_content)
            )
            
            # 调用LLM
            messages = [{"role": "user", "content": prompt}]
            response = self.llm.chat(messages)
            
            if not response.success:
                return SandboxResult(
                    success=False,
                    error=f"LLM调用失败: {response.error}"
                )
            
            # 解析路径
            paths, notes = self.parser.parse_paths(response.content)
            
            if notes:
                all_notes.append(notes)
            
            # 如果没有路径，结束筛选
            if not paths:
                break
            
            # 并行读取记忆文件
            new_contents = []
            for path in paths:
                if path not in collected_memories:
                    content = self.memory_manager.read_memory_by_path(path)
                    if content:
                        collected_memories.append(path)
                        new_contents.append(f"=== {path} ===\n{content}")
                    else:
                        new_contents.append(f"【系统提示】路径不存在: {path}")
            
            if not new_contents:
                break
            
            collected_content.extend(new_contents)
        
        return SandboxResult(
            success=True,
            collected_paths=collected_memories,
            collected_content='\n\n'.join(collected_content),
            notes='\n'.join(all_notes)
        )


class Layer3ContextAssembler:
    """第三层：上下文组装沙盒"""
    
    def __init__(self):
        self.config = get_config()
        self.llm = get_llm_interface()
    
    def execute(self, user_input: str, nng_result: SandboxResult,
                memory_result: SandboxResult) -> SandboxResult:
        """
        执行上下文组装
        
        Args:
            user_input: 用户输入
            nng_result: NNG导航结果
            memory_result: 记忆筛选结果
        
        Returns:
            SandboxResult
        """
        # 构建提示词
        prompt = PromptBuilder.build_context_assembly_prompt(
            user_input=user_input,
            nng_content=nng_result.collected_content,
            memory_content=memory_result.collected_content
        )
        
        # 调用LLM
        messages = [{"role": "user", "content": prompt}]
        response = self.llm.chat(messages)
        
        if not response.success:
            return SandboxResult(
                success=False,
                error=f"LLM调用失败: {response.error}"
            )
        
        return SandboxResult(
            success=True,
            collected_content=response.content,
            notes="上下文组装完成"
        )


class ThreeLayerSandbox:
    """三层沙盒主类"""
    
    def __init__(self):
        self.layer1 = Layer1NNGNavigator()
        self.layer2 = Layer2MemoryFilter()
        self.layer3 = Layer3ContextAssembler()
    
    def execute(self, user_input: str) -> Dict[str, Any]:
        """
        执行完整的三层沙盒流程
        
        Args:
            user_input: 用户输入
        
        Returns:
            执行结果字典
        """
        result = {
            "success": False,
            "layer1": None,
            "layer2": None,
            "layer3": None,
            "context_package": "",
            "error": ""
        }
        
        # 第一层：NNG导航
        print("[三层沙盒] 执行第一层：NNG导航...")
        layer1_result = self.layer1.execute(user_input)
        result["layer1"] = layer1_result
        
        if not layer1_result.success:
            result["error"] = f"NNG导航失败: {layer1_result.error}"
            return result
        
        print(f"[三层沙盒] NNG导航完成，收集 {len(layer1_result.collected_paths)} 个节点")
        
        # 第二层：记忆筛选
        print("[三层沙盒] 执行第二层：记忆筛选...")
        layer2_result = self.layer2.execute(user_input, layer1_result)
        result["layer2"] = layer2_result
        
        if not layer2_result.success:
            result["error"] = f"记忆筛选失败: {layer2_result.error}"
            return result
        
        print(f"[三层沙盒] 记忆筛选完成，收集 {len(layer2_result.collected_paths)} 条记忆")
        
        # 第三层：上下文组装
        print("[三层沙盒] 执行第三层：上下文组装...")
        layer3_result = self.layer3.execute(user_input, layer1_result, layer2_result)
        result["layer3"] = layer3_result
        
        if not layer3_result.success:
            result["error"] = f"上下文组装失败: {layer3_result.error}"
            return result
        
        result["success"] = True
        result["context_package"] = layer3_result.collected_content
        
        print("[三层沙盒] 上下文组装完成")
        
        return result


# 全局沙盒实例
_sandbox = None


def get_sandbox() -> ThreeLayerSandbox:
    """获取全局沙盒实例"""
    global _sandbox
    if _sandbox is None:
        _sandbox = ThreeLayerSandbox()
    return _sandbox
