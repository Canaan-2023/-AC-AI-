# AbyssAC 项目总结

## 项目概述

**AbyssAC** 是一个基于NNG导航和Y层记忆的AI操作系统，实现了LLM与记忆系统的协同工作，形成闭环反馈。

### 核心创新

1. **三层沙盒机制**: 导航定位 → 记忆筛选 → 上下文组装
2. **自由生长的NNG**: 不预设任何结构，从空系统开始自由演化
3. **Bootstrap流程**: 三阶段启动，从简单到复杂的渐进式初始化
4. **DMN维护网络**: 5个子智能体自动维护记忆和知识结构
5. **故障恢复机制**: 导航失败时自动降级处理

## 技术栈

- **语言**: Python 3.10+
- **LLM**: Ollama (本地) / OpenAI兼容API
- **前端**: Gradio
- **依赖**: requests, gradio (标准库优先)

## 项目结构

```
AbyssAC/
├── main.py                  # 主入口 (CLI + UI)
├── requirements.txt         # 依赖
├── abyssac_config.json      # 配置文件
│
├── core/                    # 核心模块
│   ├── config.py           # 配置管理
│   └── abyssac.py          # 主控制器
│
├── llm/                     # LLM接口
│   └── llm_interface.py    # Ollama/API支持
│
├── memory/                  # Y层记忆
│   └── memory_manager.py   # 记忆管理
│
├── nng/                     # NNG导航
│   └── nng_manager.py      # 导航图管理
│
├── sandbox/                 # X层沙盒
│   └── sandbox_layer.py    # 三层沙盒
│
├── dmn/                     # DMN维护
│   └── dmn_agents.py       # 5个子智能体
│
└── ui/                      # 前端界面
    └── gradio_app.py       # Gradio界面
```

## 核心模块说明

### 1. Config (配置管理)
- 支持JSON配置文件
- 默认配置自动生成
- 运行时配置更新

### 2. MemoryManager (Y层记忆)
- 四种记忆类型: 元认知/高阶整合/分类/工作
- 时间分类存储: YYYY/MM/DD
- 价值分级: 高/中/低
- 线程安全的ID计数器

### 3. NNGManager (NNG导航)
- 层级JSON结构
- 从root自由生长
- 支持无限层级节点
- 记忆关联索引

### 4. SandboxLayer (X层沙盒)
- **第一层**: 导航定位，LLM自主决策GOTO/STAY/BACK
- **第二层**: 记忆筛选，基于NNG关联选择相关记忆
- **第三层**: 上下文组装，整合记忆生成结构化上下文

### 5. DMNAgents (DMN维护)
- **Agent 1**: 问题识别
- **Agent 2**: 问题分析
- **Agent 3**: 结果审查
- **Agent 4**: 内容整理
- **Agent 5**: 格式审查

### 6. LLMInterface (LLM接口)
- Ollama本地模型支持
- OpenAI兼容API支持
- 自动检测可用服务
- 上下文管理

### 7. AbyssAC (主控制器)
- Bootstrap流程管理
- DMN触发判断
- 系统状态监控
- 导航失败处理

## Bootstrap三阶段

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

## DMN触发条件

- 工作记忆 ≥ 20条
- 导航失败 > 5次
- 系统空闲 > 5分钟
- 用户手动触发

## 导航失败处理

1. **记录失败**: 增加导航失败计数器
2. **记录日志**: 详细日志供DMN分析
3. **降级处理**: 跳过记忆筛选，直接回复
4. **自动优化**: 失败≥5次触发NNG优化DMN

## 使用方式

### Gradio界面 (推荐)
```bash
python main.py
# 访问 http://localhost:7860
```

### 命令行模式
```bash
python main.py --cli
```

### Python API
```python
from core.abyssac import AbyssAC

abyssac = AbyssAC()
response = abyssac.chat("你好")
print(response)
```

## 测试报告

| 模块 | 状态 |
|------|------|
| core/config.py | ✅ 通过 |
| memory/memory_manager.py | ✅ 通过 |
| nng/nng_manager.py | ✅ 通过 |
| llm/llm_interface.py | ✅ 通过 |
| sandbox/sandbox_layer.py | ✅ 通过 |
| dmn/dmn_agents.py | ✅ 通过 |
| core/abyssac.py | ✅ 通过 |

**总体状态**: ✅ 所有模块测试通过

## 文档列表

- **README.md**: 完整使用指南
- **QUICKSTART.md**: 5分钟快速上手
- **ARCHITECTURE.md**: 架构详解
- **EXAMPLES.md**: 使用示例
- **TEST_REPORT.md**: 测试报告
- **PROJECT_SUMMARY.md**: 项目总结

## 推荐的LLM模型

| 模型 | 参数 | 用途 |
|------|------|------|
| Qwen2.5 | 7B | 通用推荐 |
| Llama 3.1 | 8B | 英文任务 |
| Mistral | 7B | 代码任务 |
| Gemma 2 | 9B | 轻量级 |

## 便宜的API选项

- **SiliconFlow (硅基流动)**: 国产开源模型
- **OpenRouter**: 多模型聚合
- **Google AI Studio**: Gemini免费额度

## 后续优化方向

1. **向量检索**: 为记忆添加向量索引，支持语义搜索
2. **多模态支持**: 图片、音频、视频记忆
3. **分布式部署**: 支持多实例共享记忆
4. **可视化界面**: NNG结构可视化
5. **性能优化**: 大规模记忆的快速检索

## 许可证

MIT License

## 致谢

- 设计灵感：基于人工意识理论
- LLM支持：Ollama、DeepSeek、Qwen等开源模型

---

**AbyssAC** - 让AI拥有真正的记忆 🧠
