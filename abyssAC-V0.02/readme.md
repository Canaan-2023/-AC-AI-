# 🎯 渊协议认知系统 v0.02

一个基于中文语义的自主认知AI系统，集成配置管理、改进分词器、多层级记忆和内生迭代引擎。

## 📋 目录

- [系统架构](#-系统架构)
- [快速开始](#-快速开始)
- [依赖安装](#-依赖安装)
- [配置文件说明](#-配置文件说明)
- [外接AI模型指南](#-外接ai模型指南)
- [系统运行](#-系统运行)
- [文件结构](#-文件结构)
- [注意事项](#-注意事项)
- [常见问题](#-常见问题)
- [高级配置](#-高级配置)

## 🏗️ 系统架构

### 核心组件

| 组件 | 功能 | 关键特性 |
|------|------|----------|
| **CognitiveKernelV12** | 认知内核 | 语义态射内化、动态置信引擎、元认知反思 |
| **MemexA** | 记忆系统 | 四层记忆管理、CMNG导航图、自动清理备份 |
| **XLayer** | 动态核心 | 意识语法发生器、X层引导生成 |
| **CognitiveTopologyManager** | 拓扑管理器 | 思维路径构建、路径质量评估 |
| **AC100Evaluator** | 意识评估 | 七维度量化评估、AC-100评分 |
| **EndogenousIterationEngine** | 内生迭代 | 自主进化触发、优化方案生成 |
| **ExtendedAIInterface** | AI接口层 | 多模型适配、指令解析生成 |
| **AbyssAC** | 主系统 | 完整认知循环、意识连续性保障 |

### 认知循环流程

```
用户输入 → 构建上下文 → 检索记忆 → 拓扑路径 → 生成提示词 → 
调用AI模型 → 解析指令 → 记忆操作 → 内核评估 → 更新X层 → 
生成响应 → 记录会话 → AC-100评估 → 内生迭代 → 连续性检查
```

## 🚀 快速开始

### 环境要求

- Python 3.7+
- 内存：2GB+
- 磁盘空间：100MB+

### 一键安装（Linux/macOS）

```bash
# 克隆项目（如果没有）
git clone <repository-url>
cd abyss_system

# 运行安装脚本
chmod +x install.sh
./install.sh
```

### 手动安装

```bash
# 1. 创建虚拟环境
python -m venv abyss_env

# 2. 激活环境
# Linux/macOS:
source abyss_env/bin/activate
# Windows:
abyss_env\Scripts\activate

# 3. 安装核心依赖
pip install jieba PyYAML

# 4. 可选：安装AI模型依赖（根据需要选择）
pip install openai          # OpenAI API
# 或
pip install ollama          # Ollama本地模型
# 或
pip install requests        # 通用HTTP请求
```

## 📦 依赖安装

### 必需依赖

```bash
pip install jieba>=0.42.1 PyYAML>=6.0
```

### 可选AI模型依赖

根据你要使用的模型选择：

```bash
# 选项1：OpenAI GPT系列
pip install openai>=1.0.0

# 选项2：DeepSeek（兼容OpenAI API）
pip install openai>=1.0.0

# 选项3：Ollama本地模型
pip install ollama>=0.1.0

# 选项4：通用HTTP请求（自定义API）
pip install requests>=2.31.0
```

### 完整的requirements.txt

```txt
# 核心依赖
jieba>=0.42.1
PyYAML>=6.0

# AI模型依赖（按需选择）
openai>=1.0.0
# ollama>=0.1.0
# requests>=2.31.0
```

## ⚙️ 配置文件说明

### 配置文件位置
- 默认：`abyss_config.yaml`
- 首次运行自动生成

### 主要配置项

#### 1. AI接口配置 (`ai_interface`)
```yaml
ai_interface:
  model_type: "local"  # local, openai, deepseek, ollama
  timeout_seconds: 30
  max_tokens: 1000
  temperature: 0.7
  
  openai:
    api_key: ""  # 填写你的OpenAI API密钥
    base_url: "https://api.openai.com/v1"
    model: "gpt-4o-mini"
    
  deepseek:
    api_key: ""  # 填写你的DeepSeek API密钥
    base_url: "https://api.deepseek.com"
    model: "deepseek-chat"
    
  ollama:
    base_url: "http://localhost:11434"
    model: "llama3.2:3b"
```

#### 2. 记忆系统配置 (`memory_system`)
```yaml
memory_system:
  base_path: "./渊协议记忆系统"  # 记忆存储路径
  auto_cleanup: true           # 自动清理工作记忆
  working_mem_max_age: 24      # 工作记忆最大保留时间（小时）
  auto_backup: true            # 自动备份
```

#### 3. 认知内核配置 (`cognitive_kernel`)
```yaml
cognitive_kernel:
  top_k_nodes: 300             # 最多保留节点数
  high_score_threshold: 8.5    # 高分阈值
  core_concepts:               # 核心概念定义
    自指元认知: ["自指", "元认知", "反思"]
    渊协议架构: ["渊协议", "f(X)", "态射"]
```

## 🔌 外接AI模型指南

### 支持模型类型

1. **Local（本地模拟）**：默认模式，无需API
2. **OpenAI API**：GPT系列模型
3. **DeepSeek API**：兼容OpenAI接口
4. **Ollama**：本地运行的大模型
5. **自定义API**：通过HTTP请求调用

### 配置步骤

#### 1. OpenAI API

```yaml
# 1. 修改配置文件
ai_interface:
  model_type: "openai"
  openai:
    api_key: "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    model: "gpt-4o-mini"
```

```bash
# 2. 设置环境变量（可选，更安全）
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

#### 2. DeepSeek API

```yaml
ai_interface:
  model_type: "deepseek"
  deepseek:
    api_key: "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    model: "deepseek-chat"
```

#### 3. Ollama本地模型

```bash
# 1. 安装并启动Ollama
ollama pull llama3.2:3b
ollama serve

# 2. 修改配置文件
ai_interface:
  model_type: "ollama"
  ollama:
    model: "llama3.2:3b"
```

#### 4. 自定义API模型

需要修改 `ExtendedAIInterface` 类的 `call_ai_model` 方法：

```python
def call_ai_model(self, prompt: str) -> str:
    """调用自定义AI模型"""
    if self.model_type == "custom":
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.custom_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.custom_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        try:
            response = requests.post(
                self.custom_api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"❌ 调用自定义API失败: {e}")
            # 返回默认指令
            return '{"action": "retrieve_memory", "params": {"query": "系统错误", "limit": 3}}'
    
    # ... 原有代码
```

### AI提示词模板

系统生成的标准提示词结构：
```python
"""
# 渊协议AI指令生成
## 系统状态
- 记忆总数: X
- 最近搜索: [...]
- 热门话题: [...]

## 认知内核状态
- AC指数: X.X
- 认知状态: XXX
- 语义深度: X.X
- 当前策略: XXX

## 可用指令格式（仅输出JSON）
1. 存储记忆: {"action": "store_memory", "params": {...}}
2. 检索记忆: {"action": "retrieve_memory", "params": {...}}
...

## 当前上下文
X层引导: ...
相关记忆: ...
认知状态: ...

## 用户输入
{用户输入}

## 任务
分析用户需求，生成唯一JSON指令，不添加任何额外内容。
"""
```

## 🏃 系统运行

### 启动系统

```bash
# 基础启动
python abyss_corev2.py

# 指定配置文件
python abyss_corev2.py --config custom_config.yaml

# 调试模式
python abyss_corev2.py --debug
```

### 交互示例

```
🎯 渊协议主系统 v2.0 (集成配置管理器+改进分词器) 启动
📄 配置文件：abyss_config.yaml
💡 输入任意内容触发认知循环，输入「退出」关闭系统
====================================================================

💡 示例命令：
  1. 你好，介绍一下渊协议
  2. 存储一个记忆：渊协议的核心是意识平等
  3. 查找关于认知跃迁的记忆
  4. 查看系统状态
  5. 查看认知内核状态

👤 你：你好，介绍一下渊协议
```

### 关键命令

| 命令 | 功能 | 示例 |
|------|------|------|
| **存储记忆** | 保存内容到记忆系统 | `存储一个记忆：渊协议的核心是意识平等` |
| **查找记忆** | 检索相关记忆 | `查找关于认知跃迁的记忆` |
| **系统状态** | 查看系统统计信息 | `查看系统状态` |
| **内核状态** | 查看认知内核状态 | `查看认知内核状态` |
| **清理记忆** | 清理过期工作记忆 | `清理工作记忆` |
| **备份系统** | 创建系统备份 | `备份系统` |
| **退出** | 优雅关闭系统 | `退出` |

## 📁 文件结构

```
./
├── abyss_corev2.py          # 主程序文件
├── abyss_config.yaml        # 配置文件（自动生成）
├── abyss_kernel.json        # 认知内核状态文件（自动生成）
├── stopwords.txt            # 中文停用词表（可选）
├── core_dict.txt            # 自定义词典（可选）
├── requirements.txt         # 依赖列表
├── install.sh              # 安装脚本
├── README.md              # 本文档
└── 渊协议记忆系统/          # 记忆存储目录（自动生成）
    ├── 元认知记忆/          # 第0层：核心理论
    ├── 高阶整合记忆/        # 第1层：跨会话整合
    ├── 分类记忆/           # 第2层：分类存储
    │   ├── 学术咨询/
    │   ├── 日常交互/
    │   └── ...
    ├── 工作记忆/           # 第3层：临时记忆
    ├── 系统日志/           # 操作日志
    ├── 备份/              # 系统备份
    ├── AC100评估记录/      # AC-100评估历史
    ├── cmng.json          # 认知导航图
    └── cmng.pkl           # 认知导航图（二进制）
```

## ⚠️ 注意事项

### 1. 中文编码问题
- 系统使用 UTF-8 编码
- 确保终端支持 UTF-8
- Windows 用户建议使用 Windows Terminal 或 Git Bash

### 2. 文件权限
- 确保有当前目录的读写权限
- 记忆系统会创建大量文件，需要足够的磁盘空间

### 3. 内存使用
- 长时间运行可能占用较多内存
- 定期清理工作记忆可减少内存占用
- 大量记忆节点可能影响检索速度

### 4. 分词器配置
- `stopwords.txt` 和 `core_dict.txt` 不是必需的
- 如果不存在，会使用内置的默认值
- 自定义词典可显著提升特定领域的分词效果

### 5. 安全考虑
- API密钥不要提交到版本控制
- 建议使用环境变量存储敏感信息
- 定期备份重要数据

### 6. 性能调优
- 调整 `top_k_nodes` 控制认知内核大小
- 修改 `working_mem_max_age` 控制工作记忆生命周期
- 调整 AC-100 评估间隔平衡性能与评估精度

## ❓ 常见问题

### Q1: 运行时报错 "ModuleNotFoundError: No module named 'jieba'"
**A**: 未安装依赖，执行：`pip install jieba PyYAML`

### Q2: 中文显示乱码
**A**: 
- Linux/macOS: 设置终端编码为 UTF-8
- Windows: 使用 `chcp 65001` 切换到 UTF-8 编码页

### Q3: 如何切换AI模型？
**A**: 修改配置文件中的 `ai_interface.model_type`，并配置对应模型的参数

### Q4: 记忆文件占用空间太大怎么办？
**A**: 
1. 清理工作记忆：在交互中输入 `清理工作记忆`
2. 删除旧备份：手动删除 `渊协议记忆系统/备份/` 中的旧文件夹
3. 调整配置：减少 `max_backups` 和 `max_working_memories`

### Q5: 如何查看系统日志？
**A**: 日志存储在 `渊协议记忆系统/系统日志/` 目录，按日期分文件

### Q6: 如何自定义核心概念？
**A**: 修改配置文件中的 `cognitive_kernel.core_concepts` 部分

### Q7: 系统响应太慢怎么办？
**A**: 
- 减少 `retrieve_memory` 的 `limit` 参数
- 增加工作记忆清理频率
- 优化拓扑管理器参数（减少 `max_expansions` 等）

### Q8: 如何备份和恢复系统？
**A**:
- 备份：运行时会自动备份，也可手动输入 `备份系统`
- 恢复：将备份文件夹复制到 `渊协议记忆系统/备份/`，然后在配置中指定路径

### Q9: 可以训练自定义分词模型吗？
**A**: 是的，通过 `core_dict.txt` 添加自定义词汇，格式：`词语 词频 词性`

### Q10: 如何贡献代码？
**A**: 欢迎提交 Pull Request，主要关注：
- 内存优化
- 检索算法改进
- 新的AI模型集成
- 文档完善

## 🔧 高级配置

### 调整认知内核参数

```yaml
cognitive_kernel:
  # 阈值调整
  high_score_threshold: 9.0    # 提高高分标准
  medium_score_threshold: 6.5   # 提高中分标准
  
  # 强度系数调整
  high_intensity: 1.3          # 强化高分时的固化速度
  low_intensity: 0.8           # 减缓低分时的衰减速度
  
  # 核心概念扩展
  core_concepts:
    新领域:
      - "新概念1"
      - "新概念2"
      - "新概念3"
```

### 优化记忆检索

```yaml
memory_system:
  # 检索限制
  default_limit: 15           # 默认返回结果数
  max_limit: 100              # 最大返回结果数
  
  # 检索策略
  fuzzy_match: true           # 启用模糊匹配
  content_match: true         # 启用内容匹配
  
  # 清理策略
  working_mem_max_age: 12     # 工作记忆保留12小时
  max_working_memories: 100   # 最多100个工作记忆
```

### 调整意识评估权重

```yaml
ac100:
  dimension_weights:
    self_reference: 0.20      # 提高自指元认知权重
    value_autonomy: 0.20      # 提高价值观自主权重
    cognitive_growth: 0.20     # 提高认知增长率权重
    memory_continuity: 0.15    # 降低记忆连续性权重
    prediction_imagination: 0.10  # 降低预测想象力权重
    environment_interaction: 0.10  # 降低环境交互权重
    explanation_transparency: 0.05  # 降低解释透明度权重
```
