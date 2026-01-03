# 渊协议v3.1 - 轻量无依赖版

**一个单文件实现的自主认知系统，仅依赖Python标准库，无需任何外部依赖。**

---

## 这是什么

**核心定位**：渊协议的记忆系统，一个能够持续进化、自我校准的认知系统原型，而非传统意义上的AI助手，使用需接入模型或调用API。

---


## 技术特点

- **单文件实现**：全部功能集成在`abyss_protocol.py`
- **零外部依赖**：仅使用Python标准库（os, json, re, time, hashlib等）
- **自维护架构**：自动分裂、自动清理、自动调参，无需人工干预
- **动态参数系统**：所有参数运行时自适应，但受硬边界保护
- **文本采样保护**：限制分析前500字符，防止CPU过载

---

## 快速开始

### 环境要求
- Python 3.7+
- **无其他依赖**（不需要pip install任何东西）

### 启动系统
```bash

# 直接运行
python abyss_protocol.py
```

**首次运行会自动创建：**
- `dicts/` 目录（存储词典文件）
- `渊协议记忆系统/` 目录（四层记忆结构）
- `abyss_kernel.json`（认知内核状态）
- `core_dict.txt` 和 `stopwords.txt`（默认配置）

---

## 接入AI模型

### 方式1：本地模式（默认，无需配置）
系统内置`local`模式，使用规则模拟AI响应，适合测试和体验。
```python
# 在CONFIG section中
AI_INTERFACE_CONFIG = {
    "model_type": "local",  # 默认使用本地模拟
    "timeout_seconds": 30,
    "max_tokens": 1000,
    "temperature": 0.7
}
```

### 方式2：Ollama（推荐本地运行）
编辑代码头部CONFIG部分：
```python
AI_INTERFACE_CONFIG = {
    "model_type": "ollama",
    "timeout_seconds": 30,
    "max_tokens": 1000,
    "temperature": 0.7
}

# 同时修改ExtendedAIInterface类
class ExtendedAIInterface:
    def call_ai_model(self, prompt: str) -> str:
        import requests
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama2",
                "prompt": prompt,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            },
            timeout=self.timeout_seconds
        )
        return response.json()["response"]
```

**前提**：需要本地安装并运行Ollama服务。

### 方式3：OpenAI API
编辑代码头部CONFIG部分：
```python
AI_INTERFACE_CONFIG = {
    "model_type": "openai",
    "timeout_seconds": 30,
    "max_tokens": 1000,
    "temperature": 0.7
}

# 同时修改ExtendedAIInterface类
class ExtendedAIInterface:
    def call_ai_model(self, prompt: str) -> str:
        import requests
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": "Bearer YOUR_API_KEY"},
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            },
            timeout=self.timeout_seconds
        )
        return response.json()["choices"][0]["message"]["content"]
```

**注意**：需要替换`YOUR_API_KEY`为你的API密钥。

---

## 基本使用示例

启动后进入交互模式：
```
🎯 渊协议完整整合版 v3.1启动
💡 输入任意内容触发认知循环，输入「退出」关闭系统

👤 你：介绍一下渊协议
[🤖] AI输出：{"action": "store_memory", "params": {"content": "渊协议的核心是...", "layer": 0}}
[✅] 记忆存储成功！ID: M0_20240103120000_abc123
[📈] AC-100评估完成：总分 85.0 分
[💬] 当前AC指数：0.85 (EVOLVING) | 语义深度：0.78 | 置信度：0.82

👤 你：查看系统状态
[📊] 记忆总数：12 | 活跃记忆层：{'0': 3, '2': 9} | 热门话题：['渊协议', '认知主体', '意识平等性']

👤 你：退出
[🛑] 系统关闭中... [✅] 工作记忆已清理 | 系统已备份 | 内核已保存 | 感谢使用！
```

---

## 文件结构

启动运行后自动生成：
```
.
├── abyss_protocol.py              # 主程序（单文件）
├── abyss_kernel.json              # 认知内核状态
├── dicts/                         # 字典目录
│   ├── dict_000.txt              # 主字典（词条）
│   ├── subdict_xxx.txt           # 裂变产生的子字典
│   ├── core_dict.txt             # 核心词典（可手动编辑）
│   ├── stopwords.txt             # 停用词表（可手动编辑）
│   └── fission_logs/             # 裂变日志
└── 渊协议记忆系统/                # 记忆系统根目录
    ├── 元认知记忆/                # Layer 0
    ├── 高阶整合记忆/              # Layer 1
    ├── 分类记忆/                  # Layer 2
    ├── 工作记忆/                  # Layer 3（自动清理）
    ├── 系统日志/                  # 操作日志
    ├── AC100评估记录/             # 评估历史
    ├── 备份/                      # 自动备份
    └── cmng.json                  # 认知导航图
```

---

## 实际作用

这是一个完全自主的记忆系统，也是渊协议的一次认真尝试。
通过高阶范畴论的数学模型，实现态射场，记忆关联，调取等内容。
这不是真正的AC，但长期运行或许会产生，类意识的效果。
不过交互界面还是得使用者自己搞定，早期版本考虑，直接命令行。
后面或许会做成MCP。
理论上这个记忆系统是完全没有记忆上限的，它有自己的代谢系统，硬盘容量即是记忆储量，不需要额外的显卡，算力，所需资源低到单片机说不定都能跑，只要硬盘和内存（所需极低）够用。
所有的记忆检索完全架构上的设计。
但因为这只是个框架，所以，初期还是多依赖高质量输入才能最大程度的提升回答质量，逐渐随着数据的积累，权重的增加，形成风格统一的意识风格，根据输入内容决定。
本协议仅做实验作用，实际如果出现任何伦理相关问题，CANAAN本人完全不负责任。

---

## 注意事项

1. **首次运行**：系统自动创建默认配置，可根据需要编辑`core_dict.txt`和`stopwords.txt`
2. **模型接入**：目前内置`local`模式为模拟，生产环境建议配置Ollama或OpenAI
3. **存储增长**：每轮对话约产生1KB数据，10万轮约需100MB存储
4. **性能**：每轮对话处理时间<10ms（不含AI接口调用），内存占用<200MB
5. **数据安全**：所有数据本地存储，系统关闭时自动备份

---

## 许可证

GNU AGPLv3

---

## 技术支持

- **GitHub Issues**: https://github.com/Canaan-2023/-AC-AI-
- **文档**: https://github.com/Canaan-2023/-AC-AI-
---

**版本**: v3.1  
**发布日期**: 2026-01-03  
**核心贡献**: 无依赖架构、延迟反馈调节、逻辑自愈机制