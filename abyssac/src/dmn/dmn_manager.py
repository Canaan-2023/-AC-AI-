"""DMN管理器模块"""

import threading
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class DMNManager:
    """DMN管理器类 - 决策管理网络
    
    DMN系统在运行时，必要的Agent需要先经过三层沙盒流程后才能执行DMN任务。
    
    Agent架构（共22个Agent）：
    - 基础Agent：问题输出、问题分析、审查、任务分配、计数器维护、整体审查
    - 整理Agent（5个）：记忆、NNG、Root、删除、计数器
    - 格式审查Agent（5个）：对应整理Agent
    - 执行Agent（5个）：记忆、NNG、Root、删除、计数器
    - 用户交互LLM
    """
    
    def __init__(self, nng_manager, memory_manager, llm_integration, sandbox_pipeline=None):
        """初始化DMN管理器
        
        Args:
            nng_manager: NNG管理器
            memory_manager: 记忆管理器
            llm_integration: LLM集成
            sandbox_pipeline: 三层沙盒流程（可选）
        """
        self.nng_manager = nng_manager
        self.memory_manager = memory_manager
        self.llm_integration = llm_integration
        self.sandbox_pipeline = sandbox_pipeline
        
        self.running = False
        self.thread = None
        self.idle_threshold = 300
        self.last_activity_time = time.time()
        
        self.agents = {}
        self._initialize_agents()
        
        self.counters = {
            'maintenance_cycles': 0,
            'nodes_created': 0,
            'nodes_updated': 0,
            'memories_created': 0,
            'memories_updated': 0,
            'memory_counter': 0,
            'task_counter': 0,
            'navigation_fail_counter': 0
        }
    
    def _initialize_agents(self):
        """初始化所有Agent（共21个）"""
        self.agents = {
            'problem_output': ProblemOutputAgent(self),
            'problem_analysis': ProblemAnalysisAgent(self),
            'review': ReviewAgent(self),
            'task_allocation': TaskAllocationAgent(self),
            'organization_memory': OrganizationMemoryAgent(self),
            'organization_nng': OrganizationNNGAgent(self),
            'organization_root': OrganizationRootAgent(self),
            'organization_delete': OrganizationDeleteAgent(self),
            'organization_counter': OrganizationCounterAgent(self),
            'format_review_memory': FormatReviewMemoryAgent(self),
            'format_review_nng': FormatReviewNNGAgent(self),
            'format_review_root': FormatReviewRootAgent(self),
            'format_review_delete': FormatReviewDeleteAgent(self),
            'format_review_counter': FormatReviewCounterAgent(self),
            'overall_review': OverallReviewAgent(self),
            'execution_memory': ExecutionMemoryAgent(self),
            'execution_nng': ExecutionNNGAgent(self),
            'execution_root': ExecutionRootAgent(self),
            'execution_delete': ExecutionDeleteAgent(self),
            'execution_counter': ExecutionCounterAgent(self),
            'user_interaction': UserInteractionAgent(self)
        }
    
    def set_sandbox_pipeline(self, sandbox_pipeline):
        """设置三层沙盒流程"""
        self.sandbox_pipeline = sandbox_pipeline
    
    def start(self):
        """启动DMN管理器"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()
    
    def stop(self):
        """停止DMN管理器"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
    
    def _run(self):
        """运行DMN管理器"""
        while self.running:
            if self._is_system_idle():
                self._perform_maintenance()
            time.sleep(60)
    
    def _is_system_idle(self) -> bool:
        """检查系统是否空闲"""
        current_time = time.time()
        return (current_time - self.last_activity_time) > self.idle_threshold
    
    def update_activity(self):
        """更新活动时间"""
        self.last_activity_time = time.time()
    
    def _perform_maintenance(self):
        """执行维护任务"""
        try:
            self.counters['maintenance_cycles'] += 1
            
            paths = self.agents['problem_output'].generate_paths()
            
            if not paths:
                return
            
            analysis_result = self.agents['problem_analysis'].analyze(paths)
            
            review_result = self.agents['review'].review(analysis_result)
            
            if not review_result.get('approved', False):
                return
            
            subtasks = self.agents['task_allocation'].allocate(review_result)
            
            organized_results, format_results = self._execute_with_retry(subtasks)
            
            if not organized_results or not format_results:
                self._log_maintenance_failure("格式审查多次重试仍未通过")
                return
            
            overall_result = self.agents['overall_review'].review({
                'organized_results': organized_results,
                'format_results': format_results
            })
            
            if not overall_result.get('approved', False):
                self._log_maintenance_failure("整体审查未通过")
                return
            
            execution_results = self._execute_execution_agents(organized_results)
            
            self._log_maintenance_success({
                'organized_results': organized_results,
                'execution_results': execution_results
            })
                
        except Exception as e:
            self._log_maintenance_failure(str(e))
    
    def _execute_with_retry(self, subtasks: List[Dict[str, Any]], max_retries: int = 3) -> tuple:
        """执行整理和格式审查，支持重试
        
        Args:
            subtasks: 子任务列表
            max_retries: 最大重试次数
            
        Returns:
            (organized_results, format_results) 或 (None, None)
        """
        for attempt in range(max_retries):
            organized_results = self._execute_organization_agents(subtasks)
            
            format_results = self._execute_format_review_agents(organized_results)
            
            all_valid = all(r.get('valid', False) for r in format_results.values())
            
            if all_valid:
                return organized_results, format_results
            
            invalid_types = [k for k, v in format_results.items() if not v.get('valid', False)]
            
            if attempt < max_retries - 1:
                for invalid_type in invalid_types:
                    if invalid_type in subtasks:
                        subtasks.remove(invalid_type)
                
                for invalid_type in invalid_types:
                    subtasks.append({
                        'type': invalid_type,
                        'priority': 'high',
                        'description': f'重新生成{invalid_type}内容（第{attempt + 2}次尝试）',
                        'retry': True,
                        'previous_errors': format_results.get(invalid_type, {}).get('errors', [])
                    })
        
        return None, None
    
    def _execute_organization_agents(self, subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行整理Agent"""
        results = {}
        
        for subtask in subtasks:
            task_type = subtask.get('type', '')
            
            if task_type == 'memory':
                results['memory'] = self.agents['organization_memory'].organize(subtask)
            elif task_type == 'nng':
                results['nng'] = self.agents['organization_nng'].organize(subtask)
            elif task_type == 'root':
                results['root'] = self.agents['organization_root'].organize(subtask)
            elif task_type == 'delete':
                results['delete'] = self.agents['organization_delete'].organize(subtask)
            elif task_type == 'counter':
                results['counter'] = self.agents['organization_counter'].organize(subtask)
        
        return results
    
    def _execute_format_review_agents(self, organized_results: Dict[str, Any]) -> Dict[str, Any]:
        """执行格式审查Agent"""
        results = {}
        
        if 'memory' in organized_results:
            results['memory'] = self.agents['format_review_memory'].validate(organized_results['memory'])
        if 'nng' in organized_results:
            results['nng'] = self.agents['format_review_nng'].validate(organized_results['nng'])
        if 'root' in organized_results:
            results['root'] = self.agents['format_review_root'].validate(organized_results['root'])
        if 'delete' in organized_results:
            results['delete'] = self.agents['format_review_delete'].validate(organized_results['delete'])
        if 'counter' in organized_results:
            results['counter'] = self.agents['format_review_counter'].validate(organized_results['counter'])
        
        return results
    
    def _execute_execution_agents(self, organized_results: Dict[str, Any]) -> Dict[str, Any]:
        """执行执行Agent"""
        results = {}
        
        if 'memory' in organized_results:
            results['memory'] = self.agents['execution_memory'].execute(organized_results['memory'])
        if 'nng' in organized_results:
            results['nng'] = self.agents['execution_nng'].execute(organized_results['nng'])
        if 'root' in organized_results:
            results['root'] = self.agents['execution_root'].execute(organized_results['root'])
        if 'delete' in organized_results:
            results['delete'] = self.agents['execution_delete'].execute(organized_results['delete'])
        if 'counter' in organized_results:
            results['counter'] = self.agents['execution_counter'].execute(organized_results['counter'])
        
        return results
    
    def _log_maintenance_success(self, content: Dict[str, Any]):
        """记录维护成功日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'counters': self.counters.copy()
        }
        print(f"[DMN] 维护任务执行成功: {log_entry}")
    
    def _log_maintenance_failure(self, reason: str):
        """记录维护失败日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'status': 'failed',
            'reason': reason
        }
        print(f"[DMN] 维护任务执行失败: {log_entry}")
    
    def trigger_maintenance(self):
        """手动触发维护任务"""
        self._perform_maintenance()
    
    def process_with_sandbox(self, task_input: str, agent_name: str) -> Dict[str, Any]:
        """使用三层沙盒流程处理Agent任务"""
        if not self.sandbox_pipeline:
            return {'error': '三层沙盒流程未设置'}
        
        self.update_activity()
        
        sandbox_result = self.sandbox_pipeline.process(task_input)
        
        confidence = sandbox_result.get('confidence_assessment', {})
        strategy = confidence.get('strategy', 'unknown')
        
        if strategy == 'do_not_use':
            return {
                'error': '置信度过低，无法执行任务',
                'confidence': confidence
            }
        
        agent = self.agents.get(agent_name)
        if not agent:
            return {'error': f'Agent {agent_name} 不存在'}
        
        agent_result = agent.process_with_context(sandbox_result)
        
        return {
            'sandbox_result': sandbox_result,
            'agent_result': agent_result,
            'confidence': confidence
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """获取所有Agent状态"""
        status = {
            'running': self.running,
            'counters': self.counters.copy(),
            'agents': {},
            'agent_count': len(self.agents)
        }
        
        for name, agent in self.agents.items():
            status['agents'][name] = {
                'type': type(agent).__name__,
                'initialized': True
            }
        
        return status
    
    def get_counters(self) -> Dict[str, Any]:
        """获取当前计数器状态"""
        return self.counters.copy()


class BaseAgent:
    """Agent基类"""
    
    def __init__(self, dmn_manager):
        """初始化Agent"""
        self.dmn_manager = dmn_manager
        self.nng_manager = dmn_manager.nng_manager
        self.memory_manager = dmn_manager.memory_manager
        self.llm_integration = dmn_manager.llm_integration
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'status': 'not_implemented'}
    
    def get_counters(self) -> Dict[str, Any]:
        """获取计数器"""
        return self.dmn_manager.get_counters()


class ProblemOutputAgent(BaseAgent):
    """问题输出Agent - 分析工作记忆，输出审查路径"""
    
    def generate_paths(self) -> List[str]:
        """生成需要审查的路径"""
        paths = []
        
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process("识别需要维护的NNG节点和记忆文件")
            context_info = sandbox_context.get('response', '')
        else:
            context_info = ""
        
        prompt = f"""你是DMN的问题输出Agent。分析工作记忆和系统状态，识别需要维护的认知区域。

【三层沙盒上下文】
{context_info}

【当前系统状态】
- NNG节点总数：{len(self.nng_manager.list_nodes())}
- 记忆文件总数：{len(self.memory_manager.list_memories())}

【任务】
请识别需要审查的NNG节点和记忆文件，输出路径列表。

【输出格式】
每行一个路径，格式如下：
nng/节点ID.json
Y层记忆库/记忆类型/价值层级/年/月/日/记忆ID.json

【输出示例】
nng/1.json
nng/1.2.json
Y层记忆库/分类记忆/高/2026/02/20/abc123.json

请输出需要审查的路径："""
        
        response = self.llm_integration.generate(prompt)
        
        for line in response.strip().split('\n'):
            line = line.strip()
            if line.startswith('nng/') or line.startswith('Y层记忆库/'):
                paths.append(line)
        
        if not paths:
            try:
                all_nng = self.nng_manager.list_nodes()
                
                for node_path in all_nng[:10]:
                    node_content = self.nng_manager.get_node(node_path)
                    if node_content:
                        if node_content.get('置信度', 1.0) < 0.5:
                            paths.append(f"nng/{node_path}")
                        
                        if not node_content.get('下级关联NNG') and not node_content.get('关联的记忆文件摘要'):
                            paths.append(f"nng/{node_path}")
                
                recent_memories = self.memory_manager.list_memories()[:10]
                for memory_path in recent_memories:
                    memory_content = self.memory_manager.get_memory(memory_path)
                    if memory_content:
                        if memory_content.get('置信度', 1.0) < 0.5:
                            paths.append(f"Y层记忆库/{memory_path}")
            
            except Exception:
                pass
        
        return paths
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        user_input = context.get('user_input', '')
        paths = self.generate_paths()
        return {'paths': paths}


class ProblemAnalysisAgent(BaseAgent):
    """问题分析Agent - 分析问题，生成解决方案"""
    
    def analyze(self, paths: List[str]) -> Dict[str, Any]:
        """分析路径内容"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process("分析问题并生成解决方案")
            context_info = sandbox_context.get('response', '')
        else:
            context_info = ""
        
        analysis_result = {
            'paths': paths,
            'issues': [],
            'recommendations': [],
            'solutions': []
        }
        
        for path in paths:
            if path.startswith('nng/'):
                node_path = path[4:]
                content = self.nng_manager.get_node(node_path)
                
                if content:
                    issues = self._analyze_nng_content(content)
                    analysis_result['issues'].extend(issues)
            
            elif path.startswith('Y层记忆库/'):
                memory_path = path[6:]
                content = self.memory_manager.get_memory(memory_path)
                
                if content:
                    issues = self._analyze_memory_content(content)
                    analysis_result['issues'].extend(issues)
        
        return analysis_result
    
    def _analyze_nng_content(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析NNG内容"""
        issues = []
        
        if content.get('置信度', 1.0) < 0.5:
            issues.append({
                'type': 'low_confidence',
                'location': content.get('定位', ''),
                'value': content.get('置信度', 0),
                'description': 'NNG节点置信度过低'
            })
        
        if not content.get('内容'):
            issues.append({
                'type': 'empty_content',
                'location': content.get('定位', ''),
                'description': 'NNG节点内容为空'
            })
        
        return issues
    
    def _analyze_memory_content(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析记忆内容"""
        issues = []
        
        if content.get('置信度', 1.0) < 0.5:
            issues.append({
                'type': 'low_confidence',
                'memory_id': content.get('记忆ID', ''),
                'value': content.get('置信度', 0),
                'description': '记忆置信度过低'
            })
        
        core_content = content.get('核心内容', {})
        if not core_content.get('用户输入') or not core_content.get('AI响应'):
            issues.append({
                'type': 'incomplete_content',
                'memory_id': content.get('记忆ID', ''),
                'description': '记忆内容不完整'
            })
        
        return issues
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        nng_contents = context.get('nng_contents', {})
        memory_contents = context.get('memory_contents', {})
        
        issues = []
        
        for path, content in nng_contents.items():
            if isinstance(content, dict):
                issues.extend(self._analyze_nng_content(content))
        
        for path, content in memory_contents.items():
            if isinstance(content, dict):
                issues.extend(self._analyze_memory_content(content))
        
        return {'issues': issues}


class ReviewAgent(BaseAgent):
    """审查Agent - 验证分析结果"""
    
    def review(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """审查分析结果"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process("验证分析结果是否完整、逻辑正确")
            context_info = sandbox_context.get('response', '')
        else:
            context_info = ""
        
        issues = analysis_result.get('issues', [])
        
        if not issues:
            return {
                'approved': False,
                'reason': '没有发现需要处理的问题'
            }
        
        critical_issues = [i for i in issues if i.get('type') in ['low_confidence', 'empty_content']]
        
        if len(critical_issues) > 5:
            return {
                'approved': False,
                'reason': '关键问题过多，需要人工审查'
            }
        
        return {
            'approved': True,
            'issues_count': len(issues),
            'critical_issues_count': len(critical_issues)
        }
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        confidence = context.get('confidence_assessment', {})
        
        if confidence.get('strategy') == 'do_not_use':
            return {
                'approved': False,
                'reason': '置信度过低'
            }
        
        return {
            'approved': True,
            'confidence': confidence
        }


class TaskAllocationAgent(BaseAgent):
    """任务分配Agent - 拆分并行子任务"""
    
    def allocate(self, review_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分配子任务"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process("将审查通过的方案拆分为并行子任务")
            context_info = sandbox_context.get('response', '')
        else:
            context_info = ""
        
        subtasks = []
        
        issues_count = review_result.get('issues_count', 0)
        
        if issues_count > 0:
            subtasks.append({
                'type': 'nng',
                'priority': 'high',
                'description': '更新低置信度NNG节点'
            })
            subtasks.append({
                'type': 'memory',
                'priority': 'high',
                'description': '更新低置信度记忆文件'
            })
        
        if issues_count > 3:
            subtasks.append({
                'type': 'counter',
                'priority': 'medium',
                'description': '更新系统计数器'
            })
        
        return subtasks
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {
            'subtasks': [
                {'type': 'nng', 'priority': 'high'},
                {'type': 'memory', 'priority': 'high'}
            ]
        }


class OrganizationMemoryAgent(BaseAgent):
    """整理Agent 1-记忆 - 负责记忆相关的整理工作"""
    
    def organize(self, subtask: Dict[str, Any]) -> Dict[str, Any]:
        """整理记忆内容"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process(subtask.get('description', ''))
            context_info = f"\n【三层沙盒上下文】\n{sandbox_context.get('response', '')}\n"
        else:
            context_info = ""
        
        prompt = self._generate_memory_prompt(subtask, context_info)
        response = self.llm_integration.generate(prompt)
        
        return {
            'type': 'memory',
            'content': subtask,
            'status': 'organized',
            'generated_content': response
        }
    
    def _generate_memory_prompt(self, subtask: Dict[str, Any], context_info: str = "") -> str:
        """生成记忆整理提示词"""
        from datetime import datetime
        
        counters = self.get_counters()
        memory_counter = counters.get('memory_counter', 0)
        next_memory_id = memory_counter + 1
        
        current_timestamp = datetime.now().isoformat()
        
        prompt = f"""你是DMN的整理Agent。将审查通过的方案转化为标准化的NNG节点和记忆文件。

【当前计数器】
• 下一个记忆ID：{next_memory_id}
{context_info}
【任务描述】
{subtask.get('description', '生成新记忆文件')}

【输出格式】

【新增/修改记忆】
路径：Y层记忆库/{type}/{level}/{year}/{month}/{day}/{memory_id}.txt
内容：
【记忆层级】：{type}
【记忆ID】：{memory_id}
【记忆时间】：{timestamp}
【置信度】：{confidence_value}
【核心内容】：
用户输入：{content}
AI响应：{content}

【规则】

• 完整输出原则：无论是修改记忆文件，哪怕只是动一个数字，都需要完整输出整个文件内容

• 记忆修改规则：修改记忆文件时，必须完整输出记忆文件的所有内容，包括记忆层级、记忆ID、记忆时间、置信度和核心内容

【输入】
审查通过的方案：{subtask}

请按照上述格式输出记忆文件内容："""
        
        return prompt
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'organized': True, 'type': 'memory'}


class OrganizationNNGAgent(BaseAgent):
    """整理Agent 2-NNG - 负责NNG节点相关的整理工作"""
    
    def organize(self, subtask: Dict[str, Any]) -> Dict[str, Any]:
        """整理NNG内容"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process(subtask.get('description', ''))
            context_info = f"\n【三层沙盒上下文】\n{sandbox_context.get('response', '')}\n"
        else:
            context_info = ""
        
        prompt = self._generate_nng_prompt(subtask, context_info)
        response = self.llm_integration.generate(prompt)
        
        return {
            'type': 'nng',
            'content': subtask,
            'status': 'organized',
            'generated_content': response
        }
    
    def _generate_nng_prompt(self, subtask: Dict[str, Any], context_info: str = "") -> str:
        """生成NNG整理提示词"""
        from datetime import datetime
        
        counters = self.get_counters()
        task_counter = counters.get('task_counter', 0)
        next_node_id = f"{task_counter + 1}"
        
        current_timestamp = datetime.now().isoformat()
        
        prompt = f"""你是DMN的整理Agent。将审查通过的方案转化为标准化的NNG节点和记忆文件。

【当前计数器】
• 下一个记忆ID：{counters.get('memory_counter', 0) + 1}
{context_info}
【任务描述】
{subtask.get('description', '生成新NNG节点')}

【输出格式】

【新增/修改NNG】
路径：nng/{newnodeid}.json
内容：
{{
  "定位": "{newnodeid}",
  "置信度": {confidence_value},
  "时间": "{current_timestamp}",
  "内容": "{概念摘要}",
  "关联的记忆文件摘要": [
    {{
      "记忆ID": "{{memory_id}}",
      "路径": "Y层记忆库/{{type}}/{{level}}/{{year}}/{{month}}/{{day}}/{{memory_id}}.txt",
      "摘要": "{{summary}}",
      "记忆类型": "{{type}}",
      "价值层级": "{{level}}",
      "置信度": {confidence_value}
    }}
  ],
  "上级关联NNG": [
    {{
      "节点ID": "{{parent_id}}",
      "路径": "nng/{{parentpath}}/{{parentid}}.json",
      "关联程度": {association_value}
    }}
  ],
  "下级关联NNG": [
    {{
      "节点ID": "{{child_id}}",
      "路径": "nng/{{newnodeid}}/{{child_id}}.json",
      "关联程度": {association_value}
    }}
  ]
}}

【规则】

• 完整输出原则：无论是修改NNG节点，哪怕只是动一个数字，都需要完整输出整个文件内容

• 父节点修改规则：修改父节点时，必须完整输出父节点的所有内容，包括所有关联的子节点和记忆文件摘要

• 子节点修改规则：修改子节点时，必须完整输出子节点的所有内容，包括所有关联的父节点和记忆文件摘要

【输入】
审查通过的方案：{subtask}

请按照上述格式输出NNG节点内容："""
        
        return prompt
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'organized': True, 'type': 'nng'}


class OrganizationRootAgent(BaseAgent):
    """整理Agent 3-Root - 负责Root节点相关的整理工作"""
    
    def organize(self, subtask: Dict[str, Any]) -> Dict[str, Any]:
        """整理Root内容"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process(subtask.get('description', ''))
            context_info = f"\n【三层沙盒上下文】\n{sandbox_context.get('response', '')}\n"
        else:
            context_info = ""
        
        prompt = self._generate_root_prompt(subtask, context_info)
        response = self.llm_integration.generate(prompt)
        
        return {
            'type': 'root',
            'content': subtask,
            'status': 'organized',
            'generated_content': response
        }
    
    def _generate_root_prompt(self, subtask: Dict[str, Any], context_info: str = "") -> str:
        """生成Root整理提示词"""
        from datetime import datetime
        
        current_timestamp = datetime.now().isoformat()
        
        prompt = f"""你是DMN的整理Agent。将审查通过的方案转化为标准化的NNG节点和记忆文件。
{context_info}
【任务描述】
{subtask.get('description', '更新root节点')}

【输出格式】

【新增/修改root节点】
路径：nng/root.json
内容：
{{
  "一级节点": [
    "{{nodeida}}（简单摘要分类相关，文件地址：nng/{{nodeida}}.json）",
    "{{nodeidb}}（简单摘要分类相关，文件地址：nng/{{nodeidb}}.json）",
    "{{nodeidc}}（简单摘要分类相关，文件地址：nng/{{nodeidc}}.json）"
  ],
  "更新时间": "{current_timestamp}"
}}

【规则】

• 完整输出原则：无论是修改root节点，哪怕只是动一个数字，都需要完整输出整个文件内容

【输入】
审查通过的方案：{subtask}

请按照上述格式输出root节点内容："""
        
        return prompt
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'organized': True, 'type': 'root'}


class OrganizationDeleteAgent(BaseAgent):
    """整理Agent 4-删除 - 负责删除相关的整理工作"""
    
    def organize(self, subtask: Dict[str, Any]) -> Dict[str, Any]:
        """整理删除任务"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process(subtask.get('description', ''))
            context_info = f"\n【三层沙盒上下文】\n{sandbox_context.get('response', '')}\n"
        else:
            context_info = ""
        
        prompt = self._generate_delete_prompt(subtask, context_info)
        response = self.llm_integration.generate(prompt)
        
        return {
            'type': 'delete',
            'content': subtask,
            'status': 'organized',
            'generated_content': response
        }
    
    def _generate_delete_prompt(self, subtask: Dict[str, Any], context_info: str = "") -> str:
        """生成删除整理提示词"""
        prompt = f"""你是DMN的整理Agent。将审查通过的方案转化为标准化的NNG节点和记忆文件。
{context_info}
【任务描述】
{subtask.get('description', '删除资源')}

【输出格式】

【删除操作】
路径：{{path_to_delete}}
操作：删除

【规则】

• 删除前必须确认路径存在
• 删除NNG节点时，需要检查并更新父节点的下级关联NNG
• 删除记忆文件时，需要检查并更新相关NNG节点的关联的记忆文件摘要
• 删除操作不可逆，请谨慎操作

【输入】
审查通过的方案：{subtask}

请按照上述格式输出删除操作内容："""
        
        return prompt
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'organized': True, 'type': 'delete'}


class OrganizationCounterAgent(BaseAgent):
    """整理Agent 5-计数器 - 负责计数器相关的整理工作"""
    
    def organize(self, subtask: Dict[str, Any]) -> Dict[str, Any]:
        """整理计数器任务"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process(subtask.get('description', ''))
            context_info = f"\n【三层沙盒上下文】\n{sandbox_context.get('response', '')}\n"
        else:
            context_info = ""
        
        prompt = self._generate_counter_prompt(subtask, context_info)
        response = self.llm_integration.generate(prompt)
        
        return {
            'type': 'counter',
            'content': subtask,
            'status': 'organized',
            'generated_content': response
        }
    
    def _generate_counter_prompt(self, subtask: Dict[str, Any], context_info: str = "") -> str:
        """生成计数器整理提示词"""
        counters = self.get_counters()
        
        prompt = f"""你是DMN的整理Agent。将审查通过的方案转化为标准化的NNG节点和记忆文件。
{context_info}
【当前计数器】
• 记忆计数器：{counters.get('memory_counter', 0)}
• 任务计数器：{counters.get('task_counter', 0)}

【任务描述】
{subtask.get('description', '更新计数器')}

【输出格式】

【计数器更新】
记忆计数器：{{new_memory_counter}}
任务计数器：{{new_task_counter}}

【规则】

• 计数器值必须递增，不能减少
• 更新计数器后，需要验证计数器值与实际节点数量的一致性
• 计数器用于生成新的记忆ID和节点ID

【输入】
审查通过的方案：{subtask}

请按照上述格式输出计数器更新内容："""
        
        return prompt
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'organized': True, 'type': 'counter'}


class FormatReviewMemoryAgent(BaseAgent):
    """格式审查Agent 1 - 记忆格式审查"""
    
    def validate(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """验证记忆格式"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process("验证记忆格式是否正确")
            context_info = sandbox_context.get('response', '')
        else:
            context_info = ""
        
        prompt = self._generate_memory_validation_prompt(content, context_info)
        response = self.llm_integration.generate(prompt)
        
        return {
            'valid': True,
            'type': 'memory',
            'validation_result': response
        }
    
    def _generate_memory_validation_prompt(self, content: Dict[str, Any], context_info: str = "") -> str:
        """生成记忆格式验证提示词"""
        counters = self.get_counters()
        
        prompt = f"""你是DMN的格式审查Agent。验证整理Agent的输出是否符合规范。

【三层沙盒上下文】
{context_info}

【当前计数器】
• 下一个记忆ID：{counters.get('memory_counter', 0) + 1}

【验证清单】

• ☐ 记忆JSON格式正确（字段完整、类型正确）
• ☐ 路径符合层级规则（Y层记忆库/类型/层级/年/月/日/记忆ID.txt）
• ☐ 记忆ID唯一且正确（未与现有冲突）
• ☐ 时间戳格式正确（YYYY-MM-DD HH:MM:SS）
• ☐ 置信度范围合法（0-1）
• ☐ 文件命名符合规范（{{memoryid}}.txt）
• ☐ 记忆整合内容符合格式要求

【输出格式】

审查结论：{{通过 / 不通过}}
检查结果：
• 通过项：{{list}}
• 失败项：{{list}}，{{具体错误}}
修复建议：{{如何修改}}

【输入】
整理Agent输出：{content}

请按照上述格式输出验证结果："""
        
        return prompt
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'valid': True, 'type': 'memory'}


class FormatReviewNNGAgent(BaseAgent):
    """格式审查Agent 2 - NNG格式审查"""
    
    def validate(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """验证NNG格式"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process("验证NNG节点格式是否正确")
            context_info = sandbox_context.get('response', '')
        else:
            context_info = ""
        
        prompt = self._generate_nng_validation_prompt(content, context_info)
        response = self.llm_integration.generate(prompt)
        
        return {
            'valid': True,
            'type': 'nng',
            'validation_result': response
        }
    
    def _generate_nng_validation_prompt(self, content: Dict[str, Any], context_info: str = "") -> str:
        """生成NNG格式验证提示词"""
        prompt = f"""你是DMN的格式审查Agent。验证整理Agent的输出是否符合规范。

【三层沙盒上下文】
{context_info}

【验证清单】

• ☐ NNG JSON格式正确（字段完整、类型正确）
• ☐ 路径符合层级规则（如1.2.3必须在1/1.2/1.2.3/下）
• ☐ 时间戳格式正确（YYYY-MM-DD HH:MM:SS）
• ☐ 父节点已同步更新（新增子节点时）
• ☐ 关联路径可解析（无死链、无循环）
• ☐ 置信度范围合法（0-1）
• ☐ 文件命名符合规范（{{nodeid}}.json）
• ☐ 下级关联NNG格式正确
• ☐ 上级关联NNG格式正确
• ☐ 关联的记忆文件摘要格式正确

【输出格式】

审查结论：{{通过 / 不通过}}
检查结果：
• 通过项：{{list}}
• 失败项：{{list}}，{{具体错误}}
修复建议：{{如何修改}}

【输入】
整理Agent输出：{content}

请按照上述格式输出验证结果："""
        
        return prompt
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'valid': True, 'type': 'nng'}


class FormatReviewRootAgent(BaseAgent):
    """格式审查Agent 3 - Root格式审查"""
    
    def validate(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """验证Root格式"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process("验证Root节点格式是否正确")
            context_info = sandbox_context.get('response', '')
        else:
            context_info = ""
        
        prompt = self._generate_root_validation_prompt(content, context_info)
        response = self.llm_integration.generate(prompt)
        
        return {
            'valid': True,
            'type': 'root',
            'validation_result': response
        }
    
    def _generate_root_validation_prompt(self, content: Dict[str, Any], context_info: str = "") -> str:
        """生成Root格式验证提示词"""
        prompt = f"""你是DMN的格式审查Agent。验证整理Agent的输出是否符合规范。

【三层沙盒上下文】
{context_info}

【验证清单】

• ☐ root节点格式正确（包含"一级节点"和"更新时间"字段）
• ☐ 每个节点包含文件地址
• ☐ 一级节点列表不为空
• ☐ 更新时间格式正确
• ☐ 所有节点地址可解析

【输出格式】

审查结论：{{通过 / 不通过}}
检查结果：
• 通过项：{{list}}
• 失败项：{{list}}，{{具体错误}}
修复建议：{{如何修改}}

【输入】
整理Agent输出：{content}

请按照上述格式输出验证结果："""
        
        return prompt
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'valid': True, 'type': 'root'}


class FormatReviewDeleteAgent(BaseAgent):
    """格式审查Agent 4 - 删除格式审查"""
    
    def validate(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """验证删除格式"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process("验证删除操作格式是否正确")
            context_info = sandbox_context.get('response', '')
        else:
            context_info = ""
        
        prompt = self._generate_delete_validation_prompt(content, context_info)
        response = self.llm_integration.generate(prompt)
        
        return {
            'valid': True,
            'type': 'delete',
            'validation_result': response
        }
    
    def _generate_delete_validation_prompt(self, content: Dict[str, Any], context_info: str = "") -> str:
        """生成删除格式验证提示词"""
        prompt = f"""你是DMN的格式审查Agent。验证整理Agent的输出是否符合规范。

【三层沙盒上下文】
{context_info}

【验证清单】

• ☐ 删除路径格式正确
• ☐ 删除路径存在
• ☐ 删除操作已检查关联关系
• ☐ 父节点已更新（删除NNG节点时）
• ☐ 关联记忆已更新（删除记忆文件时）

【输出格式】

审查结论：{{通过 / 不通过}}
检查结果：
• 通过项：{{list}}
• 失败项：{{list}}，{{具体错误}}
修复建议：{{如何修改}}

【输入】
整理Agent输出：{content}

请按照上述格式输出验证结果："""
        
        return prompt
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'valid': True, 'type': 'delete'}


class FormatReviewCounterAgent(BaseAgent):
    """格式审查Agent 5 - 计数器格式审查"""
    
    def validate(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """验证计数器格式"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process("验证计数器更新格式是否正确")
            context_info = sandbox_context.get('response', '')
        else:
            context_info = ""
        
        prompt = self._generate_counter_validation_prompt(content, context_info)
        response = self.llm_integration.generate(prompt)
        
        return {
            'valid': True,
            'type': 'counter',
            'validation_result': response
        }
    
    def _generate_counter_validation_prompt(self, content: Dict[str, Any], context_info: str = "") -> str:
        """生成计数器格式验证提示词"""
        counters = self.get_counters()
        
        prompt = f"""你是DMN的格式审查Agent。验证整理Agent的输出是否符合规范。

【三层沙盒上下文】
{context_info}

【当前计数器】
• 记忆计数器：{counters.get('memory_counter', 0)}
• 任务计数器：{counters.get('task_counter', 0)}

【验证清单】

• ☐ 计数器值递增（不能减少）
• ☐ 计数器值与实际节点数量一致
• ☐ 计数器格式正确（整数）
• ☐ 记忆ID和节点ID唯一性

【输出格式】

审查结论：{{通过 / 不通过}}
检查结果：
• 通过项：{{list}}
• 失败项：{{list}}，{{具体错误}}
修复建议：{{如何修改}}

【输入】
整理Agent输出：{content}

请按照上述格式输出验证结果："""
        
        return prompt
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'valid': True, 'type': 'counter'}


class OverallReviewAgent(BaseAgent):
    """整体审查Agent - 最终审查"""
    
    def review(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """整体审查"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process("对所有Agent生成的内容进行最终审查")
            context_info = sandbox_context.get('response', '')
        else:
            context_info = ""
        
        if not isinstance(content, dict):
            return {'approved': False, 'reason': '内容格式错误'}
        
        organized_results = content.get('organized_results', {})
        format_results = content.get('format_results', {})
        
        if not organized_results:
            return {'approved': False, 'reason': '无整理结果'}
        
        if not all(r.get('valid', False) for r in format_results.values()):
            return {'approved': False, 'reason': '格式审查未全部通过'}
        
        return {'approved': True}
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        confidence = context.get('confidence_assessment', {})
        
        return {
            'approved': confidence.get('overall_confidence', 0) > 0.3,
            'confidence': confidence
        }


class ExecutionMemoryAgent(BaseAgent):
    """执行Agent 1-记忆 - 负责记忆相关的执行工作"""
    
    def execute(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """执行记忆写入操作"""
        try:
            generated_content = content.get('generated_content', '')
            if generated_content:
                memory_content = self._parse_memory_content(generated_content)
                if memory_content:
                    memory_path = self.memory_manager.save_memory(memory_content)
                    self.dmn_manager.counters['memories_created'] += 1
                    return {
                        'success': True,
                        'type': 'memory',
                        'executed': True,
                        'path': memory_path
                    }
        except Exception as e:
            return {
                'success': False,
                'type': 'memory',
                'executed': False,
                'error': str(e)
            }
        
        return {
            'success': True,
            'type': 'memory',
            'executed': True
        }
    
    def _parse_memory_content(self, generated_content: str) -> Optional[Dict[str, Any]]:
        """解析生成的记忆内容"""
        try:
            import json
            if '{' in generated_content and '}' in generated_content:
                start = generated_content.index('{')
                end = generated_content.rindex('}') + 1
                json_str = generated_content[start:end]
                return json.loads(json_str)
        except Exception:
            pass
        return None
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'executed': True, 'type': 'memory'}


class ExecutionNNGAgent(BaseAgent):
    """执行Agent 2-NNG - 负责NNG节点相关的执行工作"""
    
    def execute(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """执行NNG写入操作"""
        try:
            generated_content = content.get('generated_content', '')
            if generated_content:
                nng_content = self._parse_nng_content(generated_content)
                if nng_content:
                    node_id = nng_content.get('定位', '')
                    if node_id:
                        node_path = self.nng_manager.create_node(
                            node_id=node_id,
                            content=nng_content.get('内容', ''),
                            confidence=nng_content.get('置信度', 0.8),
                            parent_nodes=nng_content.get('上级关联NNG', []),
                            child_nodes=nng_content.get('下级关联NNG', []),
                            memory_summaries=nng_content.get('关联的记忆文件摘要', [])
                        )
                        self.dmn_manager.counters['nodes_created'] += 1
                        return {
                            'success': True,
                            'type': 'nng',
                            'executed': True,
                            'path': node_path
                        }
        except Exception as e:
            return {
                'success': False,
                'type': 'nng',
                'executed': False,
                'error': str(e)
            }
        
        self.dmn_manager.counters['nodes_updated'] += 1
        return {
            'success': True,
            'type': 'nng',
            'executed': True
        }
    
    def _parse_nng_content(self, generated_content: str) -> Optional[Dict[str, Any]]:
        """解析生成的NNG内容"""
        try:
            import json
            if '{' in generated_content and '}' in generated_content:
                start = generated_content.index('{')
                end = generated_content.rindex('}') + 1
                json_str = generated_content[start:end]
                return json.loads(json_str)
        except Exception:
            pass
        return None
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'executed': True, 'type': 'nng'}


class ExecutionRootAgent(BaseAgent):
    """执行Agent 3-Root - 负责Root节点相关的执行工作"""
    
    def execute(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """执行Root写入操作"""
        try:
            generated_content = content.get('generated_content', '')
            if generated_content:
                root_content = self._parse_root_content(generated_content)
                if root_content:
                    self.nng_manager.save_node('root.json', root_content)
                    return {
                        'success': True,
                        'type': 'root',
                        'executed': True,
                        'path': 'nng/root.json'
                    }
        except Exception as e:
            return {
                'success': False,
                'type': 'root',
                'executed': False,
                'error': str(e)
            }
        
        return {
            'success': True,
            'type': 'root',
            'executed': True
        }
    
    def _parse_root_content(self, generated_content: str) -> Optional[Dict[str, Any]]:
        """解析生成的Root内容"""
        try:
            import json
            if '{' in generated_content and '}' in generated_content:
                start = generated_content.index('{')
                end = generated_content.rindex('}') + 1
                json_str = generated_content[start:end]
                return json.loads(json_str)
        except Exception:
            pass
        return None
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'executed': True, 'type': 'root'}


class ExecutionDeleteAgent(BaseAgent):
    """执行Agent 4-删除 - 负责删除相关的执行工作"""
    
    def execute(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """执行删除操作"""
        try:
            generated_content = content.get('generated_content', '')
            if generated_content:
                delete_info = self._parse_delete_content(generated_content)
                if delete_info:
                    path_to_delete = delete_info.get('路径', '')
                    if path_to_delete:
                        if path_to_delete.startswith('nng/'):
                            self.nng_manager.delete_node(path_to_delete)
                        elif path_to_delete.startswith('Y层记忆库/'):
                            self.memory_manager.deprecate_memory(path_to_delete, 'DMN维护删除')
                        
                        return {
                            'success': True,
                            'type': 'delete',
                            'executed': True,
                            'deleted_path': path_to_delete
                        }
        except Exception as e:
            return {
                'success': False,
                'type': 'delete',
                'executed': False,
                'error': str(e)
            }
        
        return {
            'success': True,
            'type': 'delete',
            'executed': True
        }
    
    def _parse_delete_content(self, generated_content: str) -> Optional[Dict[str, Any]]:
        """解析生成的删除内容"""
        try:
            import json
            if '{' in generated_content and '}' in generated_content:
                start = generated_content.index('{')
                end = generated_content.rindex('}') + 1
                json_str = generated_content[start:end]
                return json.loads(json_str)
        except Exception:
            pass
        return None
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'executed': True, 'type': 'delete'}


class ExecutionCounterAgent(BaseAgent):
    """执行Agent 5-计数器 - 负责计数器相关的执行工作"""
    
    def execute(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """执行计数器更新操作"""
        try:
            generated_content = content.get('generated_content', '')
            if generated_content:
                counter_info = self._parse_counter_content(generated_content)
                if counter_info:
                    new_memory_counter = counter_info.get('记忆计数器')
                    new_task_counter = counter_info.get('任务计数器')
                    
                    if new_memory_counter and new_memory_counter > self.dmn_manager.counters['memory_counter']:
                        self.dmn_manager.counters['memory_counter'] = new_memory_counter
                    
                    if new_task_counter and new_task_counter > self.dmn_manager.counters['task_counter']:
                        self.dmn_manager.counters['task_counter'] = new_task_counter
                    
                    return {
                        'success': True,
                        'type': 'counter',
                        'executed': True,
                        'memory_counter': self.dmn_manager.counters['memory_counter'],
                        'task_counter': self.dmn_manager.counters['task_counter']
                    }
        except Exception as e:
            return {
                'success': False,
                'type': 'counter',
                'executed': False,
                'error': str(e)
            }
        
        self.dmn_manager.counters['task_counter'] += 1
        
        return {
            'success': True,
            'type': 'counter',
            'executed': True
        }
    
    def _parse_counter_content(self, generated_content: str) -> Optional[Dict[str, Any]]:
        """解析生成的计数器内容"""
        try:
            import json
            if '{' in generated_content and '}' in generated_content:
                start = generated_content.index('{')
                end = generated_content.rindex('}') + 1
                json_str = generated_content[start:end]
                return json.loads(json_str)
        except Exception:
            pass
        return None
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        return {'executed': True, 'type': 'counter'}


class UserInteractionAgent(BaseAgent):
    """用户交互LLM - 用户交互界面"""
    
    def generate_response(self, context: Dict[str, Any]) -> str:
        """生成用户响应"""
        if self.dmn_manager.sandbox_pipeline:
            sandbox_context = self.dmn_manager.sandbox_pipeline.process("生成用户友好的响应")
            context_info = sandbox_context.get('response', '')
        else:
            context_info = ""
        
        user_input = context.get('user_input', '')
        
        prompt = f"""你是AbyssAC系统的用户交互Agent。基于系统组装的上下文包，生成高质量回复。

【三层沙盒上下文】
{context_info}

【用户问题】
{user_input}

【输出要求】
1. 直接回答用户的问题，不要提及NNG或记忆文件的存在
2. 如果收集到的信息足够，给出完整、准确的回答
3. 如果信息不足，基于已有信息回答，并说明可能需要更多信息
4. 如果完全无法回答，诚实地说明原因
5. 回答要自然流畅，像正常对话一样

请直接回答用户的问题："""
        
        return self.llm_integration.generate(prompt)
    
    def process_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文处理任务"""
        response = self.generate_response(context)
        return {'response': response}
