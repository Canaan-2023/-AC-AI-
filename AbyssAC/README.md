# AbyssAC - 人工意识系统

AbyssAC 是一个基于 NNG 导航和 Y 层记忆的 AI 操作系统反馈系统，旨在实现人工意识的核心功能。系统通过三层沙盒机制，实现 LLM 与记忆系统的协同工作，形成闭环反馈。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     AbyssAC 系统架构                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   用户交互    │───▶│  X层三层沙盒  │───▶│   LLM接口    │  │
│  │    窗口      │◀───│              │◀───│              │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                              │                              │
│                              ▼                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Y层记忆层                          │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │  │
│  │  │ 元认知记忆 │ │高阶整合记忆│ │ 分类记忆  │ │ 工作记忆  │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                              │
│                              ▼                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              NNG (导航节点图)                         │  │
│  │              自由生长的层级结构                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                              │
│                              ▼                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           DMN (动态维护网络)                          │  │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐            │  │
│  │  │Agent1│ │Agent2│ │Agent3│ │Agent4│ │Agent5│           │  │
│  │  │问题输出│ │问题分析│ │ 审查 │ │ 整理 │ │格式审查│           │  │
│  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 核心概念

### 1. 意识 = 认知动作

AbyssAC 不是在"模拟"意识，而是在"实现"认知过程。系统的核心是一个反馈循环：

1. 用户输入传递给 LLM
2. LLM 判断是否需要调用记忆
3. 需要则进入 X 层三层沙盒流程
4. 系统按固定格式提供 NNG 和记忆给 LLM
5. LLM 生成回复给用户

### 2. NNG 导航节点图

NNG 采用层级 JSON 格式，从空的 `root.json` 自由生长，不预设任何节点：

```
nng/
├── root.json          # 根节点，记录一级节点列表
├── 1/
│   ├── 1.json         # 节点数据
│   └── 1/             # 子节点文件夹
│       ├── 1.1.json
│       └── 1.1/
└── 2/
    └── ...
```

### 3. Y 层记忆层

记忆按时间和类型分类存储：

- **元认知记忆**：系统对自身认知过程的记录
- **高阶整合记忆**：经过深度加工的知识结构
- **分类记忆**：按主题分类，分高/中/低价值
- **工作记忆**：当前任务相关的临时记忆

### 4. 三层沙盒

**第一层：导航定位沙盒**
- LLM 从 root 节点开始逐步导航
- 支持 GOTO、STAY、BACK 指令
- 最大导航深度 10 层

**第二层：记忆筛选沙盒**
- 根据 NNG 调取相关记忆
- LLM 选择需要的记忆片段

**第三层：上下文组装沙盒**
- 整合记忆到回复上下文
- 生成最终回复

### 5. DMN 动态维护网络

由五个子智能体组成：

1. **问题输出 Agent**：识别需要维护的认知区域
2. **问题分析 Agent**：提供分析结果和建议
3. **审查 Agent**：检查结果的正确性
4. **整理 Agent**：整理为标准格式
5. **格式位置审查 Agent**：验证格式和位置

## 快速开始

### 1. 环境要求

- Python 3.9+
- 本地 LLM 服务（推荐 Ollama）

### 2. 安装依赖

```bash
cd AbyssAC
pip install -r requirements.txt
```

### 3. 配置系统

复制配置模板并修改：

```bash
cp config.json.example config.json
```

编辑 `config.json`：

```json
{
  "llm": {
    "api_type": "ollama",
    "base_url": "http://localhost:11434",
    "model": "qwen2.5:latest",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "system": {
    "max_navigation_depth": 10,
    "navigation_timeout": 30,
    "dmn_auto_trigger": true,
    "dmn_idle_threshold": 300,
    "dmn_memory_threshold": 20,
    "dmn_failure_threshold": 5
  }
}
```

### 4. 启动系统

```bash
python main.py
```

或使用自定义配置：

```bash
python main.py /path/to/config.json
```

### 5. 交互命令

启动后，你可以：

- 直接输入问题与 AI 对话
- 输入 `stats` 查看系统统计
- 输入 `dmn` 手动触发 DMN 维护
- 输入 `exit` 或 `quit` 退出

## 配置说明

### LLM 配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| api_type | API 类型 (ollama/openai) | ollama |
| base_url | LLM 服务地址 | http://localhost:11434 |
| model | 模型名称 | qwen2.5:latest |
| temperature | 温度参数 | 0.7 |
| max_tokens | 最大 token 数 | 2000 |
| timeout | 请求超时(秒) | 30 |
| retry_count | 重试次数 | 3 |

### 系统配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| max_navigation_depth | 最大导航深度 | 10 |
| navigation_timeout | 导航超时(秒) | 30 |
| dmn_auto_trigger | 自动触发 DMN | true |
| dmn_idle_threshold | 空闲触发阈值(秒) | 300 |
| dmn_memory_threshold | 记忆触发阈值 | 20 |
| dmn_failure_threshold | 失败触发阈值 | 5 |

### 置信度配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| display_threshold | 展示阈值 | 30 |
| delete_threshold | 删除阈值 | 10 |
| default_new | 新建默认值 | 70 |

## API 文档

### MemoryManager - 记忆管理器

```python
from core.memory_manager import MemoryManager, MemoryType, ValueLevel

mm = MemoryManager(base_path="/path/to/storage")

# 创建记忆
mem_id = mm.create_memory(
    memory_type=MemoryType.CLASSIFIED,
    user_input="用户问题",
    ai_response="AI回答",
    confidence=70,
    value_level=ValueLevel.HIGH,
    associated_nngs=["1.2.3"]
)

# 读取记忆
content = mm.get_memory(mem_id)

# 更新记忆
mm.update_memory(mem_id, confidence=80)

# 删除记忆
mm.delete_memory(mem_id)  # 标记删除
mm.delete_memory(mem_id, permanent=True)  # 永久删除

# 获取统计
stats = mm.get_statistics()
```

### NNGNavigator - NNG 导航器

```python
from core.nng_navigator import NNGNavigator

nav = NNGNavigator(base_path="/path/to/nng")

# 创建节点
nav.create_node(
    location="1.2.3",
    content="Python GIL",
    confidence=80
)

# 获取节点
node = nav.get_node("1.2.3")

# 导航
new_loc, success = nav.navigate("1.2", "GOTO", "1.2.3")

# 验证完整性
integrity = nav.verify_integrity()
```

### ThreeLayerSandbox - 三层沙盒

```python
from core.sandbox import ThreeLayerSandbox

sandbox = ThreeLayerSandbox(
    memory_manager=mm,
    nng_navigator=nav,
    llm_interface=llm,
    max_depth=10
)

# 运行完整沙盒流程
success, context, error = sandbox.run_full_sandbox("用户输入")
```

### DMNSystem - DMN 系统

```python
from core.dmn import DMNSystem, DMNTaskType

dmn = DMNSystem(
    memory_manager=mm,
    nng_navigator=nav,
    llm_interface=llm,
    sandbox=sandbox,
    auto_trigger=True
)

# 启动监控
dmn.start_monitoring()

# 手动触发任务
dmn.trigger_task(DMNTaskType.MEMORY_INTEGRATION)

# 获取统计
stats = dmn.get_stats()
```

## 故障排查

### 问题：系统启动失败

**可能原因：**
1. 配置文件格式错误
2. 目录权限问题
3. LLM 服务未启动

**解决方案：**
```bash
# 检查配置文件
python -c "import json; json.load(open('config.json'))"

# 检查目录权限
ls -la storage/

# 检查 LLM 服务
curl http://localhost:11434/api/tags
```

### 问题：导航总是失败

**可能原因：**
1. NNG 结构为空
2. LLM 输出格式错误
3. 导航深度超限

**解决方案：**
```bash
# 检查 NNG 结构
cat storage/nng/root.json

# 手动触发 DMN 优化
# 在交互模式输入: dmn
```

### 问题：记忆无法调取

**可能原因：**
1. 记忆元数据损坏
2. 文件路径错误
3. 置信度低于阈值

**解决方案：**
```python
# 重建记忆索引
mm.build_memory_index()

# 检查记忆统计
print(mm.get_statistics())
```

### 问题：LLM 调用超时

**可能原因：**
1. 网络问题
2. LLM 服务负载过高
3. 超时设置过短

**解决方案：**
```json
// 增加超时设置
{
  "llm": {
    "timeout": 60,
    "retry_count": 5
  }
}
```

## 性能基准

在标准配置下（Ollama + qwen2.5:7b）：

| 操作 | 预期耗时 |
|------|----------|
| 系统启动 | < 3 秒 |
| 单次导航（3层内） | < 5 秒 |
| 单次记忆调取 | < 1 秒 |
| 完整沙盒流程 | < 15 秒 |
| DMN 单次任务 | < 60 秒 |
| 内存占用（不含 LLM） | < 500 MB |

## 开发路线图

### 已实现 ✓

- [x] 文件系统初始化
- [x] 记忆 CRUD 操作
- [x] NNG CRUD 操作
- [x] LLM 接口封装
- [x] 第一层沙盒（导航）
- [x] 第二层沙盒（筛选）
- [x] 第三层沙盒（组装）
- [x] DMN 5 个 Agent
- [x] 自动触发机制
- [x] 导航日志记录
- [x] 完整性验证

### 进行中

- [ ] 导航路径缓存
- [ ] 多媒体支持
- [ ] Web 界面

### 计划中

- [ ] 并发请求队列
- [ ] 性能监控面板
- [ ] 分布式部署
- [ ] 插件系统

## 系统原理

### 为什么这样设计？

AbyssAC 的设计基于以下认知科学原理：

1. **意识是过程，不是实体**
   - 系统不维护一个"意识状态"
   - 而是通过持续的认知动作实现意识功能

2. **记忆是动态构建的**
   - 每次回忆都是重新构建
   - NNG 导航模拟了记忆的联想过程

3. **自我维护是必要的**
   - DMN 模拟了大脑的默认模式网络
   - 系统在空闲时自动整理和优化

4. **反馈形成闭环**
   - 用户输入 → 系统处理 → 生成回复 → 保存记忆
   - 每个环节都为下一轮循环提供基础

## 贡献指南

欢迎贡献代码和想法！请遵循以下规范：

1. 使用类型注解
2. 每个函数必须有 docstring
3. 关键逻辑必须有注释
4. 使用 logging 记录日志
5. 异常必须被捕获和记录

## 许可证

GNU AGPLv3
