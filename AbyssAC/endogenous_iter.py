from memex_a import MemexA
from x_y_loader import xy_loader

class EndogenousIteration:
    def __init__(self, memex: MemexA):
        self.memex = memex
        self.ITER_TRIGGER_SCORE = 80  # AC-100触发迭代阈值

    def check_iter_condition(self) -> bool:
        """检查迭代触发条件：AC-100≥80分"""
        ac100_score = self.memex.ac100_evaluation()
        is_trigger = ac100_score >= self.ITER_TRIGGER_SCORE
        print(f"🔍 内生迭代条件检查：AC-100={ac100_score}分，{'满足' if is_trigger else '不满足'}触发条件（≥{self.ITER_TRIGGER_SCORE}分）")
        return is_trigger

    def run_iteration(self):
        """执行内生迭代：优化元认知规则，新增迭代记忆"""
        if not self.check_iter_condition():
            print("❌ 未满足内生迭代条件，不执行迭代")
            return
        
        # 1. 检索待优化的元认知记忆
        meta_memories = self.memex.search_memory("规则", level="元认知")
        if not meta_memories:
            print("⚠️ 无待优化的元认知记忆，创建初始迭代记忆")
            meta_ids = [self.memex.get_next_memory_id()]
        else:
            meta_ids = [mem["记忆ID"] for mem in meta_memories[:2]]  # 取前2个待优化记忆
        
        # 2. 新增优化后的元认知记忆
        new_meta_id = self.memex.add_memory(
            level="元认知",
            content=f"内生迭代：优化元认知规则，基于AC-100={self.memex.ac100_evaluation()}分",
            related_ids=meta_ids
        )
        
        # 3. 记录迭代日志
        log_path = xy_loader.log_y_iteration(f"内生迭代执行完成：新增优化记忆ID={new_meta_id}，关联待优化ID={meta_ids}")
        
        # 4. 触发Memex-A关联强度更新
        self.memex.update_strength()
        
        print(f"✅ 内生迭代完成！")
        print(f"  - 新增优化记忆ID：{new_meta_id}")
        print(f"  - 迭代日志路径：{log_path}")
        print(f"  - 迭代后AC-100：{self.memex.ac100_evaluation()}分")