"""NNG管理器模块"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class NNGManager:
    """NNG管理器类"""
    
    def __init__(self, nng_root_path: str):
        """初始化NNG管理器
        
        Args:
            nng_root_path: NNG根目录路径
        """
        self.nng_root_path = nng_root_path
        os.makedirs(self.nng_root_path, exist_ok=True)
        
        self.root_file_path = os.path.join(self.nng_root_path, 'root.json')
        if not os.path.exists(self.root_file_path):
            self._create_root_file()
    
    def _create_root_file(self):
        """创建root.json文件"""
        root_content = {
            "一级节点": [
                {
                    "节点ID": "1",
                    "摘要": "Python核心概念与架构",
                    "文件地址": "nng/1.json"
                },
                {
                    "节点ID": "2",
                    "摘要": "网络编程与通信",
                    "文件地址": "nng/2.json"
                },
                {
                    "节点ID": "3",
                    "摘要": "系统架构与设计模式",
                    "文件地址": "nng/3.json"
                },
                {
                    "节点ID": "4",
                    "摘要": "数据结构与算法",
                    "文件地址": "nng/4.json"
                },
                {
                    "节点ID": "5",
                    "摘要": "机器学习与人工智能",
                    "文件地址": "nng/5.json"
                }
            ],
            "更新时间": self._get_current_time()
        }
        
        with open(self.root_file_path, 'w', encoding='utf-8') as f:
            json.dump(root_content, f, ensure_ascii=False, indent=2)
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        return datetime.now().isoformat()
    
    def get_root_nodes(self) -> List[Dict[str, Any]]:
        """获取一级节点"""
        try:
            with open(self.root_file_path, 'r', encoding='utf-8') as f:
                root_content = json.load(f)
                return root_content.get('一级节点', [])
        except Exception:
            return []
    
    def get_root_content(self) -> Optional[Dict[str, Any]]:
        """获取root.json完整内容"""
        try:
            with open(self.root_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def add_root_node(self, node_id: str, summary: str, node_path: str):
        """添加一级节点
        
        Args:
            node_id: 节点ID
            summary: 节点摘要
            node_path: 节点文件路径
        """
        try:
            with open(self.root_file_path, 'r', encoding='utf-8') as f:
                root_content = json.load(f)
            
            existing_nodes = root_content.get('一级节点', [])
            node_exists = any(node.get('节点ID') == node_id for node in existing_nodes)
            
            if not node_exists:
                new_node = {
                    "节点ID": node_id,
                    "摘要": summary,
                    "文件地址": node_path
                }
                existing_nodes.append(new_node)
                
                root_content['一级节点'] = existing_nodes
                root_content['更新时间'] = self._get_current_time()
                
                with open(self.root_file_path, 'w', encoding='utf-8') as f:
                    json.dump(root_content, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def remove_root_node(self, node_id: str):
        """移除一级节点"""
        try:
            with open(self.root_file_path, 'r', encoding='utf-8') as f:
                root_content = json.load(f)
            
            existing_nodes = root_content.get('一级节点', [])
            updated_nodes = [node for node in existing_nodes if node.get('节点ID') != node_id]
            
            root_content['一级节点'] = updated_nodes
            root_content['更新时间'] = self._get_current_time()
            
            with open(self.root_file_path, 'w', encoding='utf-8') as f:
                json.dump(root_content, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def update_node_summary(self, node_id: str, summary: str):
        """更新节点摘要"""
        try:
            with open(self.root_file_path, 'r', encoding='utf-8') as f:
                root_content = json.load(f)
            
            existing_nodes = root_content.get('一级节点', [])
            for node in existing_nodes:
                if node.get('节点ID') == node_id:
                    node['摘要'] = summary
                    break
            
            root_content['一级节点'] = existing_nodes
            root_content['更新时间'] = self._get_current_time()
            
            with open(self.root_file_path, 'w', encoding='utf-8') as f:
                json.dump(root_content, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def get_node(self, node_path: str) -> Optional[Dict[str, Any]]:
        """获取节点内容
        
        Args:
            node_path: 节点文件路径（相对路径，如 "1.json" 或 "1/1.2.json"）
            
        Returns:
            节点内容
        """
        try:
            if node_path.startswith('nng/'):
                node_path = node_path[4:]
            
            full_path = os.path.join(self.nng_root_path, node_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def save_node(self, node_path: str, node_content: Dict[str, Any]):
        """保存节点内容
        
        Args:
            node_path: 节点文件路径（相对路径）
            node_content: 节点内容
        """
        try:
            if node_path.startswith('nng/'):
                node_path = node_path[4:]
            
            full_path = os.path.join(self.nng_root_path, node_path)
            directory = os.path.dirname(full_path)
            os.makedirs(directory, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(node_content, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def create_node(self, node_id: str, content: str, confidence: float = 0.8,
                    parent_nodes: List[Dict[str, Any]] = None,
                    child_nodes: List[Dict[str, Any]] = None,
                    memory_summaries: List[Dict[str, Any]] = None) -> str:
        """创建新节点
        
        Args:
            node_id: 节点ID（如 "1.2.3"）
            content: 节点内容
            confidence: 置信度
            parent_nodes: 上级关联节点
            child_nodes: 下级关联节点
            memory_summaries: 关联的记忆文件摘要
            
        Returns:
            节点路径
        """
        node_content = {
            "定位": node_id,
            "置信度": confidence,
            "时间": self._get_current_time(),
            "内容": content,
            "上级关联NNG": parent_nodes or [],
            "下级关联NNG": child_nodes or [],
            "关联的记忆文件摘要": memory_summaries or []
        }
        
        node_path = self._get_node_path(node_id)
        self.save_node(node_path, node_content)
        
        if '.' not in node_id:
            self.add_root_node(node_id, content[:50], f"nng/{node_path}")
        
        return node_path
    
    def _get_node_path(self, node_id: str) -> str:
        """根据节点ID获取节点路径
        
        Args:
            node_id: 节点ID（如 "1.2.3"）
            
        Returns:
            节点路径（如 "1/1.2/1.2.3.json"）
        """
        parts = node_id.split('.')
        if len(parts) == 1:
            return f"{node_id}.json"
        else:
            dir_path = '/'.join(['.'.join(parts[:i+1]) for i in range(len(parts)-1)])
            return f"{dir_path}/{node_id}.json"
    
    def delete_node(self, node_path: str):
        """删除节点"""
        try:
            if node_path.startswith('nng/'):
                node_path = node_path[4:]
            
            full_path = os.path.join(self.nng_root_path, node_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception:
            pass
    
    def list_nodes(self, directory: str = '') -> List[str]:
        """列出指定目录下的所有节点"""
        nodes = []
        try:
            full_directory = os.path.join(self.nng_root_path, directory)
            if not os.path.exists(full_directory):
                return nodes
            
            for root, dirs, files in os.walk(full_directory):
                for file in files:
                    if file.endswith('.json') and file != 'root.json':
                        relative_path = os.path.relpath(os.path.join(root, file), self.nng_root_path)
                        nodes.append(relative_path.replace('\\', '/'))
        except Exception:
            pass
        
        return nodes
    
    def search_nodes(self, keyword: str) -> List[str]:
        """搜索包含关键字的节点"""
        matching_nodes = []
        try:
            all_nodes = self.list_nodes()
            
            for node_path in all_nodes:
                node_content = self.get_node(node_path)
                if node_content:
                    content_str = json.dumps(node_content, ensure_ascii=False)
                    if keyword in content_str:
                        matching_nodes.append(node_path)
        except Exception:
            pass
        
        return matching_nodes
    
    def get_node_hierarchy(self, node_id: str) -> Dict[str, Any]:
        """获取节点的层级信息"""
        parts = node_id.split('.')
        hierarchy = {
            'node_id': node_id,
            'level': len(parts),
            'parent_id': '.'.join(parts[:-1]) if len(parts) > 1 else None,
            'path': self._get_node_path(node_id)
        }
        
        if hierarchy['parent_id']:
            parent_content = self.get_node(self._get_node_path(hierarchy['parent_id']))
            hierarchy['parent_content'] = parent_content
        
        return hierarchy
    
    def update_node_associations(self, node_path: str, parent_nodes: List[Dict[str, Any]], child_nodes: List[Dict[str, Any]]):
        """更新节点的关联信息"""
        try:
            node_content = self.get_node(node_path)
            if not node_content:
                return
            
            node_content['上级关联NNG'] = parent_nodes
            node_content['下级关联NNG'] = child_nodes
            
            self.save_node(node_path, node_content)
        except Exception:
            pass
    
    def add_memory_summary(self, node_path: str, memory_summary: Dict[str, Any]):
        """添加记忆摘要到节点"""
        try:
            node_content = self.get_node(node_path)
            if not node_content:
                return
            
            if '关联的记忆文件摘要' not in node_content:
                node_content['关联的记忆文件摘要'] = []
            
            node_content['关联的记忆文件摘要'].append(memory_summary)
            self.save_node(node_path, node_content)
        except Exception:
            pass
    
    def validate_node(self, node_content: Dict[str, Any]) -> bool:
        """验证节点内容"""
        try:
            required_fields = ['定位', '置信度', '时间', '内容']
            for field in required_fields:
                if field not in node_content:
                    return False
            
            if not isinstance(node_content['定位'], str):
                return False
            if not isinstance(node_content['置信度'], (int, float)):
                return False
            if not isinstance(node_content['时间'], str):
                return False
            if not isinstance(node_content['内容'], str):
                return False
            
            if node_content['置信度'] < 0 or node_content['置信度'] > 1:
                return False
            
            return True
        except Exception:
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取NNG统计信息"""
        stats = {
            'total_nodes': 0,
            'nodes_by_level': {},
            'avg_confidence': 0.0
        }
        
        try:
            all_nodes = self.list_nodes()
            stats['total_nodes'] = len(all_nodes)
            
            confidences = []
            for node_path in all_nodes:
                node_content = self.get_node(node_path)
                if node_content:
                    node_id = node_content.get('定位', '')
                    level = len(node_id.split('.'))
                    
                    if level not in stats['nodes_by_level']:
                        stats['nodes_by_level'][level] = 0
                    stats['nodes_by_level'][level] += 1
                    
                    confidence = node_content.get('置信度', 0)
                    if confidence > 0:
                        confidences.append(confidence)
            
            if confidences:
                stats['avg_confidence'] = sum(confidences) / len(confidences)
        except Exception:
            pass
        
        return stats
