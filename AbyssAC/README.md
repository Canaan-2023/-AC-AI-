# 🧠 AbyssAC - 人工意识系统

基于NNG导航和Y层记忆的AI操作系统，实现LLM与记忆系统的协同工作，形成闭环反馈。

## 📋 目录

- [系统概述](#系统概述)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [配置说明](#配置说明)
- [API文档](#api文档)
- [故障排除](#故障排除)

## 🎯 系统概述

AbyssAC是一个创新的AI记忆管理系统，通过三层沙盒机制实现：

1. **X层三层沙盒**：导航定位 → 记忆筛选 → 上下文组装
2. **Y层记忆库**：元认知/高阶整合/分类/工作 四种记忆类型
3. **NNG导航图**：层级化的知识导航结构
4. **DMN维护网络**：5个子智能体自动维护系统

### 核心特性

- 🔄 **Bootstrap流程**：从空系统逐步进化到完整功能
- 🧭 **智能导航**：LLM自主决定在NNG中的导航路径
- 💾 **分层记忆**：按价值和类型自动分类存储
- 🔧 **自动维护**：DMN自动整合记忆、优化结构
- 🛡️ **故障恢复**：导航失败时自动降级处理

## 🏗️ 架构设计

```
AbyssAC/
├── core/               # 核心模块
│   ├── config.py      # 配置管理
│   └── abyssac.py     # 主控制器
├── llm/               # LLM接口
│   └── llm_interface.py
├── memory/            # Y层记忆
│   └── memory_manager.py
├── nng/               # NNG导航
│   └── nng_manager.py
├── sandbox/           # X层沙盒
│   └── sandbox_layer.py
├── dmn/               # DMN维护
│   └── dmn_agents.py
└── ui/                # 前端界面
    └── gradio_app.py
```

### Bootstrap三阶段

```
阶段1: NNG为空
  └─→ 跳过沙盒，直接回复
  └─→ 对话存入工作记忆

阶段2: 首次DMN触发（工作记忆≥20条）
  └─→ 分析工作记忆
  └─→ 创建时间目录结构
  └─→ 生成首个NNG节点
  └─→ 更新root.json

阶段3: 正常运行
  └─→ X层三层沙盒工作
  └─→ DMN自动维护
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Ollama（推荐）或API密钥

### 安装步骤

1. **克隆/下载代码**
```bash
cd AbyssAC
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **安装Ollama（推荐）**
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: 下载安装包 https://ollama.com/download

# 拉取推荐模型
ollama pull qwen2.5:7b
```

4. **启动系统**
```bash
# Gradio界面（默认）
python main.py

# 命令行模式
python main.py --cli
```

### 首次运行

1. 打开浏览器访问 `http://localhost:7860`
2. 在"系统设置"标签页点击"初始化系统"
3. 切换到"对话"标签页开始聊天

## 📖 使用指南

### 对话模式

```python
from core.abyssac import AbyssAC
from core.config import get_config

# 初始化
config = get_config()
abyssac = AbyssAC(config)

# 对话
response = abyssac.chat("你好，请介绍一下自己")
print(response)
```

### 手动触发DMN

```python
# 触发记忆整合
result = abyssac.manual_trigger_dmn("memory_integration")
print(result)

# 触发NNG优化
result = abyssac.manual_trigger_dmn("nng_optimization")
print(result)
```

### 获取系统状态

```python
status = abyssac.get_system_status()
print(status)
# {
#     'bootstrap_stage': '阶段3_正常运行',
#     'total_conversations': 42,
#     'working_memory_count': 15,
#     'nng_node_count': 8,
#     'navigation_failures': 0
# }
```

## ⚙️ 配置说明

配置文件：`abyssac_config.json`

```json
{
  "llm": {
    "use_local": true,
    "ollama_base_url": "http://localhost:11434",
    "ollama_model": "qwen2.5:7b",
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "memory": {
    "base_path": "Y层记忆库"
  },
  "nng": {
    "base_path": "NNG",
    "max_navigation_depth": 10
  },
  "dmn": {
    "working_memory_threshold": 20,
    "navigation_failure_threshold": 5
  }
}
```

### LLM模型推荐

| 模型 | 参数 | 用途 | 命令 |
|------|------|------|------|
| Qwen2.5 | 7B | 通用推荐 | `ollama pull qwen2.5:7b` |
| Llama 3.1 | 8B | 英文任务 | `ollama pull llama3.1:8b` |
| Mistral | 7B | 代码任务 | `ollama pull mistral:7b` |
| Gemma 2 | 9B | 轻量级 | `ollama pull gemma2:9b` |

### API配置（备用）

如果不想使用Ollama，可以配置API：

```json
{
  "llm": {
    "use_local": false,
    "api_base_url": "https://api.siliconflow.cn/v1",
    "api_key": "your-api-key",
    "api_model": "deepseek-ai/DeepSeek-V2.5"
  }
}
```

推荐便宜API平台：
- **SiliconFlow (硅基流动)**: 国产开源模型，DeepSeek、Qwen等
- **OpenRouter**: 多模型聚合
- **Google AI Studio**: Gemini 2.5 Flash免费额度高

## 📚 API文档

### AbyssAC类

#### `chat(user_input: str) -> str`

用户对话接口。

**参数:**
- `user_input`: 用户输入文本

**返回:**
- AI回复文本

**示例:**
```python
response = abyssac.chat("什么是Python的GIL？")
```

#### `get_system_status() -> Dict`

获取系统状态。

**返回:**
- 包含系统状态的字典

#### `manual_trigger_dmn(task_type: str) -> str`

手动触发DMN任务。

**参数:**
- `task_type`: 任务类型
  - `memory_integration`: 记忆整合
  - `association_discovery`: 关联发现
  - `bias_review`: 偏差审查
  - `strategy_rehearsal`: 策略预演
  - `concept_recombination`: 概念重组
  - `nng_optimization`: NNG优化

### MemoryManager类

#### `save_memory(content, memory_type, value_level=None) -> MemoryEntry`

保存记忆。

**参数:**
- `content`: 记忆内容
- `memory_type`: MemoryType枚举（META_COGNITION/HIGH_LEVEL/CLASSIFIED/WORKING）
- `value_level`: ValueLevel枚举（HIGH/MEDIUM/LOW，仅CLASSIFIED需要）

#### `get_memory(memory_id: int) -> Optional[MemoryEntry]`

根据ID获取记忆。

#### `get_working_memories(limit=20) -> List[MemoryEntry]`

获取工作记忆列表。

### NNGManager类

#### `create_node(parent_id, content) -> Optional[str]`

创建新节点。

**参数:**
- `parent_id`: 父节点ID（如"root"或"1.2"）
- `content`: 节点内容描述

**返回:**
- 新节点ID或None

#### `get_node(node_id: str) -> Optional[NNGNode]`

获取节点数据。

#### `add_memory_to_node(node_id, memory_id, summary, memory_type)`

向节点添加记忆关联。

## 🔧 故障排除

### Ollama连接失败

**问题:** `Ollama检测失败`

**解决:**
```bash
# 检查Ollama是否运行
curl http://localhost:11434/api/tags

# 如果没有响应，启动Ollama
ollama serve

# 拉取模型
ollama pull qwen2.5:7b
```

### 导航失败过多

**问题:** 导航失败次数超过阈值

**解决:**
1. 系统会自动触发NNG优化DMN任务
2. 或手动触发：`python main.py --cli` 后输入 `dmn`
3. 检查NNG结构是否合理

### 内存占用过高

**解决:**
1. 使用更小的模型（如qwen2.5:1.5b）
2. 降低`max_tokens`配置
3. 定期清理工作记忆

### Gradio界面无法访问

**解决:**
```bash
# 检查端口占用
lsof -i :7860

# 使用其他端口
# 修改 ui/gradio_app.py 中的端口配置
```

## 📁 目录结构说明

### Y层记忆库

```
Y层记忆库/
├── id_counter.txt           # ID计数器
├── 元认知记忆/              # 系统自我认知
│   └── 2026/01/01/1.txt
├── 高阶整合记忆/            # 深度整合的知识
│   └── 2026/01/01/2.txt
├── 分类记忆/                # 按价值分类
│   ├── 高价值/
│   ├── 中价值/
│   └── 低价值/
└── 工作记忆/                # 临时对话记忆
    └── 2026/01/01/10.txt
```

### NNG导航图

```
NNG/
├── root.json                # 根节点
├── 1/
│   ├── 1.json              # 节点1数据
│   └── 1/                  # 节点1的子节点
│       ├── 1.1.json
│       └── 1.1/
│           └── 1.1.1.json
└── 2/
    ├── 2.json
    └── 2/
```

## 🧪 运行自测

```bash
# 测试所有模块
python main.py --test

# 测试单个模块
python -m core.config
python -m memory.memory_manager
python -m nng.nng_manager
python -m llm.llm_interface
python -m sandbox.sandbox_layer
python -m dmn.dmn_agents
python -m core.abyssac
```

## 🤝 贡献

欢迎提交Issue和PR！

## 📄 许可证

AGPLv3

---

**AbyssAC** - 让AI拥有真正的记忆 🧠
