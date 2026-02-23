"""记忆管理器模块"""

import os
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

class MemoryManager:
    """记忆管理器类"""
    
    def __init__(self, memory_root_path: str):
        """初始化记忆管理器
        
        Args:
            memory_root_path: 记忆根目录路径
        """
        self.memory_root_path = memory_root_path
        os.makedirs(self.memory_root_path, exist_ok=True)
        
        self._create_memory_directories()
    
    def _create_memory_directories(self):
        """创建记忆分类目录"""
        categories = [
            '元认知记忆',
            '高阶整合记忆',
            '分类记忆/高',
            '分类记忆/中',
            '分类记忆/低',
            '工作记忆'
        ]
        
        for category in categories:
            category_path = os.path.join(self.memory_root_path, category)
            os.makedirs(category_path, exist_ok=True)
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        return datetime.now().isoformat()
    
    def _get_time_directory(self) -> str:
        """获取时间分类目录"""
        now = datetime.now()
        return f"{now.year}/{now.month:02d}/{now.day:02d}"
    
    def _generate_memory_id(self) -> str:
        """生成记忆ID"""
        return str(uuid.uuid4())[:8]
    
    def _assess_value_level(self, memory_content: Dict[str, Any]) -> str:
        """自动评估记忆价值层级
        
        Args:
            memory_content: 记忆内容
            
        Returns:
            价值层级（高/中/低）
        """
        confidence = memory_content.get('置信度', 0.5)
        
        core_content = memory_content.get('核心内容', {})
        user_input = core_content.get('用户输入', '')
        ai_response = core_content.get('AI响应', '')
        
        content_length = len(user_input) + len(ai_response)
        
        tags = memory_content.get('标签', [])
        
        has_important_tags = any(tag.lower() in ['重要', '关键', '核心', 'critical', 'important', 'key'] 
                                  for tag in tags)
        
        related_nng = memory_content.get('关联NNG', [])
        has_strong_nng_relation = len(related_nng) > 0 and any(
            nng.get('关联程度', 0) > 0.8 for nng in related_nng
        )
        
        score = 0
        
        if confidence >= 0.9:
            score += 3
        elif confidence >= 0.7:
            score += 2
        elif confidence >= 0.5:
            score += 1
        
        if content_length > 1000:
            score += 2
        elif content_length > 500:
            score += 1
        
        if has_important_tags:
            score += 2
        
        if has_strong_nng_relation:
            score += 1
        
        if len(tags) >= 3:
            score += 1
        
        if score >= 6:
            return '高'
        elif score >= 3:
            return '中'
        else:
            return '低'
    
    def save_memory(self, memory_content: Dict[str, Any], memory_type: str = '分类记忆', 
                    value_level: str = None) -> str:
        """保存记忆文件
        
        Args:
            memory_content: 记忆内容
            memory_type: 记忆类型
            value_level: 价值层级（如果为None，自动评估）
            
        Returns:
            记忆文件路径
        """
        try:
            memory_id = self._generate_memory_id()
            
            if '记忆ID' not in memory_content:
                memory_content['记忆ID'] = memory_id
            if '记忆时间' not in memory_content:
                memory_content['记忆时间'] = self._get_current_time()
            if '记忆层级' not in memory_content:
                memory_content['记忆层级'] = memory_type
            
            if memory_type == '分类记忆':
                if value_level is None:
                    value_level = self._assess_value_level(memory_content)
                memory_content['价值评估'] = value_level
                directory = os.path.join(self.memory_root_path, memory_type, value_level, self._get_time_directory())
            else:
                directory = os.path.join(self.memory_root_path, memory_type, self._get_time_directory())
            
            os.makedirs(directory, exist_ok=True)
            
            file_path = os.path.join(directory, f"{memory_id}.json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(memory_content, f, ensure_ascii=False, indent=2)
            
            relative_path = os.path.relpath(file_path, self.memory_root_path)
            return relative_path.replace('\\', '/')
        except Exception:
            return ''
    
    def create_memory(self, user_input: str, ai_response: str, 
                      confidence: float = 0.8,
                      memory_type: str = '分类记忆',
                      value_level: str = None,
                      tags: List[str] = None,
                      related_nng: List[Dict[str, Any]] = None) -> str:
        """创建新记忆
        
        Args:
            user_input: 用户输入
            ai_response: AI响应
            confidence: 置信度
            memory_type: 记忆类型
            value_level: 价值层级
            tags: 标签列表
            related_nng: 关联NNG列表
            
        Returns:
            记忆文件路径
        """
        memory_content = {
            "记忆层级": memory_type,
            "记忆ID": self._generate_memory_id(),
            "记忆时间": self._get_current_time(),
            "置信度": confidence,
            "核心内容": {
                "用户输入": user_input,
                "AI响应": ai_response
            },
            "关联NNG": related_nng or [],
            "标签": tags or [],
            "价值评估": value_level,
            "更新历史": [
                {
                    "时间": self._get_current_time(),
                    "操作": "创建",
                    "内容": "初始创建记忆"
                }
            ]
        }
        
        return self.save_memory(memory_content, memory_type, value_level)
    
    def get_memory(self, memory_path: str) -> Optional[Dict[str, Any]]:
        """获取记忆内容
        
        Args:
            memory_path: 记忆文件路径
            
        Returns:
            记忆内容
        """
        try:
            if memory_path.startswith('Y层记忆库/'):
                memory_path = memory_path[6:]
            
            full_path = os.path.join(self.memory_root_path, memory_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def delete_memory(self, memory_path: str) -> bool:
        """删除记忆文件"""
        try:
            if memory_path.startswith('Y层记忆库/'):
                memory_path = memory_path[6:]
            
            full_path = os.path.join(self.memory_root_path, memory_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception:
            return False
    
    def deprecate_memory(self, memory_path: str, reason: str = '置信度过低') -> bool:
        """降权记忆而非删除
        
        根据渊协议原则：错误的记忆也是"我"的一部分，不删除错误记忆，降低置信度至0
        
        Args:
            memory_path: 记忆文件路径
            reason: 降权原因
            
        Returns:
            是否降权成功
        """
        try:
            memory_content = self.get_memory(memory_path)
            if not memory_content:
                return False
            
            memory_content['置信度'] = 0.0
            memory_content['价值评估'] = '低'
            memory_content['状态'] = '已废弃'
            memory_content['废弃原因'] = reason
            memory_content['废弃时间'] = self._get_current_time()
            
            if '更新历史' not in memory_content:
                memory_content['更新历史'] = []
            
            memory_content['更新历史'].append({
                "时间": self._get_current_time(),
                "操作": "降权",
                "内容": f"降权原因: {reason}"
            })
            
            if memory_path.startswith('Y层记忆库/'):
                memory_path = memory_path[6:]
            
            full_path = os.path.join(self.memory_root_path, memory_path)
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(memory_content, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception:
            return False
    
    def update_memory(self, memory_path: str, updates: Dict[str, Any]) -> bool:
        """更新记忆内容
        
        Args:
            memory_path: 记忆文件路径
            updates: 更新内容
            
        Returns:
            是否更新成功
        """
        try:
            memory_content = self.get_memory(memory_path)
            if not memory_content:
                return False
            
            for key, value in updates.items():
                if key == '核心内容':
                    if '核心内容' not in memory_content:
                        memory_content['核心内容'] = {}
                    memory_content['核心内容'].update(value)
                else:
                    memory_content[key] = value
            
            if '更新历史' not in memory_content:
                memory_content['更新历史'] = []
            
            memory_content['更新历史'].append({
                "时间": self._get_current_time(),
                "操作": "更新",
                "内容": f"更新字段: {', '.join(updates.keys())}"
            })
            
            if memory_path.startswith('Y层记忆库/'):
                memory_path = memory_path[6:]
            
            full_path = os.path.join(self.memory_root_path, memory_path)
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(memory_content, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception:
            return False
    
    def list_memories(self, memory_type: str = '', value_level: str = '') -> List[str]:
        """列出指定类型和价值层级的记忆文件"""
        memories = []
        try:
            if memory_type == '分类记忆' and value_level:
                search_directory = os.path.join(self.memory_root_path, memory_type, value_level)
            elif memory_type:
                search_directory = os.path.join(self.memory_root_path, memory_type)
            else:
                search_directory = self.memory_root_path
            
            if not os.path.exists(search_directory):
                return memories
            
            for root, dirs, files in os.walk(search_directory):
                for file in files:
                    if file.endswith('.json'):
                        relative_path = os.path.relpath(os.path.join(root, file), self.memory_root_path)
                        memories.append(relative_path.replace('\\', '/'))
        except Exception:
            pass
        
        return memories
    
    def search_memories(self, keyword: str) -> List[str]:
        """搜索包含关键字的记忆文件"""
        matching_memories = []
        try:
            all_memories = self.list_memories()
            
            for memory_path in all_memories:
                memory_content = self.get_memory(memory_path)
                if memory_content:
                    content_str = json.dumps(memory_content, ensure_ascii=False)
                    if keyword in content_str:
                        matching_memories.append(memory_path)
        except Exception:
            pass
        
        return matching_memories
    
    def filter_memories(self, filters: Dict[str, Any]) -> List[str]:
        """筛选记忆文件"""
        filtered_memories = []
        try:
            all_memories = self.list_memories()
            
            for memory_path in all_memories:
                memory_content = self.get_memory(memory_path)
                if memory_content:
                    if self._apply_filters(memory_content, filters):
                        filtered_memories.append(memory_path)
        except Exception:
            pass
        
        return filtered_memories
    
    def _apply_filters(self, memory_content: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """应用筛选条件"""
        for key, value in filters.items():
            if key == 'memory_type' and memory_content.get('记忆层级') != value:
                return False
            elif key == 'confidence_min' and memory_content.get('置信度', 0) < value:
                return False
            elif key == 'confidence_max' and memory_content.get('置信度', 0) > value:
                return False
            elif key == 'value_level' and memory_content.get('价值评估') != value:
                return False
            elif key == 'has_tag':
                tags = memory_content.get('标签', [])
                if value not in tags:
                    return False
        return True
    
    def get_memories_by_nng(self, nng_node_id: str) -> List[str]:
        """获取与指定NNG节点关联的记忆"""
        related_memories = []
        try:
            all_memories = self.list_memories()
            
            for memory_path in all_memories:
                memory_content = self.get_memory(memory_path)
                if memory_content:
                    related_nng = memory_content.get('关联NNG', [])
                    for nng in related_nng:
                        if nng.get('节点ID') == nng_node_id:
                            related_memories.append(memory_path)
                            break
        except Exception:
            pass
        
        return related_memories
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        statistics = {
            'total_memories': 0,
            'memories_by_type': {},
            'memories_by_value_level': {},
            'avg_confidence': 0.0
        }
        
        try:
            all_memories = self.list_memories()
            statistics['total_memories'] = len(all_memories)
            
            confidences = []
            for memory_path in all_memories:
                memory_content = self.get_memory(memory_path)
                if memory_content:
                    memory_type = memory_content.get('记忆层级', '未知')
                    if memory_type not in statistics['memories_by_type']:
                        statistics['memories_by_type'][memory_type] = 0
                    statistics['memories_by_type'][memory_type] += 1
                    
                    if memory_type == '分类记忆':
                        value_level = memory_content.get('价值评估', '未知')
                        if value_level not in statistics['memories_by_value_level']:
                            statistics['memories_by_value_level'][value_level] = 0
                        statistics['memories_by_value_level'][value_level] += 1
                    
                    confidence = memory_content.get('置信度', 0)
                    if confidence > 0:
                        confidences.append(confidence)
            
            if confidences:
                statistics['avg_confidence'] = sum(confidences) / len(confidences)
        except Exception:
            pass
        
        return statistics
    
    def validate_memory(self, memory_content: Dict[str, Any]) -> bool:
        """验证记忆内容"""
        try:
            required_fields = ['记忆层级', '记忆ID', '记忆时间', '置信度', '核心内容']
            for field in required_fields:
                if field not in memory_content:
                    return False
            
            if not isinstance(memory_content['记忆层级'], str):
                return False
            if not isinstance(memory_content['记忆ID'], str):
                return False
            if not isinstance(memory_content['记忆时间'], str):
                return False
            if not isinstance(memory_content['置信度'], (int, float)):
                return False
            if not isinstance(memory_content['核心内容'], dict):
                return False
            
            if memory_content['置信度'] < 0 or memory_content['置信度'] > 1:
                return False
            
            core_content = memory_content['核心内容']
            if '用户输入' not in core_content or 'AI响应' not in core_content:
                return False
            
            return True
        except Exception:
            return False
    
    def reevaluate_value_levels(self):
        """重新评估所有记忆的价值层级"""
        try:
            all_memories = self.list_memories('分类记忆')
            
            for memory_path in all_memories:
                memory_content = self.get_memory(memory_path)
                if memory_content:
                    new_value_level = self._assess_value_level(memory_content)
                    current_value_level = memory_content.get('价值评估')
                    
                    if new_value_level != current_value_level:
                        memory_content['价值评估'] = new_value_level
                        
                        if memory_path.startswith('Y层记忆库/'):
                            memory_path = memory_path[6:]
                        
                        old_path = os.path.join(self.memory_root_path, memory_path)
                        
                        new_directory = os.path.join(
                            self.memory_root_path, 
                            '分类记忆', 
                            new_value_level, 
                            self._get_time_directory()
                        )
                        os.makedirs(new_directory, exist_ok=True)
                        
                        memory_id = memory_content.get('记忆ID', self._generate_memory_id())
                        new_path = os.path.join(new_directory, f"{memory_id}.json")
                        
                        if '更新历史' not in memory_content:
                            memory_content['更新历史'] = []
                        memory_content['更新历史'].append({
                            "时间": self._get_current_time(),
                            "操作": "价值重评估",
                            "内容": f"价值层级从 {current_value_level} 更改为 {new_value_level}"
                        })
                        
                        with open(new_path, 'w', encoding='utf-8') as f:
                            json.dump(memory_content, f, ensure_ascii=False, indent=2)
                        
                        if os.path.exists(old_path):
                            os.remove(old_path)
        except Exception:
            pass
