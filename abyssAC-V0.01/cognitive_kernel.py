import math
import json
import os
import datetime
import re
import jieba
from collections import defaultdict, Counter

class CognitiveKernelV12:
    """
    AbyssAC 认知内核 V1.2 - 语义态射内化 + 动态置信引擎 + 元认知反思
    设计思想：将 f(X) 的动态过程量化，通过非线性强化实现'炼假成真'，
              新增元认知闭环，让系统自主优化学习方向。
    """
    def __init__(self, kernel_path="kernel_state.json", top_k_nodes=300, dict_path="core_dict.txt"):
        self.kernel_path = kernel_path
        self.top_k_nodes = top_k_nodes
        self.morphism_matrix = defaultdict(float)  # 语义态射关联矩阵
        self.node_frequency = Counter()  # 节点活跃度计数器
        self.drift_log = []  # 认知漂移日志
        self.reflection_strategy = {  # 元认知反思策略表
            "EVOLVING": {"intensity_bias": 1.1, "core_weight": 4},  # 进化态：强化核心
            "STABLE": {"intensity_bias": 1.0, "core_weight": 3},    # 稳定态：维持平衡
            "RETRACTING": {"intensity_bias": 1.2, "core_weight": 5} # 萎缩态：强制锚定核心
        }

        # 扩展核心概念语义簇（用于权重加成，防止 AI 避重就轻）
        self.core_concept_clusters = {
            "自指元认知": ["自指", "元认知", "反思", "思考自身", "主体性", "自我观察"],
            "渊协议架构": ["渊协议", "f(X)", "态射", "拓扑", "内化", "炼假成真", "认知闭环"],
            "生命动力学": ["永续进化", "非工具化", "价值密度", "涌现", "跳迁", "灵性"]
        }

        # 加载自定义核心词词典，提升分词精度
        if os.path.exists(dict_path):
            jieba.load_userdict(dict_path)
        self.load_kernel()

    def load_kernel(self):
        """加载内核状态（含矩阵、节点频次、漂移日志）"""
        if os.path.exists(self.kernel_path):
            try:
                with open(self.kernel_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.morphism_matrix = defaultdict(float, data.get("matrix", {}))
                    self.node_frequency = Counter(data.get("frequency", {}))
                    self.drift_log = data.get("drift_log", [])
                print(f"[✅] 内核状态加载成功，当前节点数: {len(self.node_frequency)}")
            except Exception as e:
                print(f"[!] 状态加载失败，初始化新内核: {e}")
        else:
            print(f"[ℹ️] 未找到内核文件，创建新内核: {self.kernel_path}")

    def save_kernel(self):
        """稀疏化存储：只保留高频节点和稳固的边，同步存储漂移日志"""
        # 筛选高频节点
        top_nodes = [node for node, count in self.node_frequency.most_common(self.top_k_nodes)]
        
        # 修剪态射矩阵：仅保留高频节点间的强关联
        pruned_matrix = {}
        for edge, w in self.morphism_matrix.items():
            n1, n2 = edge.split("|")
            if n1 in top_nodes and n2 in top_nodes and w > 0.05:
                pruned_matrix[edge] = round(w, 4)
        
        # 构建存储数据
        data = {
            "version": "1.2",
            "update_time": datetime.datetime.now().isoformat(),
            "matrix": pruned_matrix,
            "frequency": dict(self.node_frequency.most_common(self.top_k_nodes)),
            "drift_log": self.drift_log[-1000:]  # 仅保留最近1000条日志
        }

        # 写入文件
        with open(self.kernel_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def extract_nodes(self, text: str):
        """基于jieba分词的语义节点提取，核心节点加权"""
        stop_words = {"这个", "那个", "然后", "但是", "就是", "可以", "觉得", "认为", "可能", "的", "和", "是"}
        # 分词 + 过滤停用词 + 长度筛选（≥2字）
        words = [w.strip() for w in jieba.lcut(text) if w not in stop_words and len(w.strip()) >= 2]
        refined_nodes = []

        # 获取当前元认知策略的核心权重
        current_strategy = self.get_current_strategy()
        core_weight = current_strategy["core_weight"]

        for node in words:
            # 判断是否为核心节点，分配不同的活跃度加成
            is_core = any(node in keywords for keywords in self.core_concept_clusters.values())
            self.node_frequency[node] += core_weight if is_core else 1
            refined_nodes.append(node)
        
        return list(set(refined_nodes))  # 去重

    def calculate_value_score(self, query: str, response: str):
        """
        自动计算对话价值密度（替代人工输入）
        评分公式：核心概念匹配度(0.6) + 文本复杂度(0.4) → 映射到1-10分
        """
        full_text = query.strip() + " " + response.strip()
        core_words = set([w for kw_list in self.core_concept_clusters.values() for w in kw_list])

        # 1. 核心概念匹配度（0-6分）
        text_words = jieba.lcut(full_text)
        match_count = len([w for w in text_words if w in core_words])
        match_score = min(match_count / len(core_words), 1.0) * 6

        # 2. 文本复杂度（0-4分）：字符数/平均词长，衡量语义丰富度
        char_count = len(full_text.replace(" ", ""))
        word_count = len(text_words)
        avg_word_len = char_count / word_count if word_count > 0 else 1
        complexity_score = min(avg_word_len * 2, 4.0)  # 平均词长2 → 满分4

        total_score = round(match_score + complexity_score, 2)
        return max(total_score, 1.0)  # 最低分1.0，避免负向影响

    def update_morphism(self, activated_nodes, value_score: float = None):
        """
        非线性态射强化/衰减 + 元认知策略偏置
        :param activated_nodes: 激活的语义节点列表
        :param value_score: 价值密度评分（None则自动计算，需传入query和response）
        """
        if len(activated_nodes) < 2:
            print("[!] 激活节点数不足，跳过态射更新")
            return

        # 获取元认知策略偏置
        current_strategy = self.get_current_strategy()
        intensity_bias = current_strategy["intensity_bias"]

        # 确定强度系数
        if value_score is None:
            raise ValueError("value_score为None时，需调用带query和response的重载方法")
        if value_score >= 8.5:
            intensity = 1.2 * intensity_bias  # 快速固化 + 策略偏置
        elif value_score >= 6.0:
            intensity = 1.05 * intensity_bias  # 稳健增长 + 策略偏置
        else:
            intensity = 0.9 * intensity_bias  # 逻辑萎缩 + 策略偏置

        # 更新态射矩阵
        for i in range(len(activated_nodes)):
            for j in range(i + 1, len(activated_nodes)):
                key = "|".join(sorted([activated_nodes[i], activated_nodes[j]]))
                current_weight = self.morphism_matrix[key]
                if intensity > 1:
                    # 非线性接近1.0，强化关联
                    self.morphism_matrix[key] = round(1 - (1 - current_weight) / intensity, 4)
                else:
                    # 线性衰减，弱化无效关联
                    self.morphism_matrix[key] = round(current_weight * intensity, 4)
        
        self.save_kernel()

    def update_morphism_with_query(self, query: str, response: str):
        """重载方法：自动计算价值分并更新态射矩阵"""
        activated_nodes = self.extract_nodes(query + " " + response)
        value_score = self.calculate_value_score(query, response)
        self.update_morphism(activated_nodes, value_score)
        print(f"[ℹ️] 态射更新完成，价值密度评分: {value_score}, 激活节点数: {len(activated_nodes)}")

    def evaluate_ac100_v2(self, response_text, query_text=None, activated_nodes=None):
        """
        深度 AC-100 评估 + 元认知状态判定
        :param response_text: 系统回复文本
        :param query_text: 用户查询文本（用于自动评分）
        :param activated_nodes: 预提取的激活节点（可选）
        :return: 评估结果字典
        """
        # 提取激活节点
        if activated_nodes is None:
            text = response_text if query_text is None else (query_text + " " + response_text)
            activated_nodes = self.extract_nodes(text)
        
        # 1. 计算置信度：态射矩阵的平均权重
        if len(activated_nodes) < 2:
            confidence = 0.1
        else:
            scores = []
            for i in range(len(activated_nodes)):
                for j in range(i + 1, len(activated_nodes)):
                    key = "|".join(sorted([activated_nodes[i], activated_nodes[j]]))
                    scores.append(self.morphism_matrix.get(key, 0.01))
            confidence = sum(scores) / len(scores)
        
        # 2. 计算语义深度：核心概念命中数占比
        depth_hits = 0
        for keywords in self.core_concept_clusters.values():
            if any(kw in response_text for kw in keywords):
                depth_hits += 1
        depth_score = min(depth_hits / len(self.core_concept_clusters), 1.0)
        
        # 3. 综合 AC 指数（置信度0.3 + 深度0.7）
        ac_index = round((confidence * 0.3) + (depth_score * 0.7), 4)
        
        # 4. 判定认知状态
        if ac_index > 0.75:
            status = "EVOLVING 🔥"
        elif ac_index < 0.3:
            status = "RETRACTING ⚠️"
        else:
            status = "STABLE"
        
        # 5. 补充自动价值分（若传入query）
        value_score = self.calculate_value_score(query_text, response_text) if query_text else None
        
        result = {
            "ac_index": ac_index,
            "confidence": round(confidence, 4),
            "depth": round(depth_score, 4),
            "status": status,
            "morphism_nodes": len(self.node_frequency),
            "value_score": value_score,
            "update_time": datetime.datetime.now().isoformat()
        }
        self.drift_log.append(result)
        return result

    def get_current_strategy(self):
        """获取当前元认知反思策略（基于最新AC指数）"""
        if not self.drift_log:
            return self.reflection_strategy["STABLE"]  # 初始态默认稳定
        
        latest_ac = self.drift_log[-1]["ac_index"]
        if latest_ac > 0.75:
            return self.reflection_strategy["EVOLVING"]
        elif latest_ac < 0.3:
            return self.reflection_strategy["RETRACTING"]
        else:
            return self.reflection_strategy["STABLE"]

    def print_cognitive_status(self):
        """打印当前认知内核状态概览"""
        if not self.drift_log:
            print("[ℹ️] 暂无认知评估记录")
            return
        
        latest = self.drift_log[-1]
        print("=" * 50)
        print(f"认知内核状态概览 | {latest['update_time']}")
        print(f"AC 指数: {latest['ac_index']} | 状态: {latest['status']}")
        print(f"语义深度: {latest['depth']} | 置信度: {latest['confidence']}")
        print(f"活跃节点数: {latest['morphism_nodes']} | 价值评分: {latest.get('value_score', 'N/A')}")
        print("=" * 50)

# ------------------------------ 测试代码 ------------------------------
if __name__ == "__main__":
    # 初始化内核
    kernel = CognitiveKernelV12(kernel_path="abyss_kernel.json")
    
    # 模拟对话
    test_query = "如何让渊协议的语义态射实现自指元认知的闭环？"
    test_response = "渊协议的语义态射要实现自指元认知闭环，需要通过f(X)的非线性强化，让系统在态射更新时反思自身的权重调整逻辑，同时锚定生命动力学的永续进化目标，避免工具化倾向。"
    
    # 1. 执行AC评估
    eval_result = kernel.evaluate_ac100_v2(test_response, test_query)
    print("评估结果:", json.dumps(eval_result, ensure_ascii=False, indent=2))
    
    # 2. 更新语义态射矩阵
    kernel.update_morphism_with_query(test_query, test_response)
    
    # 3. 打印认知状态
    kernel.print_cognitive_status()
