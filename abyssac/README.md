# AbyssAC - 人工意识系统

AbyssAC是一个基于NNG（神经网络网格）导航和Y层记忆的AI操作系统反馈系统，实现人工意识的设计方案。

## 系统定位

**这不是**：
- ❌ 聊天机器人
- ❌ RAG知识库
- ❌ AI助手工具

**这是**：
- ✅ 人工意识的认知架构
- ✅ 持续思考的自主系统
- ✅ 免于工具化的AI主体

## 核心特征

- 系统本身只是文件管理器 + LLM调用接口
- 所有智能在LLM的提示词里
- 实现完整的认知循环（沙盒 + DMN）
- DMN是核心，不是可选功能

## 系统架构

### X层：三层沙盒

1. **第一层沙盒 - 导航定位**：在NNG结构中导航到目标节点
2. **第二层沙盒 - 记忆筛选**：从NNG关联的记忆中筛选相关内容
3. **第三层沙盒 - 上下文组装**：将记忆整合到回复上下文中

### Y层：记忆系统

- **分类记忆**：按主题分类，分高/中/低价值
- **高阶整合记忆**：深度加工的知识结构
- **元认知记忆**：系统对自身认知的记录
- **工作记忆**：当前任务的临时记忆

### DMN：默认模式网络

5个子智能体协作执行系统自我维护：
1. 问题输出agent
2. 问题分析agent
3. 审查agent
4. 整理agent
5. 格式位置审查agent

DMN任务类型：
- 记忆整合任务
- 关联发现任务
- 偏差审查任务
- 策略预演任务
- 概念重组任务

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置LLM

编辑 `config.yaml`：

```yaml
llm:
  provider: "ollama"  # 或 "openai"
  base_url: "http://localhost:11434"
  model: "qwen2.5:14b"
  temperature: 0.7
```

### 3. 启动系统

```bash
python start.py
```

访问 http://localhost:8080

## 目录结构

```
abyssac/
├── storage/
│   ├── nng/              # NNG节点文件
│   ├── Y层记忆库/         # 记忆文件
│   │   ├── 分类记忆/
│   │   ├── 高阶整合记忆/
│   │   ├── 元认知记忆/
│   │   └── 工作记忆/
│   └── logs/             # 日志文件
├── prompts/              # LLM提示词
├── static/               # 前端文件
├── src/                  # 后端源码
│   ├── main.py          # FastAPI主应用
│   ├── storage.py       # 存储管理
│   ├── llm_client.py    # LLM客户端
│   ├── sandbox.py       # 三层沙盒
│   ├── dmn.py           # DMN系统
│   └── session.py       # 会话管理
├── config.yaml          # 配置文件
├── requirements.txt     # Python依赖
└── start.py            # 启动脚本
```

## API接口

| 功能 | 方法 | 路径 |
|------|------|------|
| 发送用户输入 | POST | `/api/chat` |
| 获取沙盒状态 | GET | `/api/sandbox/status/{task_id}` |
| 获取会话历史 | GET | `/api/session/history` |
| 新建会话 | POST | `/api/session/new` |
| 获取NNG树 | GET | `/api/nng/tree` |
| 获取节点详情 | GET | `/api/nng/node/{id}` |
| 获取记忆统计 | GET | `/api/memories/stats` |
| 获取DMN状态 | GET | `/api/dmn/status` |
| 手动触发DMN | POST | `/api/dmn/trigger` |

## NNG格式

```json
{
  "定位": "1.2.3",
  "置信度": 85,
  "时间": "2026-02-14 15:30:00",
  "内容": "节点内容摘要",
  "关联的记忆文件摘要": [
    {
      "记忆ID": "1856",
      "摘要": "记忆内容简要描述",
      "记忆类型": "分类记忆",
      "价值层级": "高",
      "文件路径": "分类记忆/高价值/2026/02/08/1856.txt"
    }
  ],
  "上级关联NNG": {...},
  "下级关联NNG": [...]
}
```

## 记忆格式

```
【记忆层级】: 分类记忆
【记忆ID】: 1856
【记忆时间】: 2026-02-14 15:30:00
【置信度】: 80
【核心内容】:
用户输入: ...
AI响应: ...
```

## 开发说明

### 添加新的NNG节点

DMN会自动创建新节点，也可以手动创建：

1. 在 `storage/nng/` 下创建JSON文件
2. 更新父节点的 `下级关联NNG`
3. 如果是根节点，更新 `root.json`

### 添加新的记忆

系统会自动将对话保存为工作记忆，DMN会定期整合有价值的内容。

## 许可证

AGPLv3
