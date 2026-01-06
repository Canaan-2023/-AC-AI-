#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字典控制器 - 字典相关操作
"""

from typing import Dict, Any, List, Optional
from ..models.dictionary_manager import DictionaryManager
from ..core.logger import AbyssLogger


class DictionaryController:
    """字典控制器"""
    
    def __init__(self, dict_manager: DictionaryManager):
        self.dict_manager = dict_manager
        self.logger = AbyssLogger("DictionaryController")
    
    def add_word(self, word: str) -> str:
        """添加词到字典"""
        dict_id = self.dict_manager.add_word(word)
        self.logger.info(f"添加词: {word} -> {dict_id}")
        return dict_id
    
    def find_dictionary(self, word: str) -> Optional[str]:
        """查找包含词的字典"""
        return self.dict_manager.find_dictionary(word)
    
    def search_words(self, prefix: str, limit: int = 10) -> List[str]:
        """搜索以指定前缀开头的词"""
        return self.dict_manager.search_words(prefix, limit)
    
    def get_dictionaries(self) -> Dict[str, Any]:
        """获取字典统计"""
        return self.dict_manager.get_stats()
    
    def trigger_fission(self) -> bool:
        """触发裂变"""
        result = self.dict_manager.check_and_perform_fission()
        self.logger.info(f"裂变触发: {'成功' if result else '无需裂变'}")
        return result
    
    def save_all(self):
        """保存所有字典"""
        self.dict_manager.save_all_dictionaries()
        self.logger.info("所有字典已保存")