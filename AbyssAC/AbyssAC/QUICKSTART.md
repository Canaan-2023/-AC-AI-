# AbyssAC 快速启动指南

## 5分钟快速上手

### 1. 环境准备 (1分钟)

```bash
# 确保Python版本
python --version  # 需要 3.10+

# 安装依赖
pip install -r requirements.txt
```

### 2. 安装Ollama (2分钟)

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: 下载安装包 https://ollama.com/download

# 启动Ollama服务
ollama serve

# 在另一个终端，拉取推荐模型
ollama pull qwen2.5:7b
```

### 3. 启动系统 (1分钟)

```bash
# 方式1: Gradio界面（推荐）
python main.py

# 方式2: 命令行模式
python main.py --cli
```

### 4. 开始使用 (1分钟)

**Gradio界面:**
1. 打开浏览器访问 `http://localhost:7860`
2. 点击"系统设置" → "初始化系统"
3. 切换到"对话"标签页
4. 开始聊天！

**命令行模式:**
```
你: 你好
AI: 你好！有什么可以帮助你的？

你: 什么是Python的GIL？
AI: GIL（Global Interpreter Lock）是Python的全局解释器锁...
```

## 常见问题

### Q: Ollama连接失败？

```bash
# 检查Ollama是否运行
curl http://localhost:11434/api/tags

# 如果没有响应，重新启动
ollama serve
```

### Q: 如何更换模型？

```bash
# 拉取新模型
ollama pull llama3.1:8b

# 修改配置
# 编辑 abyssac_config.json
{
  "llm": {
    "ollama_model": "llama3.1:8b"
  }
}
```

### Q: 如何使用API？

```json
// 编辑 abyssac_config.json
{
  "llm": {
    "use_local": false,
    "api_base_url": "https://api.siliconflow.cn/v1",
    "api_key": "your-api-key",
    "api_model": "deepseek-ai/DeepSeek-V2.5"
  }
}
```

### Q: DMN什么时候触发？

自动触发条件:
- 工作记忆 ≥ 20条
- 导航失败 > 5次
- 系统空闲 > 5分钟

手动触发:
- Gradio界面: "DMN维护"标签页
- 命令行: 输入 `dmn`

## 目录结构速览

```
AbyssAC/
├── main.py              # 主入口
├── requirements.txt     # 依赖
├── abyssac_config.json  # 配置文件
│
├── core/                # 核心模块
│   ├── config.py       # 配置管理
│   └── abyssac.py      # 主控制器
│
├── llm/                 # LLM接口
│   └── llm_interface.py
│
├── memory/              # Y层记忆
│   └── memory_manager.py
│
├── nng/                 # NNG导航
│   └── nng_manager.py
│
├── sandbox/             # X层沙盒
│   └── sandbox_layer.py
│
├── dmn/                 # DMN维护
│   └── dmn_agents.py
│
└── ui/                  # 前端界面
    └── gradio_app.py
```

## 核心概念速查

| 概念 | 说明 |
|------|------|
| **X层沙盒** | 三层处理流程：导航→筛选→组装 |
| **Y层记忆** | 四种记忆类型：元认知/高阶整合/分类/工作 |
| **NNG** | 导航节点图，层级化的知识索引 |
| **DMN** | 动态维护网络，5个子智能体自动维护 |
| **Bootstrap** | 三阶段启动流程 |

## 下一步

- 阅读 [README.md](README.md) 了解完整功能
- 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 了解架构设计
- 阅读 [EXAMPLES.md](EXAMPLES.md) 查看更多使用示例
