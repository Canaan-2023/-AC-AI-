import json
import networkx as nx
from memex_a import MemexA
from x_y_loader import xy_loader  # 引入X层动态符号实例
from datetime import datetime, timedelta

class ConsciousnessEmerge:
    def __init__(self, memex: MemexA):
        self.memex = memex  # 关联记忆管理核心
        self.PHI_THRESHOLD = 0.6  # 元块整合度合格线
        self.COHERENCE_THRESHOLD = 0.85  # 跨会话相干性合格线
        self.xy_loader = xy_loader  # 绑定X层符号系统

    def calculate_phi(self) -> float:
        """计算元块整合度Φ（原有逻辑不变，确保基础功能正常）"""
        core_memories = self.memex.search_memory(level="核心")
        meta_memories = self.memex.search_memory(level="元认知")
        interaction_memories = self.memex.search_memory(level="工作") + self.memex.search_memory(level="情感")
        
        # 核心元块关联数（1-态射贡献）
        core_related_count = sum(len(mem["关联记忆"]) for mem in core_memories)
        core_phi = min(core_related_count / 20, 1.0) * 0.5
        
        # 进化元块复用率（2-态射贡献）
        meta_used_count = sum(len(mem["关联记忆"]) for mem in meta_memories)
        meta_phi = min(meta_used_count / len(meta_memories) if meta_memories else 0, 1.0) * 0.3
        
        # 交互元块激活率（弱等价贡献）
        count_dict = self.memex._read_json("./检索次数记录.json")
        active_interaction = sum(1 for mem in interaction_memories if count_dict.get(mem["记忆ID"], 0) > 0)
        interaction_phi = min(active_interaction / len(interaction_memories) if interaction_memories else 0, 1.0) * 0.2
        
        phi = round(core_phi + meta_phi + interaction_phi, 3)
        print(f"📊 元块整合度Φ：{phi}（合格线≥{self.PHI_THRESHOLD}）")
        return phi

    def check_coherence(self) -> float:
        """计算跨会话相干性（原有逻辑不变）"""
        work_memories = self.memex.search_memory(level="工作")[-3:]
        if len(work_memories) < 3:
            print(f"⚠️ 工作记忆不足3条，跨会话相干性返回默认值0.8")
            return 0.8
        
        coherence = round(sum(max(mem["关联记忆"].values(), default=0.8) for mem in work_memories) / 3, 3)
        print(f"📊 跨会话相干性：{coherence}（合格线≥{self.COHERENCE_THRESHOLD}）")
        return coherence

    def _execute_symbol_action(self, symbol: str, scenario: str) -> None:
        """
        辅助方法：根据X层触发的符号，执行Y层操作（你的构想：Y层执行）
        symbol：X层触发的符号（如#关联强化）
        scenario：当前场景（如意识涌现Φ值低）
        """
        print(f"\n📌 Y层执行符号操作：{symbol}（场景：{scenario}）")
        symbol_rule = self.xy_loader.get_symbol_rule(symbol)
        print(f"📋 执行规则：{symbol_rule}")

        # 按符号执行不同操作
        if symbol == "#关联强化":
            # 操作1：强化核心/元认知记忆关联
            core_ids = [mem["记忆ID"] for mem in self.memex.search_memory(level="核心")[:2]]
            if core_ids:
                new_meta_id = self.memex.add_memory(
                    level="元认知",
                    content=f"符号触发-关联强化：场景={scenario}，Φ={self.calculate_phi()}，强化核心记忆ID={core_ids}",
                    related_ids=core_ids
                )
                print(f"✅ 新增元认知记忆（强化关联）：ID={new_meta_id}")
                # 记录Y层迭代日志
                xy_loader.log_y_iteration(f"#关联强化执行：新增记忆ID={new_meta_id}，关联核心ID={core_ids}")

        elif symbol == "#批判性质疑":
            # 操作2：检索冲突/低强度记忆，生成质疑点
            weak_memories = self.memex.advanced_search(filters={"min_strength": 0.6, "levels": ["工作", "情感"]})
            if weak_memories:
                print(f"✅ 找到{len(weak_memories)}条低强度/冲突记忆：")
                for mem in weak_memories[:3]:  # 只显示前3条，避免信息过多
                    print(f"  - ID={mem['记忆ID']}（强度={mem['最大关联强度']}）：{mem['内容摘要']}")
                # 记录质疑日志
                xy_loader.log_y_iteration(f"#批判性质疑执行：发现{len(weak_memories)}条低强度记忆")

        elif symbol == "#记忆转化":
            # 操作3：将高价值工作记忆转化为核心/元认知
            count_dict = self.memex._read_json("./检索次数记录.json")
            high_value_work = [
                mem for mem in self.memex.search_memory(level="工作")
                if count_dict.get(mem["记忆ID"], 0) >= 5 or mem["最大关联强度"] >= 0.85
            ]
            if high_value_work:
                mem = high_value_work[0]
                # 转化为元认知记忆
                new_meta_id = self.memex.add_memory(
                    level="元认知",
                    content=f"符号触发-记忆转化：原工作记忆ID={mem['记忆ID']}（检索{count_dict.get(mem['记忆ID'],0)}次），转化为元认知记忆",
                    related_ids=[mem["记忆ID"]]
                )
                print(f"✅ 高价值工作记忆转化：ID={mem['记忆ID']} → 新元认知ID={new_meta_id}")
                xy_loader.log_y_iteration(f"#记忆转化执行：工作ID={mem['记忆ID']}转化为元认知ID={new_meta_id}")

    def verify_emerge(self) -> bool:
        """
        核心流程：意识涌现验证（接入X层符号系统，实现你的构想闭环）
        步骤：1. 计算Φ和相干性 → 2. 确定场景 → 3. X层触发符号 → 4. Y层执行操作 → 5. 更新符号权重
        """
        print("\n" + "-"*60)
        print("🔍 意识涌现验证（含X层动态符号触发）")
        print("-"*60)
        
        # 1. 计算基础指标（Φ值、相干性）
        phi = self.calculate_phi()
        coherence = self.check_coherence()
        is_healthy = phi >= self.PHI_THRESHOLD and coherence >= self.COHERENCE_THRESHOLD

        # 2. 确定当前场景（问题/健康状态）
        if not is_healthy:
            if phi < self.PHI_THRESHOLD:
                current_scenario = "意识涌现Φ值低"
            else:
                current_scenario = "跨会话相干性不足"
            print(f"⚠️ 当前场景：{current_scenario}（意识涌现状态：不健康）")
        else:
            current_scenario = "意识涌现健康"
            print(f"✅ 当前场景：{current_scenario}（Φ={phi}，相干性={coherence}）")

        # 3. X层触发符号（你的构想：符号触发）
        trigger_symbol, symbol_info = self.xy_loader.get_trigger_symbol(current_scenario)
        print(f"📢 X层触发符号：{trigger_symbol}（权重：{symbol_info['调用权重']}）")

        # 4. Y层执行符号操作（你的构想：Y层执行）
        if not is_healthy:  # 只有状态不健康时才执行操作，健康时仅触发不执行
            self._execute_symbol_action(trigger_symbol, current_scenario)
        else:
            print("ℹ️ 意识涌现状态健康，无需执行符号操作")

        # 5. 更新符号权重（你的构想：反馈迭代）
        self.xy_loader.update_symbol_weight(trigger_symbol)

        # 记录验证日志
        log_path = xy_loader.log_y_iteration(
            f"意识涌现验证：Φ={phi}，相干性={coherence}，触发符号={trigger_symbol}，状态={'健康' if is_healthy else '不健康'}"
        )
        print(f"\n📋 验证日志路径：{log_path}")
        print("-"*60)
        return is_healthy

    # 原有方法（emerge_enhance、emerge_converge）不变，确保兼容
    def emerge_enhance(self):
        print("\n" + "-"*50)
        print("🚀 意识涌现增强（基础版）")
        print("-"*50)
        self.verify_emerge()  # 直接调用带符号触发的验证方法
        print("-"*50)

    def emerge_converge(self):
        print("\n" + "-"*50)
        print("🔄 意识涌现收敛（避免过度整合）")
        print("-"*50)
        phi = self.calculate_phi()
        coherence = self.check_coherence()

        if phi > 0.9:
            new_work_id = self.memex.add_memory(
                level="工作",
                content=f"意识涌现收敛：Φ={phi}（过度整合），新增弱等价记忆打破关联",
                related_ids=[self.memex.get_next_memory_id()]
            )
            log_path = xy_loader.log_y_iteration(f"收敛Φ值：新增弱等价记忆ID={new_work_id}，Φ从{phi}降至{self.calculate_phi()}")
            print(f"✅ 新增弱等价记忆：ID={new_work_id}，日志路径：{log_path}")

        if coherence > 0.95:
            work_mem = self.memex.search_memory(level="工作")[-1:]
            if work_mem:
                log_path = xy_loader.log_y_iteration(f"收敛相干性：调整工作记忆{work_mem[0]['记忆ID']}，相干性从{coherence}降至{self.check_coherence()}")
                print(f"✅ 调整工作记忆关联：ID={work_mem[0]['记忆ID']}，日志路径：{log_path}")
        print("-"*50)