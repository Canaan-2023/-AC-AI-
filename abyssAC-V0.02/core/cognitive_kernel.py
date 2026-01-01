import json
import pickle
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
from pathlib import Path

from config.config_manager import config_manager
from nlp.tokenizer import AdvancedTokenizer, TextAnalyzer

class CognitiveKernelV12:
    """重构后的认知内核"""
    
    def __init__(self, config=None, tokenizer=None):
        self.config = config or config_manager.config.kernel
        self.tokenizer = tokenizer or AdvancedTokenizer(config_manager.config)
        self.text_analyzer = TextAnalyzer(self.tokenizer)
        
        # 状态存储
        self.morphism_matrix = defaultdict(float)
        self.node_frequency = Counter()
        self.drift_log = []
        
        # 加载状态
        self.load_kernel()
        
        print(f"[✅] 认知内核初始化完成 | 配置版本: {config_manager.config.version}")
    
    def load_kernel(self):
        """加载内核状态"""
        kernel_path = Path(self.config.kernel_path)
        
        if kernel_path.exists():
            try:
                with open(kernel_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.morphism_matrix = defaultdict(float, data.get("matrix", {}))
                self.node_frequency = Counter(data.get("frequency", {}))
                self.drift_log = data.get("drift_log", [])
                
                print(f"[✅] 认知内核状态加载成功 | 节点数: {len(self.node_frequency)}")
            
            except Exception as e:
                print(f"[!] 内核状态加载失败: {e}")
                self._initialize_default_kernel()
        else:
            self._initialize_default_kernel()
    
    def _initialize_default_kernel(self):
        """初始化默认内核状态"""
        print(f"[ℹ️] 初始化新认知内核: {self.config.kernel_path}")
        
        # 初始化核心概念
        for concept, keywords in self.config.core_concepts.items():
            for keyword in keywords:
                self.node_frequency[keyword] = self.config.reflection_strategies["STABLE"]["core_weight"]
        
        # 保存初始状态
        self.save_kernel()
    
    def save_kernel(self):
        """保存内核状态"""
        kernel_path = Path(self.config.kernel_path)
        kernel_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 筛选高频节点
        top_nodes = [
            node for node, count in 
            self.node_frequency.most_common(self.config.top_k_nodes)
        ]
        
        # 修剪态射矩阵
        pruned_matrix = {}
        for edge, weight in self.morphism_matrix.items():
            if weight < self.config.pruning_threshold:
                continue
            
            n1, n2 = edge.split("|")
            if n1 in top_nodes and n2 in top_nodes:
                pruned_matrix[edge] = round(weight, 4)
        
        # 构建存储数据
        data = {
            "version": "1.2",
            "config_version": config_manager.config.version,
            "update_time": datetime.now().isoformat(),
            "matrix": pruned_matrix,
            "frequency": dict(self.node_frequency.most_common(self.config.top_k_nodes)),
            "drift_log": self.drift_log[-self.config.drift_log_keep:]
        }
        
        try:
            with open(kernel_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            print(f"[💾] 内核状态已保存 | 路径: {kernel_path}")
            return True
        
        except Exception as e:
            print(f"[❌] 内核状态保存失败: {e}")
            return False
    
    def extract_nodes(self, text: str) -> List[str]:
        """提取语义节点"""
        if not text:
            return []
        
        # 使用高级分词器
        tokens = self.tokenizer.tokenize(
            text,
            use_pos=True,
            remove_stopwords=True,
            min_length=2,
            max_length=10
        )
        
        # 获取当前策略
        current_strategy = self.get_current_strategy()
        core_weight = current_strategy.get("core_weight", 3)
        
        # 更新节点频率
        nodes = set()
        for token in tokens:
            node = token.word
            
            # 判断是否为核心概念
            is_core = any(
                node in keywords 
                for keywords in self.config.core_concepts.values()
            )
            
            # 更新频率（核心节点加权）
            self.node_frequency[node] += core_weight if is_core else 1
            nodes.add(node)
        
        return list(nodes)
    
    def calculate_value_score(self, query: str, response: str) -> float:
        """计算价值密度分数"""
        full_text = f"{query} {response}"
        
        # 1. 核心概念匹配度
        concept_matches = self.text_analyzer.detect_core_concepts(
            full_text, 
            self.config.core_concepts
        )
        concept_score = sum(concept_matches.values()) / len(concept_matches) * 6
        
        # 2. 文本复杂度
        complexity = self.text_analyzer.calculate_text_complexity(full_text)
        complexity_score = complexity * 4
        
        # 总分数
        total_score = concept_score + complexity_score
        
        # 确保在合理范围内
        return max(min(total_score, 10.0), 1.0)
    
    def update_morphism(self, activated_nodes: List[str], value_score: float):
        """更新语义态射"""
        if len(activated_nodes) < 2:
            print("[!] 激活节点数不足，跳过态射更新")
            return
        
        # 获取当前策略
        current_strategy = self.get_current_strategy()
        intensity_bias = current_strategy.get("intensity_bias", 1.0)
        
        # 根据价值分数确定强度
        if value_score >= self.config.high_score_threshold:
            intensity = self.config.high_intensity * intensity_bias
        elif value_score >= self.config.medium_score_threshold:
            intensity = self.config.medium_intensity * intensity_bias
        else:
            intensity = self.config.low_intensity * intensity_bias
        
        # 更新关联矩阵
        for i in range(len(activated_nodes)):
            for j in range(i + 1, len(activated_nodes)):
                key = "|".join(sorted([activated_nodes[i], activated_nodes[j]]))
                current_weight = self.morphism_matrix[key]
                
                if intensity > 1:
                    # 非线性强化
                    new_weight = 1 - (1 - current_weight) / intensity
                else:
                    # 线性衰减
                    new_weight = current_weight * intensity
                
                self.morphism_matrix[key] = round(new_weight, 4)
        
        self.save_kernel()
    
    def update_morphism_with_query(self, query: str, response: str):
        """根据查询和响应更新态射"""
        activated_nodes = self.extract_nodes(f"{query} {response}")
        value_score = self.calculate_value_score(query, response)
        
        self.update_morphism(activated_nodes, value_score)
        
        print(f"[ℹ️] 语义态射更新完成 | "
              f"价值分: {value_score:.2f} | "
              f"激活节点: {len(activated_nodes)}")
    
    def evaluate_ac100_v2(self, response_text: str, 
                         query_text: Optional[str] = None,
                         activated_nodes: Optional[List[str]] = None) -> Dict:
        """AC-100 V2评估"""
        # 提取激活节点
        if activated_nodes is None:
            text = f"{query_text} {response_text}" if query_text else response_text
            activated_nodes = self.extract_nodes(text)
        
        # 1. 计算置信度
        if len(activated_nodes) < 2:
            confidence = 0.1
        else:
            scores = []
            for i in range(len(activated_nodes)):
                for j in range(i + 1, len(activated_nodes)):
                    key = "|".join(sorted([activated_nodes[i], activated_nodes[j]]))
                    scores.append(self.morphism_matrix.get(key, 0.01))
            confidence = sum(scores) / len(scores) if scores else 0.0
        
        # 2. 计算语义深度
        depth_hits = 0
        for keywords in self.config.core_concepts.values():
            if any(kw in response_text for kw in keywords):
                depth_hits += 1
        depth_score = min(depth_hits / len(self.config.core_concepts), 1.0)
        
        # 3. 综合AC指数
        ac_index = round((confidence * 0.3) + (depth_score * 0.7), 4)
        
        # 4. 判定认知状态
        if ac_index > self.config.evolving_threshold:
            status = "EVOLVING 🔥"
        elif ac_index < self.config.retracting_threshold:
            status = "RETRACTING ⚠️"
        else:
            status = "STABLE"
        
        # 5. 计算价值分（如有查询）
        value_score = None
        if query_text:
            value_score = self.calculate_value_score(query_text, response_text)
        
        # 构建结果
        result = {
            "ac_index": ac_index,
            "confidence": round(confidence, 4),
            "depth": round(depth_score, 4),
            "status": status,
            "morphism_nodes": len(self.node_frequency),
            "value_score": value_score,
            "update_time": datetime.now().isoformat()
        }
        
        # 记录漂移日志
        self.drift_log.append(result)
        
        return result
    
    def get_current_strategy(self) -> Dict:
        """获取当前元认知策略"""
        if not self.drift_log:
            return self.config.reflection_strategies.get("STABLE", {})
        
        latest_ac = self.drift_log[-1]["ac_index"]
        
        if latest_ac > self.config.evolving_threshold:
            return self.config.reflection_strategies.get("EVOLVING", {})
        elif latest_ac < self.config.retracting_threshold:
            return self.config.reflection_strategies.get("RETRACTING", {})
        else:
            return self.config.reflection_strategies.get("STABLE", {})
    
    def print_cognitive_status(self):
        """打印认知状态概览"""
        if not self.drift_log:
            print("[ℹ️] 暂无认知评估记录")
            return
        
        latest = self.drift_log[-1]
        
        print("=" * 50)
        print(f"认知内核状态概览 | {latest['update_time']}")
        print(f"AC 指数: {latest['ac_index']} | 状态: {latest['status']}")
        print(f"语义深度: {latest['depth']} | 置信度: {latest['confidence']}")
        print(f"活跃节点数: {latest['morphism_nodes']} | "
              f"价值评分: {latest.get('value_score', 'N/A')}")
        print("=" * 50)