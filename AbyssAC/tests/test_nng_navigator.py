"""NNG导航器测试"""

import os
import sys
import unittest
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.nng_navigator import NNGNavigator


class TestNNGNavigator(unittest.TestCase):
    """测试NNG导航器"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.nav = NNGNavigator(base_path=self.test_dir)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_create_node(self):
        """测试创建节点"""
        success = self.nav.create_node(
            location="1",
            content="一级节点测试",
            confidence=80
        )
        self.assertTrue(success)
        
        # 验证节点存在
        node = self.nav.get_node("1")
        self.assertIsNotNone(node)
        self.assertEqual(node.content, "一级节点测试")
    
    def test_create_child_node(self):
        """测试创建子节点"""
        # 先创建父节点
        self.nav.create_node("1", "父节点", 80)
        
        # 创建子节点
        success = self.nav.create_node(
            location="1.1",
            content="子节点",
            confidence=75
        )
        self.assertTrue(success)
        
        # 验证父节点更新
        parent = self.nav.get_node("1")
        self.assertEqual(len(parent.child_nngs), 1)
        self.assertEqual(parent.child_nngs[0]["节点"], "1.1")
    
    def test_get_root(self):
        """测试获取根节点"""
        root = self.nav.get_root()
        self.assertIn("一级节点", root)
        self.assertIn("更新时间", root)
    
    def test_navigate(self):
        """测试导航"""
        # 创建节点链
        self.nav.create_node("1", "节点1", 80)
        self.nav.create_node("1.1", "节点1.1", 75)
        self.nav.create_node("1.1.1", "节点1.1.1", 70)
        
        # 测试GOTO
        new_loc, success = self.nav.navigate("1", "GOTO", "1.1")
        self.assertTrue(success)
        self.assertEqual(new_loc, "1.1")
        
        # 测试BACK
        new_loc, success = self.nav.navigate("1.1", "BACK")
        self.assertEqual(new_loc, "1")
        
        # 测试ROOT
        new_loc, success = self.nav.navigate("1.1.1", "ROOT")
        self.assertEqual(new_loc, "root")
        
        # 测试STAY
        new_loc, success = self.nav.navigate("1", "STAY")
        self.assertEqual(new_loc, "1")
    
    def test_add_memory_summary(self):
        """测试添加记忆摘要"""
        self.nav.create_node("1", "节点1", 80)
        
        success = self.nav.add_memory_summary(
            location="1",
            memory_id=123,
            summary="测试记忆",
            memory_type="分类记忆",
            value_level="高"
        )
        self.assertTrue(success)
        
        node = self.nav.get_node("1")
        self.assertEqual(len(node.memory_summaries), 1)
        self.assertEqual(node.memory_summaries[0]["记忆ID"], "123")
    
    def test_delete_node(self):
        """测试删除节点"""
        self.nav.create_node("1", "节点1", 80)
        
        success = self.nav.delete_node("1")
        self.assertTrue(success)
        
        node = self.nav.get_node("1")
        self.assertIsNone(node)
    
    def test_verify_integrity(self):
        """测试完整性验证"""
        # 创建正常结构
        self.nav.create_node("1", "节点1", 80)
        self.nav.create_node("1.1", "节点1.1", 75)
        
        integrity = self.nav.verify_integrity()
        
        self.assertIn("valid", integrity)
        self.assertIn("errors", integrity)
        self.assertIn("warnings", integrity)
        self.assertIn("stats", integrity)
    
    def test_get_children(self):
        """测试获取子节点"""
        self.nav.create_node("1", "节点1", 80)
        self.nav.create_node("1.1", "节点1.1", 75)
        self.nav.create_node("1.2", "节点1.2", 70)
        
        children = self.nav.get_children("1")
        self.assertEqual(len(children), 2)
        
        child_locs = [c["节点"] for c in children]
        self.assertIn("1.1", child_locs)
        self.assertIn("1.2", child_locs)
    
    def test_get_statistics(self):
        """测试统计功能"""
        self.nav.create_node("1", "节点1", 80)
        self.nav.create_node("1.1", "节点1.1", 75)
        self.nav.create_node("2", "节点2", 70)
        
        stats = self.nav.get_statistics()
        
        self.assertIn("total_nodes", stats)
        self.assertIn("max_depth", stats)
        self.assertIn("avg_confidence", stats)
        
        self.assertEqual(stats["total_nodes"], 3)
        self.assertEqual(stats["max_depth"], 2)


if __name__ == "__main__":
    unittest.main()
