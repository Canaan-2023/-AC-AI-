"""
AbyssAC 存储模块
处理NNG和记忆的文件操作
"""

import os
import json
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml

# 获取项目根目录（src的父目录）
PROJECT_ROOT = Path(__file__).parent.parent

# 加载配置
config_path = PROJECT_ROOT / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        CONFIG = yaml.safe_load(f)
else:
    CONFIG = {
        "storage": {
            "base_path": "./storage",
            "nng_path": "./storage/nng",
            "memory_path": "./storage/Y层记忆库",
            "logs_path": "./storage/logs"
        }
    }

BASE_PATH = PROJECT_ROOT / Path(CONFIG["storage"]["base_path"])
NNG_PATH = PROJECT_ROOT / Path(CONFIG["storage"]["nng_path"])
MEMORY_PATH = PROJECT_ROOT / Path(CONFIG["storage"]["memory_path"])
LOGS_PATH = PROJECT_ROOT / Path(CONFIG["storage"]["logs_path"])


class StorageManager:
    """存储管理器"""
    
    @staticmethod
    def nng_id_to_path(nng_id: str) -> Path:
        """
        NNG ID转文件路径
        例如：1.6.5.7 → storage/nng/1/1.6/1.6.5/1.6.5.7.json
        """
        if nng_id == "root":
            return NNG_PATH / "root.json"
        
        parts = nng_id.split('.')
        path_parts = []
        
        # 逐步累积构建目录路径
        for i in range(len(parts) - 1):
            path_parts.append('.'.join(parts[:i+1]))
        
        # 构造完整路径
        if path_parts:
            file_path = '/'.join(path_parts) + '/' + nng_id + '.json'
        else:
            file_path = nng_id + '.json'
        
        return NNG_PATH / file_path
    
    @staticmethod
    def get_parent_nng_id(nng_id: str) -> Optional[str]:
        """获取父节点ID"""
        if nng_id == "root" or '.' not in nng_id:
            return "root"
        parts = nng_id.rsplit('.', 1)
        return parts[0]
    
    @staticmethod
    def allocate_memory_id() -> str:
        """分配新的记忆ID（线程安全）"""
        counter_file = BASE_PATH / "memory_counter.txt"
        
        with open(counter_file, 'r+') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                content = f.read().strip()
                current = int(content) if content else 0
                new_id = current + 1
                f.seek(0)
                f.write(str(new_id))
                f.truncate()
                return str(new_id)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    
    @staticmethod
    def get_memory_path(memory_type: str, value_tier: Optional[str], 
                        memory_id: str, ext: str = ".txt") -> Path:
        """
        构建记忆文件路径
        
        Args:
            memory_type: 记忆类型（分类记忆/高阶整合记忆/元认知记忆/工作记忆）
            value_tier: 价值层级（高/中/低），仅分类记忆需要
            memory_id: 记忆ID
            ext: 文件扩展名
        """
        now = datetime.now()
        year, month, day = now.strftime("%Y"), now.strftime("%m"), now.strftime("%d")
        
        if memory_type == "分类记忆":
            tier = value_tier or "中价值"
            path = MEMORY_PATH / memory_type / tier / year / month / day / f"{memory_id}{ext}"
        else:
            path = MEMORY_PATH / memory_type / year / month / day / f"{memory_id}{ext}"
        
        return path
    
    @staticmethod
    def read_nng(nng_id: str) -> Optional[Dict[str, Any]]:
        """读取NNG节点"""
        file_path = StorageManager.nng_id_to_path(nng_id)
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取NNG {nng_id} 失败: {e}")
            return None
    
    @staticmethod
    def write_nng(nng_id: str, data: Dict[str, Any]) -> bool:
        """写入NNG节点"""
        file_path = StorageManager.nng_id_to_path(nng_id)
        
        try:
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"写入NNG {nng_id} 失败: {e}")
            return False
    
    @staticmethod
    def delete_nng(nng_id: str) -> bool:
        """删除NNG节点"""
        file_path = StorageManager.nng_id_to_path(nng_id)
        
        if not file_path.exists():
            return False
        
        try:
            # 检查是否有子节点
            parent_path = file_path.parent / nng_id
            if parent_path.exists() and any(parent_path.iterdir()):
                print(f"NNG {nng_id} 有子节点，无法删除")
                return False
            
            # 删除文件
            file_path.unlink()
            
            # 删除空目录
            if parent_path.exists() and not any(parent_path.iterdir()):
                parent_path.rmdir()
            
            # 从父节点移除
            parent_id = StorageManager.get_parent_nng_id(nng_id)
            if parent_id:
                parent_data = StorageManager.read_nng(parent_id)
                if parent_data and "下级关联NNG" in parent_data:
                    parent_data["下级关联NNG"] = [
                        n for n in parent_data["下级关联NNG"] 
                        if n.get("名称") != nng_id
                    ]
                    StorageManager.write_nng(parent_id, parent_data)
            
            # 更新root.json
            if '.' not in nng_id:
                root_data = StorageManager.read_nng("root")
                if root_data and nng_id in root_data.get("一级节点", []):
                    root_data["一级节点"].remove(nng_id)
                    StorageManager.write_nng("root", root_data)
            
            return True
        except Exception as e:
            print(f"删除NNG {nng_id} 失败: {e}")
            return False
    
    @staticmethod
    def read_memory(memory_id: str, file_path: Optional[str] = None) -> Optional[str]:
        """读取记忆文件内容"""
        if file_path:
            full_path = MEMORY_PATH / file_path
        else:
            # 搜索记忆文件
            full_path = StorageManager._find_memory_file(memory_id)
        
        if not full_path or not full_path.exists():
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取记忆 {memory_id} 失败: {e}")
            return None
    
    @staticmethod
    def _find_memory_file(memory_id: str) -> Optional[Path]:
        """搜索记忆文件"""
        for memory_type in ["分类记忆", "高阶整合记忆", "元认知记忆", "工作记忆"]:
            base = MEMORY_PATH / memory_type
            if not base.exists():
                continue
            
            for path in base.rglob(f"{memory_id}.*"):
                return path
        
        return None
    
    @staticmethod
    def write_memory(memory_id: str, content: str, memory_type: str,
                     value_tier: Optional[str] = None, ext: str = ".txt") -> bool:
        """写入记忆文件"""
        file_path = StorageManager.get_memory_path(memory_type, value_tier, memory_id, ext)
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"写入记忆 {memory_id} 失败: {e}")
            return False
    
    @staticmethod
    def get_memory_file_path_from_nng(nng_data: Dict, memory_id: str) -> Optional[str]:
        """从NNG数据中获取记忆文件路径"""
        for mem in nng_data.get("关联的记忆文件摘要", []):
            if mem.get("记忆ID") == memory_id:
                return mem.get("文件路径")
        return None
    
    @staticmethod
    def list_nng_tree() -> Dict[str, Any]:
        """获取NNG树结构"""
        root_data = StorageManager.read_nng("root")
        if not root_data:
            return {"nodes": [], "count": 0}
        
        def build_tree(nng_id: str) -> Dict[str, Any]:
            data = StorageManager.read_nng(nng_id)
            if not data:
                return {"id": nng_id, "children": []}
            
            children = []
            for child in data.get("下级关联NNG", []):
                child_id = child.get("名称")
                if child_id:
                    children.append(build_tree(child_id))
            
            return {
                "id": nng_id,
                "content": data.get("内容", ""),
                "confidence": data.get("置信度", 0),
                "memory_count": len(data.get("关联的记忆文件摘要", [])),
                "children": children
            }
        
        tree = []
        for node_id in root_data.get("一级节点", []):
            tree.append(build_tree(node_id))
        
        return {"nodes": tree, "count": len(root_data.get("一级节点", []))}
    
    @staticmethod
    def get_memory_stats() -> Dict[str, int]:
        """获取记忆统计"""
        stats = {
            "total": 0,
            "high_value": 0,
            "medium_value": 0,
            "low_value": 0,
            "working": 0,
            "meta": 0,
            "integrated": 0
        }
        
        # 分类记忆
        for tier in ["高价值", "中价值", "低价值"]:
            path = MEMORY_PATH / "分类记忆" / tier
            if path.exists():
                count = len(list(path.rglob("*.txt")))
                stats["total"] += count
                if tier == "高价值":
                    stats["high_value"] = count
                elif tier == "中价值":
                    stats["medium_value"] = count
                else:
                    stats["low_value"] = count
        
        # 其他记忆类型
        for mem_type, key in [("高阶整合记忆", "integrated"), 
                              ("元认知记忆", "meta"),
                              ("工作记忆", "working")]:
            path = MEMORY_PATH / mem_type
            if path.exists():
                count = len(list(path.rglob("*.txt")))
                stats["total"] += count
                stats[key] = count
        
        return stats
    
    @staticmethod
    def write_navigation_log(log_data: Dict[str, Any]) -> bool:
        """写入导航日志"""
        now = datetime.now()
        log_dir = LOGS_PATH / "navigation" / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"nav_{now.strftime('%H%M%S')}_{log_data.get('session_id', 'unknown')}.json"
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"写入导航日志失败: {e}")
            return False
    
    @staticmethod
    def write_error_log(error_data: Dict[str, Any]) -> bool:
        """写入错误日志"""
        log_dir = LOGS_PATH / "error"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        now = datetime.now()
        log_file = log_dir / f"error_{now.strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"写入错误日志失败: {e}")
            return False
    
    @staticmethod
    def write_dmn_log(task_type: str, log_data: Dict[str, Any]) -> bool:
        """写入DMN任务日志"""
        log_dir = LOGS_PATH / "dmn"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        now = datetime.now()
        log_file = log_dir / f"dmn_{task_type}_{now.strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"写入DMN日志失败: {e}")
            return False
