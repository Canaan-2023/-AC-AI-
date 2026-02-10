"""记忆管理器测试"""

import os
import sys
import unittest
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory_manager import MemoryManager, MemoryType, ValueLevel


class TestMemoryManager(unittest.TestCase):
    """测试记忆管理器"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.mm = MemoryManager(base_path=self.test_dir)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_create_memory(self):
        """测试创建记忆"""
        mem_id = self.mm.create_memory(
            memory_type=MemoryType.WORKING,
            user_input="测试输入",
            ai_response="测试响应",
            confidence=80
        )
        
        self.assertIsInstance(mem_id, int)
        self.assertGreater(mem_id, 0)
    
    def test_get_memory(self):
        """测试读取记忆"""
        mem_id = self.mm.create_memory(
            memory_type=MemoryType.CLASSIFIED,
            user_input="问题",
            ai_response="答案",
            confidence=75,
            value_level=ValueLevel.HIGH
        )
        
        content = self.mm.get_memory(mem_id)
        self.assertIsNotNone(content)
        self.assertIn("测试输入", content)
        self.assertIn("测试响应", content)
    
    def test_update_memory(self):
        """测试更新记忆"""
        mem_id = self.mm.create_memory(
            memory_type=MemoryType.WORKING,
            user_input="原问题",
            ai_response="原答案",
            confidence=70
        )
        
        success = self.mm.update_memory(mem_id, confidence=90)
        self.assertTrue(success)
        
        meta = self.mm.get_memory_metadata(mem_id)
        self.assertEqual(meta.confidence, 90)
    
    def test_delete_memory(self):
        """测试删除记忆"""
        mem_id = self.mm.create_memory(
            memory_type=MemoryType.WORKING,
            user_input="问题",
            ai_response="答案"
        )
        
        # 标记删除
        success = self.mm.delete_memory(mem_id)
        self.assertTrue(success)
        
        # 应该获取不到
        content = self.mm.get_memory(mem_id)
        self.assertIsNone(content)
    
    def test_nng_association(self):
        """测试NNG关联"""
        mem_id = self.mm.create_memory(
            memory_type=MemoryType.CLASSIFIED,
            user_input="问题",
            ai_response="答案"
        )
        
        # 添加关联
        success = self.mm.add_nng_association(mem_id, "1.2.3")
        self.assertTrue(success)
        
        # 获取关联的记忆
        memories = self.mm.get_memories_by_nng("1.2.3")
        self.assertIn(mem_id, memories)
        
        # 移除关联
        success = self.mm.remove_nng_association(mem_id, "1.2.3")
        self.assertTrue(success)
        
        memories = self.mm.get_memories_by_nng("1.2.3")
        self.assertNotIn(mem_id, memories)
    
    def test_working_memory(self):
        """测试工作记忆"""
        # 创建多条工作记忆
        for i in range(5):
            self.mm.create_memory(
                memory_type=MemoryType.WORKING,
                user_input=f"问题{i}",
                ai_response=f"答案{i}"
            )
        
        count = self.mm.get_working_memory_count()
        self.assertEqual(count, 5)
        
        memories = self.mm.get_working_memories()
        self.assertEqual(len(memories), 5)
        
        # 清空
        cleared = self.mm.clear_working_memory()
        self.assertEqual(cleared, 5)
        
        count = self.mm.get_working_memory_count()
        self.assertEqual(count, 0)
    
    def test_statistics(self):
        """测试统计功能"""
        # 创建不同类型的记忆
        self.mm.create_memory(
            memory_type=MemoryType.META_COGNITIVE,
            user_input="元认知",
            ai_response="反思"
        )
        
        self.mm.create_memory(
            memory_type=MemoryType.CLASSIFIED,
            user_input="分类",
            ai_response="知识",
            value_level=ValueLevel.HIGH
        )
        
        stats = self.mm.get_statistics()
        
        self.assertIn("total", stats)
        self.assertIn("by_type", stats)
        self.assertIn("avg_confidence", stats)


if __name__ == "__main__":
    unittest.main()
