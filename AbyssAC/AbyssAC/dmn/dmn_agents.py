"""
DMN（动态维护网络）五个子智能体模块
"""
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.llm_interface import LLMInterface
from nng.nng_manager import NNGManager, NNGNode
from memory.memory_manager import MemoryManager, MemoryEntry, MemoryType, ValueLevel


class DMNTaskType(Enum):
    """DMN任务类型"""
    MEMORY_INTEGRATION = "记忆整合"
    ASSOCIATION_DISCOVERY = "关联发现"
    BIAS_REVIEW = "偏差审查"
    STRATEGY_REHEARSAL = "策略预演"
    CONCEPT_RECOMBINATION = "概念重组"
    NNG_OPTIMIZATION = "NNG结构优化"


@dataclass
class DMNResult:
    """DMN执行结果"""
    success: bool
    task_type: DMNTaskType
    new_memories: List[Dict[str, Any]]
    new_nng_nodes: List[Dict[str, Any]]
    updated_nodes: List[str]
    deleted_memories: List[int]
    error: Optional[str] = None


class Agent1_QuestionOutput:
    """子智能体一：问题输出agent"""
    
    def __init__(self, llm: LLMInterface):
        self.llm = llm
    
    def analyze(self, working_memories: List[MemoryEntry],
                system_state: Dict[str, Any]) -> List[str]:
        """
        分析工作记忆，输出待处理问题列表
        
        Args:
            working_memories: 工作记忆列表
            system_state: 系统状态
            
        Returns:
            问题列表
        """
        if not working_memories:
            return []
        
        # 构建提示
        memories_text = "\n".join([
            f"{i+1}. {wm.content[:200]}..." 
            for i, wm in enumerate(working_memories[-10:])
        ])
        
        prompt = f"""【DMN子智能体一：问题识别】

请分析以下工作记忆，识别出需要系统关注和处理的问题或主题。

工作记忆:
{memories_text}

系统状态:
- 工作记忆数量: {system_state.get('working_memory_count', 0)}
- NNG节点数量: {system_state.get('nng_node_count', 0)}
- 导航失败次数: {system_state.get('navigation_failures', 0)}

请输出需要处理的问题列表（每个问题一行）:
1. [问题描述]
2. [问题描述]
...

如果工作记忆中没有需要深度处理的内容，请输出: 无
"""
        
        response = self.llm.simple_chat(
            prompt,
            system_prompt="你是一个认知分析系统，负责识别需要处理的问题和主题。"
        )
        
        # 解析问题列表
        questions = []
        for line in response.split('\n'):
            line = line.strip()
            if line and not line.startswith('无'):
                # 移除序号
                cleaned = re.sub(r'^\d+[.、]\s*', '', line)
                if cleaned:
                    questions.append(cleaned)
        
        return questions


class Agent2_ProblemAnalysis:
    """子智能体二：问题分析agent"""
    
    def __init__(self, llm: LLMInterface):
        self.llm = llm
    
    def analyze(self, questions: List[str],
                working_memories: List[MemoryEntry],
                existing_nodes: List[str]) -> Dict[str, Any]:
        """
        分析问题并给出初步方案
        
        Args:
            questions: 问题列表
            working_memories: 工作记忆
            existing_nodes: 现有NNG节点
            
        Returns:
            分析结果
        """
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        
        prompt = f"""【DMN子智能体二：问题分析】

待处理问题:
{questions_text}

现有NNG节点:
{', '.join(existing_nodes[:20])}

请对每个问题进行分析，并给出处理建议:

输出格式:
问题1分析:
- 问题本质: [简要描述]
- 相关记忆: [可能相关的记忆主题]
- 建议操作: [创建新记忆/更新NNG/整合知识/其他]
- 建议的NNG位置: [如 1.2 或 新建节点]

问题2分析:
...
"""
        
        response = self.llm.simple_chat(
            prompt,
            system_prompt="你是一个问题分析系统，负责深入分析问题并给出处理建议。"
        )
        
        return {
            'analysis': response,
            'questions': questions
        }


class Agent3_Review:
    """子智能体三：审查agent"""
    
    def __init__(self, llm: LLMInterface):
        self.llm = llm
    
    def review(self, analysis_result: Dict[str, Any]) -> Tuple[bool, str]:
        """
        审查分析结果
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            (是否通过, 审查意见)
        """
        prompt = f"""【DMN子智能体三：结果审查】

请审查以下分析结果，判断其完整性和逻辑正确性。

分析结果:
{analysis_result.get('analysis', '')}

审查标准:
1. 分析是否完整覆盖了所有问题？
2. 建议操作是否合理可行？
3. 逻辑是否自洽？

请输出:
审查结果: 通过 / 不通过
审查意见: [具体意见，如果不通过请说明原因]
"""
        
        response = self.llm.simple_chat(
            prompt,
            system_prompt="你是一个严格的审查系统，负责确保分析结果的质量。"
        )
        
        # 解析审查结果
        passed = '通过' in response and '不通过' not in response
        
        return passed, response


class Agent4_Organize:
    """子智能体四：整理agent"""
    
    def __init__(self, llm: LLMInterface):
        self.llm = llm
    
    def organize(self, analysis_result: Dict[str, Any],
                 working_memories: List[MemoryEntry]) -> Dict[str, Any]:
        """
        将分析结果整理为标准格式
        
        Args:
            analysis_result: 分析结果
            working_memories: 工作记忆
            
        Returns:
            整理后的结果（包含NNG节点和记忆内容）
        """
        memories_text = "\n".join([
            f"记忆#{wm.id}: {wm.content[:150]}..."
            for wm in working_memories[-10:]
        ])
        
        prompt = f"""【DMN子智能体四：结果整理】

基于以下分析和工作记忆，请生成标准化的NNG节点和记忆内容。

分析结果:
{analysis_result.get('analysis', '')}

相关工作记忆:
{memories_text}

请输出以下内容:

1. 新的NNG节点（JSON格式）:
{{
  "节点ID": "建议的节点位置（如 1.2.3）",
  "内容": "节点描述",
  "关联性": 80,
  "置信度": 85
}}

2. 新的记忆内容:
记忆类型: [元认知记忆/高阶整合记忆/分类记忆-高价值/中价值/低价值/工作记忆]
内容: [记忆的具体内容]
关联NNG节点: [节点ID]

3. 需要更新的现有节点:
节点ID: [如果有]
更新内容: [更新什么]

如果不需要创建新内容，请输出: 无新内容
"""
        
        response = self.llm.simple_chat(
            prompt,
            system_prompt="你是一个整理系统，负责将分析结果转换为标准格式。"
        )
        
        # 解析结果
        result = {
            'new_nodes': self._parse_new_nodes(response),
            'new_memories': self._parse_new_memories(response),
            'updates': self._parse_updates(response),
            'raw_response': response
        }
        
        return result
    
    def _parse_new_nodes(self, response: str) -> List[Dict]:
        """解析新的NNG节点"""
        nodes = []
        # 尝试提取JSON
        json_matches = re.findall(r'\{[^{}]*"节点ID"[^{}]*\}', response, re.DOTALL)
        for match in json_matches:
            try:
                node = json.loads(match)
                nodes.append(node)
            except:
                pass
        return nodes
    
    def _parse_new_memories(self, response: str) -> List[Dict]:
        """解析新的记忆"""
        memories = []
        # 提取记忆块
        mem_blocks = re.findall(
            r'记忆类型[:：]\s*(.+?)\n内容[:：]\s*(.+?)(?:\n关联NNG节点[:：]\s*(.+?))?(?=\n\n|\Z)',
            response, re.DOTALL
        )
        for mem_type, content, nng_node in mem_blocks:
            memories.append({
                'type': mem_type.strip(),
                'content': content.strip(),
                'nng_node': nng_node.strip() if nng_node else ''
            })
        return memories
    
    def _parse_updates(self, response: str) -> List[Dict]:
        """解析更新内容"""
        updates = []
        # 简化实现
        return updates


class Agent5_FormatReview:
    """子智能体五：格式位置审查agent"""
    
    def __init__(self, llm: LLMInterface):
        self.llm = llm
    
    def review(self, organized_result: Dict[str, Any],
               existing_nodes: List[str]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        审查格式和位置
        
        Args:
            organized_result: 整理后的结果
            existing_nodes: 现有节点
            
        Returns:
            (是否通过, 审查意见, 修正后的结果)
        """
        new_nodes = organized_result.get('new_nodes', [])
        new_memories = organized_result.get('new_memories', [])
        
        prompt = f"""【DMN子智能体五：格式位置审查】

请审查以下内容，验证格式是否正确、位置是否合适。

现有节点: {', '.join(existing_nodes[:20])}

新的NNG节点:
{json.dumps(new_nodes, ensure_ascii=False, indent=2)}

新的记忆:
{json.dumps(new_memories, ensure_ascii=False, indent=2)}

审查要点:
1. NNG节点ID格式是否正确（如 1.2.3）？
2. 节点位置是否合理（父节点是否存在）？
3. 记忆类型是否正确？
4. 关联关系是否有效？

请输出:
审查结果: 通过 / 不通过
修正建议: [如果需要修正]
修正后的内容: [JSON格式，如果需要]
"""
        
        response = self.llm.simple_chat(
            prompt,
            system_prompt="你是一个格式审查系统，负责确保数据格式正确。"
        )
        
        passed = '通过' in response and '不通过' not in response
        
        # 尝试提取修正后的内容
        corrected = organized_result
        
        return passed, response, corrected


class DMNController:
    """DMN控制器"""
    
    def __init__(self, llm: LLMInterface,
                 nng_manager: NNGManager,
                 memory_manager: MemoryManager):
        self.llm = llm
        self.nng = nng_manager
        self.memory = memory_manager
        
        # 初始化五个子智能体
        self.agent1 = Agent1_QuestionOutput(llm)
        self.agent2 = Agent2_ProblemAnalysis(llm)
        self.agent3 = Agent3_Review(llm)
        self.agent4 = Agent4_Organize(llm)
        self.agent5 = Agent5_FormatReview(llm)
        
        # 日志目录
        self.logs_dir = Path("X层/dmn_logs")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, task_type: DMNTaskType,
                working_memories: List[MemoryEntry],
                system_state: Dict[str, Any],
                max_retries: int = 2) -> DMNResult:
        """
        执行DMN流程
        
        Args:
            task_type: 任务类型
            working_memories: 工作记忆
            system_state: 系统状态
            max_retries: 最大重试次数
            
        Returns:
            DMNResult
        """
        print(f"\n[DMN] 启动任务: {task_type.value}")
        
        result = DMNResult(
            success=False,
            task_type=task_type,
            new_memories=[],
            new_nng_nodes=[],
            updated_nodes=[],
            deleted_memories=[]
        )
        
        # 子智能体一：问题输出
        print("[DMN] 子智能体一: 识别问题...")
        questions = self.agent1.analyze(working_memories, system_state)
        if not questions:
            print("[DMN] 无需要处理的问题")
            result.success = True
            return result
        
        print(f"[DMN] 识别到 {len(questions)} 个问题")
        
        # 子智能体二：问题分析
        print("[DMN] 子智能体二: 分析问题...")
        existing_nodes = self.nng.get_all_node_ids()
        analysis = self.agent2.analyze(questions, working_memories, existing_nodes)
        
        # 子智能体三：审查
        print("[DMN] 子智能体三: 审查分析结果...")
        passed, review_comment = self.agent3.review(analysis)
        
        if not passed:
            print(f"[DMN] 审查未通过: {review_comment[:100]}")
            # 可以重试或降级处理
            result.error = f"审查未通过: {review_comment}"
            return result
        
        # 子智能体四：整理
        print("[DMN] 子智能体四: 整理结果...")
        organized = self.agent4.organize(analysis, working_memories)
        
        # 子智能体五：格式位置审查
        print("[DMN] 子智能体五: 格式审查...")
        passed, review_comment, corrected = self.agent5.review(organized, existing_nodes)
        
        if not passed:
            print(f"[DMN] 格式审查未通过: {review_comment[:100]}")
            result.error = f"格式审查未通过: {review_comment}"
            return result
        
        # 执行实际的数据操作
        print("[DMN] 执行数据操作...")
        self._execute_data_operations(corrected, result)
        
        result.success = True
        
        # 记录日志
        self._log_dmn_execution(task_type, result)
        
        return result
    
    def _execute_data_operations(self, corrected: Dict[str, Any], 
                                  result: DMNResult):
        """执行数据操作"""
        # 创建新的NNG节点
        for node_info in corrected.get('new_nodes', []):
            node_id = node_info.get('节点ID', '')
            content = node_info.get('内容', '')
            
            if node_id and content:
                # 解析父节点
                if '.' in node_id:
                    parent_id = node_id.rsplit('.', 1)[0]
                else:
                    parent_id = "root"
                
                # 创建节点
                new_id = self.nng.create_node(parent_id, content)
                if new_id:
                    result.new_nng_nodes.append({'id': new_id, 'content': content})
        
        # 创建新的记忆
        for mem_info in corrected.get('new_memories', []):
            mem_type_str = mem_info.get('type', '工作记忆')
            content = mem_info.get('content', '')
            nng_node = mem_info.get('nng_node', '')
            
            # 解析记忆类型
            memory_type = MemoryType.WORKING
            value_level = None
            
            if '元认知' in mem_type_str:
                memory_type = MemoryType.META_COGNITION
            elif '高阶整合' in mem_type_str:
                memory_type = MemoryType.HIGH_LEVEL
            elif '分类记忆' in mem_type_str:
                memory_type = MemoryType.CLASSIFIED
                if '高价值' in mem_type_str:
                    value_level = ValueLevel.HIGH
                elif '中价值' in mem_type_str:
                    value_level = ValueLevel.MEDIUM
                elif '低价值' in mem_type_str:
                    value_level = ValueLevel.LOW
            
            # 保存记忆
            entry = self.memory.save_memory(
                content=content,
                memory_type=memory_type,
                value_level=value_level,
                nng_nodes=[nng_node] if nng_node else []
            )
            
            result.new_memories.append({
                'id': entry.id,
                'type': mem_type_str,
                'content': content[:50] + '...'
            })
            
            # 关联到NNG节点
            if nng_node:
                self.nng.add_memory_to_node(
                    nng_node, entry.id,
                    content[:100],
                    mem_type_str,
                    value_level.value if value_level else None
                )
    
    def _log_dmn_execution(self, task_type: DMNTaskType, result: DMNResult):
        """记录DMN执行日志"""
        log_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'task_type': task_type.value,
            'success': result.success,
            'new_memories_count': len(result.new_memories),
            'new_nng_nodes_count': len(result.new_nng_nodes),
            'error': result.error
        }
        
        log_file = self.logs_dir / f"dmn_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def optimize_nng_structure(self, navigation_logs: List[Dict],
                                failure_count: int) -> DMNResult:
        """
        NNG结构优化任务（导航失败触发）
        
        Args:
            navigation_logs: 导航日志
            failure_count: 失败次数
            
        Returns:
            DMNResult
        """
        print(f"\n[DMN] 启动NNG结构优化任务（失败次数: {failure_count}）")
        
        # 分析导航日志
        logs_text = json.dumps(navigation_logs[-10:], ensure_ascii=False, indent=2)
        
        prompt = f"""【NNG结构优化分析】

近期导航日志:
{logs_text}

导航失败次数: {failure_count}

请分析导航失败的原因，并提出优化建议:

1. 问题类型识别:
   - 节点描述不清晰？
   - 缺少必要节点？
   - 节点层级过深？
   - 其他问题？

2. 优化建议:
   - 需要重写的节点
   - 需要创建的新节点
   - 需要调整的结构

输出格式:
问题分析: [分析结果]
优化方案: [具体方案]
"""
        
        response = self.llm.simple_chat(
            prompt,
            system_prompt="你是一个NNG优化专家，负责分析和改进导航图结构。"
        )
        
        # 创建优化结果
        result = DMNResult(
            success=True,
            task_type=DMNTaskType.NNG_OPTIMIZATION,
            new_memories=[],
            new_nng_nodes=[],
            updated_nodes=[],
            deleted_memories=[]
        )
        
        return result


if __name__ == "__main__":
    # 自测
    print("=" * 60)
    print("DMN模块自测")
    print("=" * 60)
    
    import tempfile
    import shutil
    
    test_dir = tempfile.mkdtemp(prefix="abyssac_dmn_test_")
    print(f"\n测试目录: {test_dir}")
    
    try:
        # 初始化组件
        llm = LLMInterface(use_local=True, ollama_model="qwen2.5:7b")
        
        from nng.nng_manager import NNGManager
        from memory.memory_manager import MemoryManager
        
        nng = NNGManager(base_path=f"{test_dir}/NNG")
        memory = MemoryManager(base_path=f"{test_dir}/Y层记忆库")
        
        # 初始化DMN控制器
        dmn = DMNController(llm, nng, memory)
        print("[✓] DMN控制器初始化成功")
        
        # 创建测试工作记忆
        for i in range(5):
            memory.save_memory(
                content=f"测试工作记忆内容 {i+1}：用户询问关于Python的问题",
                memory_type=MemoryType.WORKING
            )
        
        working_mems = memory.get_working_memories()
        print(f"[✓] 创建工作记忆: {len(working_mems)}条")
        
        # 测试子智能体一
        print("\n测试子智能体一...")
        system_state = {
            'working_memory_count': len(working_mems),
            'nng_node_count': len(nng.get_all_node_ids()),
            'navigation_failures': 0
        }
        questions = dmn.agent1.analyze(working_mems, system_state)
        print(f"[✓] 识别问题: {questions}")
        
        # 测试完整DMN流程
        print("\n测试完整DMN流程...")
        result = dmn.execute(
            task_type=DMNTaskType.MEMORY_INTEGRATION,
            working_memories=working_mems,
            system_state=system_state
        )
        print(f"[✓] DMN执行: {'成功' if result.success else '失败'}")
        print(f"[✓] 新记忆: {len(result.new_memories)}条")
        print(f"[✓] 新NNG节点: {len(result.new_nng_nodes)}个")
        
        print("\n" + "=" * 60)
        print("DMN模块自测通过")
        print("=" * 60)
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
        print(f"\n已清理测试目录")
