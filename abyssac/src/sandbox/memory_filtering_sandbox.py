"""记忆筛选沙盒模块"""

import os
import time
from typing import Dict, Any, Optional, List, Set

class MemoryFilteringSandbox:
    """记忆筛选沙盒类"""
    
    def __init__(self, memory_manager, llm_integration, path_parser, parallel_io, config_manager=None):
        """初始化记忆筛选沙盒"""
        self.memory_manager = memory_manager
        self.llm_integration = llm_integration
        self.path_parser = path_parser
        self.parallel_io = parallel_io
        self.config_manager = config_manager
        
        self.max_depth = 6
        self.max_files = 100
        self.max_size = 10 * 1024 * 1024
        
        self.visited_paths: Set[str] = set()
        self.error_paths: Dict[str, str] = {}
        
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Dict[str, float] = {}
        self._cache_ttl = 300
    
    def _get_cache(self, key: str) -> Optional[Any]:
        if key in self._cache:
            timestamp = self._cache_timestamp.get(key, 0)
            if time.time() - timestamp < self._cache_ttl:
                return self._cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any):
        self._cache[key] = value
        self._cache_timestamp[key] = time.time()
    
    def process(self, nng_context: Dict[str, Any]) -> Dict[str, Any]:
        """处理NNG上下文"""
        context = {
            'user_input': nng_context['user_input'],
            'nng_paths': nng_context['nng_paths'],
            'nng_contents': nng_context['nng_contents'],
            'memory_paths': [],
            'memory_contents': {},
            'notes': '',
            'current_depth': 0,
            'max_depth': self.max_depth,
            'errors': [],
            'memory_summaries_from_nng': [],
            'total_size': 0
        }
        
        self.visited_paths.clear()
        self.error_paths.clear()
        
        context['memory_summaries_from_nng'] = self._extract_memory_summaries(nng_context['nng_contents'])
        
        while context['current_depth'] < context['max_depth']:
            prompt = self._generate_prompt(context)
            
            response = self.llm_integration.generate(prompt)
            
            if not response or not response.strip():
                break
            
            parsed_output = self.path_parser.split_paths_and_notes(response)
            paths = parsed_output['paths']
            notes = parsed_output['notes']
            
            context['notes'] = notes
            
            if not paths:
                break
            
            valid_paths = []
            for path in paths:
                normalized_path = self.path_parser.normalize_path(path)
                
                if not normalized_path.startswith('Y层记忆库/'):
                    continue
                
                if normalized_path in self.visited_paths:
                    context['errors'].append(f"循环路径：{normalized_path}")
                    continue
                
                if normalized_path in self.error_paths:
                    continue
                
                valid_paths.append(normalized_path)
            
            if not valid_paths:
                break
            
            base_dir = self._get_base_dir()
            path_exists = self.parallel_io.exists(valid_paths, base_dir)
            
            existing_paths = []
            for path in valid_paths:
                if path_exists.get(path, False):
                    existing_paths.append(path)
                    self.visited_paths.add(path)
                else:
                    self.error_paths[path] = "文件不存在"
                    context['errors'].append(f"文件不存在：{path}")
            
            if not existing_paths:
                if context['current_depth'] == 0:
                    break
                continue
            
            file_infos = self.parallel_io.get_file_info(existing_paths, base_dir)
            
            size_filtered_paths = []
            for path in existing_paths:
                info = file_infos.get(path, {})
                file_size = info.get('file_size', 0)
                
                if context['total_size'] + file_size > self.max_size:
                    continue
                
                size_filtered_paths.append(path)
                context['total_size'] += file_size
            
            if not size_filtered_paths:
                break
            
            contents = self.parallel_io.read_files(size_filtered_paths, base_dir)
            
            for path, content in contents.items():
                if isinstance(content, dict) and 'error' not in content:
                    self._set_cache(path, content)
            
            context['memory_paths'].extend(size_filtered_paths)
            context['memory_contents'].update(contents)
            context['current_depth'] += 1
            
            if len(context['memory_paths']) >= self.max_files:
                context['errors'].append(f"达到最大文件数限制({self.max_files})，停止筛选")
                break
        
        if context['current_depth'] >= context['max_depth']:
            context['max_depth_reached'] = True
            context['errors'].append(f"达到最大筛选轮次({self.max_depth})，停止筛选")
        
        return context
    
    def _extract_memory_summaries(self, nng_contents: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从NNG内容中提取记忆摘要"""
        summaries = []
        for path, content in nng_contents.items():
            if isinstance(content, dict) and 'error' not in content:
                memory_summaries = content.get('关联的记忆文件摘要', [])
                for summary in memory_summaries:
                    summary['source_nng'] = path
                    summaries.append(summary)
        return summaries
    
    def _get_base_dir(self) -> str:
        return self.memory_manager.memory_root_path
    
    def _generate_prompt(self, context: Dict[str, Any]) -> str:
        """生成提示词"""
        user_input = context['user_input']
        nng_contents = context['nng_contents']
        memory_contents = context['memory_contents']
        memory_summaries = context['memory_summaries_from_nng']
        errors = context.get('errors', [])
        current_depth = context['current_depth']
        
        if current_depth == 0:
            status_info = "【当前状态】第一轮筛选，正在从NNG记忆摘要中选择"
        else:
            status_info = f"【当前状态】第{current_depth + 1}轮筛选，已读取{len(memory_contents)}个记忆文件"
        
        prompt = f"""你是记忆筛选系统。根据用户问题和NNG节点中的记忆摘要，选择需要读取的记忆文件。

{status_info}

【用户问题】
{user_input}

【NNG节点信息】
{self._format_nng_contents(nng_contents)}

【NNG中的记忆摘要】
{self._format_memory_summaries(memory_summaries)}

【已读取的记忆文件】
{self._format_memory_contents(memory_contents)}

【系统提示】
{self._format_errors(errors)}

【输出规则】
1. 每行输出一个记忆文件路径
2. 路径格式：Y层记忆库/记忆类型/价值层级/年/月/日/记忆ID.json
3. 记忆类型：分类记忆、元认知记忆、高阶整合记忆、工作记忆
4. 价值层级：高、中、低
5. 如果已获取足够信息或没有相关记忆，输出：完成
6. 最后一行写"笔记："开头，说明选择理由

【输出示例】
Y层记忆库/分类记忆/高/2026/02/20/abc123.json
Y层记忆库/分类记忆/中/2026/02/18/def456.json
笔记：选择高置信度的GIL相关记忆，与用户问题直接相关

现在请输出你选择的记忆文件路径："""
        
        return prompt
    
    def _format_nng_contents(self, nng_contents: Dict[str, Any]) -> str:
        if not nng_contents:
            return "无"
        
        formatted = []
        for path, content in nng_contents.items():
            if isinstance(content, dict) and 'error' not in content:
                content_str = str(content.get('内容', '无内容'))[:150]
                location = content.get('定位', '')
                formatted.append(f"[{path}] 定位:{location}\n  内容:{content_str}")
        
        return '\n'.join(formatted) if formatted else "无"
    
    def _format_memory_summaries(self, memory_summaries: List[Dict[str, Any]]) -> str:
        if not memory_summaries:
            return "（NNG中没有关联的记忆摘要）\n如果没有相关记忆，请输出：完成"
        
        formatted = []
        for i, summary in enumerate(memory_summaries[:15], 1):
            memory_id = summary.get('记忆ID', '未知')
            path = summary.get('路径', '未知')
            abstract = str(summary.get('摘要', '无摘要'))[:100]
            memory_type = summary.get('记忆类型', '未知')
            value_level = summary.get('价值层级', '未知')
            confidence = summary.get('置信度', 0)
            
            formatted.append(f"{i}. [{memory_id}] {memory_type}/{value_level} 置信度:{confidence:.2f}\n   路径: {path}\n   摘要: {abstract}")
        
        if len(memory_summaries) > 15:
            formatted.append(f"... 还有 {len(memory_summaries) - 15} 条记忆摘要")
        
        return '\n'.join(formatted)
    
    def _format_memory_contents(self, memory_contents: Dict[str, Any]) -> str:
        if not memory_contents:
            return "（无，这是第一轮筛选）"
        
        formatted = []
        for path, content in memory_contents.items():
            if isinstance(content, dict) and 'error' not in content:
                core = content.get('核心内容', {})
                user_in = str(core.get('用户输入', ''))[:50]
                ai_out = str(core.get('AI响应', ''))[:80]
                confidence = content.get('置信度', 0.0)
                
                formatted.append(f"[{path}] 置信度:{confidence:.2f}\n  用户:{user_in}\n  AI:{ai_out}")
        
        return '\n'.join(formatted) if formatted else "无"
    
    def _format_errors(self, errors: List[str]) -> str:
        if not errors:
            return "无"
        return '\n'.join([f"- {e}" for e in errors[-3:]])
    
    def reset(self):
        self.visited_paths.clear()
        self.error_paths.clear()
        self._cache.clear()
        self._cache_timestamp.clear()
