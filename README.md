# AbyssAc Memory MCP

<div align="center">

**一个为AI助手设计的智能记忆管理系统**

[![Version](https://img.shields.io/badge/version-7.0.0-blue.svg)](https://github.com/Canaan-2023/AbyssAC)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-2024--11--05-purple.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-AGPLv3-red.svg)](LICENSE)

</div>

---

## 📍 定位

纯文件维持的LLM记忆系统，通过MCP协议为AI提供持久化记忆能力。

---

## ✨ 特性

### 🔒 步骤级验证
每个步骤执行后立即验证，确保正确性：
- 🔴 **必须通过** - 不通过必须回退
- 🟡 **应该通过** - 可选择回退或继续
- 🟢 **建议通过** - 记录问题，继续执行

### ⏪ 回退机制
验证不通过时自动返回上一步重做，支持无限回退链。

### 📝 禁止事项提示
每个步骤明确告诉AI不要做什么，避免常见错误。

### 💻 代码型NNG支持
为源代码创建记忆节点（NNG），支持：
- **文件级NNG** - 关联具体代码文件
- **过渡型NNG** - 文件夹级组织节点

### 🧠 智能缓存管理
- LLM决策，工具执行
- 动态淘汰/保护
- 分数参考，可override

### 📁 纯文件存储
无需数据库，所有记忆以文件形式存储，简单可靠。

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- 支持MCP协议的IDE（如Trae、Claude Desktop等）

### 安装

```bash
# 克隆仓库
git clone https://github.com/Canaan-2023/AbyssAC.git
cd AbyssAC/abyssac-memory-mcp
```

### 配置

1. 设置环境变量（可选）：
```bash
# Linux/macOS
export ABYSSAC_ROOT=~/.abyssac

# Windows PowerShell
$env:ABYSSAC_ROOT = "$HOME\.abyssac"
```

2. 在你的MCP客户端配置文件中添加：

```json
{
  "mcpServers": {
    "abyssac-memory": {
      "command": "python",
      "args": ["abyssac_memory_mcp.py"],
      "env": {
        "ABYSSAC_ROOT": "~/.abyssac",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

### 验证安装

```bash
python abyssac_memory_mcp.py
```

---

## 📖 使用指南

### 工作流概览

```
┌─────────────────────────────────────────────────────────────┐
│                      检索流程                                │
├─────────────────────────────────────────────────────────────┤
│  ENTRY → R1_1 → R1_2 → R2_1 → R2_2 → R2_3 → R2_4           │
│         ↓                                                   │
│  R3_1 → R3_2 → R3_3 → R3_4 → R4_1 → R4_2 → REVIEW_R → DONE │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    存储流程（记忆型）                         │
├─────────────────────────────────────────────────────────────┤
│  S1 → S2_1 → S2_2 → S2_3 → S3_1 → S3_2 → S3_3 → S3_4       │
│      → S4 → S5_1 → S6_1 → S6_2 → REVIEW_S → DONE           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    存储流程（代码型）                         │
├─────────────────────────────────────────────────────────────┤
│  S1 → S2_1 → S2_2 → S2_3 → S3_1 → C1 → C2 → C3 → C4 → C5   │
│      → REVIEW_C → DONE                                      │
└─────────────────────────────────────────────────────────────┘
```

### 步骤结构

每个步骤包含以下字段：

```python
{
    "step": "步骤名称",
    "cmd": "命令标识",
    "desc": "简短描述",
    "then": [...],      # 执行指令
    "not_do": [...],    # 禁止事项
    "verify": [...],    # 验证项
    "output": {...},    # 输出格式
    "prev": "上一步",   # 回退用
    "next": "下一步"    # 流程控制
}
```

### MCP工具

| 工具名 | 描述 |
|--------|------|
| `mcp_instruction` | 获取指定步骤的指令模板 |
| `list_steps` | 列出所有可用步骤 |
| `workflow_overview` | 获取工作流概览 |

---

## 📁 目录结构

```
abyssac-memory-mcp/
├── abyssac_memory_mcp.py   # 主程序
├── mcp.json                # MCP配置文件
├── README.md               # 说明文档
└── LICENSE                 # 许可证 (AGPLv3)
```

---

## 🔧 高级配置

### 环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `ABYSSAC_ROOT` | `~/.abyssac` | 数据存储根目录 |

### 自定义数据目录

```json
{
  "mcpServers": {
    "abyssac-memory": {
      "command": "python",
      "args": ["abyssac_memory_mcp.py"],
      "env": {
        "ABYSSAC_ROOT": "/your/custom/path",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

---

## 🎯 核心原则

1. **格式统一** - 只有ROOT节点特殊，其他所有NNG格式统一
2. **双向关联** - 父节点必须记录子节点，子节点必须记录父节点
3. **内容概要** - 下级关联必须有内容概要
4. **关系说明** - 上级关联必须有关系说明
5. **LLM判断** - 代码理解是LLM判断，不是机械提取
6. **质量优先** - 宁可少而精，不要多而空
7. **智能缓存** - 工具提供信息，LLM决策缓存管理
8. **分数参考** - 评估分数是参考，LLM可以override

---

## 📊 步骤统计

| 流程类型 | 步骤数 |
|----------|--------|
| 检索流程 | 16 |
| 存储流程（记忆型） | 18 |
| 存储流程（代码型） | 12 |
| **总计** | **46** |

---

## ⚖️ 许可证与商用授权

### 开源协议

本项目采用 **GNU Affero General Public License v3.0 (AGPLv3)** 开源协议。

### 规则

- 本项目所有使用行为需遵守 **GNU AGPLv3** 开源协议（详见项目根目录 LICENSE 文件）
- 若需豁免 AGPLv3 义务（如闭源商用、企业内网部署却不开源、不向用户提供源码）：**必须联系作者获取书面授权**

### 商用授权联系方式

- **唯一渠道**：CanaanMonika@foxmail.com
- 未经授权不得豁免义务商用
- 商用授权细节（费用/范围/权益）双方协商，无预设标准

### 免责声明

- 本协议仅提供技术参考，使用风险自负，作者不承担连带责任
- 最终解释权归作者所有

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

---

## 🔗 相关链接

- **主仓库**：[https://github.com/Canaan-2023/AbyssAC](https://github.com/Canaan-2023/AbyssAC)
- **MCP协议**：[https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)

---

<div align="center">

**Made with ❤️ by AbyssAc**

</div>
