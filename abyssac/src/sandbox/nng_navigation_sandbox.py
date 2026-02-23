"""NNG导航沙盒模块"""

import os
import time
from typing import Dict, Any, Optional, List, Set

class NNGNavigationSandbox:
    """NNG导航沙盒类"""
    
    def __init__(self, nng_manager, llm_integration, path_parser, parallel_io, config_manager=None):
        """初始化NNG导航沙盒"""
        self.nng_manager = nng_manager
        self.llm_integration = llm_integration
        self.path_parser = path_parser
        self.parallel_io = parallel_io
        self.config_manager = config_manager
        
        self.max_depth = 10
        self.max_nodes = 200
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
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入"""
        context = {
            'user_input': user_input,
            'nng_paths': [],
            'nng_contents': {},
            'notes': '',
            'current_depth': 0,
            'max_depth': self.max_depth,
            'errors': [],
            'navigation_path': []
        }
        
        self.visited_paths.clear()
        self.error_paths.clear()
        
        root_content = self._get_root_content()
        if root_content:
            context['nng_paths'].append('nng/root.json')
            context['nng_contents']['nng/root.json'] = root_content
            self.visited_paths.add('nng/root.json')
        
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
                
                if not normalized_path.startswith('nng/'):
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
                    self.error_paths[path] = f"路径不存在"
                    context['errors'].append(f"路径不存在：{path}")
            
            if not existing_paths:
                if context['current_depth'] == 0:
                    break
                continue
            
            contents = self.parallel_io.read_files(existing_paths, base_dir)
            
            for path, content in contents.items():
                if isinstance(content, dict) and 'error' not in content:
                    self._set_cache(path, content)
                    context['navigation_path'].append({
                        'path': path,
                        'content_preview': str(content.get('内容', ''))[:100],
                        'confidence': content.get('置信度', 0)
                    })
            
            context['nng_paths'].extend(existing_paths)
            context['nng_contents'].update(contents)
            context['current_depth'] += 1
            
            if len(context['nng_paths']) >= self.max_nodes:
                context['errors'].append(f"达到最大节点数限制({self.max_nodes})，停止导航")
                break
        
        if context['current_depth'] >= context['max_depth']:
            context['max_depth_reached'] = True
            context['errors'].append(f"达到最大导航轮次({self.max_depth})，停止导航")
        
        return context
    
    def _get_root_content(self) -> Optional[Dict[str, Any]]:
        """获取root.json内容"""
        try:
            root_path = os.path.join(self.nng_manager.nng_root_path, 'root.json')
            if os.path.exists(root_path):
                import json
                with open(root_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return None
    
    def _get_base_dir(self) -> str:
        return self.nng_manager.nng_root_path
    
    def _generate_prompt(self, context: Dict[str, Any]) -> str:
        """生成提示词"""
        user_input = context['user_input']
        nng_contents = context['nng_contents']
        current_depth = context['current_depth']
        errors = context.get('errors', [])
        
        if current_depth == 0:
            nng_info = "【当前状态】第一轮导航，已读取root.json"
        else:
            nng_info = f"【当前状态】第{current_depth + 1}轮导航，已收集{len(nng_contents)}个NNG节点"
        
        prompt = f"""你是NNG导航系统。根据用户问题，在NNG知识树中选择相关节点。

{nng_info}

【用户问题】
{user_input}

【已收集的NNG节点】
{self._format_nng_contents(nng_contents)}

【系统提示】
{self._format_errors(errors)}

【输出规则】
1. 每行输出一个路径，格式：nng/节点ID.json
2. 可以输出多个路径，系统会并行读取
3. 如果路径不存在，系统会提示，你可以换其他路径
4. 如果已找到足够信息或没有更多相关节点，输出：完成
5. 最后一行写"笔记："开头，说明选择理由

【输出示例】
nng/1.json
nng/2.json
笔记：选择Python核心和网络编程节点，与用户问题相关

现在请输出你选择的NNG节点路径："""
        
        return prompt
    
    def _format_nng_contents(self, nng_contents: Dict[str, Any]) -> str:
        if not nng_contents:
            return "（无，这是第一轮）\n请从root.json中的一级节点开始选择。"
        
        formatted = []
        for path, content in nng_contents.items():
            if isinstance(content, dict) and 'error' not in content:
                content_str = str(content.get('内容', '无内容'))[:200]
                confidence = content.get('置信度', 0.0)
                location = content.get('定位', '')
                
                child_nodes = content.get('下级关联NNG', [])
                child_info = ""
                if child_nodes:
                    child_ids = [c.get('节点ID', '') for c in child_nodes[:5]]
                    child_info = f"\n  可选子节点: nng/{'.json, nng/'.join(child_ids)}.json"
                
                formatted.append(f"[{path}]\n  定位: {location}\n  置信度: {confidence:.2f}\n  内容: {content_str}{child_info}")
            else:
                formatted.append(f"[{path}] 读取失败")
        
        return '\n\n'.join(formatted)
    
    def _format_errors(self, errors: List[str]) -> str:
        if not errors:
            return "无"
        return '\n'.join([f"- {e}" for e in errors[-3:]])
    
    def reset(self):
        self.visited_paths.clear()
        self.error_paths.clear()
        self._cache.clear()
        self._cache_timestamp.clear()
