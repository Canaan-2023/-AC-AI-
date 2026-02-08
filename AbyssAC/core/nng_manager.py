"""
NNG导航节点图管理器
"""
import json
import os
import fcntl
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class NNGNode:
    """NNG节点数据"""
    定位: str  # 如 "1.1.2"
    关联性: int  # 0-100
    置信度: int  # 0-100
    时间: str
    内容: str
    关联的记忆文件摘要: List[Dict]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "NNGNode":
        return cls(**data)


class NNGManager:
    """NNG导航图管理器"""
    
    def __init__(self, config: Dict):
        self.nng_dir = Path(config["paths"]["nng_dir"])
        self.root_file = self.nng_dir / "root.json"
        self._ensure_root()
    
    def _ensure_root(self):
        """确保root.json存在"""
        if not self.root_file.exists():
            self._save_root({"一级节点": [], "更新时间": ""})
    
    def _save_root(self, data: Dict):
        """保存root.json"""
        with open(self.root_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_root(self) -> Dict:
        """加载root.json"""
        with open(self.root_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_node_file_path(self, node_id: str) -> Path:
        """获取节点文件路径"""
        parts = node_id.split('.')
        path = self.nng_dir
        for i, part in enumerate(parts[:-1]):
            path = path / '.'.join(parts[:i+1])
        path = path / f"{node_id}.json"
        return path
    
    def _get_node_dir_path(self, node_id: str) -> Path:
        """获取节点目录路径（用于存储子节点）"""
        parts = node_id.split('.')
        path = self.nng_dir
        for part in parts:
            path = path / '.'.join(parts[:parts.index(part)+1])
        return path
    
    def _parse_node_id(self, node_id: str) -> Tuple[str, Optional[str]]:
        """
        解析节点ID
        返回: (父节点ID, 当前节点序号)
        例如: "1.2.3" -> ("1.2", "3")
        """
        parts = node_id.split('.')
        if len(parts) == 1:
            return ("root", parts[0])
        else:
            parent = '.'.join(parts[:-1])
            return (parent, parts[-1])
    
    def is_empty(self) -> bool:
        """检查NNG是否为空"""
        root = self._load_root()
        return len(root.get("一级节点", [])) == 0
    
    def create_node(self, node_id: str, content: str,
                   confidence: int = 80,
                   related_memories: Optional[List[Dict]] = None,
                   relevance: int = 50) -> bool:
        """
        创建NNG节点
        
        Args:
            node_id: 节点定位，如 "1", "1.1", "1.1.2"
            content: 节点内容描述
            confidence: 置信度 0-100
            related_memories: 关联的记忆摘要列表
            relevance: 关联性 0-100
        
        Returns:
            是否成功
        """
        try:
            # 确保父节点存在
            parent_id, _ = self._parse_node_id(node_id)
            
            if parent_id != "root":
                parent_path = self._get_node_file_path(parent_id)
                if not parent_path.exists():
                    return False  # 父节点不存在
            
            # 创建节点目录
            node_dir = self._get_node_dir_path(node_id)
            node_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建节点文件
            node_file = self._get_node_file_path(node_id)
            
            node_data = {
                "定位": node_id,
                "关联性": relevance,
                "置信度": confidence,
                "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "内容": content,
                "关联的记忆文件摘要": related_memories or []
            }
            
            with open(node_file, 'w', encoding='utf-8') as f:
                json.dump(node_data, f, ensure_ascii=False, indent=2)
            
            # 更新父节点引用
            self._update_parent_reference(node_id, content)
            
            return True
        except Exception as e:
            print(f"创建NNG节点失败: {e}")
            return False
    
    def _update_parent_reference(self, node_id: str, content: str):
        """更新父节点对子节点的引用"""
        parent_id, seq = self._parse_node_id(node_id)
        
        if parent_id == "root":
            # 更新root.json
            root = self._load_root()
            nodes = root.get("一级节点", [])
            
            # 检查是否已存在
            existing = False
            for i, node in enumerate(nodes):
                if node.startswith(f"{seq}("):
                    nodes[i] = f"{seq}({content[:30]})"
                    existing = True
                    break
            
            if not existing:
                nodes.append(f"{seq}({content[:30]})")
            
            root["一级节点"] = nodes
            root["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._save_root(root)
        else:
            # 更新父节点文件
            parent_file = self._get_node_file_path(parent_id)
            if parent_file.exists():
                with open(parent_file, 'r', encoding='utf-8') as f:
                    parent_data = json.load(f)
                
                # 在内容中添加子节点信息
                sub_nodes_key = "子节点"
                if sub_nodes_key not in parent_data:
                    parent_data[sub_nodes_key] = []
                
                sub_nodes = parent_data[sub_nodes_key]
                existing = False
                for i, sub in enumerate(sub_nodes):
                    if isinstance(sub, str) and sub.startswith(f"{seq}("):
                        sub_nodes[i] = f"{seq}({content[:30]})"
                        existing = True
                        break
                
                if not existing:
                    sub_nodes.append(f"{seq}({content[:30]})")
                
                parent_data[sub_nodes_key] = sub_nodes
                parent_data["时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                with open(parent_file, 'w', encoding='utf-8') as f:
                    json.dump(parent_data, f, ensure_ascii=False, indent=2)
    
    def get_node(self, node_id: str) -> Optional[NNGNode]:
        """获取节点"""
        node_file = self._get_node_file_path(node_id)
        if not node_file.exists():
            return None
        
        try:
            with open(node_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return NNGNode.from_dict(data)
        except:
            return None
    
    def update_node(self, node_id: str, **kwargs) -> bool:
        """更新节点"""
        node_file = self._get_node_file_path(node_id)
        if not node_file.exists():
            return False
        
        try:
            with open(node_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for key, value in kwargs.items():
                if key in data:
                    data[key] = value
            
            data["时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(node_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except:
            return False
    
    def delete_node(self, node_id: str) -> bool:
        """删除节点及其所有子节点"""
        try:
            # 删除节点文件
            node_file = self._get_node_file_path(node_id)
            if node_file.exists():
                node_file.unlink()
            
            # 删除节点目录（包含所有子节点）
            node_dir = self._get_node_dir_path(node_id)
            if node_dir.exists():
                import shutil
                shutil.rmtree(node_dir)
            
            # 从父节点引用中移除
            parent_id, seq = self._parse_node_id(node_id)
            if parent_id == "root":
                root = self._load_root()
                nodes = root.get("一级节点", [])
                root["一级节点"] = [n for n in nodes if not n.startswith(f"{seq}(")]
                self._save_root(root)
            else:
                parent_file = self._get_node_file_path(parent_id)
                if parent_file.exists():
                    with open(parent_file, 'r', encoding='utf-8') as f:
                        parent_data = json.load(f)
                    sub_nodes = parent_data.get("子节点", [])
                    parent_data["子节点"] = [n for n in sub_nodes if not n.startswith(f"{seq}(")]
                    with open(parent_file, 'w', encoding='utf-8') as f:
                        json.dump(parent_data, f, ensure_ascii=False, indent=2)
            
            return True
        except:
            return False
    
    def get_structure(self) -> Dict:
        """获取NNG整体结构（用于展示给LLM）"""
        root = self._load_root()
        structure = {
            "根节点": root.get("一级节点", []),
            "结构说明": "使用 'NNG1.2.3' 格式请求特定节点"
        }
        return structure
    
    def get_node_tree(self, node_id: Optional[str] = None, depth: int = 2) -> Dict:
        """
        获取节点树结构
        
        Args:
            node_id: 起始节点ID，None表示从root开始
            depth: 递归深度
        """
        if depth <= 0:
            return {}
        
        if node_id is None:
            # 返回一级节点列表
            root = self._load_root()
            return {"一级节点": root.get("一级节点", [])}
        
        node = self.get_node(node_id)
        if not node:
            return {}
        
        result = {
            "定位": node.定位,
            "内容": node.内容,
            "置信度": node.置信度,
        }
        
        # 获取子节点
        node_file = self._get_node_file_path(node_id)
        if node_file.exists():
            with open(node_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            sub_nodes = data.get("子节点", [])
            result["子节点"] = sub_nodes
            
            # 递归获取子节点详情
            if depth > 1 and sub_nodes:
                result["子节点详情"] = {}
                for sub in sub_nodes:
                    # 提取子节点ID
                    import re
                    match = re.match(r'(\d+)', sub)
                    if match:
                        sub_id = f"{node_id}.{match.group(1)}"
                        sub_tree = self.get_node_tree(sub_id, depth - 1)
                        if sub_tree:
                            result["子节点详情"][sub_id] = sub_tree
        
        return result
    
    def find_nodes_by_content(self, keyword: str) -> List[str]:
        """根据内容关键词查找节点"""
        results = []
        
        for json_file in self.nng_dir.rglob("*.json"):
            if json_file.name == "root.json":
                continue
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                content = data.get("内容", "")
                if keyword.lower() in content.lower():
                    results.append(data.get("定位", ""))
            except:
                pass
        
        return results
    
    def add_memory_to_node(self, node_id: str, memory_summary: Dict) -> bool:
        """向节点添加关联记忆"""
        node = self.get_node(node_id)
        if not node:
            return False
        
        memories = node.关联的记忆文件摘要
        memories.append(memory_summary)
        
        return self.update_node(node_id, 关联的记忆文件摘要=memories)
    
    def remove_memory_from_node(self, node_id: str, memory_id: int) -> bool:
        """从节点移除关联记忆"""
        node = self.get_node(node_id)
        if not node:
            return False
        
        memories = [m for m in node.关联的记忆文件摘要 
                   if m.get("记忆ID") != memory_id]
        
        return self.update_node(node_id, 关联的记忆文件摘要=memories)
    
    def get_next_child_id(self, parent_id: str) -> Optional[str]:
        """获取下一个可用子节点ID"""
        if parent_id == "root":
            root = self._load_root()
            nodes = root.get("一级节点", [])
            existing = set()
            for node in nodes:
                import re
                match = re.match(r'(\d+)', node)
                if match:
                    existing.add(int(match.group(1)))
            
            for i in range(1, 1000):
                if i not in existing:
                    return str(i)
        else:
            parent_file = self._get_node_file_path(parent_id)
            if not parent_file.exists():
                return None
            
            with open(parent_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            sub_nodes = data.get("子节点", [])
            existing = set()
            for sub in sub_nodes:
                import re
                match = re.match(r'(\d+)', sub)
                if match:
                    existing.add(int(match.group(1)))
            
            for i in range(1, 1000):
                if i not in existing:
                    return f"{parent_id}.{i}"
        
        return None


# 全局实例
_nng_manager: Optional[NNGManager] = None


def init_nng_manager(config: Dict) -> NNGManager:
    """初始化NNG管理器"""
    global _nng_manager
    _nng_manager = NNGManager(config)
    return _nng_manager


def get_nng_manager() -> Optional[NNGManager]:
    """获取NNG管理器实例"""
    return _nng_manager
