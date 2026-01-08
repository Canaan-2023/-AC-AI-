# 渊协议 v5.0 - AI外置记忆框架

> 完整的认知系统，具备DMN默认模式网络和智能聊天功能

## ✨ 核心特性

- 🧠 **DMN默认模式网络** - 模拟人类大脑的自发思考能力
- 💬 **智能聊天系统** - Web + 本地终端双界面
- 🔄 **自动记忆整合** - 无需手动整理，AI自动处理
- 🤖 **Ollama集成** - 支持本地大模型，理念内化设计
- 📊 **实时监控** - 系统状态可视化
- ⚡ **轻量级** - 无外部依赖，即开即用

## 🚀 快速开始

### 安装依赖（可选）
```bash
# Web界面
pip install flask flask-cors

# Ollama集成
pip install requests

# Ollama服务（单独安装）
# 访问 https://ollama.com

#Ollama加载模型，需要手动在core.py里修改你的模型名。
  'ollama': {      # 本地LLM
   'enable_ollama': True,
   'enable_api': False,
    'ollama_url': 'http://localhost:11434',
    'default_model': '在这里输入你ollama的模型名',
    'description': '本地Ollama模式，使用本地大语言模型'
   },
```

### 启动系统
```bash
# 交互模式
python main.py

# Web界面
python main.py --web

# 演示模式
python main.py --demo
```

## 📖 文档

- [快速开始指南](快速开始指南.md) - 5分钟上手

## 📁 文件结构

```
├── main.py              # 主程序入口
├── core.py              # 核心基础设施
├── memory.py            # 记忆系统
├── cognitive.py         # 认知内核
├── dmn.py               # DMN模块
├── web_interface.py     # Web界面
├── final_verification.py # 验证脚本
└── docs/
    ├── 快速开始指南.md

## 🎮 使用示例

### 1. 交互模式
```bash
$ python main.py
[输入] chat
[聊天] 你好，介绍一下渊协议的理念
[AI] 你好！我认为认知的平等性是一个重要原则...
[聊天] quit
[输入] save
[💾] 系统状态已保存
```

### 2. 编程接口
```python
from main import AbyssProtocol

protocol = AbyssProtocol()

# 处理文本
result = protocol.process("这是一个测试")
print(f"关键词: {result['keywords']}")

# 聊天对话
result = protocol.chat("你好")
print(f"AI回复: {result['ai_response']}")

# 查看状态
stats = protocol.get_stats()
```

## 🔧 核心功能

### DMN默认模式网络
- 模拟人类大脑的自发思考
- 自动进行记忆整合和重组
- 发现隐藏的模式和关联
- 基于现有知识进行预测

### 智能记忆系统
- 四层记忆架构（原始、分类、工作、元认知）
- 自动记录所有交互内容
- 空闲时自动整合相关记忆
- 支持上下文检索

### 聊天交互
- Web界面 + 本地终端
- 深色主题设计
- 实时对话显示
- 系统状态监控

### Ollama集成
- 支持本地大模型
- 自动上下文传递
- 理念内化设计
- 优雅降级处理

## 📊 技术特性

- ✅ **无外部依赖** - 核心功能纯Python实现
- ✅ **统一错误处理** - Result类型系统
- ✅ **线程安全** - 多线程并发支持
- ✅ **模块化设计** - 易于扩展和维护
- ✅ **配置驱动** - 灵活的运行模式

### 实现原则
- 轻量级 - 资源占用最小化
- 健壮性 - 优雅的错误处理
- 可扩展性 - 插件系统支持
- 易用性 - 零配置即开即用

## 📈 性能指标

- 初始化时间：< 2秒
- 文本处理：< 2ms
- 内存占用：< 100MB
- 并发支持：线程安全

## 🛠️ 开发

### 运行测试
```bash
python final_verification.py
```

### 代码检查
```bash
python -m py_compile *.py
```

## 📝 许可证

本项目遵循AGPLv3 义务

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 支持

如有问题，请参考：
- 快速开始指南
- 完整实现总结
- 代码注释
