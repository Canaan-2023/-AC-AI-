"""
NNG（导航节点图）管理模块
负责NNG节点的创建、读取、更新、导航
"""
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading


@dataclass
class NNGNode:
    """NNG节点数据结构"""
    定位: str  # 节点ID，如 "1.2.3"
    内容: str  # 节点内容描述
    关联性: int = 50  # 与其他节点的关联程度 0-100
    置信度: int = 80  # 节点可信程度 0-100
    时间: str = ""  # 时间戳
    关联的记忆文件摘要: List[Dict[str, Any]] = None  # 关联的记忆
    子节点: List[str] = None  # 子节点ID列表
    关联节点: List[Dict[str, Any]] = None  # 关联节点列表
    
    def __post_init__(self):
        if self.时间 == "":
            self.时间 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.关联的记忆文件摘要 is None:
            self.关联的记忆文件摘要 = []
        if self.子节点 is None:
            self.子节点 = []
        if self.关联节点 is None:
            self.关联节点 = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "定位": self.定位,
            "内容": self.内容,
            "关联性": self.关联性,
            "置信度": self.置信度,
            "时间": self.时间,
            "关联的记忆文件摘要": self.关联的记忆文件摘要,
            "子节点": self.子节点,
            "关联节点": self.关联节点
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NNGNode':
        """从字典创建"""
        return cls(
            定位=data.get("定位", ""),
            内容=data.get("内容", ""),
            关联性=data.get("关联性", 50),
            置信度=data.get("置信度", 80),
            时间=data.get("时间", ""),
            关联的记忆文件摘要=data.get("关联的记忆文件摘要", []),
            子节点=data.get("子节点", []),
            关联节点=data.get("关联节点", [])
        )


class NNGManager:
    """NNG导航图管理器"""
    
    def __init__(self, base_path: str = "NNG", root_file: str = "root.json"):
        self.base_path = Path(base_path)
        self.root_file = self.base_path / root_file
        self.lock = threading.Lock()
        
        # 初始化目录结构
        self._init_directories()
    
    def _init_directories(self):
        """初始化NNG目录结构"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 创建root.json（如果不存在）
        if not self.root_file.exists():
            root_data = {
                "一级节点": [],
                "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.root_file, 'w', encoding='utf-8') as f:
                json.dump(root_data, f, ensure_ascii=False, indent=2)
    
    def _get_node_file_path(self, node_id: str) -> Path:
        """获取节点文件的完整路径"""
        if node_id == "root":
            return self.root_file
        
        parts = node_id.split('.')
        # 构建路径: NNG/1/1.json 或 NNG/1/1/1.1.json
        path_parts = []
        current = ""
        for i, part in enumerate(parts):
            if i == 0:
                current = part
                path_parts.append(part)
            else:
                current = f"{current}.{part}"
                path_parts.append(current)
        
        # 最后一个部分是文件名
        dir_path = self.base_path
        for part in path_parts[:-1]:
            dir_path = dir_path / part
        
        return dir_path / f"{node_id}.json"
    
    def _get_node_dir_path(self, node_id: str) -> Path:
        """获取节点目录的完整路径"""
        if node_id == "root":
            return self.base_path
        
        parts = node_id.split('.')
        path_parts = []
        current = ""
        for i, part in enumerate(parts):
            if i == 0:
                current = part
            else:
                current = f"{current}.{part}"
            path_parts.append(current)
        
        dir_path = self.base_path
        for part in path_parts:
            dir_path = dir_path / part
        
        return dir_path
    
    def _extract_node_number(self, node_id: str) -> int:
        """从节点ID提取数字部分"""
        match = re.search(r'(\d+)$', node_id)
        return int(match.group(1)) if match else 0
    
    def is_nng_empty(self) -> bool:
        """检查NNG是否为空（只有root，没有一级节点）"""
        root_data = self.get_root()
        return len(root_data.get("一级节点", [])) == 0
    
    def get_root(self) -> Dict[str, Any]:
        """获取root节点数据"""
        try:
            with open(self.root_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[NNG] 读取root失败: {e}")
            return {"一级节点": [], "更新时间": ""}
    
    def get_node(self, node_id: str) -> Optional[NNGNode]:
        """
        获取指定节点的完整数据
        
        Args:
            node_id: 节点ID，如 "1.2.3" 或 "root"
            
        Returns:
            NNGNode或None
        """
        if node_id == "root":
            root_data = self.get_root()
            return NNGNode(
                定位="root",
                内容="NNG根节点，包含所有一级节点",
                子节点=root_data.get("一级节点", [])
            )
        
        file_path = self._get_node_file_path(node_id)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return NNGNode.from_dict(data)
        except Exception as e:
            print(f"[NNG] 读取节点失败 {node_id}: {e}")
            return None
    
    def get_node_children_info(self, node_id: str) -> List[Dict[str, str]]:
        """
        获取节点的子节点简要信息列表
        
        Args:
            node_id: 节点ID
            
        Returns:
            子节点信息列表 [{"id": "1.1", "描述": "..."}, ...]
        """
        node = self.get_node(node_id)
        if not node:
            return []
        
        children_info = []
        for child_id in node.子节点:
            child_node = self.get_node(child_id)
            if child_node:
                children_info.append({
                    "id": child_id,
                    "描述": child_node.内容[:50] + "..." if len(child_node.内容) > 50 else child_node.内容
                })
            else:
                children_info.append({
                    "id": child_id,
                    "描述": "[节点数据缺失]"
                })
        
        return children_info
    
    def validate_node_exists(self, node_id: str) -> bool:
        """验证节点是否存在"""
        if node_id == "root":
            return True
        file_path = self._get_node_file_path(node_id)
        return file_path.exists()
    
    def create_node(self, parent_id: str, content: str, 
                    associations: Optional[List[Dict]] = None,
                    memory_summaries: Optional[List[Dict]] = None) -> Optional[str]:
        """
        创建新节点
        
        Args:
            parent_id: 父节点ID
            content: 节点内容描述
            associations: 关联节点列表
            memory_summaries: 关联的记忆摘要
            
        Returns:
            新节点ID或None
        """
        with self.lock:
            # 获取父节点
            parent = self.get_node(parent_id)
            if not parent:
                print(f"[NNG] 父节点不存在: {parent_id}")
                return None
            
            # 生成新节点ID
            if parent_id == "root":
                # 一级节点，直接递增
                existing_children = parent.子节点
                new_num = 1
                while str(new_num) in existing_children:
                    new_num += 1
                new_node_id = str(new_num)
            else:
                # 子节点，在父节点ID后添加
                existing_children = parent.子节点
                new_num = 1
                new_node_id = f"{parent_id}.{new_num}"
                while new_node_id in existing_children:
                    new_num += 1
                    new_node_id = f"{parent_id}.{new_num}"
            
            # 创建节点目录
            node_dir = self._get_node_dir_path(new_node_id)
            node_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建节点文件
            node_file = self._get_node_file_path(new_node_id)
            node_data = NNGNode(
                定位=new_node_id,
                内容=content,
                关联的记忆文件摘要=memory_summaries or [],
                关联节点=associations or []
            )
            
            with open(node_file, 'w', encoding='utf-8') as f:
                json.dump(node_data.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 更新父节点的子节点列表
            parent.子节点.append(new_node_id)
            if parent_id == "root":
                root_data = self.get_root()
                root_data["一级节点"] = parent.子节点
                root_data["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(self.root_file, 'w', encoding='utf-8') as f:
                    json.dump(root_data, f, ensure_ascii=False, indent=2)
            else:
                parent_file = self._get_node_file_path(parent_id)
                with open(parent_file, 'w', encoding='utf-8') as f:
                    json.dump(parent.to_dict(), f, ensure_ascii=False, indent=2)
            
            print(f"[NNG] 已创建节点 {new_node_id}")
            return new_node_id
    
    def update_node(self, node_id: str, **kwargs) -> bool:
        """更新节点数据"""
        if node_id == "root":
            return False
        
        node = self.get_node(node_id)
        if not node:
            return False
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(node, key):
                setattr(node, key, value)
        
        # 更新时间
        node.时间 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 保存
        file_path = self._get_node_file_path(node_id)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(node.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[NNG] 更新节点失败 {node_id}: {e}")
            return False
    
    def delete_node(self, node_id: str) -> bool:
        """删除节点及其所有子节点"""
        if node_id == "root":
            print("[NNG] 不能删除root节点")
            return False
        
        node = self.get_node(node_id)
        if not node:
            return False
        
        # 递归删除子节点
        for child_id in node.子节点:
            self.delete_node(child_id)
        
        # 删除节点文件和目录
        try:
            file_path = self._get_node_file_path(node_id)
            dir_path = self._get_node_dir_path(node_id)
            
            if file_path.exists():
                file_path.unlink()
            
            if dir_path.exists():
                import shutil
                shutil.rmtree(dir_path)
            
            # 从父节点中移除
            parent_id = node_id.rsplit('.', 1)[0] if '.' in node_id else "root"
            parent = self.get_node(parent_id)
            if parent and node_id in parent.子节点:
                parent.子节点.remove(node_id)
                if parent_id == "root":
                    root_data = self.get_root()
                    root_data["一级节点"] = parent.子节点
                    root_data["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with open(self.root_file, 'w', encoding='utf-8') as f:
                        json.dump(root_data, f, ensure_ascii=False, indent=2)
                else:
                    parent_file = self._get_node_file_path(parent_id)
                    with open(parent_file, 'w', encoding='utf-8') as f:
                        json.dump(parent.to_dict(), f, ensure_ascii=False, indent=2)
            
            print(f"[NNG] 已删除节点 {node_id}")
            return True
            
        except Exception as e:
            print(f"[NNG] 删除节点失败 {node_id}: {e}")
            return False
    
    def add_memory_to_node(self, node_id: str, memory_id: int, 
                           summary: str, memory_type: str,
                           value_level: Optional[str] = None) -> bool:
        """向节点添加记忆关联"""
        node = self.get_node(node_id)
        if not node:
            return False
        
        memory_entry = {
            "记忆ID": memory_id,
            "摘要": summary,
            "记忆类型": memory_type
        }
        if value_level:
            memory_entry["价值层级"] = value_level
        
        node.关联的记忆文件摘要.append(memory_entry)
        
        return self.update_node(node_id, 关联的记忆文件摘要=node.关联的记忆文件摘要)
    
    def get_all_node_ids(self) -> List[str]:
        """获取所有节点ID"""
        node_ids = ["root"]
        
        def collect_children(node_id: str):
            node = self.get_node(node_id)
            if node:
                for child_id in node.子节点:
                    node_ids.append(child_id)
                    collect_children(child_id)
        
        collect_children("root")
        return node_ids


if __name__ == "__main__":
    # 自测
    print("=" * 60)
    print("NNGManager模块自测")
    print("=" * 60)
    
    import tempfile
    import shutil
    
    # 创建临时测试目录
    test_dir = tempfile.mkdtemp(prefix="abyssac_nng_test_")
    print(f"\n测试目录: {test_dir}")
    
    try:
        # 初始化NNG管理器
        nng = NNGManager(base_path=test_dir)
        print("[✓] NNG管理器初始化成功")
        
        # 测试NNG是否为空
        is_empty = nng.is_nng_empty()
        print(f"[✓] NNG为空: {is_empty}")
        
        # 测试获取root
        root = nng.get_root()
        print(f"[✓] Root节点: {root}")
        
        # 测试创建一级节点
        node1_id = nng.create_node("root", "系统核心概念与架构")
        print(f"[✓] 创建一级节点: {node1_id}")
        
        node2_id = nng.create_node("root", "用户交互与界面设计")
        print(f"[✓] 创建一级节点: {node2_id}")
        
        # 测试创建二级节点
        node1_1_id = nng.create_node(node1_id, "Python编程相关内容")
        print(f"[✓] 创建二级节点: {node1_1_id}")
        
        node1_1_1_id = nng.create_node(node1_1_id, "GIL全局解释器锁")
        print(f"[✓] 创建三级节点: {node1_1_1_id}")
        
        # 测试获取节点
        node = nng.get_node(node1_1_id)
        if node:
            print(f"[✓] 获取节点 {node1_1_id}: {node.内容}")
        
        # 测试获取子节点信息
        children = nng.get_node_children_info(node1_id)
        print(f"[✓] 节点 {node1_id} 的子节点: {[c['id'] for c in children]}")
        
        # 测试验证节点存在
        exists = nng.validate_node_exists(node1_1_1_id)
        print(f"[✓] 节点 {node1_1_1_id} 存在: {exists}")
        
        # 测试添加记忆关联
        success = nng.add_memory_to_node(
            node1_1_1_id, 
            memory_id=1,
            summary="GIL详解内容",
            memory_type="分类记忆",
            value_level="高价值"
        )
        print(f"[✓] 添加记忆关联: {'成功' if success else '失败'}")
        
        # 测试获取所有节点ID
        all_ids = nng.get_all_node_ids()
        print(f"[✓] 所有节点ID: {all_ids}")
        
        # 测试更新节点
        success = nng.update_node(node1_id, 内容="更新的描述", 置信度=95)
        print(f"[✓] 更新节点: {'成功' if success else '失败'}")
        
        # 测试删除节点
        success = nng.delete_node(node1_1_1_id)
        print(f"[✓] 删除节点: {'成功' if success else '失败'}")
        
        # 验证删除
        exists_after = nng.validate_node_exists(node1_1_1_id)
        print(f"[✓] 删除后节点存在: {exists_after}")
        
        print("\n" + "=" * 60)
        print("NNGManager模块自测通过")
        print("=" * 60)
        
    finally:
        # 清理测试目录
        shutil.rmtree(test_dir, ignore_errors=True)
        print(f"\n已清理测试目录")
