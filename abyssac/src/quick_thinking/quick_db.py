"""快思考系统模块"""

import os
import json
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class QuickThinkingDB:
    """快思考数据库"""
    
    def __init__(self, db_path: str = 'storage/quick_thinking.db'):
        """初始化快思考数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quick_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                question_hash TEXT NOT NULL,
                answer TEXT NOT NULL,
                confidence REAL DEFAULT 0.8,
                question_type TEXT DEFAULT 'simple',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_question_hash ON quick_answers(question_hash)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_confidence ON quick_answers(confidence)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_question_type ON quick_answers(question_type)
        ''')
        
        conn.commit()
        conn.close()
    
    def _hash_question(self, question: str) -> str:
        """生成问题的哈希值"""
        import hashlib
        return hashlib.md5(question.encode('utf-8')).hexdigest()
    
    def add_answer(self, question: str, answer: str, confidence: float = 0.8, 
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        question_hash = self._hash_question(question)
        current_time = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO quick_answers (question, question_hash, answer, confidence, question_type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (question, question_hash, answer, confidence, question_type, current_time, current_time))
        
        answer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return answer_id
    
    def update_answer(self, answer_id: int, answer: str = None, confidence: float = None):
        """更新答案"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = datetime.now().isoformat()
        
        if answer is not None and confidence is not None:
            cursor.execute('''
                UPDATE quick_answers SET answer = ?, confidence = ?, updated_at = ? WHERE id = ?
            ''', (answer, confidence, current_time, answer_id))
        elif answer is not None:
            cursor.execute('''
                UPDATE quick_answers SET answer = ?, updated_at = ? WHERE id = ?
            ''', (answer, current_time, answer_id))
        elif confidence is not None:
            cursor.execute('''
                UPDATE quick_answers SET confidence = ?, updated_at = ? WHERE id = ?
            ''', (confidence, current_time, answer_id))
        
        conn.commit()
        conn.close()
    
    def query_answer(self, question: str, threshold: float = 0.5) -> Optional[Dict[str, Any]]:
        """查询快速答案
        
        Args:
            question: 用户问题
            threshold: 置信度阈值
            
        Returns:
            答案内容或None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        question_hash = self._hash_question(question)
        
        cursor.execute('''
            SELECT id, question, answer, confidence, question_type, created_at, access_count
            FROM quick_answers 
            WHERE question_hash = ? AND confidence >= ?
            ORDER BY confidence DESC
            LIMIT 1
        ''', (question_hash, threshold))
        
        result = cursor.fetchone()
        
        if result:
            cursor.execute('''
                UPDATE quick_answers SET access_count = access_count + 1 WHERE id = ?
            ''', (result[0],))
            conn.commit()
            
            conn.close()
            return {
                'id': result[0],
                'question': result[1],
                'answer': result[2],
                'confidence': result[3],
                'question_type': result[4],
                'created_at': result[5],
                'access_count': result[6] + 1
            }
        
        cursor.execute('''
            SELECT id, question, answer, confidence, question_type, created_at, access_count
            FROM quick_answers 
            WHERE question LIKE ? AND confidence >= ?
            ORDER BY confidence DESC
            LIMIT 5
        ''', (f'%{question}%', threshold))
        
        results = cursor.fetchall()
        conn.close()
        
        if results:
            best_match = results[0]
            return {
                'id': best_match[0],
                'question': best_match[1],
                'answer': best_match[2],
                'confidence': best_match[3] * 0.9,
                'question_type': best_match[4],
                'created_at': best_match[5],
                'access_count': best_match[6],
                'is_fuzzy_match': True
            }
        
        return None
    
    def get_all_answers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有答案"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, question, answer, confidence, question_type, created_at, access_count
            FROM quick_answers 
            ORDER BY access_count DESC, confidence DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'id': r[0],
            'question': r[1],
            'answer': r[2],
            'confidence': r[3],
            'question_type': r[4],
            'created_at': r[5],
            'access_count': r[6]
        } for r in results]
    
    def delete_answer(self, answer_id: int):
        """删除答案"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM quick_answers WHERE id = ?', (answer_id,))
        conn.commit()
        conn.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM quick_answers')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(confidence) FROM quick_answers')
        avg_confidence = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT question_type, COUNT(*) FROM quick_answers GROUP BY question_type')
        by_type = dict(cursor.fetchall())
        
        cursor.execute('SELECT SUM(access_count) FROM quick_answers')
        total_access = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_answers': total,
            'avg_confidence': avg_confidence,
            'by_type': by_type,
            'total_access': total_access
        }
