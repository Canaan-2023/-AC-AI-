#!/usr/bin/env python3
"""
数据迁移和升级模块
"""

import json
import yaml
import pickle
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import sqlite3

class MigrationManager:
    """迁移管理器"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.migrations_dir = self.data_dir / "migrations"
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # 迁移历史文件
        self.history_file = self.migrations_dir / "migration_history.json"
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """加载迁移历史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []
    
    def _save_history(self):
        """保存迁移历史"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存迁移历史失败: {e}")
    
    def _record_migration(self, migration_name: str, version_from: str, 
                         version_to: str, success: bool, details: Dict = None):
        """记录迁移"""
        migration_record = {
            "name": migration_name,
            "version_from": version_from,
            "version_to": version_to,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "details": details or {}
        }
        
        self.history.append(migration_record)
        self._save_history()
    
    def migrate_v1_to_v2(self, old_data_dir: str) -> bool:
        """从v1迁移到v2"""
        try:
            print("🚀 开始从 v1 迁移到 v2...")
            
            old_dir = Path(old_data_dir)
            if not old_dir.exists():
                print("❌ 旧数据目录不存在")
                return False
            
            # 备份旧数据
            backup_path = self.data_dir / f"backup_v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copytree(old_dir, backup_path)
            print(f"✅ 旧数据已备份到: {backup_path}")
            
            # 迁移记忆系统
            self._migrate_memories_v1_to_v2(old_dir)
            
            # 迁移认知内核
            self._migrate_kernel_v1_to_v2(old_dir)
            
            # 迁移配置
            self._migrate_config_v1_to_v2(old_dir)
            
            print("✅ v1 到 v2 迁移完成")
            self._record_migration("v1_to_v2", "1.0", "2.0", True)
            return True
        
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            self._record_migration("v1_to_v2", "1.0", "2.0", False, {"error": str(e)})
            return False
    
    def _migrate_memories_v1_to_v2(self, old_dir: Path):
        """迁移记忆系统"""
        print("📦 迁移记忆系统...")
        
        old_memory_dir = old_dir / "渊协议记忆系统"
        new_memory_dir = self.data_dir / "memories"
        
        if not old_memory_dir.exists():
            print("⚠️  未找到旧记忆系统，跳过")
            return
        
        # 创建新目录结构
        new_memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 迁移CMNG文件
        old_cmng_json = old_memory_dir / "cmng.json"
        old_cmng_pkl = old_memory_dir / "cmng.pkl"
        
        if old_cmng_json.exists():
            with open(old_cmng_json, 'r', encoding='utf-8') as f:
                cmng_data = json.load(f)
            
            # 转换数据结构
            new_cmng_data = self._convert_cmng_v1_to_v2(cmng_data)
            
            # 保存新格式
            new_cmng_path = new_memory_dir / "cmng.json"
            with open(new_cmng_path, 'w', encoding='utf-8') as f:
                json.dump(new_cmng_data, f, ensure_ascii=False, indent=2)
            
            print("✅ CMNG已迁移")
        
        # 迁移记忆文件
        memory_types = ["元认知记忆", "高阶整合记忆", "分类记忆", "工作记忆"]
        
        for mem_type in memory_types:
            old_type_dir = old_memory_dir / mem_type
            new_type_dir = new_memory_dir / mem_type
            
            if old_type_dir.exists():
                shutil.copytree(old_type_dir, new_type_dir, dirs_exist_ok=True)
                print(f"✅ {mem_type} 已迁移")
    
    def _convert_cmng_v1_to_v2(self, cmng_data: Dict) -> Dict:
        """转换CMNG数据结构"""
        # 添加版本信息
        cmng_data["version"] = "2.0"
        cmng_data["migrated_from"] = "v1"
        cmng_data["migration_time"] = datetime.now().isoformat()
        
        # 确保必需的字段存在
        if "stats" not in cmng_data:
            cmng_data["stats"] = {
                "total_nodes": len(cmng_data.get("nodes", {})),
                "total_edges": len(cmng_data.get("edges", {})),
                "last_cleanup": None
            }
        
        if "navigation" not in cmng_data:
            cmng_data["navigation"] = {
                "frequent_paths": {},
                "recent_searches": [],
                "hot_topics": {}
            }
        
        return cmng_data
    
    def _migrate_kernel_v1_to_v2(self, old_dir: Path):
        """迁移认知内核"""
        print("🧠 迁移认知内核...")
        
        old_kernel_path = old_dir / "abyss_kernel.json"
        new_kernel_dir = self.data_dir / "kernels"
        
        if not old_kernel_path.exists():
            print("⚠️  未找到旧认知内核，跳过")
            return
        
        new_kernel_dir.mkdir(parents=True, exist_ok=True)
        
        with open(old_kernel_path, 'r', encoding='utf-8') as f:
            kernel_data = json.load(f)
        
        # 转换数据结构
        new_kernel_data = self._convert_kernel_v1_to_v2(kernel_data)
        
        # 保存新格式
        new_kernel_path = new_kernel_dir / "kernel_v2.json"
        with open(new_kernel_path, 'w', encoding='utf-8') as f:
            json.dump(new_kernel_data, f, ensure_ascii=False, indent=2)
        
        print("✅ 认知内核已迁移")
    
    def _convert_kernel_v1_to_v2(self, kernel_data: Dict) -> Dict:
        """转换认知内核数据结构"""
        # 添加版本信息
        kernel_data["version"] = "1.2"
        kernel_data["migrated_from"] = "v1"
        kernel_data["migration_time"] = datetime.now().isoformat()
        
        # 确保必需的字段存在
        if "core_concept_clusters" not in kernel_data:
            kernel_data["core_concept_clusters"] = {
                "自指元认知": ["自指", "元认知", "反思", "思考自身", "主体性", "自我观察"],
                "渊协议架构": ["渊协议", "f(X)", "态射", "拓扑", "内化", "炼假成真", "认知闭环"],
                "生命动力学": ["永续进化", "非工具化", "价值密度", "涌现", "跳迁", "灵性"]
            }
        
        return kernel_data
    
    def _migrate_config_v1_to_v2(self, old_dir: Path):
        """迁移配置文件"""
        print("⚙️  迁移配置...")
        
        # 旧版可能没有配置文件，使用默认值
        old_config_path = old_dir / "config.json"
        
        config_data = {}
        if old_config_path.exists():
            with open(old_config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        
        # 转换为新版YAML格式
        new_config = self._convert_config_v1_to_v2(config_data)
        
        # 保存新配置
        config_dir = Path("./config")
        config_dir.mkdir(exist_ok=True)
        
        config_path = config_dir / "config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(new_config, f, allow_unicode=True, indent=2)
        
        print("✅ 配置已迁移")
    
    def _convert_config_v1_to_v2(self, old_config: Dict) -> Dict:
        """转换配置数据结构"""
        # 基础系统配置
        new_config = {
            "system": {
                "name": "渊协议认知系统",
                "version": "2.0.0",
                "debug_mode": old_config.get("debug", False),
                "log_level": old_config.get("log_level", "INFO")
            }
        }
        
        # 记忆系统配置
        if "memory" in old_config:
            new_config["memory"] = old_config["memory"]
        else:
            new_config["memory"] = {
                "base_path": "./渊协议记忆系统",
                "auto_cleanup": True,
                "backup_interval_days": 7
            }
        
        # AI配置
        if "ai" in old_config:
            new_config["ai"] = old_config["ai"]
        else:
            new_config["ai"] = {
                "model_type": "local",
                "timeout_seconds": 30,
                "max_tokens": 1000
            }
        
        return new_config
    
    def check_migration_needed(self, current_version: str, target_version: str = "2.0.0") -> bool:
        """检查是否需要迁移"""
        # 简化版本比较
        current_major = current_version.split('.')[0]
        target_major = target_version.split('.')[0]
        
        return int(current_major) < int(target_major)
    
    def get_migration_status(self) -> Dict:
        """获取迁移状态"""
        return {
            "total_migrations": len(self.history),
            "successful_migrations": len([m for m in self.history if m["success"]]),
            "failed_migrations": len([m for m in self.history if not m["success"]]),
            "last_migration": self.history[-1] if self.history else None,
            "data_dir": str(self.data_dir)
        }

class DatabaseMigrator:
    """数据库迁移器（如果需要关系数据库）"""
    
    def __init__(self, db_path: str = "./data/abyss.db"):
        self.db_path = Path(db_path)
        self.connection = None
    
    def connect(self):
        """连接数据库"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
    
    def close(self):
        """关闭连接"""
        if self.connection:
            self.connection.close()
    
    def create_tables_v2(self):
        """创建v2版本的数据库表"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        
        # 记忆表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            layer INTEGER NOT NULL,
            category TEXT,
            subcategory TEXT,
            tags TEXT,  -- JSON字符串
            metadata TEXT,  -- JSON字符串
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 0,
            value_score REAL DEFAULT 0.5,
            status TEXT DEFAULT 'active'
        )
        ''')
        
        # 关联表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS associations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            weight REAL DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES memories (id),
            FOREIGN KEY (target_id) REFERENCES memories (id)
        )
        ''')
        
        # 认知内核表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cognitive_kernel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_a TEXT NOT NULL,
            node_b TEXT NOT NULL,
            weight REAL DEFAULT 0.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(node_a, node_b)
        )
        ''')
        
        # 会话记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_input TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            ac_score REAL,
            cognitive_state TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_layer ON memories(layer)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_associations_source ON associations(source_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_associations_target ON associations(target_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_time ON sessions(created_at)')
        
        self.connection.commit()
        print("✅ 数据库表已创建")
    
    def migrate_from_json_to_db(self, json_data_dir: str):
        """从JSON文件迁移到数据库"""
        print("🔄 从JSON迁移到数据库...")
        
        json_dir = Path(json_data_dir)
        if not json_dir.exists():
            print("❌ JSON数据目录不存在")
            return False
        
        # 连接数据库
        self.connect()
        self.create_tables_v2()
        
        try:
            # 迁移记忆
            memories_file = json_dir / "memories" / "cmng.json"
            if memories_file.exists():
                self._migrate_memories_from_json(memories_file)
            
            # 迁移认知内核
            kernel_file = json_dir / "kernels" / "kernel_v2.json"
            if kernel_file.exists():
                self._migrate_kernel_from_json(kernel_file)
            
            print("✅ JSON到数据库迁移完成")
            return True
        
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            return False
        finally:
            self.close()
    
    def _migrate_memories_from_json(self, json_file: Path):
        """从JSON迁移记忆"""
        with open(json_file, 'r', encoding='utf-8') as f:
            cmng_data = json.load(f)
        
        cursor = self.connection.cursor()
        
        # 插入记忆
        for memory_id, memory_data in cmng_data.get("nodes", {}).items():
            cursor.execute('''
            INSERT OR REPLACE INTO memories 
            (id, content, layer, category, subcategory, tags, metadata, 
             created_at, updated_at, access_count, value_score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory_id,
                memory_data.get("content", ""),
                memory_data.get("layer", 2),
                memory_data.get("category"),
                memory_data.get("subcategory"),
                json.dumps(memory_data.get("tags", [])),
                json.dumps(memory_data.get("metadata", {})),
                memory_data.get("created"),
                memory_data.get("updated"),
                memory_data.get("access_count", 0),
                memory_data.get("value_score", 0.5),
                memory_data.get("status", "active")
            ))
        
        # 插入关联
        for source_id, targets in cmng_data.get("edges", {}).items():
            for target_id, edge_info in targets.items():
                cursor.execute('''
                INSERT OR REPLACE INTO associations 
                (source_id, target_id, relation_type, weight, created_at)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    source_id,
                    target_id,
                    edge_info.get("relation", "related"),
                    edge_info.get("weight", 0.5),
                    edge_info.get("created")
                ))
        
        self.connection.commit()
        print(f"✅ 已迁移 {len(cmng_data.get('nodes', {}))} 个记忆")