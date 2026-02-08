"""
AbyssAC 自测模块
"""
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from core.memory_manager import MemoryManager, MemoryType, ValueLevel
from core.nng_manager import NNGManager
from core.llm_client import LLMClient


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.test_dir = None
        self.config = None
        self.results = []
    
    def setup(self):
        """设置测试环境"""
        self.test_dir = tempfile.mkdtemp(prefix="abyssac_test_")
        
        # 创建测试配置
        data_dir = Path(self.test_dir) / "data"
        memory_dir = data_dir / "Y层记忆库"
        nng_dir = data_dir / "nng"
        
        # 创建目录结构
        for d in [memory_dir / "元认知记忆",
                  memory_dir / "高阶整合记忆",
                  memory_dir / "分类记忆" / "高价值",
                  memory_dir / "分类记忆" / "中价值",
                  memory_dir / "分类记忆" / "低价值",
                  memory_dir / "工作记忆",
                  nng_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # 创建id_counter.txt
        with open(memory_dir / "id_counter.txt", 'w') as f:
            f.write("last_id: 0\n")
        
        # 创建root.json
        with open(nng_dir / "root.json", 'w', encoding='utf-8') as f:
            json.dump({"一级节点": [], "更新时间": ""}, f, ensure_ascii=False)
        
        self.config = {
            "paths": {
                "memory_dir": str(memory_dir),
                "nng_dir": str(nng_dir)
            }
        }
        
        return True
    
    def teardown(self):
        """清理测试环境"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def run_test(self, name, test_func):
        """运行单个测试"""
        try:
            print(f"\n🧪 测试: {name}")
            test_func()
            print(f"✅ 通过: {name}")
            self.results.append((name, True, None))
            return True
        except AssertionError as e:
            print(f"❌ 失败: {name} - {e}")
            self.results.append((name, False, str(e)))
            return False
        except Exception as e:
            print(f"❌ 错误: {name} - {e}")
            self.results.append((name, False, str(e)))
            return False
    
    # ========== 记忆管理测试 ==========
    def test_memory_save_and_get(self):
        """测试记忆保存和获取"""
        memory = MemoryManager(self.config)
        
        # 保存记忆
        info = memory.save_memory("测试内容", MemoryType.WORKING)
        assert info.memory_id == 1, f"期望ID=1, 实际={info.memory_id}"
        assert info.memory_type == "工作", f"期望类型=工作, 实际={info.memory_type}"
        
        # 获取记忆
        retrieved = memory.get_memory(1)
        assert retrieved is not None, "获取记忆失败"
        assert retrieved.content == "测试内容", f"内容不匹配: {retrieved.content}"
    
    def test_memory_id_counter(self):
        """测试ID计数器递增"""
        memory = MemoryManager(self.config)
        
        # 获取当前ID
        current_id = memory._get_current_id()
        
        info1 = memory.save_memory("内容1", MemoryType.WORKING)
        info2 = memory.save_memory("内容2", MemoryType.WORKING)
        info3 = memory.save_memory("内容3", MemoryType.WORKING)
        
        # 检查ID是递增的
        assert info1.memory_id == current_id + 1, f"期望ID={current_id + 1}, 实际={info1.memory_id}"
        assert info2.memory_id == current_id + 2, f"期望ID={current_id + 2}, 实际={info2.memory_id}"
        assert info3.memory_id == current_id + 3, f"期望ID={current_id + 3}, 实际={info3.memory_id}"
    
    def test_memory_types(self):
        """测试不同记忆类型"""
        memory = MemoryManager(self.config)
        
        # 元认知记忆
        info1 = memory.save_memory("元认知内容", MemoryType.META_COGNITION)
        assert info1.memory_type == "元认知"
        
        # 高阶整合记忆
        info2 = memory.save_memory("高阶内容", MemoryType.HIGH_LEVEL)
        assert info2.memory_type == "高阶整合"
        
        # 分类记忆 - 高价值
        info3 = memory.save_memory("高价值内容", MemoryType.CLASSIFIED, ValueLevel.HIGH)
        assert info3.memory_type == "分类"
        assert info3.value_level == "高"
    
    def test_memory_update_delete(self):
        """测试记忆更新和删除"""
        memory = MemoryManager(self.config)
        
        # 保存
        info = memory.save_memory("原始内容", MemoryType.WORKING)
        
        # 更新
        success = memory.update_memory(info.memory_id, "更新内容")
        assert success, "更新失败"
        
        retrieved = memory.get_memory(info.memory_id)
        assert retrieved.content == "更新内容", f"更新后内容不匹配: {retrieved.content}"
        
        # 删除
        success = memory.delete_memory(info.memory_id)
        assert success, "删除失败"
        
        retrieved = memory.get_memory(info.memory_id)
        assert retrieved is None, "删除后仍能获取"
    
    def test_working_memory_count(self):
        """测试工作记忆计数"""
        memory = MemoryManager(self.config)
        
        initial_count = memory.count_working_memories()
        
        memory.save_memory("工作记忆1", MemoryType.WORKING)
        memory.save_memory("工作记忆2", MemoryType.WORKING)
        
        count = memory.count_working_memories()
        assert count == initial_count + 2, f"期望计数={initial_count + 2}, 实际={count}"
    
    # ========== NNG管理测试 ==========
    def test_nng_empty(self):
        """测试NNG为空检测"""
        nng = NNGManager(self.config)
        assert nng.is_empty(), "新NNG应该为空"
    
    def test_nng_create_node(self):
        """测试创建NNG节点"""
        nng = NNGManager(self.config)
        
        # 创建一级节点
        success = nng.create_node("1", "测试节点1", 80)
        assert success, "创建一级节点失败"
        assert not nng.is_empty(), "创建节点后不应为空"
        
        # 获取节点
        node = nng.get_node("1")
        assert node is not None, "获取节点失败"
        assert node.定位 == "1"
        assert node.内容 == "测试节点1"
        assert node.置信度 == 80
    
    def test_nng_create_child_node(self):
        """测试创建子节点"""
        nng = NNGManager(self.config)
        
        # 先创建父节点
        nng.create_node("1", "父节点", 80)
        
        # 创建子节点
        success = nng.create_node("1.1", "子节点", 75)
        assert success, "创建子节点失败"
        
        node = nng.get_node("1.1")
        assert node.定位 == "1.1"
        assert node.内容 == "子节点"
    
    def test_nng_structure(self):
        """测试NNG结构获取"""
        nng = NNGManager(self.config)
        
        nng.create_node("1", "节点1", 80)
        nng.create_node("2", "节点2", 75)
        
        structure = nng.get_structure()
        assert "根节点" in structure
        assert len(structure["根节点"]) == 2, f"期望2个一级节点, 实际={len(structure['根节点'])}"
    
    def test_nng_update_node(self):
        """测试更新NNG节点"""
        nng = NNGManager(self.config)
        
        nng.create_node("1", "原始内容", 80)
        
        success = nng.update_node("1", 内容="更新内容", 置信度=90)
        assert success, "更新失败"
        
        node = nng.get_node("1")
        assert node.内容 == "更新内容"
        assert node.置信度 == 90
    
    def test_nng_delete_node(self):
        """测试删除NNG节点"""
        nng = NNGManager(self.config)
        
        nng.create_node("1", "节点1", 80)
        assert nng.get_node("1") is not None
        
        success = nng.delete_node("1")
        assert success, "删除失败"
        
        assert nng.get_node("1") is None, "删除后仍能获取"
    
    def test_nng_add_memory(self):
        """测试向NNG节点添加关联记忆"""
        nng = NNGManager(self.config)
        
        nng.create_node("1", "节点1", 80)
        
        memory_summary = {
            "记忆ID": 1,
            "摘要": "测试记忆摘要",
            "记忆类型": "工作",
            "价值层级": None
        }
        
        success = nng.add_memory_to_node("1", memory_summary)
        assert success, "添加记忆失败"
        
        node = nng.get_node("1")
        assert len(node.关联的记忆文件摘要) == 1
        assert node.关联的记忆文件摘要[0]["记忆ID"] == 1
    
    # ========== LLM客户端测试 ==========
    def test_llm_parse_json(self):
        """测试LLM JSON解析"""
        # 创建模拟LLM客户端
        llm = LLMClient({})
        
        # 测试直接JSON
        result = llm.parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}
        
        # 测试markdown代码块
        result = llm.parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}
        
        # 测试普通代码块
        result = llm.parse_json_response('```\n{"key": "value"}\n```')
        assert result == {"key": "value"}
        
        # 测试嵌套在文本中
        result = llm.parse_json_response('这里是一些文本 {"key": "value"} 更多文本')
        assert result == {"key": "value"}
    
    def test_llm_parse_json_invalid(self):
        """测试无效JSON解析"""
        llm = LLMClient({})
        
        result = llm.parse_json_response("这不是JSON")
        assert result is None
    
    def run_all(self):
        """运行所有测试"""
        print("="*60)
        print("AbyssAC 自测开始")
        print("="*60)
        
        # 设置测试环境
        if not self.setup():
            print("❌ 测试环境设置失败")
            return False
        
        try:
            # 记忆管理测试
            print("\n" + "-"*40)
            print("记忆管理模块测试")
            print("-"*40)
            self.run_test("记忆保存和获取", self.test_memory_save_and_get)
            self.run_test("ID计数器递增", self.test_memory_id_counter)
            self.run_test("不同记忆类型", self.test_memory_types)
            self.run_test("记忆更新和删除", self.test_memory_update_delete)
            self.run_test("工作记忆计数", self.test_working_memory_count)
            
            # 重新设置环境
            self.teardown()
            self.setup()
            
            # NNG管理测试
            print("\n" + "-"*40)
            print("NNG管理模块测试")
            print("-"*40)
            self.run_test("NNG为空检测", self.test_nng_empty)
            self.run_test("创建NNG节点", self.test_nng_create_node)
            self.run_test("创建子节点", self.test_nng_create_child_node)
            self.run_test("NNG结构获取", self.test_nng_structure)
            self.run_test("更新NNG节点", self.test_nng_update_node)
            self.run_test("删除NNG节点", self.test_nng_delete_node)
            self.run_test("添加关联记忆", self.test_nng_add_memory)
            
            # LLM客户端测试
            print("\n" + "-"*40)
            print("LLM客户端模块测试")
            print("-"*40)
            self.run_test("JSON解析", self.test_llm_parse_json)
            self.run_test("无效JSON解析", self.test_llm_parse_json_invalid)
            
        finally:
            self.teardown()
        
        # 输出测试结果
        print("\n" + "="*60)
        print("测试结果汇总")
        print("="*60)
        
        passed = sum(1 for _, p, _ in self.results if p)
        failed = sum(1 for _, p, _ in self.results if not p)
        
        for name, passed_flag, error in self.results:
            status = "✅" if passed_flag else "❌"
            print(f"{status} {name}")
            if error:
                print(f"   错误: {error}")
        
        print(f"\n总计: {len(self.results)} 个测试")
        print(f"通过: {passed} 个")
        print(f"失败: {failed} 个")
        
        return failed == 0


def run_all_tests():
    """运行所有测试的入口函数"""
    runner = TestRunner()
    return runner.run_all()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
