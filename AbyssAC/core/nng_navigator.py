"""AbyssAC NNG导航系统模块

管理NNG（导航节点图）的CRUD操作，提供导航功能，
支持节点间的双向链接和完整性验证。
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, asdict

from utils.file_ops import safe_read_json, safe_write_json, FileLock
from utils.logger import get_logger


logger = get_logger()


@dataclass
class NNGNode:
    """NNG节点数据结构"""
    location: str  # 节点位置，如 "1.2.3"
    confidence: int  # 置信度 0-100
    timestamp: str  # 创建时间
    content: str  # 节点内容描述
    memory_summaries: List[Dict[str, Any]]  # 关联的记忆摘要列表
    parent_nng: Optional[str]  # 上级NNG
    child_nngs: List[Dict[str, Any]]  # 下级NNG列表


class NNGNavigator:
    """NNG导航管理器"""
    
    def __init__(self, base_path: str):
        """
        初始化NNG导航器
        
        Args:
            base_path: NNG存储基础路径
        """
        self.nng_path = base_path
        self.root_file = os.path.join(self.nng_path, "root.json")
        
        # 内存中的节点缓存
        self._node_cache: Dict[str, NNGNode] = {}
        
        self._ensure_structure()
    
    def _ensure_structure(self) -> None:
        """确保目录结构存在"""
        os.makedirs(self.nng_path, exist_ok=True)
        
        # 确保root.json存在
        if not os.path.exists(self.root_file):
            root_data = {
                "一级节点": [],
                "更新时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            safe_write_json(self.root_file, root_data)
    
    def _get_node_filepath(self, location: str) -> str:
        """获取节点文件的完整路径
        
        Args:
            location: 节点位置，如 "1.2.3"
        
        Returns:
            文件完整路径
        """
        if location == "root":
            return self.root_file
        
        parts = location.split('.')
        
        # 构建路径: nng/1/1/1.2/1.2/1.2.3.json
        path_parts = [self.nng_path]
        current = ""
        for i, part in enumerate(parts):
            if i == 0:
                current = part
                path_parts.append(current)
            else:
                current = f"{current}.{part}"
                if i < len(parts) - 1:
                    path_parts.append(current)
        
        path_parts.append(f"{location}.json")
        return os.path.join(*path_parts)
    
    def _get_parent_location(self, location: str) -> Optional[str]:
        """获取父节点位置
        
        Args:
            location: 节点位置
        
        Returns:
            父节点位置，根节点返回None
        """
        if location == "root" or '.' not in location:
            return "root"
        
        parts = location.rsplit('.', 1)
        return parts[0]
    
    def _load_node(self, location: str) -> Optional[NNGNode]:
        """加载节点数据
        
        Args:
            location: 节点位置
        
        Returns:
            节点数据，不存在返回None
        """
        # 先检查缓存
        if location in self._node_cache:
            return self._node_cache[location]
        
        filepath = self._get_node_filepath(location)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            data = safe_read_json(filepath)
            
            node = NNGNode(
                location=data.get("定位", location),
                confidence=data.get("置信度", 70),
                timestamp=data.get("时间", ""),
                content=data.get("内容", ""),
                memory_summaries=data.get("关联的记忆文件摘要", []),
                parent_nng=data.get("上级关联NNG"),
                child_nngs=data.get("下级关联NNG", [])
            )
            
            self._node_cache[location] = node
            return node
        
        except Exception as e:
            logger.error(f"加载NNG节点失败 {location}: {e}")
            return None
    
    def _save_node(self, node: NNGNode) -> bool:
        """保存节点数据
        
        Args:
            node: 节点数据
        
        Returns:
            是否保存成功
        """
        filepath = self._get_node_filepath(node.location)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        data = {
            "定位": node.location,
            "置信度": node.confidence,
            "时间": node.timestamp,
            "内容": node.content,
            "关联的记忆文件摘要": node.memory_summaries,
            "上级关联NNG": node.parent_nng,
            "下级关联NNG": node.child_nngs
        }
        
        try:
            safe_write_json(filepath, data)
            self._node_cache[node.location] = node
            return True
        except Exception as e:
            logger.error(f"保存NNG节点失败 {node.location}: {e}")
            return False
    
    def create_node(
        self,
        location: str,
        content: str,
        confidence: int = 70,
        memory_summaries: Optional[List[Dict]] = None
    ) -> bool:
        """
        创建新NNG节点
        
        Args:
            location: 节点位置，如 "1.2.3"
            content: 节点内容描述
            confidence: 置信度
            memory_summaries: 关联的记忆摘要列表
        
        Returns:
            是否创建成功
        """
        # 检查节点是否已存在
        if self._load_node(location):
            logger.warning(f"NNG节点已存在: {location}")
            return False
        
        # 获取父节点
        parent_location = self._get_parent_location(location)
        
        # 如果不是根节点，确保父节点存在
        if parent_location != "root" and not self._load_node(parent_location):
            logger.error(f"父节点不存在: {parent_location}")
            return False
        
        # 创建节点
        node = NNGNode(
            location=location,
            confidence=confidence,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            content=content,
            memory_summaries=memory_summaries or [],
            parent_nng=parent_location if parent_location != "root" else None,
            child_nngs=[]
        )
        
        # 保存节点
        if not self._save_node(node):
            return False
        
        # 更新父节点的子节点列表
        if parent_location == "root":
            self._update_root_children(location, content)
        else:
            self._update_parent_children(parent_location, location, content)
        
        logger.info(f"创建NNG节点成功: {location}")
        
        return True
    
    def _update_root_children(self, child_location: str, child_content: str) -> bool:
        """更新root.json的子节点列表
        
        Args:
            child_location: 子节点位置
            child_content: 子节点内容摘要
        
        Returns:
            是否更新成功
        """
        try:
            data = safe_read_json(self.root_file, {"一级节点": [], "更新时间": ""})
            
            # 添加新节点到列表
            node_entry = f"{child_location}（{child_content[:20]}...）"
            if node_entry not in data["一级节点"]:
                data["一级节点"].append(node_entry)
            
            data["更新时间"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            safe_write_json(self.root_file, data)
            return True
        
        except Exception as e:
            logger.error(f"更新root.json失败: {e}")
            return False
    
    def _update_parent_children(
        self,
        parent_location: str,
        child_location: str,
        child_content: str,
        relation_score: int = 80
    ) -> bool:
        """更新父节点的子节点列表
        
        Args:
            parent_location: 父节点位置
            child_location: 子节点位置
            child_content: 子节点内容摘要
            relation_score: 关联程度分数
        
        Returns:
            是否更新成功
        """
        parent = self._load_node(parent_location)
        if not parent:
            return False
        
        # 检查是否已存在
        existing = [c for c in parent.child_nngs if c.get("节点") == child_location]
        if existing:
            return True
        
        # 添加子节点信息
        child_info = {
            "节点": child_location,
            "摘要": child_content[:50],
            "关联程度": relation_score
        }
        
        parent.child_nngs.append(child_info)
        
        return self._save_node(parent)
    
    def get_node(self, location: str) -> Optional[NNGNode]:
        """
        获取节点数据
        
        Args:
            location: 节点位置
        
        Returns:
            节点数据
        """
        return self._load_node(location)
    
    def get_root(self) -> Dict[str, Any]:
        """
        获取根节点数据
        
        Returns:
            root.json内容
        """
        return safe_read_json(self.root_file, {"一级节点": [], "更新时间": ""})
    
    def update_node(
        self,
        location: str,
        content: Optional[str] = None,
        confidence: Optional[int] = None,
        memory_summaries: Optional[List[Dict]] = None
    ) -> bool:
        """
        更新节点数据
        
        Args:
            location: 节点位置
            content: 新内容
            confidence: 新置信度
            memory_summaries: 新的记忆摘要列表
        
        Returns:
            是否更新成功
        """
        node = self._load_node(location)
        if not node:
            return False
        
        if content is not None:
            node.content = content
        
        if confidence is not None:
            node.confidence = confidence
        
        if memory_summaries is not None:
            node.memory_summaries = memory_summaries
        
        return self._save_node(node)
    
    def add_memory_summary(
        self,
        location: str,
        memory_id: int,
        summary: str,
        memory_type: str,
        value_level: Optional[str] = None
    ) -> bool:
        """
        添加记忆摘要到节点
        
        Args:
            location: 节点位置
            memory_id: 记忆ID
            summary: 记忆摘要
            memory_type: 记忆类型
            value_level: 价值层级
        
        Returns:
            是否添加成功
        """
        node = self._load_node(location)
        if not node:
            return False
        
        # 检查是否已存在
        existing = [m for m in node.memory_summaries if m.get("记忆ID") == str(memory_id)]
        if existing:
            return True
        
        summary_info = {
            "记忆ID": str(memory_id),
            "摘要": summary,
            "记忆类型": memory_type
        }
        
        if value_level:
            summary_info["价值层级"] = value_level
        
        node.memory_summaries.append(summary_info)
        
        return self._save_node(node)
    
    def remove_memory_summary(self, location: str, memory_id: int) -> bool:
        """
        从节点移除记忆摘要
        
        Args:
            location: 节点位置
            memory_id: 记忆ID
        
        Returns:
            是否移除成功
        """
        node = self._load_node(location)
        if not node:
            return False
        
        node.memory_summaries = [
            m for m in node.memory_summaries 
            if m.get("记忆ID") != str(memory_id)
        ]
        
        return self._save_node(node)
    
    def delete_node(self, location: str, transfer_to: Optional[str] = None) -> bool:
        """
        删除节点
        
        Args:
            location: 要删除的节点位置
            transfer_to: 内容转移到的目标节点
        
        Returns:
            是否删除成功
        """
        if location == "root":
            logger.error("不能删除root节点")
            return False
        
        node = self._load_node(location)
        if not node:
            return False
        
        # 如果有子节点，不能删除
        if node.child_nngs:
            logger.error(f"节点 {location} 有子节点，不能删除")
            return False
        
        # 如果需要转移内容
        if transfer_to:
            target = self._load_node(transfer_to)
            if target:
                target.memory_summaries.extend(node.memory_summaries)
                self._save_node(target)
        
        # 从父节点移除
        parent_location = self._get_parent_location(location)
        if parent_location == "root":
            self._remove_from_root(location)
        else:
            self._remove_from_parent(parent_location, location)
        
        # 删除文件
        filepath = self._get_node_filepath(location)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            
            # 从缓存移除
            if location in self._node_cache:
                del self._node_cache[location]
            
            logger.info(f"删除NNG节点: {location}")
            return True
        
        except Exception as e:
            logger.error(f"删除NNG节点失败 {location}: {e}")
            return False
    
    def _remove_from_root(self, location: str) -> bool:
        """从root.json移除节点"""
        try:
            data = safe_read_json(self.root_file, {"一级节点": [], "更新时间": ""})
            
            data["一级节点"] = [
                n for n in data["一级节点"] 
                if not n.startswith(f"{location}（")
            ]
            
            data["更新时间"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            safe_write_json(self.root_file, data)
            return True
        
        except Exception as e:
            logger.error(f"从root.json移除节点失败: {e}")
            return False
    
    def _remove_from_parent(self, parent_location: str, child_location: str) -> bool:
        """从父节点移除子节点"""
        parent = self._load_node(parent_location)
        if not parent:
            return False
        
        parent.child_nngs = [
            c for c in parent.child_nngs 
            if c.get("节点") != child_location
        ]
        
        return self._save_node(parent)
    
    def get_children(self, location: str) -> List[Dict[str, Any]]:
        """
        获取子节点列表
        
        Args:
            location: 节点位置
        
        Returns:
            子节点信息列表
        """
        if location == "root":
            data = safe_read_json(self.root_file, {"一级节点": []})
            children = []
            for node_entry in data.get("一级节点", []):
                match = re.match(r'(\d+)（(.+)）', node_entry)
                if match:
                    children.append({
                        "节点": match.group(1),
                        "摘要": match.group(2).rstrip('.'),
                        "关联程度": 80
                    })
            return children
        
        node = self._load_node(location)
        if not node:
            return []
        
        return node.child_nngs
    
    def get_siblings(self, location: str) -> List[str]:
        """
        获取兄弟节点列表
        
        Args:
            location: 节点位置
        
        Returns:
            兄弟节点位置列表
        """
        parent = self._get_parent_location(location)
        children = self.get_children(parent)
        
        return [c["节点"] for c in children if c["节点"] != location]
    
    def navigate(self, current: str, action: str, target: Optional[str] = None) -> Tuple[str, bool]:
        """
        执行导航操作
        
        Args:
            current: 当前位置
            action: 操作类型 (GOTO, BACK, STAY, ROOT)
            target: 目标位置（GOTO时使用）
        
        Returns:
            (新位置, 是否成功)
        """
        if action == "STAY":
            return current, True
        
        if action == "ROOT":
            return "root", True
        
        if action == "BACK":
            parent = self._get_parent_location(current)
            return parent, True
        
        if action == "GOTO":
            if not target:
                return current, False
            
            # 检查目标是否存在
            if not self._load_node(target):
                logger.warning(f"导航目标不存在: {target}")
                return current, False
            
            return target, True
        
        return current, False
    
    def verify_integrity(self) -> Dict[str, Any]:
        """
        验证NNG完整性
        
        Returns:
            验证结果
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {
                "total_nodes": 0,
                "orphan_nodes": [],
                "broken_links": []
            }
        }
        
        # 收集所有节点
        all_nodes: Set[str] = set()
        
        for root, dirs, files in os.walk(self.nng_path):
            for filename in files:
                if filename.endswith('.json') and filename != 'root.json':
                    location = filename[:-5]  # 移除.json
                    all_nodes.add(location)
        
        result["stats"]["total_nodes"] = len(all_nodes)
        
        # 检查每个节点
        for location in all_nodes:
            node = self._load_node(location)
            if not node:
                result["errors"].append(f"无法加载节点: {location}")
                continue
            
            # 检查父节点
            parent = self._get_parent_location(location)
            if parent != "root":
                parent_node = self._load_node(parent)
                if not parent_node:
                    result["errors"].append(f"父节点不存在: {location} -> {parent}")
                    result["stats"]["orphan_nodes"].append(location)
                else:
                    # 检查父节点是否包含此节点
                    child_locations = [c.get("节点") for c in parent_node.child_nngs]
                    if location not in child_locations:
                        result["warnings"].append(
                            f"父节点未引用子节点: {parent} -> {location}"
                        )
            
            # 检查子节点
            for child_info in node.child_nngs:
                child_loc = child_info.get("节点")
                if child_loc and child_loc not in all_nodes:
                    result["warnings"].append(
                        f"子节点不存在: {location} -> {child_loc}"
                    )
                    result["stats"]["broken_links"].append((location, child_loc))
        
        if result["errors"] or result["warnings"]:
            result["valid"] = False
        
        return result
    
    def find_nodes_by_content(self, keyword: str) -> List[str]:
        """
        按内容关键词搜索节点
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            匹配的节点位置列表
        """
        results = []
        
        for root, dirs, files in os.walk(self.nng_path):
            for filename in files:
                if filename.endswith('.json'):
                    filepath = os.path.join(root, filename)
                    try:
                        data = safe_read_json(filepath)
                        content = data.get("内容", "")
                        if keyword.lower() in content.lower():
                            location = filename[:-5]
                            results.append(location)
                    except:
                        pass
        
        return results
    
    def get_all_paths(self) -> List[List[str]]:
        """
        获取所有从根到叶的路径
        
        Returns:
            路径列表，每个路径是节点位置列表
        """
        paths = []
        
        def dfs(current: str, path: List[str]):
            path = path + [current]
            children = self.get_children(current)
            
            if not children:
                paths.append(path)
                return
            
            for child_info in children:
                child_loc = child_info.get("节点")
                if child_loc:
                    dfs(child_loc, path)
        
        # 从root开始
        root_children = self.get_children("root")
        for child_info in root_children:
            child_loc = child_info.get("节点")
            if child_loc:
                dfs(child_loc, ["root"])
        
        return paths
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取NNG统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "total_nodes": 0,
            "max_depth": 0,
            "avg_confidence": 0,
            "total_memories": 0,
            "by_depth": {}
        }
        
        total_confidence = 0
        
        for root, dirs, files in os.walk(self.nng_path):
            for filename in files:
                if filename.endswith('.json') and filename != 'root.json':
                    location = filename[:-5]
                    node = self._load_node(location)
                    
                    if node:
                        stats["total_nodes"] += 1
                        total_confidence += node.confidence
                        stats["total_memories"] += len(node.memory_summaries)
                        
                        depth = location.count('.') + 1
                        stats["max_depth"] = max(stats["max_depth"], depth)
                        stats["by_depth"][depth] = stats["by_depth"].get(depth, 0) + 1
        
        if stats["total_nodes"] > 0:
            stats["avg_confidence"] = round(total_confidence / stats["total_nodes"], 2)
        
        return stats
