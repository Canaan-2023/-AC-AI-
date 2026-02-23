"""快思考管理器模块"""

import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from .quick_db import QuickThinkingDB
from .question_classifier import QuestionClassifier


class QuickThinkingManager:
    """快思考管理器 - 整合快思考数据库和问题分类器"""
    
    def __init__(self, db_path: str = 'storage/quick_thinking.db', llm_integration=None):
        """初始化快思考管理器
        
        Args:
            db_path: 数据库文件路径
            llm_integration: LLM集成（可选）
        """
        self.db = QuickThinkingDB(db_path)
        self.classifier = QuestionClassifier(llm_integration)
        self.llm_integration = llm_integration
        self.sync_threshold = 0.8
    
    def process(self, question: str) -> Dict[str, Any]:
        """处理用户问题
        
        Args:
            question: 用户问题
            
        Returns:
            处理结果
        """
        question = question.strip()
        
        if not question:
            return {
                'success': False,
                'use_quick': False,
                'reason': '问题为空'
            }
        
        quick_answer = self.db.query_answer(question)
        has_quick_answer = quick_answer is not None
        
        use_quick, reason = self.classifier.should_use_quick_thinking(question, has_quick_answer)
        
        if use_quick and quick_answer:
            return {
                'success': True,
                'use_quick': True,
                'answer': quick_answer['answer'],
                'confidence': quick_answer['confidence'],
                'reason': reason,
                'answer_id': quick_answer['id'],
                'is_fuzzy_match': quick_answer.get('is_fuzzy_match', False)
            }
        
        return {
            'success': False,
            'use_quick': False,
            'reason': reason,
            'question_type': self.classifier.classify(question)[0],
            'complexity': self.classifier.classify(question)[1]
        }
    
    def add_quick_answer(self, question: str, answer: str, confidence: float = 0.8,
                         question_type: str = 'simple') -> int:
        """添加快速答案
        
        Args:
            question: 用户问题
            answer: 答案内容
            confidence: 置信度
            question_type: 问题类型
            
        Returns:
            答案ID
        """
        return self.db.add_answer(question, answer, confidence, question_type)
    
    def sync_from_slow_thinking(self, question: str, answer: str, confidence: float,
                                 question_type: str = 'simple'):
        """从慢思考系统同步答案
        
        Args:
            question: 用户问题
            answer: 答案内容
            confidence: 置信度
            question_type: 问题类型
        """
        if confidence >= self.sync_threshold:
            existing = self.db.query_answer(question)
            
            if existing:
                if confidence > existing['confidence']:
                    self.db.update_answer(existing['id'], answer, confidence)
            else:
                self.db.add_answer(question, answer, confidence, question_type)
    
    def batch_sync(self, items: list):
        """批量同步
        
        Args:
            items: [(question, answer, confidence, question_type), ...]
        """
        for item in items:
            if len(item) >= 3:
                question = item[0]
                answer = item[1]
                confidence = item[2]
                question_type = item[3] if len(item) > 3 else 'simple'
                self.sync_from_slow_thinking(question, answer, confidence, question_type)
    
    def get_all_quick_answers(self, limit: int = 100) -> list:
        """获取所有快速答案"""
        return self.db.get_all_answers(limit)
    
    def delete_quick_answer(self, answer_id: int):
        """删除快速答案"""
        self.db.delete_answer(answer_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.db.get_statistics()
    
    def should_use_quick(self, question: str) -> Tuple[bool, str]:
        """判断是否应该使用快思考
        
        Args:
            question: 用户问题
            
        Returns:
            (是否使用快思考, 原因)
        """
        quick_answer = self.db.query_answer(question)
        has_quick_answer = quick_answer is not None
        return self.classifier.should_use_quick_thinking(question, has_quick_answer)
    
    def classify_question(self, question: str) -> Tuple[str, str, float]:
        """分类问题
        
        Args:
            question: 用户问题
            
        Returns:
            (问题类型, 复杂度, 置信度)
        """
        return self.classifier.classify(question)
    
    def update_answer_confidence(self, answer_id: int, new_confidence: float):
        """更新答案置信度"""
        self.db.update_answer(answer_id, confidence=new_confidence)
    
    def cleanup_low_confidence(self, threshold: float = 0.3):
        """清理低置信度答案"""
        all_answers = self.db.get_all_answers(limit=1000)
        for answer in all_answers:
            if answer['confidence'] < threshold:
                self.db.delete_answer(answer['id'])
