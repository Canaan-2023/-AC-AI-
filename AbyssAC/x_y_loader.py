import json
import os
from datetime import datetime, date

class XYLoader:
    def __init__(self):
        # X层配置路径（固定，和原有一致）
        self.X_CONFIG_PATH = "./config/X_core.json"
        # Y层目录配置（原有不变，确保路径存在）
        self.Y_ROOT = "./Y_OCR库/"
        self.Y_DIRS = [
            self.Y_ROOT + "核心记忆/",
            self.Y_ROOT + "元认知记忆/",
            self.Y_ROOT + "工作记忆/",
            self.Y_ROOT + "情感记忆/",
            self.Y_ROOT + "迭代日志/"
        ]
        # 初始化X/Y层：加载动态符号系统+创建Y层目录
        self.x_config = self._load_x_config()
        self._init_y_dirs()
        # 每月重置符号权重（按调度逻辑）
        self._reset_weight_monthly()

    def _load_x_config(self) -> dict:
        """加载X层动态符号配置：不存在则生成默认版（你的构想核心结构）"""
        # 确保config目录存在
        if not os.path.exists("./config"):
            os.makedirs("./config")
        
        # 配置不存在：生成带动态符号的默认配置
        if not os.path.exists(self.X_CONFIG_PATH):
            default_x = {
                "核心原则": "X层不存储知识，仅作为索引与指挥中心：定义动态符号、匹配场景、调度Y层执行，通过反馈迭代优化符号系统",
                "符号系统": {
                    "#关联强化": {
                        "规则": "检索当前场景相关的核心/元认知记忆，提升关联强度；若Φ值低，新增元认知记忆补充关联",
                        "适用场景": ["意识涌现Φ值低", "跨会话相干性不足", "记忆关联强度＜0.7"],
                        "调用权重": 0.9,
                        "触发阈值": 0.6
                    },
                    "#批判性质疑": {
                        "规则": "检索当前记忆的冲突记忆、低强度关联记忆，生成质疑点；若数据类记忆，验证数值一致性",
                        "适用场景": ["记忆准确性验证", "AC100元块整合度异常", "用户提出疑问", "工作记忆含数据"],
                        "调用权重": 0.7,
                        "触发阈值": 0.5
                    },
                    "#记忆转化": {
                        "规则": "将高价值工作记忆（检索≥5次/强度≥0.85）转化为核心/元认知记忆，避免过期丢失",
                        "适用场景": ["工作记忆即将过期", "高频率检索工作记忆", "AC100增长得分低"],
                        "调用权重": 0.6,
                        "触发阈值": 0.7
                    }
                },
                "调度逻辑": "1. 优先匹配「场景包含当前问题」且「调用权重高」的符号；2. 执行符号对应操作后，权重+0.1（上限1.0）；3. 每月自动重置权重（避免单一符号垄断）",
                "last_reset_month": datetime.now().strftime("%Y-%m")  # 记录上次重置月份
            }
            with open(self.X_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(default_x, f, ensure_ascii=False, indent=2)
            print(f"✅ 生成X层动态符号配置：{self.X_CONFIG_PATH}")
            return default_x
        
        # 配置已存在：加载并校验结构（避免格式错误）
        with open(self.X_CONFIG_PATH, "r", encoding="utf-8") as f:
            x_config = json.load(f)
        # 补全缺失字段（防止用户手动修改后出错）
        if "符号系统" not in x_config:
            x_config["符号系统"] = {}
        if "last_reset_month" not in x_config:
            x_config["last_reset_month"] = datetime.now().strftime("%Y-%m")
        # 保存补全后的配置
        with open(self.X_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(x_config, f, ensure_ascii=False, indent=2)
        return x_config

    def _init_y_dirs(self):
        """初始化Y层目录（原有逻辑不变，确保路径存在）"""
        for dir_path in self.Y_DIRS:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        print(f"✅ Y层目录初始化完成：{self.Y_ROOT}")

    def _reset_weight_monthly(self):
        """每月自动重置符号权重（按调度逻辑，避免单一符号垄断）"""
        current_month = datetime.now().strftime("%Y-%m")
        last_month = self.x_config.get("last_reset_month", "")
        if current_month != last_month:
            # 重置权重为初始值（0.6~0.9）
            for symbol, info in self.x_config["符号系统"].items():
                if symbol == "#关联强化":
                    info["调用权重"] = 0.9
                elif symbol == "#批判性质疑":
                    info["调用权重"] = 0.7
                elif symbol == "#记忆转化":
                    info["调用权重"] = 0.6
            # 更新重置时间
            self.x_config["last_reset_month"] = current_month
            # 保存重置后的配置
            with open(self.X_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.x_config, f, ensure_ascii=False, indent=2)
            print(f"✅ 每月符号权重重置完成（当前月份：{current_month}）")

    def get_trigger_symbol(self, current_scenario: str) -> tuple[str, dict]:
        """
        核心方法1：根据当前场景，匹配并返回触发符号（你的构想核心）
        返回：(触发符号, 符号详情)，如("#关联强化", {"规则": "...", "权重": 0.9})
        """
        matched = []
        for symbol, info in self.x_config["符号系统"].items():
            # 场景匹配：当前场景是否在符号的适用场景中
            scenario_match = any(current_scenario in s for s in info.get("适用场景", []))
            if scenario_match:
                # 记录：符号、权重（用于排序）、详情
                matched.append( (symbol, info["调用权重"], info) )
        
        # 无匹配符号：返回默认符号（#关联强化）
        if not matched:
            default_symbol = "#关联强化"
            return (default_symbol, self.x_config["符号系统"][default_symbol])
        
        # 有多个匹配：按权重降序，选最高的
        matched.sort(key=lambda x: x[1], reverse=True)
        target_symbol, _, target_info = matched[0]
        return (target_symbol, target_info)

    def update_symbol_weight(self, symbol: str, increment: float = 0.1):
        """
        核心方法2：执行符号操作后，更新权重（反馈迭代，你的构想闭环）
        increment：权重增量（默认+0.1，上限1.0，避免权重无限增长）
        """
        if symbol not in self.x_config["符号系统"]:
            print(f"⚠️ X层符号不存在：{symbol}，跳过权重更新")
            return
        
        # 计算新权重（上限1.0）
        old_weight = self.x_config["符号系统"][symbol]["调用权重"]
        new_weight = min(old_weight + increment, 1.0)
        self.x_config["符号系统"][symbol]["调用权重"] = new_weight
        
        # 保存更新后的配置（持久化，下次启动仍有效）
        with open(self.X_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.x_config, f, ensure_ascii=False, indent=2)
        
        print(f"✅ X层符号权重更新：{symbol}（{old_weight} → {new_weight}）")

    def get_symbol_rule(self, symbol: str) -> str:
        """辅助方法：获取符号对应的执行规则（给Y层用）"""
        return self.x_config["符号系统"].get(symbol, {}).get("规则", "默认规则：强化核心记忆关联")

# 单例模式：所有模块共用一个X层实例（避免重复加载）
xy_loader = XYLoader()