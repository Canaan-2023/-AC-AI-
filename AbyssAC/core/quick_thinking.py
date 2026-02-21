"""
Quick Thinking System & Question Classifier
快思考系统与问题分类器
"""

import sqlite3
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from config.system_config import get_config
from core.llm_interface import get_llm_interface


@dataclass
class QuickAnswer:
    """快速答案数据结构"""
    id: int
    question: str
    answer: str
    confidence: float
    created_at: str


class QuickThinkingDB:
    """快思考数据库"""
    
    def __init__(self, db_path: str = "storage/quick_thinking.db"):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """确保数据库和表存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建快答案表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quick_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建全文搜索索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_question ON quick_answers(question)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_confidence ON quick_answers(confidence)
        ''')
        
        conn.commit()
        conn.close()
    
    def add_answer(self, question: str, answer: str, confidence: float = 0.5) -> int:
        """添加快速答案"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO quick_answers (question, answer, confidence, created_at)
            VALUES (?, ?, ?, ?)
        ''', (question, answer, confidence, datetime.now().isoformat()))
        
        answer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return answer_id
    
    def search_answers(self, query: str, limit: int = 5) -> List[QuickAnswer]:
        """搜索相关答案"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 使用简单的LIKE匹配（生产环境可用更复杂的相似度算法）
        cursor.execute('''
            SELECT id, question, answer, confidence, created_at
            FROM quick_answers
            WHERE question LIKE ?
            ORDER BY confidence DESC, created_at DESC
            LIMIT ?
        ''', (f'%{query}%', limit))
        
        results = []
        for row in cursor.fetchall():
            results.append(QuickAnswer(
                id=row[0],
                question=row[1],
                answer=row[2],
                confidence=row[3],
                created_at=row[4]
            ))
        
        conn.close()
        return results
    
    def get_answer(self, answer_id: int) -> Optional[QuickAnswer]:
        """获取指定答案"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, question, answer, confidence, created_at
            FROM quick_answers
            WHERE id = ?
        ''', (answer_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return QuickAnswer(
                id=row[0],
                question=row[1],
                answer=row[2],
                confidence=row[3],
                created_at=row[4]
            )
        return None
    
    def update_confidence(self, answer_id: int, new_confidence: float) -> bool:
        """更新答案置信度"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE quick_answers
            SET confidence = ?
            WHERE id = ?
        ''', (new_confidence, answer_id))
        
        conn.commit()
        conn.close()
        
        return True
    
    def delete_answer(self, answer_id: int) -> bool:
        """删除答案"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM quick_answers WHERE id = ?', (answer_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    def list_all(self, limit: int = 100) -> List[QuickAnswer]:
        """列出所有答案"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, question, answer, confidence, created_at
            FROM quick_answers
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append(QuickAnswer(
                id=row[0],
                question=row[1],
                answer=row[2],
                confidence=row[3],
                created_at=row[4]
            ))
        
        conn.close()
        return results


class QuestionClassifier:
    """问题分类器"""
    
    def __init__(self):
        self.llm = get_llm_interface()
    
    def classify(self, question: str) -> Dict[str, Any]:
        """
        分类问题类型和复杂度
        
        Returns:
            {
                "question_type": "事实性/解释性/创造性/...",
                "complexity": "简单/中等/复杂",
                "use_quick": True/False,
                "reason": "..."
            }
        """
        prompt = f"""你是问题分类器。分析用户问题的类型和复杂度，决定使用快思考还是慢思考。

【分类维度】
1. 问题类型：
   - 事实性问题：有明确答案的问题（如"Python是谁创建的"）
   - 解释性问题：需要解释说明的问题（如"什么是GIL"）
   - 创造性问题：需要创造性回答的问题（如"设计一个算法"）
   - 分析性问题：需要分析推理的问题（如"比较A和B的优劣"）

2. 复杂度：
   - 简单：单一概念，直接回答
   - 中等：需要一定推理，涉及多个概念
   - 复杂：深度分析，需要大量背景知识

【输出格式】
问题类型：{{类型}}
复杂度：{{简单/中等/复杂}}
建议使用：{{快思考/慢思考}}
理由：{{为什么这样分类}}

【输入】
用户问题：{question}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = self.llm.chat(messages)
        
        if not response.success:
            # 默认使用慢思考
            return {
                "question_type": "未知",
                "complexity": "复杂",
                "use_quick": False,
                "reason": f"分类失败: {response.error}"
            }
        
        return self._parse_classification(response.content)
    
    def _parse_classification(self, content: str) -> Dict[str, Any]:
        """解析分类结果"""
        result = {
            "question_type": "未知",
            "complexity": "中等",
            "use_quick": False,
            "reason": ""
        }
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('问题类型：'):
                result["question_type"] = line.replace('问题类型：', '').strip()
            elif line.startswith('复杂度：'):
                result["complexity"] = line.replace('复杂度：', '').strip()
            elif line.startswith('建议使用：'):
                use_quick = '快思考' in line
                result["use_quick"] = use_quick
            elif line.startswith('理由：'):
                result["reason"] = line.replace('理由：', '').strip()
        
        # 根据复杂度和类型做最终决定
        if result["complexity"] == "简单" and result["question_type"] == "事实性":
            result["use_quick"] = True
        elif result["complexity"] == "复杂" or result["question_type"] in ["创造性", "分析性"]:
            result["use_quick"] = False
        
        return result


class QuickThinkingSystem:
    """快思考系统"""
    
    def __init__(self):
        self.config = get_config()
        self.db = QuickThinkingDB()
        self.classifier = QuestionClassifier()
    
    def query(self, question: str, confidence_threshold: float = 0.6) -> Optional[str]:
        """
        快速查询答案
        
        Args:
            question: 用户问题
            confidence_threshold: 置信度阈值
        
        Returns:
            答案或None
        """
        # 搜索相关答案
        answers = self.db.search_answers(question, limit=3)
        
        if not answers:
            return None
        
        # 检查最高置信度的答案
        best_answer = answers[0]
        if best_answer.confidence >= confidence_threshold:
            return best_answer.answer
        
        return None
    
    def add_from_slow_thinking(self, question: str, answer: str,
                                confidence: float = 0.7) -> int:
        """从慢思考系统添加快答案"""
        return self.db.add_answer(question, answer, confidence)
    
    def should_use_quick(self, question: str) -> bool:
        """判断是否使用快思考"""
        classification = self.classifier.classify(question)
        return classification.get("use_quick", False)


# 全局实例
_quick_system = None


def get_quick_system() -> QuickThinkingSystem:
    """获取全局快思考系统"""
    global _quick_system
    if _quick_system is None:
        _quick_system = QuickThinkingSystem()
    return _quick_system
