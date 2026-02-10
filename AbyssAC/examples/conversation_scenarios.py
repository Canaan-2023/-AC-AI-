"""AbyssAC 对话场景示例

展示系统在不同对话场景下的工作流程。
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def scenario_1_new_topic():
    """场景1: 讨论全新话题
    
    预期行为:
    1. 导航发现无相关节点
    2. 系统记录这次对话到工作记忆
    3. DMN后续可能创建新节点
    """
    print("=" * 60)
    print("场景1: 讨论全新话题")
    print("=" * 60)
    print()
    print("用户: 什么是量子计算？")
    print()
    print("系统处理流程:")
    print("  1. LLM判断需要记忆")
    print("  2. 进入第一层沙盒导航")
    print("     - 从root开始")
    print("     - 检查一级节点，无相关主题")
    print("     - STAY在root")
    print("  3. 第二层沙盒：无相关记忆")
    print("  4. 第三层沙盒：仅使用用户输入")
    print("  5. 生成回复（基于LLM内部知识）")
    print("  6. 保存到工作记忆")
    print()
    print("预期回复:")
    print("  AI: 量子计算是一种利用量子力学原理进行计算的技术...")
    print()
    print("后续DMN处理:")
    print("  - 检测到新主题'量子计算'")
    print("  - 可能创建新的一级节点")
    print("  - 将对话整理为分类记忆")
    print()


def scenario_2_related_topic():
    """场景2: 讨论相关话题
    
    预期行为:
    1. 导航到相关NNG节点
    2. 调取关联记忆
    3. 基于记忆生成回复
    """
    print("=" * 60)
    print("场景2: 讨论相关话题")
    print("=" * 60)
    print()
    print("假设已存在NNG结构:")
    print("  root")
    print("  └── 1 (技术知识)")
    print("      └── 1.1 (编程语言)")
    print("          └── 1.1.1 (Python)")
    print()
    print("用户: Python的GIL是什么？")
    print()
    print("系统处理流程:")
    print("  1. LLM判断需要记忆")
    print("  2. 进入第一层沙盒导航")
    print("     - root -> GOTO(1) [技术相关]")
    print("     - 1 -> GOTO(1.1) [编程语言]")
    print("     - 1.1 -> GOTO(1.1.1) [Python]")
    print("     - 1.1.1 -> STAY [找到相关节点]")
    print("  3. 第二层沙盒：调取节点关联记忆")
    print("     - 记忆123: Python基础介绍")
    print("     - 记忆124: Python性能优化")
    print("  4. 第三层沙盒：整合记忆和输入")
    print("  5. 生成回复")
    print()
    print("预期回复:")
    print("  AI: 根据我们之前的讨论，GIL（全局解释器锁）是Python...")
    print()


def scenario_3_multi_topic():
    """场景3: 多主题对话
    
    预期行为:
    1. 导航到多个不同节点
    2. 调取多组记忆
    3. 整合后回复
    """
    print("=" * 60)
    print("场景3: 多主题对话")
    print("=" * 60)
    print()
    print("假设已存在NNG结构:")
    print("  root")
    print("  ├── 1 (技术知识)")
    print("  │   └── 1.1 (编程语言)")
    print("  │       ├── 1.1.1 (Python)")
    print("  │       └── 1.1.2 (JavaScript)")
    print("  └── 2 (项目管理)")
    print("      └── 2.1 (敏捷开发)")
    print()
    print("用户: 结合我们之前讨论的Python和敏捷开发，谈谈技术选型")
    print()
    print("系统处理流程:")
    print("  1. LLM判断需要记忆")
    print("  2. 第一层沙盒：多节点导航")
    print("     - 第一次导航: root -> 1 -> 1.1 -> 1.1.1 [Python]")
    print("     - 询问是否继续: 是")
    print("     - 第二次导航: root -> 2 -> 2.1 [敏捷开发]")
    print("  3. 第二层沙盒：调取两组记忆")
    print("     - Python相关记忆")
    print("     - 敏捷开发相关记忆")
    print("  4. 第三层沙盒：整合多组记忆")
    print("  5. 生成综合回复")
    print()
    print("预期回复:")
    print("  AI: 结合我们之前对Python的讨论和敏捷开发实践...")
    print()


def scenario_4_follow_up():
    """场景4: 追问对话
    
    预期行为:
    1. 快速定位到上次的节点
    2. 调取相关记忆
    3. 深入回答
    """
    print("=" * 60)
    print("场景4: 追问对话")
    print("=" * 60)
    print()
    print("上下文: 之前讨论了Python的GIL")
    print()
    print("用户: 那有什么方法可以绕过GIL吗？")
    print()
    print("系统处理流程:")
    print("  1. LLM判断需要记忆（基于上下文）")
    print("  2. 第一层沙盒：快速导航")
    print("     - 可以直接定位到 1.1.1 (Python节点)")
    print("     - 或从上次导航终点继续")
    print("  3. 调取GIL相关记忆")
    print("  4. 整合后生成深入回复")
    print()
    print("预期回复:")
    print("  AI: 关于绕过GIL，有几种常见方法...")
    print("      1. 使用多进程代替多线程")
    print("      2. 使用C扩展")
    print("      3. 使用其他Python实现如Jython")
    print()


def scenario_5_no_memory_needed():
    """场景5: 不需要记忆的对话
    
    预期行为:
    1. LLM判断不需要记忆
    2. 直接生成回复
    3. 仍保存到工作记忆
    """
    print("=" * 60)
    print("场景5: 不需要记忆的对话")
    print("=" * 60)
    print()
    print("用户: 你好")
    print()
    print("系统处理流程:")
    print("  1. LLM判断不需要记忆")
    print("     - 简单问候不需要历史上下文")
    print("  2. 直接生成回复")
    print("  3. 保存到工作记忆（用于对话连贯性）")
    print()
    print("预期回复:")
    print("  AI: 你好！有什么可以帮助你的吗？")
    print()


def scenario_6_dmn_trigger():
    """场景6: DMN自动触发
    
    预期行为:
    1. 系统空闲超过阈值
    2. 自动触发DMN
    3. 整理工作记忆
    """
    print("=" * 60)
    print("场景6: DMN自动触发")
    print("=" * 60)
    print()
    print("触发条件:")
    print("  - 系统空闲 > 5分钟")
    print("  - 工作记忆 > 20条")
    print("  - 导航失败 > 5次")
    print()
    print("DMN处理流程:")
    print("  1. Agent 1: 问题输出")
    print("     - 分析工作记忆")
    print("     - 识别需要整理的内容")
    print("  2. Agent 2: 问题分析")
    print("     - 分析记忆间的关联")
    print("     - 提出整理方案")
    print("  3. Agent 3: 审查")
    print("     - 检查分析结果")
    print("  4. Agent 4: 整理")
    print("     - 创建新的NNG节点（如果需要）")
    print("     - 将工作记忆整理为分类记忆")
    print("  5. Agent 5: 格式审查")
    print("     - 验证格式正确")
    print("     - 写入系统")
    print()
    print("处理结果:")
    print("  - 工作记忆清空")
    print("  - 新增分类记忆")
    print("  - 可能新增NNG节点")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AbyssAC 对话场景示例")
    print("=" * 60 + "\n")
    
    scenario_1_new_topic()
    scenario_2_related_topic()
    scenario_3_multi_topic()
    scenario_4_follow_up()
    scenario_5_no_memory_needed()
    scenario_6_dmn_trigger()
    
    print("=" * 60)
    print("所有场景示例完成")
    print("=" * 60)
