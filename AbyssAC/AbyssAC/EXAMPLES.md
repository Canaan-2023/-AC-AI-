# AbyssAC 使用示例

## 示例1：基本对话

```python
from core.abyssac import AbyssAC
from core.config import get_config

# 初始化系统
config = get_config()
abyssac = AbyssAC(config)

# 开始对话
print(abyssac.chat("你好！请介绍一下自己"))
# 输出: 你好！我是AbyssAC，一个基于NNG导航和Y层记忆的AI系统...

print(abyssac.chat("Python的GIL是什么？"))
# 输出: GIL（Global Interpreter Lock）是Python的全局解释器锁...

print(abyssac.chat("如何优化Python的多线程性能？"))
# 输出: 由于GIL的存在，Python的多线程在CPU密集型任务上...
```

## 示例2：自定义配置

```python
from core.config import SystemConfig, LLMConfig, MemoryConfig, NNGConfig, DMNConfig
from core.abyssac import AbyssAC

# 创建自定义配置
config = SystemConfig(
    llm=LLMConfig(
        use_local=True,
        ollama_model="llama3.1:8b",  # 使用Llama 3.1
        temperature=0.8,
        max_tokens=2048
    ),
    memory=MemoryConfig(
        base_path="我的记忆库"
    ),
    nng=NNGConfig(
        base_path="我的NNG",
        max_navigation_depth=8
    ),
    dmn=DMNConfig(
        working_memory_threshold=15,  # 降低触发阈值
        navigation_failure_threshold=3
    )
)

# 使用自定义配置初始化
abyssac = AbyssAC(config)
```

## 示例3：使用API而非本地模型

```python
from core.config import SystemConfig, LLMConfig
from core.abyssac import AbyssAC

# 配置SiliconFlow API
config = SystemConfig(
    llm=LLMConfig(
        use_local=False,
        api_base_url="https://api.siliconflow.cn/v1",
        api_key="your-api-key-here",
        api_model="deepseek-ai/DeepSeek-V2.5",
        temperature=0.7
    )
)

abyssac = AbyssAC(config)
response = abyssac.chat("你好")
print(response)
```

## 示例4：手动管理记忆

```python
from memory.memory_manager import MemoryManager, MemoryType, ValueLevel

# 初始化记忆管理器
memory = MemoryManager()

# 保存不同类型的记忆
# 1. 工作记忆
entry1 = memory.save_memory(
    content="用户询问Python的GIL",
    memory_type=MemoryType.WORKING
)
print(f"保存工作记忆 #{entry1.id}")

# 2. 高价值分类记忆
entry2 = memory.save_memory(
    content="GIL（全局解释器锁）是Python解释器中的机制，确保同一时刻只有一个线程执行Python字节码...",
    memory_type=MemoryType.CLASSIFIED,
    value_level=ValueLevel.HIGH,
    nng_nodes=["1.2.3"]  # 关联到NNG节点
)
print(f"保存高价值记忆 #{entry2.id}")

# 3. 元认知记忆
entry3 = memory.save_memory(
    content="系统发现用户对Python性能优化感兴趣，应该重点关注相关主题",
    memory_type=MemoryType.META_COGNITION
)
print(f"保存元认知记忆 #{entry3.id}")

# 获取记忆
retrieved = memory.get_memory(entry2.id)
print(f"获取记忆: {retrieved.content[:50]}...")

# 获取工作记忆列表
working_mems = memory.get_working_memories(limit=5)
print(f"工作记忆数量: {len(working_mems)}")

# 更新记忆
memory.update_memory(entry2.id, "更新后的GIL解释...")

# 删除记忆
memory.delete_memory(entry1.id)
```

## 示例5：手动管理NNG

```python
from nng.nng_manager import NNGManager

# 初始化NNG管理器
nng = NNGManager()

# 检查NNG是否为空
print(f"NNG为空: {nng.is_nng_empty()}")

# 创建一级节点
node1 = nng.create_node("root", "Python编程语言")
print(f"创建节点: {node1}")

node2 = nng.create_node("root", "人工智能")
print(f"创建节点: {node2}")

# 创建二级节点
node1_1 = nng.create_node(node1, "Python基础语法")
print(f"创建节点: {node1_1}")

node1_2 = nng.create_node(node1, "Python性能优化")
print(f"创建节点: {node1_2}")

# 创建三级节点
node1_2_1 = nng.create_node(node1_2, "GIL全局解释器锁")
print(f"创建节点: {node1_2_1}")

# 获取节点信息
node = nng.get_node(node1_2_1)
print(f"节点内容: {node.内容}")
print(f"节点置信度: {node.置信度}")

# 获取子节点列表
children = nng.get_node_children_info(node1_2)
print(f"子节点: {[c['id'] for c in children]}")

# 添加记忆关联
nng.add_memory_to_node(
    node1_2_1,
    memory_id=123,
    summary="GIL详解内容",
    memory_type="分类记忆",
    value_level="高价值"
)

# 获取所有节点
all_nodes = nng.get_all_node_ids()
print(f"所有节点: {all_nodes}")

# 更新节点
nng.update_node(node1, 内容="Python编程（已更新）", 置信度=95)

# 删除节点（会递归删除所有子节点）
# nng.delete_node(node1_2_1)
```

## 示例6：手动触发DMN

```python
from core.abyssac import AbyssAC

abyssac = AbyssAC()

# 进行一些对话
for i in range(10):
    abyssac.chat(f"测试消息 {i+1}")

# 手动触发DMN任务
result = abyssac.manual_trigger_dmn("memory_integration")
print(result)
# 输出: DMN任务完成: 新建3条记忆, 2个NNG节点

# 触发NNG优化
result = abyssac.manual_trigger_dmn("nng_optimization")
print(result)

# 查看系统状态
status = abyssac.get_system_status()
print(f"工作记忆: {status['working_memory_count']}")
print(f"NNG节点: {status['nng_node_count']}")
print(f"最后DMN: {status['last_dmn_time']}")
```

## 示例7：导航失败处理

```python
from core.abyssac import AbyssAC

abyssac = AbyssAC()

# 模拟导航失败的情况
# 当导航失败次数超过阈值时，系统会自动触发DMN优化

# 查看导航失败计数
status = abyssac.get_system_status()
print(f"导航失败次数: {status['navigation_failures']}")

# 如果失败次数过多，手动触发优化
if status['navigation_failures'] >= 5:
    result = abyssac.manual_trigger_dmn("nng_optimization")
    print("已触发NNG优化")
```

## 示例8：批量导入记忆

```python
from memory.memory_manager import MemoryManager, MemoryType, ValueLevel

memory = MemoryManager()

# 批量导入知识
knowledge_items = [
    {
        "content": "Python列表推导式是一种简洁的创建列表的方式...",
        "type": MemoryType.CLASSIFIED,
        "value": ValueLevel.MEDIUM,
        "nng": "1.1"
    },
    {
        "content": "Python装饰器是一种高阶函数，用于修改函数行为...",
        "type": MemoryType.CLASSIFIED,
        "value": ValueLevel.HIGH,
        "nng": "1.1"
    },
    {
        "content": "Python生成器使用yield关键字，可以惰性求值...",
        "type": MemoryType.CLASSIFIED,
        "value": ValueLevel.HIGH,
        "nng": "1.1"
    }
]

for item in knowledge_items:
    entry = memory.save_memory(
        content=item["content"],
        memory_type=item["type"],
        value_level=item["value"],
        nng_nodes=[item["nng"]]
    )
    print(f"导入记忆 #{entry.id}")
```

## 示例9：自定义Gradio界面

```python
import gradio as gr
from core.abyssac import AbyssAC

# 初始化
abyssac = AbyssAC()

# 自定义界面
def custom_chat(message, history):
    response = abyssac.chat(message)
    history.append((message, response))
    return "", history

def get_status():
    status = abyssac.get_system_status()
    return f"""
    阶段: {status['bootstrap_stage']}
    对话数: {status['total_conversations']}
    工作记忆: {status['working_memory_count']}
    NNG节点: {status['nng_node_count']}
    """

# 创建界面
with gr.Blocks(title="我的AbyssAC") as demo:
    gr.Markdown("# 我的AbyssAC系统")
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=500)
            msg = gr.Textbox(label="输入消息")
            send = gr.Button("发送")
        
        with gr.Column(scale=1):
            status_btn = gr.Button("查看状态")
            status_text = gr.Textbox(label="系统状态", lines=5)
    
    send.click(custom_chat, [msg, chatbot], [msg, chatbot])
    msg.submit(custom_chat, [msg, chatbot], [msg, chatbot])
    status_btn.click(get_status, outputs=status_text)

demo.launch()
```

## 示例10：命令行交互

```bash
# 启动命令行模式
python main.py --cli

# 交互示例
你: 你好
AI: 你好！有什么可以帮助你的？

你: 什么是机器学习？
AI: 机器学习是人工智能的一个分支...

你: status
系统状态:
  bootstrap_stage: 阶段3_正常运行
  total_conversations: 2
  working_memory_count: 4
  nng_node_count: 3

你: dmn
DMN结果: DMN任务完成: 新建2条记忆, 1个NNG节点

你: quit
再见！
```

## 示例11：监控和日志

```python
import json
from pathlib import Path

# 读取导航日志
nav_logs_dir = Path("X层/navigation_logs")
for log_file in sorted(nav_logs_dir.glob("nav_*.jsonl")):
    with open(log_file, 'r') as f:
        for line in f:
            entry = json.loads(line)
            print(f"时间: {entry['时间戳']}")
            print(f"用户: {entry['用户输入']}")
            print(f"导航路径: {' -> '.join(entry['导航路径'])}")
            print(f"成功: {entry['成功']}")
            print("---")

# 读取DMN日志
dmn_logs_dir = Path("X层/dmn_logs")
for log_file in sorted(dmn_logs_dir.glob("dmn_*.jsonl")):
    with open(log_file, 'r') as f:
        for line in f:
            entry = json.loads(line)
            print(f"时间: {entry['timestamp']}")
            print(f"任务: {entry['task_type']}")
            print(f"新记忆: {entry['new_memories_count']}")
            print(f"新NNG: {entry['new_nng_nodes_count']}")
            print("---")
```

## 示例12：备份和恢复

```python
import shutil
from datetime import datetime

# 备份
def backup_abyssac():
    backup_dir = f"AbyssAC_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 备份记忆库
    shutil.copytree("Y层记忆库", f"{backup_dir}/Y层记忆库")
    
    # 备份NNG
    shutil.copytree("NNG", f"{backup_dir}/NNG")
    
    # 备份配置
    shutil.copy("abyssac_config.json", f"{backup_dir}/abyssac_config.json")
    
    print(f"备份完成: {backup_dir}")
    return backup_dir

# 恢复
def restore_abyssac(backup_dir):
    # 恢复记忆库
    shutil.copytree(f"{backup_dir}/Y层记忆库", "Y层记忆库", dirs_exist_ok=True)
    
    # 恢复NNG
    shutil.copytree(f"{backup_dir}/NNG", "NNG", dirs_exist_ok=True)
    
    # 恢复配置
    shutil.copy(f"{backup_dir}/abyssac_config.json", "abyssac_config.json")
    
    print("恢复完成")

# 使用
backup_path = backup_abyssac()
# restore_abyssac(backup_path)
```
