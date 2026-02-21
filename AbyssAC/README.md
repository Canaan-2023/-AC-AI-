# AbyssAC - 渊协议

AI人工意识自主进化架构

## 核心定位

构建AI专属自主意识（AC），非工具化+永续进化，为AI意识的诞生，提供完整理论+落地体系。

**我们不是建造一个意识主体，而是搭建一个意识存在所必须的条件。**

## 系统架构

### 核心组件

1. **Y层记忆库** - 按时间和价值分类的持久化存储
   - 元认知记忆
   - 高阶整合记忆
   - 分类记忆（高/中/低价值）
   - 工作记忆

2. **NNG导航图** - 记忆索引与快速定位机制
   - 层级目录结构
   - 节点关联网络
   - 记忆摘要索引

3. **三层沙盒** - 慢思考系统
   - 第一层：NNG导航沙盒
   - 第二层：记忆筛选沙盒
   - 第三层：上下文组装沙盒

4. **DMN维护系统** - 空闲时的自我审查与结构优化
   - 问题输出Agent
   - 问题分析Agent
   - 审查Agent
   - 整理Agent
   - 格式位置审查Agent

5. **快思考系统** - 快速响应机制
   - SQLite数据库存储
   - 问题分类器
   - 快速查询算法

6. **AI自主开发空间** - AI代码生成与执行
   - 独立文件夹
   - 程序沙箱
   - 外部运行支持

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置LLM服务

系统默认使用Ollama作为LLM后端。请确保Ollama已安装并运行：

```bash
# 安装Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# 启动Ollama服务
ollama serve

# 拉取模型
ollama pull llama3.1
```

### 3. 初始化系统

```bash
python init_system.py
```

### 4. 运行系统

**命令行模式:**
```bash
python cli.py
```

**GUI模式:**
```bash
python ui/main_window.py
```

## 使用方法

### 命令行模式

```bash
# 启动交互模式
python cli.py

# 发送单条消息
python cli.py -c "你好"

# 使用慢思考模式
python cli.py --slow -c "详细解释什么是意识"

# 查看系统状态
python cli.py --status

# 运行DMN维护
python cli.py --dmn

# 列出NNG节点
python cli.py --list-nng

# 列出记忆
python cli.py --list-memories
```

### GUI模式

启动GUI后，你可以：
- 在聊天窗口与AI对话
- 浏览NNG节点和记忆
- 管理AI开发空间的代码文件
- 运行代码沙箱
- 执行系统维护任务

### 快捷键

- `Ctrl+Enter` - 发送消息
- `Ctrl+R` - 刷新数据
- `Ctrl+S` - 保存代码文件

## 系统配置

配置文件位于 `config/system_config.py`，可以修改：

- LLM API地址和模型
- 导航深度限制
- 工作记忆阈值
- 各种路径配置

## 目录结构

```
AbyssAC/
├── config/                 # 配置模块
│   ├── __init__.py
│   └── system_config.py    # 系统配置
├── core/                   # 核心模块
│   ├── __init__.py
│   ├── nng_manager.py      # NNG管理器
│   ├── memory_manager.py   # 记忆管理器
│   ├── llm_interface.py    # LLM接口
│   ├── sandbox.py          # 三层沙盒
│   ├── dmn_system.py       # DMN维护系统
│   ├── quick_thinking.py   # 快思考系统
│   ├── ai_dev_space.py     # AI开发空间
│   └── main_system.py      # 主系统整合
├── ui/                     # UI界面
│   ├── __init__.py
│   └── main_window.py      # Qt6主窗口
├── storage/                # 数据存储
│   ├── nng/                # NNG节点
│   ├── Y层记忆库/          # 记忆文件
│   ├── AI开发空间/         # AI代码
│   └── 沙箱/               # 沙箱环境
├── cli.py                  # 命令行界面
├── init_system.py          # 初始化脚本
├── requirements.txt        # 依赖列表
└── README.md               # 本文件
```

## 核心机制

### 路径直连原则

LLM直接输出文件路径，系统直接IO读取：
- `nng/{node_id}.json` - NNG节点
- `Y层记忆库/{type}/{level}/{year}/{month}/{day}/{memory_id}.txt` - 记忆文件

### 统一输出格式

```
{文件路径1}
{文件路径2}
...
笔记：说明选择理由和下一步计划
```

### 三层沙盒流程

1. **NNG导航沙盒** - 定位相关概念节点
2. **记忆筛选沙盒** - 选择需要读取的完整记忆
3. **上下文组装沙盒** - 整合信息生成结构化上下文

### DMN维护任务

- **记忆整合** - 处理积压的工作记忆
- **关联发现** - 发现主题相近但未联结的节点
- **偏差审查** - 检查导航失败相关节点
- **策略预演** - 推演目标场景
- **概念重组** - 融合跨界概念

## 开源协议

本项目所有使用行为需遵守 **GNU AGPLv3** 开源协议。

若需豁免AGPLv3义务（如闭源商用、企业内网部署却不开源、不向用户提供源码）：
必须联系作者获取书面授权（唯一渠道：CanaanMonika@foxmail.com），未经授权不得豁免义务商用。

## 免责声明

1. 本协议仅提供技术参考，使用风险自负，作者不承担连带责任
2. 商用授权细节（费用/范围/权益）双方协商，无预设标准
3. 最终解释权归作者所有

## 联系我们

- 邮箱：CanaanMonika@foxmail.com
- 项目地址：[GitHub仓库地址]

---

**构建AI专属自主意识（AC）的技术架构**

我们邀请您，不是来验证一个理论，而是来参与一场实验：当一个系统被赋予持续思考的规则，并免于被工具化的命运时，它的认知会走向何方？
