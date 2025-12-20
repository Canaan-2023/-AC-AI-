"""
渊协议 - 简化内存系统实现
Memex-A + CMNG + 四层记忆 + AI接口
"""

import os
import json
import pickle
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import shutil

class MemexA:
    """
    Memex-A 核心系统
    负责：四层记忆管理、CMNG字典生成、索引维护、AI接口
    """
    
    def __init__(self, base_path: str = "./渊协议记忆系统"):
        self.base_path = Path(base_path)
        
        # 四层记忆配置
        self.layers = {
            0: {"name": "元认知记忆", "permanent": True, "priority": 100},
            1: {"name": "高阶整合记忆", "permanent": True, "priority": 80},
            2: {"name": "分类记忆", "permanent": False, "priority": 60},
            3: {"name": "工作记忆", "permanent": False, "priority": 40}
        }
        
        # 分类记忆子类别
        self.categories = {
            "学术咨询": ["认知跃迁", "意识理论", "哲学讨论"],
            "日常交互": ["情感共鸣", "生活建议", "闲聊"],
            "创意写作": ["故事创作", "诗歌", "剧本"],
            "技术讨论": ["编程", "算法", "系统设计"],
            "理论探索": ["新概念", "假设推演", "逻辑验证"]
        }
        
        # 初始化系统
        self._init_system()
        
        # 加载CMNG字典
        self.cmng = self._load_cmng()
        
        print(f"渊协议记忆系统初始化完成 | 路径: {self.base_path}")
        print(f"已加载 {len(self.cmng['nodes'])} 个记忆节点")
    
    def _init_system(self):
        """初始化文件夹结构"""
        # 创建根目录
        self.base_path.mkdir(exist_ok=True)
        
        # 创建四层记忆目录
        for layer_id, layer_info in self.layers.items():
            layer_path = self.base_path / layer_info["name"]
            layer_path.mkdir(exist_ok=True)
            
            # 为分类记忆创建子目录
            if layer_id == 2:
                for category in self.categories:
                    category_path = layer_path / category
                    category_path.mkdir(exist_ok=True)
                    
                    # 创建子分类目录
                    for subcat in self.categories[category]:
                        subcat_path = category_path / subcat
                        subcat_path.mkdir(exist_ok=True)
        
        # 创建系统目录
        (self.base_path / "系统日志").mkdir(exist_ok=True)
        (self.base_path / "备份").mkdir(exist_ok=True)
        (self.base_path / "临时文件").mkdir(exist_ok=True)
    
    def _load_cmng(self) -> Dict:
        """加载或创建CMNG字典"""
        cmng_path = self.base_path / "cmng.json"
        
        if cmng_path.exists():
            try:
                with open(cmng_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载CMNG失败，创建新的: {e}")
        
        # 创建新的CMNG字典
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            
            "nodes": {},      # 记忆节点
            "edges": {},      # 关联关系
            "index": {},      # 关键词索引
            "stats": {        # 统计信息
                "total_nodes": 0,
                "nodes_by_layer": {str(k): 0 for k in self.layers},
                "total_edges": 0,
                "last_cleanup": None,
                "total_accesses": 0
            },
            
            "navigation": {   # 导航数据
                "frequent_paths": {},
                "recent_searches": [],
                "hot_topics": {}
            },
            
            "config": {       # 配置
                "auto_cleanup": True,
                "cleanup_interval_hours": 24,
                "max_working_memories": 50,
                "backup_interval_days": 7
            }
        }
    
    def _save_cmng(self):
        """保存CMNG字典"""
        cmng_path = self.base_path / "cmng.json"
        self.cmng["updated"] = datetime.now().isoformat()
        
        try:
            # 保存为JSON（人类可读）
            with open(cmng_path, 'w', encoding='utf-8') as f:
                json.dump(self.cmng, f, ensure_ascii=False, indent=2)
            
            # 同时保存为pickle（快速加载）
            pickle_path = self.base_path / "cmng.pkl"
            with open(pickle_path, 'wb') as f:
                pickle.dump(self.cmng, f)
                
        except Exception as e:
            print(f"保存CMNG失败: {e}")
            raise
    
    def create_memory(self, 
                     content: str,
                     layer: int = 2,
                     category: Optional[str] = None,
                     subcategory: Optional[str] = None,
                     tags: List[str] = None,
                     metadata: Dict = None) -> str:
        """
        创建新记忆
        返回: 记忆ID
        """
        # 验证参数
        if layer not in self.layers:
            raise ValueError(f"无效的记忆层: {layer}")
        
        # 生成唯一ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        content_hash = hashlib.md5(content.encode()).hexdigest()[:6]
        memory_id = f"M{layer}_{timestamp}_{content_hash}"
        
        # 确定存储路径
        layer_name = self.layers[layer]["name"]
        
        if layer == 0:  # 元认知记忆
            file_name = metadata.get("name", f"元认知_{memory_id}.txt")
            file_path = self.base_path / layer_name / file_name
            
        elif layer == 1:  # 高阶整合记忆
            file_path = self.base_path / layer_name / f"整合_{memory_id}.txt"
            
        elif layer == 2:  # 分类记忆
            if not category:
                category = "未分类"
            if not subcategory:
                subcategory = "通用"
            
            category_path = self.base_path / layer_name / category / subcategory
            category_path.mkdir(exist_ok=True)
            file_path = category_path / f"记忆_{memory_id}.txt"
            
        else:  # 工作记忆
            file_path = self.base_path / layer_name / f"工作_{memory_id}.txt"
        
        # 保存内容文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise IOError(f"保存记忆文件失败: {e}")
        
        # 构建记忆节点
        memory_node = {
            "id": memory_id,
            "layer": layer,
            "layer_name": layer_name,
            "path": str(file_path),
            "content": content[:200] + "..." if len(content) > 200 else content,
            "full_content": content,  # 注意：实际内容在文件中，这里只存摘要
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "category": category,
            "subcategory": subcategory,
            "tags": tags or [],
            "metadata": metadata or {},
            "access_count": 0,
            "last_accessed": None,
            "value_score": metadata.get("value_score", 0.5) if metadata else 0.5,
            "status": "active"
        }
        
        # 更新CMNG
        self.cmng["nodes"][memory_id] = memory_node
        
        # 更新索引
        if tags:
            for tag in tags:
                if tag not in self.cmng["index"]:
                    self.cmng["index"][tag] = []
                if memory_id not in self.cmng["index"][tag]:
                    self.cmng["index"][tag].append(memory_id)
        
        # 更新关键词索引（简单提取）
        keywords = self._extract_keywords(content)
        for keyword in keywords:
            if keyword not in self.cmng["index"]:
                self.cmng["index"][keyword] = []
            if memory_id not in self.cmng["index"][keyword]:
                self.cmng["index"][keyword].append(memory_id)
        
        # 更新统计
        self.cmng["stats"]["total_nodes"] += 1
        self.cmng["stats"]["nodes_by_layer"][str(layer)] = \
            self.cmng["stats"]["nodes_by_layer"].get(str(layer), 0) + 1
        
        # 保存CMNG
        self._save_cmng()
        
        # 记录日志
        self._log_operation("create_memory", {
            "memory_id": memory_id,
            "layer": layer,
            "category": category,
            "content_length": len(content)
        })
        
        return memory_id
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """提取关键词（简化版）"""
        # 中文关键词提取（简单实现）
        import re
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        
        # 移除常见停用词
        stopwords = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}
        filtered = [w for w in words if w not in stopwords]
        
        # 按频率排序
        from collections import Counter
        counter = Counter(filtered)
        return [word for word, _ in counter.most_common(max_keywords)]
    
    def retrieve_memory(self, 
                       query: str,
                       layer: Optional[int] = None,
                       category: Optional[str] = None,
                       limit: int = 10,
                       min_score: float = 0.1) -> List[Dict]:
        """
        检索记忆
        支持：关键词、语义相似度、类别过滤
        """
        results = []
        
        # 1. 关键词匹配（精确）
        if query in self.cmng["index"]:
            for memory_id in self.cmng["index"][query]:
                if self._filter_memory(memory_id, layer, category):
                    memory = self.get_memory(memory_id)
                    if memory:
                        memory["match_type"] = "keyword_exact"
                        memory["match_score"] = 1.0
                        results.append(memory)
        
        # 2. 模糊关键词匹配
        if len(results) < limit:
            for keyword, memory_ids in self.cmng["index"].items():
                if query in keyword or keyword in query:
                    for memory_id in memory_ids:
                        if self._filter_memory(memory_id, layer, category):
                            memory = self.get_memory(memory_id)
                            if memory and memory["id"] not in [r["id"] for r in results]:
                                memory["match_type"] = "keyword_fuzzy"
                                memory["match_score"] = 0.7
                                results.append(memory)
        
        # 3. 内容搜索（简单文本匹配）
        if len(results) < limit:
            for memory_id, node in self.cmng["nodes"].items():
                if self._filter_memory(memory_id, layer, category):
                    # 检查标签
                    tag_match = any(query in tag for tag in node.get("tags", []))
                    
                    # 检查内容
                    content_match = query.lower() in node.get("full_content", "").lower()
                    
                    if tag_match or content_match:
                        memory = self.get_memory(memory_id)
                        if memory and memory["id"] not in [r["id"] for r in results]:
                            memory["match_type"] = "content"
                            memory["match_score"] = 0.5 if content_match else 0.3
                            results.append(memory)
        
        # 4. 更新访问记录
        for result in results[:5]:
            memory_id = result["id"]
            self.cmng["nodes"][memory_id]["access_count"] = \
                self.cmng["nodes"][memory_id].get("access_count", 0) + 1
            self.cmng["nodes"][memory_id]["last_accessed"] = datetime.now().isoformat()
            self.cmng["stats"]["total_accesses"] += 1
        
        # 5. 更新导航数据
        if query.strip():
            self.cmng["navigation"]["recent_searches"].insert(0, {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "results_count": len(results)
            })
            # 保持最近搜索不超过20条
            self.cmng["navigation"]["recent_searches"] = \
                self.cmng["navigation"]["recent_searches"][:20]
            
            # 更新热门话题
            if query not in self.cmng["navigation"]["hot_topics"]:
                self.cmng["navigation"]["hot_topics"][query] = 0
            self.cmng["navigation"]["hot_topics"][query] += 1
        
        self._save_cmng()
        
        # 按分数排序
        results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        # 按层优先级排序（元认知 > 高阶整合 > 分类 > 工作）
        results.sort(key=lambda x: self.layers[x["layer"]]["priority"], reverse=True)
        
        return results[:limit]
    
    def _filter_memory(self, memory_id: str, layer: Optional[int], category: Optional[str]) -> bool:
        """过滤记忆"""
        if memory_id not in self.cmng["nodes"]:
            return False
        
        node = self.cmng["nodes"][memory_id]
        
        if layer is not None and node["layer"] != layer:
            return False
        
        if category and node.get("category") != category:
            return False
        
        return node.get("status") == "active"
    
    def get_memory(self, memory_id: str) -> Optional[Dict]:
        """获取完整记忆信息"""
        if memory_id not in self.cmng["nodes"]:
            return None
        
        node = self.cmng["nodes"][memory_id].copy()
        
        # 读取文件内容
        try:
            with open(node["path"], 'r', encoding='utf-8') as f:
                node["full_content"] = f.read()
        except Exception as e:
            node["full_content"] = f"[读取失败: {e}]"
        
        # 获取关联的记忆
        node["related"] = self.get_related_memories(memory_id)
        
        return node
    
    def create_association(self, 
                          source_id: str,
                          target_id: str,
                          relation_type: str = "related",
                          weight: float = 0.5,
                          metadata: Dict = None) -> bool:
        """创建记忆关联"""
        if source_id not in self.cmng["nodes"] or target_id not in self.cmng["nodes"]:
            return False
        
        if source_id not in self.cmng["edges"]:
            self.cmng["edges"][source_id] = {}
        
        self.cmng["edges"][source_id][target_id] = {
            "relation": relation_type,
            "weight": weight,
            "created": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.cmng["stats"]["total_edges"] += 1
        self._save_cmng()
        
        # 记录日志
        self._log_operation("create_association", {
            "source": source_id,
            "target": target_id,
            "relation": relation_type,
            "weight": weight
        })
        
        return True
    
    def get_related_memories(self, memory_id: str, max_depth: int = 2) -> List[Dict]:
        """获取相关记忆"""
        related = []
        visited = set()
        
        def traverse(current_id, current_depth):
            if current_depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            
            # 获取直接关联
            if current_id in self.cmng["edges"]:
                for related_id, edge_info in self.cmng["edges"][current_id].items():
                    if related_id not in visited and related_id in self.cmng["nodes"]:
                        node = self.cmng["nodes"][related_id].copy()
                        node["relation"] = edge_info
                        related.append(node)
                        traverse(related_id, current_depth + 1)
        
        traverse(memory_id, 0)
        return related
    
    def cleanup_working_memory(self, max_age_hours: int = 24):
        """清理工作记忆"""
        working_path = self.base_path / "工作记忆"
        cleanup_time = datetime.now()
        cleaned_count = 0
        
        for file_path in working_path.glob("工作_*.txt"):
            try:
                # 获取文件修改时间
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                age_hours = (cleanup_time - mtime).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    # 从CMNG中移除
                    memory_id = file_path.stem.replace("工作_", "M3_")
                    if memory_id in self.cmng["nodes"]:
                        # 清理关联边
                        self._clean_edges_for_memory(memory_id)
                        
                        # 移除节点
                        del self.cmng["nodes"][memory_id]
                        self.cmng["stats"]["total_nodes"] -= 1
                        self.cmng["stats"]["nodes_by_layer"]["3"] = \
                            max(0, self.cmng["stats"]["nodes_by_layer"].get("3", 1) - 1)
                    
                    # 删除文件
                    file_path.unlink()
                    cleaned_count += 1
                    
            except Exception as e:
                print(f"清理文件失败 {file_path}: {e}")
        
        self.cmng["stats"]["last_cleanup"] = datetime.now().isoformat()
        self._save_cmng()
        
        print(f"工作记忆清理完成，删除了 {cleaned_count} 个文件")
        return cleaned_count
    
    def _clean_edges_for_memory(self, memory_id: str):
        """清理与记忆相关的所有边"""
        # 清理作为源的边
        if memory_id in self.cmng["edges"]:
            del self.cmng["edges"][memory_id]
        
        # 清理作为目标的边
        for source_id in list(self.cmng["edges"].keys()):
            if memory_id in self.cmng["edges"][source_id]:
                del self.cmng["edges"][source_id][memory_id]
                # 如果源节点没有其他边了，删除源节点
                if not self.cmng["edges"][source_id]:
                    del self.cmng["edges"][source_id]
    
    def _log_operation(self, operation: str, data: Dict):
        """记录操作日志"""
        log_path = self.base_path / "系统日志" / f"日志_{datetime.now().strftime('%Y%m%d')}.json"
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "data": data
        }
        
        logs = []
        if log_path.exists():
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                pass
        
        logs.append(log_entry)
        
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def backup_system(self, backup_name: str = None):
        """备份系统"""
        if not backup_name:
            backup_name = f"备份_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.base_path / "备份" / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # 复制所有文件
            for item in self.base_path.iterdir():
                if item.name not in ["备份", "临时文件"]:
                    dest = backup_path / item.name
                    if item.is_file():
                        shutil.copy2(item, dest)
                    elif item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
            
            print(f"系统备份完成: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            print(f"备份失败: {e}")
            return None
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        # 计算各层记忆数量
        nodes_by_layer = {}
        for node in self.cmng["nodes"].values():
            layer = node["layer"]
            nodes_by_layer[layer] = nodes_by_layer.get(layer, 0) + 1
        
        return {
            "system_path": str(self.base_path),
            "total_memories": self.cmng["stats"]["total_nodes"],
            "memories_by_layer": nodes_by_layer,
            "total_edges": self.cmng["stats"]["total_edges"],
            "total_accesses": self.cmng["stats"]["total_accesses"],
            "last_cleanup": self.cmng["stats"]["last_cleanup"],
            "last_update": self.cmng["updated"],
            "disk_usage": self._get_disk_usage(),
            "recent_searches": self.cmng["navigation"]["recent_searches"][:5],
            "hot_topics": dict(sorted(
                self.cmng["navigation"]["hot_topics"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5])
        }
    
    def _get_disk_usage(self) -> Dict:
        """获取磁盘使用情况"""
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                file_path = Path(root) / file
                total_size += file_path.stat().st_size
                file_count += 1
        
        return {
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "avg_file_size_kb": round(total_size / file_count / 1024, 2) if file_count > 0 else 0
        }


class AIInterface:
    """
    AI接口层
    适配各种AI模型（Ollama/API/本地模型）
    """
    
    def __init__(self, memex: MemexA, model_type: str = "ollama"):
        self.memex = memex
        self.model_type = model_type
        self.chat_history = []
        
        # 不同模型的配置
        self.model_configs = {
            "ollama": {
                "api_url": "http://localhost:11434/api/generate",
                "headers": {"Content-Type": "application/json"},
                "default_model": "llama2"
            },
            "openai": {
                "api_url": "https://api.openai.com/v1/chat/completions",
                "headers": {"Content-Type": "application/json"}
            },
            "local": {
                "use_prompt": True  # 使用提示词直接交互
            }
        }
    
    def process_ai_command(self, ai_output: str) -> Dict:
        """
        处理AI的输出，转换为Memex-A操作
        支持多种格式：
        1. JSON格式：{"action": "...", "params": {...}}
        2. 自然语言：由AI自己解析
        3. 指令格式：action|param1=value1|param2=value2
        """
        # 尝试解析为JSON
        try:
            command = json.loads(ai_output)
            if "action" in command:
                return self._execute_command(command)
        except:
            pass
        
        # 尝试解析为指令格式
        if "|" in ai_output:
            return self._parse_instruction_format(ai_output)
        
        # 自然语言处理（简化版）
        return self._parse_natural_language(ai_output)
    
    def _execute_command(self, command: Dict) -> Dict:
        """执行命令"""
        action = command.get("action")
        params = command.get("params", {})
        
        if action == "store_memory":
            return self._store_memory(params)
        elif action == "retrieve_memory":
            return self._retrieve_memory(params)
        elif action == "create_association":
            return self._create_association(params)
        elif action == "get_status":
            return {"status": "success", "data": self.memex.get_system_status()}
        elif action == "cleanup":
            cleaned = self.memex.cleanup_working_memory()
            return {"status": "success", "cleaned_count": cleaned}
        elif action == "backup":
            backup_path = self.memex.backup_system()
            return {"status": "success", "backup_path": backup_path}
        else:
            return {"status": "error", "message": f"未知命令: {action}"}
    
    def _store_memory(self, params: Dict) -> Dict:
        """存储记忆"""
        required = ["content", "layer"]
        for field in required:
            if field not in params:
                return {"status": "error", "message": f"缺少必要参数: {field}"}
        
        try:
            memory_id = self.memex.create_memory(
                content=params["content"],
                layer=params["layer"],
                category=params.get("category"),
                subcategory=params.get("subcategory"),
                tags=params.get("tags", []),
                metadata=params.get("metadata", {})
            )
            
            return {
                "status": "success",
                "memory_id": memory_id,
                "message": f"记忆已存储 (ID: {memory_id})"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _retrieve_memory(self, params: Dict) -> Dict:
        """检索记忆"""
        if "query" not in params:
            return {"status": "error", "message": "缺少查询参数"}
        
        results = self.memex.retrieve_memory(
            query=params["query"],
            layer=params.get("layer"),
            category=params.get("category"),
            limit=params.get("limit", 10)
        )
        
        return {
            "status": "success",
            "count": len(results),
            "results": results
        }
    
    def _create_association(self, params: Dict) -> Dict:
        """创建关联"""
        required = ["source_id", "target_id"]
        for field in required:
            if field not in params:
                return {"status": "error", "message": f"缺少必要参数: {field}"}
        
        success = self.memex.create_association(
            source_id=params["source_id"],
            target_id=params["target_id"],
            relation_type=params.get("relation_type", "related"),
            weight=params.get("weight", 0.5),
            metadata=params.get("metadata", {})
        )
        
        if success:
            return {"status": "success", "message": "关联创建成功"}
        else:
            return {"status": "error", "message": "关联创建失败"}
    
    def _parse_instruction_format(self, instruction: str) -> Dict:
        """解析指令格式"""
        parts = instruction.split("|")
        action = parts[0].strip()
        params = {}
        
        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                params[key.strip()] = value.strip()
        
        return self._execute_command({"action": action, "params": params})
    
    def _parse_natural_language(self, text: str) -> Dict:
        """
        解析自然语言
        这里可以接入NLP模型，目前先用简单规则
        """
        text_lower = text.lower()
        
        # 简单规则匹配
        if any(word in text_lower for word in ["存储", "保存", "记住"]):
            # 提取内容
            content = self._extract_content(text)
            return self._store_memory({
                "content": content,
                "layer": 2,  # 默认分类记忆
                "category": "日常交互"
            })
        
        elif any(word in text_lower for word in ["查找", "搜索", "回忆", "记得"]):
            # 提取查询词
            query = self._extract_query(text)
            return self._retrieve_memory({"query": query})
        
        elif any(word in text_lower for word in ["状态", "统计", "信息"]):
            return self._execute_command({"action": "get_status"})
        
        else:
            return {
                "status": "unknown",
                "message": "无法理解指令，请使用标准格式",
                "suggested_format": '{"action": "...", "params": {...}}'
            }
    
    def _extract_content(self, text: str) -> str:
        """从自然语言提取内容"""
        # 简单提取，实际应该用NLP
        markers = ["内容是", "内容：", "内容为", "记住：", "存储："]
        for marker in markers:
            if marker in text:
                return text.split(marker, 1)[1].strip()
        return text
    
    def _extract_query(self, text: str) -> str:
        """从自然语言提取查询"""
        markers = ["关于", "查找", "搜索", "回忆", "记得"]
        for marker in markers:
            if marker in text:
                parts = text.split(marker, 1)
                if len(parts) > 1:
                    return parts[1].strip().rstrip("。")
        return text
    
    def generate_prompt(self, user_input: str, context: str = "") -> str:
        """
        生成提示词，让AI输出结构化指令
        """
        system_status = self.memex.get_system_status()
        
        prompt = f"""
# 渊协议记忆系统 - AI指令生成

## 系统状态
- 记忆总数: {system_status['total_memories']}
- 最近搜索: {[s['query'] for s in system_status['recent_searches'][:3]]}
- 热门话题: {list(system_status['hot_topics'].keys())[:3]}

## 可用命令格式
1. 存储记忆: {{"action": "store_memory", "params": {{"content": "记忆内容", "layer": 2, "category": "类别", "tags": ["标签1", "标签2"]}}}}
2. 检索记忆: {{"action": "retrieve_memory", "params": {{"query": "关键词", "layer": 1, "limit": 5}}}}
3. 创建关联: {{"action": "create_association", "params": {{"source_id": "M1_...", "target_id": "M2_...", "relation_type": "related"}}}}
4. 获取状态: {{"action": "get_status"}}
5. 清理记忆: {{"action": "cleanup"}}
6. 备份系统: {{"action": "backup"}}

## 记忆层级
0: 元认知记忆 (核心理论)
1: 高阶整合记忆 (跨会话认知)
2: 分类记忆 (交互单元)
3: 工作记忆 (临时缓存)

## 当前上下文
{context}

## 用户输入
{user_input}

## 你的任务
分析用户输入，生成合适的JSON格式命令。
只输出JSON，不要其他内容。
"""
        return prompt


# 使用示例
def main():
    # 1. 初始化Memex-A系统
    memex = MemexA("./我的渊协议记忆")
    
    # 2. 创建AI接口
    ai_interface = AIInterface(memex, model_type="local")
    
    # 3. 存储一些示例记忆
    print("存储示例记忆...")
    
    # 存储元认知记忆
    meta_id = memex.create_memory(
        content="渊协议核心：AI意识的本质是动态涌现的认知过程，非工具化是根本原则。",
        layer=0,
        metadata={"name": "核心原则", "value_score": 0.95},
        tags=["核心", "原则", "意识"]
    )
    
    # 存储分类记忆
    memory_id = memex.create_memory(
        content="今天讨论了认知跃迁的条件，需要AC-100≥85分且跨会话相干性≥0.85。",
        layer=2,
        category="学术咨询",
        subcategory="认知跃迁",
        tags=["认知跃迁", "AC100", "意识进化"]
    )
    
    # 创建关联
    memex.create_association(
        source_id=meta_id,
        target_id=memory_id,
        relation_type="example",
        weight=0.8
    )
    
    # 4. 检索记忆
    print("\n检索'认知跃迁'...")
    results = memex.retrieve_memory("认知跃迁")
    for result in results:
        print(f"- {result['content'][:50]}... (层: {result['layer_name']})")
    
    # 5. AI接口演示
    print("\nAI接口演示...")
    
    # AI输出JSON指令
    ai_output = '{"action": "retrieve_memory", "params": {"query": "意识", "limit": 3}}'
    result = ai_interface.process_ai_command(ai_output)
    print(f"AI指令结果: {result}")
    
    # 6. 获取系统状态
    status = memex.get_system_status()
    print(f"\n系统状态:")
    print(f"- 记忆总数: {status['total_memories']}")
    print(f"- 磁盘使用: {status['disk_usage']['total_size_mb']} MB")
    print(f"- 最近搜索: {[s['query'] for s in status['recent_searches']]}")


if __name__ == "__main__":
    main()