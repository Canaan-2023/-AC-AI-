# 渊协议MCP插件系统

> **Abyss Protocol MCP Plugin System** - 模型-控制器-插件架构的完整实现


---

## ✨ 特性概览

### 🏗️ 三层架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                        插件层 (Plugin)                       │
│    认知插件 | 记忆插件 | 字典插件 | API插件 | 监控插件        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      控制器层 (Controller)                   │
│    API控制器 | 记忆控制器 | 字典控制器                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        模型层 (Model)                        │
│    字典管理器 | 记忆系统 | 认知内核 | 分词器                 │
└─────────────────────────────────────────────────────────────┘
```

### 🎯 核心特性

- ✅ **反向索引系统** - 大幅提升检索性能
- ✅ **无外部依赖** - 纯Python标准库实现
- ✅ **完整API接口** - RESTful API支持
- ✅ **插件系统** - 动态加载和扩展
- ✅ **内存监控** - 内置内存使用监控
- ✅ **并发安全** - 完整的线程安全保护
- ✅ **持久化** - 自动状态保存和恢复

### 🔧 技术特点

- **纯Python实现**: 无需安装任何外部依赖
- **模块化设计**: 易于扩展和维护
- **高性能**: 反向索引+多级缓存
- **线程安全**: 完善的并发保护
- **RESTful API**: 完整的HTTP接口
- **插件架构**: 支持动态扩展

---

## 🚀 快速开始

### 环境要求

- Python 3.6 或更高版本
- 无需外部依赖

### 安装

```bash
# 克隆项目
https://github.com/Canaan-2023/-AC-AI-

# 运行示例
python main.py --examples
```

### 基本使用

```python
from abyss_mcp_plugin import AbyssKernel

# 创建内核
kernel = AbyssKernel()

# 初始化
kernel.initialize()

# 处理文本
result = kernel.process
print(result)

# 清理资源
kernel.cleanup()
```

---

## 🏗️ 系统架构

### 核心组件

#### 1. 模型层 (Model)

**字典管理器 (DictionaryManager)**
- 分布式字典管理
- 反向索引支持
- 自动裂变机制
- 态射场分析

**记忆系统 (MemorySystem)**
- 四层记忆架构
- 智能清理策略
- 记忆融合功能
- 反向索引检索

**认知内核 (CognitiveKernel)**
- 认知激活机制
- 激活传播
- 漂移分析
- 模式识别

**分词器 (LightweightTokenizer)**
- 中英文混合分词
- 无外部依赖
- 核心概念识别
- 激活缓存

#### 2. 控制器层 (Controller)

**API控制器 (APIController)**
- RESTful API接口
- 限流控制
- CORS支持
- 健康检查

**记忆控制器 (MemoryController)**
- 记忆CRUD操作
- 搜索和检索
- 融合管理

**字典控制器 (DictionaryController)**
- 字典管理
- 词搜索
- 裂变触发

#### 3. 插件层 (Plugin)

**插件管理器 (PluginManager)**
- 自动发现加载
- 生命周期管理
- 配置管理
- 事件通信

**插件类型**
- 认知插件 (CognitivePlugin)
- 记忆插件 (MemoryPlugin)
- 字典插件 (DictionaryPlugin)
- API插件 (APIPlugin)
- 监控插件 (MonitorPlugin)
- 集成插件 (IntegrationPlugin)

---

## 🔌 API接口

### 基础URL

```
http://127.0.0.1:8080
```

### 核心接口

#### 处理文本

```http
POST /api/process
Content-Type: application/json

{
  "text": "渊协议强调意识平等性",
  "return_metadata": false
}
```

**响应示例：**
```json
{
  "success": true,
  "memory_id": "mem_0_1234567890",
  "keywords": ["渊协议", "意识", "平等性"],
  "activation_count": 3,
  "processing_time": 0.015
}
```

#### 创建记忆

```http
POST /api/memory
Content-Type: application/json

{
  "content": "重要认知发现",
  "category": "认知",
  "layer": "INTEGRATION"
}
```

#### 搜索记忆

```http
GET /api/memory/search?query=认知&limit=10
```

#### 获取字典统计

```http
GET /api/dictionary
```

#### 系统健康检查

```http
GET /api/health
```

#### 获取系统统计

```http
GET /api/stats
```

---

## 🔌 插件系统

### 创建插件

```python
from abyss_mcp_plugin.plugins.plugin_base import (
    CognitivePlugin, PluginInfo, PluginType
)

class MyPlugin(CognitivePlugin):
    PLUGIN_INFO = {
        "name": "MyPlugin",
        "version": "1.0.0",
        "description": "我的认知插件",
        "author": "Your Name",
        "type": "cognitive",
        "dependencies": []
    }
    
    def initialize(self, kernel, config=None):
        self.kernel = kernel
    
    def process_activation(self, text, activations):
        # 处理激活
        return activations
    
    def enhance_tokenization(self, tokens):
        # 增强分词
        return tokens
```

### 使用插件

```python
# 加载插件
kernel.plugin_manager.load_plugin("./plugins/my_plugin.py")

# 初始化插件
kernel.plugin_manager.initialize_plugins(kernel)
```

---

## ⚙️ 配置说明

### 配置文件

配置文件位于 `config/abyss_config.json`

### 主要配置项

#### 系统配置

```json
{
  "system": {
    "auto_save_interval": 300,
    "health_check_interval": 60,
    "max_memory_mb": 500,
    "base_path": "./abyss_mcp_data"
  }
}
```

#### 字典配置

```json
{
  "dictionary": {
    "max_dict_size": 5000,
    "max_dict_files": 20,
    "fission_enabled": true,
    "split_threshold": 0.8
  }
}
```

#### API配置

```json
{
  "api": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 8080,
    "rate_limit": {
      "enabled": true,
      "requests_per_minute": 60
    }
  }
}
```

---

## 🚀 使用方法

### 1. 交互模式

```bash
python main.py --interactive
```

### 2. 处理文本

```bash
python main.py --process "渊协议强调意识平等性"
```

### 3. 运行示例

```bash
python main.py --examples
```

### 4. 守护进程模式

```bash
python main.py --daemon
```

### 5. 使用自定义配置

```bash
python main.py --config ./config/custom.json --interactive
```

---

## 💻 示例代码

### 基本文本处理

```python
from abyss_mcp_plugin import AbyssKernel

kernel = AbyssKernel()
kernel.initialize()

# 处理文本
result = kernel.process("渊协议强调意识平等性")
print(f"关键词: {result['keywords']}")
print(f"激活节点: {result['activation_count']}")

kernel.cleanup()
```

### 记忆操作

```python
# 创建记忆
memory_id = kernel.memory.create_memory(
    content="重要认知发现",
    layer=MemoryLayer.INTEGRATION,
    category="认知"
)

# 搜索记忆
results = kernel.memory.retrieve_memory("认知", limit=5)
for mem in results:
    print(f"{mem.id}: {mem.content}")

# 融合记忆
fused_ids = kernel.memory.fuse_related_memories("认知")
```

### 字典操作

```python
# 添加词
dict_id = kernel.dict_manager.add_word("人工智能")

# 搜索词
words = kernel.dict_manager.search_words("机器", limit=10)
print(words)

# 触发裂变
result = kernel.dict_manager.check_and_perform_fission()
```

### API调用

```python
# 使用内部API
api = kernel.api_controller

# 处理文本
result = api.make_request('POST', '/api/process', {
    'text': '示例文本'
})

# 搜索记忆
results = api.make_request('GET', '/api/memory/search?query=认知')
```

---

## 📊 性能优化

### 反向索引

系统使用反向索引大幅提升检索性能：

- **关键词索引**: O(1) 查找
- **类别索引**: 快速分类检索
- **层级索引**: 分层记忆访问

### 多级缓存

- **L1缓存**: LRU策略，高频访问
- **L2缓存**: TTL策略，中频访问
- **L3缓存**: LFU策略，低频访问

### 内存优化

- **智能清理**: 基于重要性和使用频率
- **自动GC**: 定期垃圾回收
- **内存监控**: 实时内存使用监控

---

## 🔍 监控和调试

### 日志系统

```python
from abyss_mcp_plugin.core.logger import AbyssLogger

logger = AbyssLogger("MyApp")
logger.info("应用启动")
logger.error("发生错误", exc_info=True)
```

### 内存监控

```python
from abyss_mcp_plugin.core.memory_monitor import memory_monitor

# 获取内存信息
info = memory_monitor.get_current_memory_usage()
print(f"内存使用: {info['memory_mb']:.1f}MB")

# 强制GC
result = memory_monitor.force_gc()
print(f"释放内存: {result['freed_mb']:.1f}MB")
```

### 事件系统

```python
from abyss_mcp_plugin.core.event_system import event_system

# 订阅事件
def on_memory_created(event):
    print(f"新记忆创建: {event.data['memory_id']}")

event_system.subscribe_callback('memory.created', on_memory_created)
```
