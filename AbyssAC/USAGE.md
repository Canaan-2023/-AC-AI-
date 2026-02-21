# AbyssAC 使用指南

## 系统要求

- Python 3.8+
- LLM服务（如Ollama）
- 2GB+ 内存
- 500MB+ 磁盘空间

## 安装步骤

### 1. 克隆/下载项目

```bash
cd AbyssAC
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置LLM服务

#### 使用Ollama（推荐）

```bash
# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 启动服务
ollama serve

# 拉取模型（在另一个终端）
ollama pull llama3.1
```

#### 使用其他LLM服务

修改 `config/system_config.py` 中的LLM配置：

```python
@dataclass
class LLMConfig:
    api_base: str = "http://localhost:11434"  # 你的LLM API地址
    model_name: str = "llama3.1"               # 模型名称
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60
```

### 4. 初始化系统

```bash
python init_system.py
```

## 使用方法

### 命令行模式

#### 交互模式

```bash
python cli.py
```

进入交互模式后，你可以：
- 直接输入消息与AI对话
- 输入 `/slow` 切换到慢思考模式
- 输入 `/fast` 切换到快思考模式
- 输入 `/status` 查看系统状态
- 输入 `/dmn` 运行DMN维护
- 输入 `/help` 查看帮助
- 输入 `quit` 或 `exit` 退出

#### 单条消息

```bash
# 快速查询
python cli.py -c "你好"

# 慢思考模式（使用三层沙盒）
python cli.py --slow -c "详细解释什么是意识"
```

#### 系统管理

```bash
# 查看系统状态
python cli.py --status

# 运行DMN维护
python cli.py --dmn

# 列出NNG节点
python cli.py --list-nng

# 列出记忆
python cli.py --list-memories

# 创建NNG节点
python cli.py --create-nng "1.1" "子节点内容" "1"

# 导出记忆
python cli.py --export-memory "1" "memory_1.txt"
```

### GUI模式

```bash
python ui/main_window.py
```

GUI界面包含三个主要区域：

1. **左侧面板** - 数据浏览
   - NNG节点树
   - 记忆列表
   - 系统状态

2. **中间面板** - 聊天界面
   - 对话历史
   - 输入框
   - 慢思考切换

3. **右侧面板** - AI开发空间
   - 文件列表
   - 代码编辑器
   - 运行按钮

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Enter` | 发送消息 |
| `Ctrl+R` | 刷新数据 |
| `Ctrl+S` | 保存代码文件 |

## 核心概念

### NNG导航图

NNG（Navigation Network Graph）是系统的记忆索引结构：

- **root.json** - 根节点，包含所有一级节点
- **{node_id}.json** - 节点文件，包含内容和关联
- **层级结构** - 支持多级节点（如 1 → 1.1 → 1.1.1）

### Y层记忆库

记忆按类型和价值分类存储：

```
Y层记忆库/
├── 元认知记忆/        # 关于认知的认知
├── 高阶整合记忆/      # 深度整合的记忆
├── 分类记忆/
│   ├── 高价值/       # 重要记忆
│   ├── 中价值/       # 一般记忆
│   └── 低价值/       # 次要记忆
└── 工作记忆/          # 临时缓存
```

### 三层沙盒

慢思考系统的核心流程：

1. **NNG导航沙盒** - 在NNG树中定位相关概念
2. **记忆筛选沙盒** - 基于NNG摘要选择完整记忆
3. **上下文组装沙盒** - 整合信息生成结构化上下文

### DMN维护

默认模式网络，空闲时执行：

- 记忆整合
- 关联发现
- 偏差审查
- 策略预演
- 概念重组

## 开发指南

### 添加自定义NNG节点

```python
from core.main_system import get_system

system = get_system()
system.create_nng_node(
    node_id="4.1",
    content="自定义概念",
    parent_id="4"
)
```

### 手动创建记忆

```python
from core.memory_manager import get_memory_manager

mm = get_memory_manager()
memory_id = mm.create_memory(
    user_input="用户问题",
    ai_response="AI回答",
    memory_type="分类记忆",
    value_level="高价值",
    confidence=0.9
)
```

### 关联记忆到NNG

```python
system.link_memory_to_nng(
    memory_id="1",
    nng_node_id="1",
    summary="记忆摘要"
)
```

### 在沙箱中执行代码

```python
from core.ai_dev_space import get_sandbox

sandbox = get_sandbox()
result = sandbox.execute_code(
    code="print('Hello, World!')",
    language='python'
)

print(result.stdout)
```

## 配置说明

### 系统配置

编辑 `config/system_config.py`：

```python
# 路径配置
paths = PathConfig(
    nng_root_path="storage/nng/",
    memory_root_path="storage/Y层记忆库/",
    # ...
)

# 运行时参数
runtime = RuntimeConfig(
    max_nav_depth=10,           # 最大导航深度
    work_memory_threshold=20,   # 工作记忆阈值
    idle_time_threshold=300,    # 空闲时间阈值
    # ...
)
```

### 占位符系统

系统使用占位符动态替换：

- `{nng_root_path}` - NNG根目录
- `{memory_root_path}` - 记忆库路径
- `{current_timestamp}` - 当前时间戳
- `{memory_counter}` - 记忆计数器
- `{node_id}` - NNG节点ID
- `{memory_id}` - 记忆ID
- `{year}/{month}/{day}` - 当前日期

## 故障排除

### LLM连接失败

```
[错误] LLM调用失败
```

**解决方案：**
1. 检查Ollama是否运行：`ollama serve`
2. 检查API地址配置
3. 检查模型是否已下载：`ollama list`

### 模块导入错误

```
ModuleNotFoundError: No module named 'xxx'
```

**解决方案：**
```bash
pip install -r requirements.txt
```

### 权限错误

```
PermissionError: [Errno 13] Permission denied
```

**解决方案：**
```bash
chmod -R 755 storage/
```

## 性能优化

### 减少LLM调用次数

- 使用快思考系统缓存常见答案
- 调整 `work_memory_threshold` 减少DMN频率

### 优化导航深度

- 合理设计NNG层级结构
- 避免过深的节点嵌套（建议不超过5层）

### 定期维护

- 定期运行DMN维护
- 清理低价值记忆
- 合并重复节点

## 安全注意事项

1. **沙箱执行** - AI生成的代码在隔离环境中运行
2. **外部运行** - 需要用户明确授权
3. **数据备份** - 定期备份 `storage/` 目录
4. **API密钥** - 不要在代码中硬编码敏感信息

## 进阶用法

### 批量导入记忆

```python
import json

with open('memories.json', 'r') as f:
    memories = json.load(f)

for mem in memories:
    system.memory_manager.create_memory(**mem)
```

### 自定义DMN任务

```python
from core.dmn_system import get_dmn_system, DMNTaskType

dmn = get_dmn_system()
task = dmn.create_task(
    task_type=DMNTaskType.CONCEPT_REORG,
    priority=1,
    description="重组概念节点"
)
result = dmn.execute_task(task)
```

### 监控日志

```bash
# 实时查看导航日志
tail -f X层/navigation_logs/*.log

# 查看系统日志
tail -f logs/system.log
```

## 贡献指南

欢迎提交Issue和PR！

1. Fork项目
2. 创建分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -am 'Add xxx'`)
4. 推送分支 (`git push origin feature/xxx`)
5. 创建Pull Request

## 许可证

GNU AGPLv3 - 详见 LICENSE 文件
