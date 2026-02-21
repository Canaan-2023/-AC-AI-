"""
NNG Navigation Graph Manager
NNG导航图管理器 - 负责NNG节点的创建、读取、更新、删除和导航
"""

import os
import json
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from config.system_config import get_config


@dataclass
class NNGNode:
    """NNG节点数据结构"""
    node_id: str
    confidence: float
    timestamp: str
    content: str
    parent_nngs: List[Dict[str, Any]] = None
    child_nngs: List[Dict[str, Any]] = None
    memory_summaries: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.parent_nngs is None:
            self.parent_nngs = []
        if self.child_nngs is None:
            self.child_nngs = []
        if self.memory_summaries is None:
            self.memory_summaries = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "定位": self.node_id,
            "置信度": self.confidence,
            "时间": self.timestamp,
            "内容": self.content,
            "上级关联NNG": self.parent_nngs,
            "下级关联NNG": self.child_nngs,
            "关联的记忆文件摘要": self.memory_summaries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NNGNode':
        """从字典创建"""
        return cls(
            node_id=data.get("定位", ""),
            confidence=data.get("置信度", 0.0),
            timestamp=data.get("时间", ""),
            content=data.get("内容", ""),
            parent_nngs=data.get("上级关联NNG", []),
            child_nngs=data.get("下级关联NNG", []),
            memory_summaries=data.get("关联的记忆文件摘要", [])
        )


class NNGManager:
    """NNG管理器"""
    
    def __init__(self):
        self.config = get_config()
        self.nng_root = self.config.paths.nng_root_path
        self._ensure_root_exists()
    
    def _ensure_root_exists(self):
        """确保root.json存在"""
        root_path = os.path.join(self.nng_root, "root.json")
        if not os.path.exists(root_path):
            self._create_root_node()
    
    def _create_root_node(self):
        """创建根节点"""
        root_data = {
            "一级节点": [],
            "更新时间": self.config.time.get_current_timestamp()
        }
        root_path = os.path.join(self.nng_root, "root.json")
        with open(root_path, 'w', encoding='utf-8') as f:
            json.dump(root_data, f, ensure_ascii=False, indent=2)
    
    def _get_node_path(self, node_id: str) -> str:
        """根据节点ID获取文件路径"""
        if node_id == "root":
            return os.path.join(self.nng_root, "root.json")
        
        parts = node_id.split('.')
        if len(parts) == 1:
            # 一级节点: nng/{node_id}/{node_id}.json
            return os.path.join(self.nng_root, parts[0], f"{parts[0]}.json")
        else:
            # 多级节点: nng/{parent_path}/{node_id}/{node_id}.json
            parent_path = '/'.join(parts[:-1])
            return os.path.join(self.nng_root, parent_path, node_id, f"{node_id}.json")
    
    def _get_node_dir(self, node_id: str) -> str:
        """获取节点所在目录"""
        if node_id == "root":
            return self.nng_root
        
        parts = node_id.split('.')
        if len(parts) == 1:
            return os.path.join(self.nng_root, parts[0])
        else:
            parent_path = '/'.join(parts[:-1])
            return os.path.join(self.nng_root, parent_path, node_id)
    
    def create_node(self, node_id: str, content: str, confidence: float = 1.0,
                    parent_id: Optional[str] = None) -> bool:
        """创建新节点"""
        try:
            # 创建节点目录
            node_dir = self._get_node_dir(node_id)
            os.makedirs(node_dir, exist_ok=True)
            
            # 创建节点文件
            node = NNGNode(
                node_id=node_id,
                confidence=confidence,
                timestamp=self.config.time.get_current_timestamp(),
                content=content
            )
            
            # 如果有父节点，添加关联
            if parent_id:
                parent_path = self._get_relative_path(parent_id)
                node.parent_nngs.append({
                    "节点ID": parent_id,
                    "路径": parent_path,
                    "关联程度": 1.0
                })
                # 更新父节点的子节点列表
                self._add_child_to_parent(parent_id, node_id)
            
            # 保存节点
            node_path = os.path.join(node_dir, f"{node_id}.json")
            with open(node_path, 'w', encoding='utf-8') as f:
                json.dump(node.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 更新root.json中的一级节点列表
            if '.' not in node_id:
                self._add_to_root(node_id, content)
            
            return True
        except Exception as e:
            print(f"创建NNG节点失败: {e}")
            return False
    
    def _get_relative_path(self, node_id: str) -> str:
        """获取相对于nng根目录的路径"""
        if node_id == "root":
            return "nng/root.json"
        
        parts = node_id.split('.')
        if len(parts) == 1:
            return f"nng/{node_id}/{node_id}.json"
        else:
            parent_path = '/'.join(parts[:-1])
            return f"nng/{parent_path}/{node_id}/{node_id}.json"
    
    def _add_child_to_parent(self, parent_id: str, child_id: str):
        """向父节点添加子节点"""
        parent_path = self._get_node_path(parent_id)
        if os.path.exists(parent_path):
            with open(parent_path, 'r', encoding='utf-8') as f:
                parent_data = json.load(f)
            
            child_entry = {
                "节点ID": child_id,
                "路径": self._get_relative_path(child_id),
                "关联程度": 1.0
            }
            
            if "下级关联NNG" not in parent_data:
                parent_data["下级关联NNG"] = []
            
            # 检查是否已存在
            existing = [c["节点ID"] for c in parent_data["下级关联NNG"]]
            if child_id not in existing:
                parent_data["下级关联NNG"].append(child_entry)
                with open(parent_path, 'w', encoding='utf-8') as f:
                    json.dump(parent_data, f, ensure_ascii=False, indent=2)
    
    def _add_to_root(self, node_id: str, content: str):
        """添加节点到root.json"""
        root_path = os.path.join(self.nng_root, "root.json")
        with open(root_path, 'r', encoding='utf-8') as f:
            root_data = json.load(f)
        
        # 添加节点摘要
        node_entry = f"{node_id}（{content}）"
        if node_entry not in root_data["一级节点"]:
            root_data["一级节点"].append(node_entry)
            root_data["更新时间"] = self.config.time.get_current_timestamp()
            with open(root_path, 'w', encoding='utf-8') as f:
                json.dump(root_data, f, ensure_ascii=False, indent=2)
    
    def read_node(self, node_id: str) -> Optional[NNGNode]:
        """读取节点"""
        try:
            node_path = self._get_node_path(node_id)
            if not os.path.exists(node_path):
                return None
            
            with open(node_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return NNGNode.from_dict(data)
        except Exception as e:
            print(f"读取NNG节点失败: {e}")
            return None
    
    def read_node_raw(self, node_id: str) -> Optional[str]:
        """读取节点原始内容"""
        try:
            node_path = self._get_node_path(node_id)
            if not os.path.exists(node_path):
                return None
            
            with open(node_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取NNG节点失败: {e}")
            return None
    
    def update_node(self, node_id: str, **kwargs) -> bool:
        """更新节点"""
        try:
            node = self.read_node(node_id)
            if not node:
                return False
            
            for key, value in kwargs.items():
                if hasattr(node, key):
                    setattr(node, key, value)
            
            node.timestamp = self.config.time.get_current_timestamp()
            
            node_path = self._get_node_path(node_id)
            with open(node_path, 'w', encoding='utf-8') as f:
                json.dump(node.to_dict(), f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"更新NNG节点失败: {e}")
            return False
    
    def delete_node(self, node_id: str) -> bool:
        """删除节点"""
        try:
            import shutil
            node_dir = self._get_node_dir(node_id)
            if os.path.exists(node_dir):
                shutil.rmtree(node_dir)
            
            # 从root.json中移除
            if '.' not in node_id:
                root_path = os.path.join(self.nng_root, "root.json")
                with open(root_path, 'r', encoding='utf-8') as f:
                    root_data = json.load(f)
                
                root_data["一级节点"] = [
                    n for n in root_data["一级节点"] 
                    if not n.startswith(f"{node_id}（")
                ]
                root_data["更新时间"] = self.config.time.get_current_timestamp()
                
                with open(root_path, 'w', encoding='utf-8') as f:
                    json.dump(root_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"删除NNG节点失败: {e}")
            return False
    
    def add_memory_summary(self, node_id: str, memory_id: str, memory_path: str,
                          summary: str, memory_type: str, value_level: str,
                          confidence: float) -> bool:
        """向节点添加记忆摘要"""
        try:
            node = self.read_node(node_id)
            if not node:
                return False
            
            memory_entry = {
                "记忆ID": memory_id,
                "路径": memory_path,
                "摘要": summary,
                "记忆类型": memory_type,
                "价值层级": value_level,
                "置信度": confidence
            }
            
            # 检查是否已存在
            existing = [m["记忆ID"] for m in node.memory_summaries]
            if memory_id not in existing:
                node.memory_summaries.append(memory_entry)
                return self.update_node(node_id, memory_summaries=node.memory_summaries)
            
            return True
        except Exception as e:
            print(f"添加记忆摘要失败: {e}")
            return False
    
    def get_root_content(self) -> str:
        """获取root.json内容"""
        root_path = os.path.join(self.nng_root, "root.json")
        if os.path.exists(root_path):
            with open(root_path, 'r', encoding='utf-8') as f:
                return f.read()
        return "{}"
    
    def list_all_nodes(self) -> List[str]:
        """列出所有节点ID"""
        nodes = []
        for root, dirs, files in os.walk(self.nng_root):
            for file in files:
                if file.endswith('.json'):
                    node_id = file.replace('.json', '')
                    nodes.append(node_id)
        return nodes
    
    def get_child_nodes(self, parent_id: str) -> List[str]:
        """获取子节点列表"""
        node = self.read_node(parent_id)
        if node and node.child_nngs:
            return [c["节点ID"] for c in node.child_nngs]
        return []


# 全局NNG管理器实例
_nng_manager = None


def get_nng_manager() -> NNGManager:
    """获取全局NNG管理器"""
    global _nng_manager
    if _nng_manager is None:
        _nng_manager = NNGManager()
    return _nng_manager
