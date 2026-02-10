# AbyssAC 快速开始指南

本指南帮助您在5分钟内启动并运行 AbyssAC 系统。

## 前提条件

1. Python 3.9 或更高版本
2. 本地 LLM 服务（推荐 Ollama）

## 安装步骤

### 1. 克隆/下载项目

```bash
cd AbyssAC
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 初始化系统

```bash
python setup.py
```

这将创建必要的目录结构和配置文件。

### 4. 配置 LLM

编辑 `config.json`，配置您的 LLM 服务：

**使用 Ollama（推荐）：**
```json
{
  "llm": {
    "api_type": "ollama",
    "base_url": "http://localhost:11434",
    "model": "qwen2.5:latest"
  }
}
```

**使用其他 OpenAI 兼容 API：**
```json
{
  "llm": {
    "api_type": "openai",
    "base_url": "https://api.example.com/v1",
    "model": "gpt-3.5-turbo"
  }
}
```

### 5. 启动 LLM 服务

如果使用 Ollama：

```bash
ollama run qwen2.5:latest
```

确保 Ollama 服务在后台运行。

### 6. 启动 AbyssAC

```bash
python main.py
```

## 基本使用

启动后，您会看到交互提示：

```
==================================================
AbyssAC 人工意识系统
输入 'exit' 或 'quit' 退出
输入 'stats' 查看统计
输入 'dmn' 手动触发DMN
==================================================

[用户] 
```

### 示例对话

```
[用户] 你好

[AI] 你好！有什么可以帮助你的吗？

[系统] 处理耗时: 0.52秒

[用户] 什么是Python的GIL？

[AI] Python的GIL（全局解释器锁）是一个机制...

[系统] 处理耗时: 3.21秒

[用户] stats

==================================================
系统统计
==================================================

记忆统计:
  总记忆数: 2
  按类型: {'工作记忆': 2}
  工作记忆: 2
  平均置信度: 70.0

NNG统计:
  总节点数: 0
  最大深度: 0
  平均置信度: 0

==================================================
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `exit` / `quit` / `退出` | 退出系统 |
| `stats` | 查看系统统计 |
| `dmn` | 手动触发 DMN 维护 |

## 系统工作原理

### 首次对话

1. 用户输入传递给 LLM
2. LLM 判断是否需要记忆
3. 需要则进入三层沙盒流程
4. 导航 NNG 找到相关节点
5. 调取关联记忆
6. 生成回复
7. 保存到工作记忆

### DMN 自动维护

当满足以下条件时，DMN 自动触发：
- 系统空闲超过 5 分钟
- 工作记忆超过 20 条
- 导航失败超过 5 次

DMN 会：
1. 分析工作记忆
2. 整理有价值内容
3. 创建新的 NNG 节点
4. 将工作记忆转为分类记忆

## 故障排查

### 问题：无法连接到 LLM

**症状：**
```
LLM调用失败: 请求错误: Connection refused
```

**解决：**
1. 检查 LLM 服务是否运行
2. 检查 `config.json` 中的 `base_url` 是否正确
3. 测试连接：
   ```bash
   curl http://localhost:11434/api/tags
   ```

### 问题：导航总是失败

**症状：**
```
导航失败: 达到最大导航深度
```

**解决：**
1. 这是正常现象，NNG 从空开始生长
2. 系统会自动创建工作记忆
3. DMN 会在适当时机创建 NNG 节点

### 问题：权限错误

**症状：**
```
文件写入错误: Permission denied
```

**解决：**
```bash
chmod -R 755 storage/
```

## 下一步

- 阅读 [README.md](README.md) 了解详细文档
- 查看 [examples/](examples/) 中的使用示例
- 运行测试：`python -m pytest tests/`

## 性能优化建议

1. **使用更快的模型**：如 qwen2.5:7b 代替更大的模型
2. **调整导航深度**：降低 `max_navigation_depth` 减少 LLM 调用
3. **关闭 DMN 自动触发**：设置 `dmn_auto_trigger: false`

## 获取帮助

如有问题，请：
1. 查看日志：`storage/system/logs/`
2. 检查配置文件格式
3. 确保 LLM 服务正常运行

---

**享受您的 AbyssAC 之旅！**
