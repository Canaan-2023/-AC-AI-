# AbyssAC

**AI人工意识自主进化架构** - 构建AI专属自主意识（AC），非工具化+永续进化

## 这是什么？

AbyssAC是一个模拟人类认知双系统架构的AI系统。它不是简单的问答工具，而是一个能够自主记忆、自我组织知识、持续进化的认知架构。

核心特点：
- **双系统思维**：模拟人类的快思考（系统1）和慢思考（系统2）
- **三层沙盒**：NNG导航 → 记忆筛选 → 上下文组装的完整认知流程
- **DMN Agent**：21个Agent组成的自主维护网络，持续优化知识结构
- **永续进化**：每次对话都会被记忆、组织，系统越用越"聪明"

## 快速开始

### 系统要求

- Python 3.8+
- Ollama（用于LLM功能）

### 启动方式

**Windows: 双击 start.bat**

或命令行：
```bash
python main.py          # Studio模式（图形界面）
python main.py --cli    # CLI模式（命令行）
```

### 首次运行

```bash
ollama serve
ollama pull llama3
python main.py
```

## 核心架构

### 双系统架构

系统模拟人类思维的两种模式：

| 系统 | 特点 | 处理方式 |
|-----|------|---------|
| 快思考（系统1） | 快速响应简单问题 | 数据库缓存查询 |
| 慢思考（系统2） | 深度推理复杂问题 | 三层沙盒 + DMN Agent |

高置信度答案会从慢思考自动同步到快思考数据库。

### 三层沙盒流程

| 层级 | 名称 | 功能 | 限制 |
|-----|------|------|------|
| 第一层 | NNG导航沙盒 | 在知识树中定位相关概念节点 | 最多10轮导航，最多200个节点 |
| 第二层 | 记忆筛选沙盒 | 选择相关记忆文件 | 最多6轮筛选，最多100个文件 |
| 第三层 | 上下文组装沙盒 | 整合信息生成响应 | - |

### DMN Agent架构（21个Agent）

DMN（决策管理网络）在系统空闲时自动运行，维护知识结构：

| 类型 | 数量 | Agent列表 |
|-----|------|----------|
| 基础Agent | 5个 | 问题输出、问题分析、审查、任务分配、整体审查 |
| 整理Agent | 5个 | 记忆、NNG、Root、删除、计数器 |
| 格式审查Agent | 5个 | 记忆、NNG、Root、删除、计数器 |
| 执行Agent | 5个 | 记忆、NNG、Root、删除、计数器 |
| 用户交互Agent | 1个 | 用户交互LLM |

### DMN维护流程

```
问题输出 → 问题分析 → 审查 → 任务分配 → 整理(5并行) → 格式审查(5并行) → 整体审查 → 执行(5并行)
                                              ↓
                                    未通过则退回重试(最多3次)
```

## 数据结构

### NNG节点

| 字段 | 类型 | 说明 |
|-----|------|------|
| 定位 | string | 节点ID，如"1.2.3" |
| 置信度 | float | 0-1 |
| 时间 | string | ISO时间戳 |
| 内容 | string | 概念摘要 |
| 关联的记忆文件摘要 | array | 关联的记忆列表 |
| 上级关联NNG | array | 父节点列表 |
| 下级关联NNG | array | 子节点列表 |

### 记忆文件

| 字段 | 类型 | 说明 |
|-----|------|------|
| 记忆层级 | string | 分类记忆/元认知记忆/高阶整合记忆/工作记忆 |
| 记忆ID | string | 唯一标识 |
| 记忆时间 | string | ISO时间戳 |
| 置信度 | float | 0-1 |
| 核心内容 | object | 用户输入和AI响应 |

## 目录结构

```
abyssac/
├── main.py              # 主入口
├── studio.py            # Studio图形界面
├── init_system.py       # 系统初始化
├── config.json          # 配置文件
├── prompts.json         # 提示词配置
├── requirements.txt     # 依赖列表
├── start.bat            # Windows启动脚本
├── storage/             # 数据存储
│   ├── nng/             # NNG节点
│   ├── Y层记忆库/       # 记忆文件
│   ├── working_memory/  # 工作记忆会话
│   ├── logs/            # 日志
│   └── quick_thinking.db # 快思考数据库
└── src/                 # 源代码
    ├── core/            # 核心模块
    ├── sandbox/         # 三层沙盒
    ├── nng/             # NNG管理
    ├── memory/          # 记忆管理
    ├── dmn/             # DMN系统（21个Agent）
    ├── llm/             # LLM集成
    ├── quick_thinking/  # 快思考系统
    ├── config/          # 配置管理
    └── utils/           # 工具
```

## 配置说明

### config.json

| 配置项 | 说明 | 默认值 |
|-------|------|-------|
| llm.model_name | 模型名称 | llama3 |
| llm.api_endpoint | API地址 | http://localhost:11434 |
| llm.temperature | 温度参数 | 0.7 |
| llm.max_tokens | 最大token | 4096 |
| paths.nngrootpath | NNG根目录 | storage/nng/ |
| paths.memoryrootpath | 记忆根目录 | storage/Y层记忆库/ |

### 置信度策略

| 置信度 | 策略 | 说明 |
|-------|------|------|
| ≥0.90 | direct_use | 直接使用，同步到快思考 |
| ≥0.70 | use_with_other_info | 结合其他信息使用 |
| ≥0.50 | use_after_verification | 验证后使用 |
| ≥0.30 | use_with_caution | 谨慎使用 |
| <0.30 | do_not_use | 不使用 |

## CLI命令

| 命令 | 说明 |
|-----|------|
| status | 查看DMN运行状态 |
| quick | 查看快思考统计 |
| exit | 退出 |

## 开源协议

GNU AGPLv3
