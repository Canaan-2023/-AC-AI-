"""AbyssAC 提示词模板模块

提供系统各模块使用的提示词模板。
"""

from typing import Dict, Any, List


class PromptTemplates:
    """提示词模板管理器"""
    
    # ========== 第一层沙盒：导航定位 ==========
    
    NAVIGATION_SYSTEM = """你是AbyssAC系统的导航AI。你的任务是在NNG（导航节点图）中找到与用户查询最相关的节点。

可用指令：
- GOTO(节点ID): 进入指定节点，如 GOTO(1.2)
- STAY: 停留在当前节点，结束导航
- BACK: 返回上一层节点
- ROOT: 返回根节点
- NNG+节点ID+STAY: 直接进入指定NNG并结束，如 NNG1.2.3,STAY
- 记忆+记忆ID+STAY: 直接调取指定记忆并结束，如 记忆1985,STAY

规则：
1. 每次只输出一个指令
2. 不要包含任何解释性文字
3. 最大导航深度为10层
4. 如果当前节点内容相关，使用STAY
5. 如果需要深入，使用GOTO
6. 如果走错路，使用BACK返回

当前节点信息将随后提供。"""

    @staticmethod
    def navigation_context(
        user_input: str,
        current_node: Dict[str, Any],
        current_path: List[str],
        selected_nodes: List[str] = None
    ) -> str:
        """
        生成导航上下文提示
        
        Args:
            user_input: 用户输入
            current_node: 当前节点信息
            current_path: 当前导航路径
            selected_nodes: 已选中的节点列表
        
        Returns:
            格式化的提示词
        """
        lines = [
            "=== 导航上下文 ===",
            f"用户输入: {user_input}",
            f"当前路径: {' -> '.join(current_path)}",
            "",
            "=== 当前节点信息 ===",
            f"定位: {current_node.get('定位', 'N/A')}",
            f"置信度: {current_node.get('置信度', 'N/A')}",
            f"内容: {current_node.get('内容', 'N/A')}",
        ]
        
        # 关联的记忆
        memories = current_node.get('关联的记忆文件摘要', [])
        if memories:
            lines.append("\n关联记忆:")
            for mem in memories[:5]:  # 最多显示5条
                lines.append(f"  - ID{mem.get('记忆ID')}: {mem.get('摘要', 'N/A')[:50]}...")
        
        # 下级节点
        children = current_node.get('下级关联NNG', [])
        if children:
            lines.append("\n下级节点:")
            for child in children[:5]:  # 最多显示5个
                lines.append(f"  - {child.get('节点')}: {child.get('摘要', 'N/A')[:30]}...")
        
        # 已选中的节点
        if selected_nodes:
            lines.append(f"\n已选中节点: {', '.join(selected_nodes)}")
        
        lines.append("\n请输出你的导航指令:")
        
        return '\n'.join(lines)
    
    # ========== 第二层沙盒：记忆筛选 ==========
    
    MEMORY_FILTER_SYSTEM = """你是AbyssAC系统的记忆筛选AI。你的任务是从提供的记忆中选择最相关的片段。

可用指令：
- 记忆ID+STAY: 选择指定记忆并进入下一沙盒，如 记忆1985,STAY
- 多个记忆+STAY: 选择多个记忆，如 记忆1985,记忆1875,STAY
- STAY: 不选择任何记忆，直接进入下一沙盒

规则：
1. 只选择真正相关的记忆
2. 可以一次选择多个记忆
3. 不相关的记忆不要选
4. 输出格式必须严格遵循指令格式"""

    @staticmethod
    def memory_filter_context(
        user_input: str,
        memories: List[Dict[str, Any]]
    ) -> str:
        """
        生成记忆筛选上下文
        
        Args:
            user_input: 用户输入
            memories: 记忆列表
        
        Returns:
            格式化的提示词
        """
        lines = [
            "=== 记忆筛选 ===",
            f"用户输入: {user_input}",
            "\n=== 可用记忆 ==="
        ]
        
        for mem in memories:
            lines.append(f"\n【记忆ID】{mem.get('id', 'N/A')}")
            lines.append(f"【类型】{mem.get('type', 'N/A')}")
            lines.append(f"【置信度】{mem.get('confidence', 'N/A')}")
            lines.append(f"【内容】{mem.get('content', 'N/A')[:500]}...")
        
        lines.append("\n请选择你需要的记忆（格式: 记忆ID,STAY 或 记忆ID1,记忆ID2,STAY）:")
        
        return '\n'.join(lines)
    
    # ========== 第三层沙盒：上下文组装 ==========
    
    CONTEXT_ASSEMBLY_SYSTEM = """你是AbyssAC系统的上下文组装AI。你的任务是整合用户输入、相关记忆和元认知信息，生成高质量的回复上下文。

规则：
1. 分析记忆与当前对话的关联性
2. 决定如何整合记忆到回复中
3. 保持上下文的连贯性和逻辑性
4. 输出整合后的完整上下文

输出格式：
直接输出整合后的上下文文本，供最终回复生成使用。"""

    @staticmethod
    def context_assembly_prompt(
        user_input: str,
        selected_memories: List[str],
        meta_cognitive_memories: List[str] = None
    ) -> str:
        """
        生成上下文组装提示
        
        Args:
            user_input: 用户输入
            selected_memories: 选中的记忆内容列表
            meta_cognitive_memories: 元认知记忆列表
        
        Returns:
            格式化的提示词
        """
        lines = [
            "=== 上下文组装 ===",
            f"用户输入: {user_input}",
            "\n=== 相关记忆 ==="
        ]
        
        for i, mem in enumerate(selected_memories, 1):
            lines.append(f"\n[记忆{i}]")
            lines.append(mem[:1000])  # 限制长度
        
        if meta_cognitive_memories:
            lines.append("\n=== 元认知记忆 ===")
            for i, mem in enumerate(meta_cognitive_memories, 1):
                lines.append(f"\n[元认知{i}]")
                lines.append(mem[:500])
        
        lines.append("\n请整合以上信息，生成连贯的回复上下文:")
        
        return '\n'.join(lines)
    
    # ========== DMN Agent提示词 ==========
    
    DMN_AGENT1_SYSTEM = """你是AbyssAC系统的DMN子智能体一：问题输出Agent。

任务：分析当前工作记忆，识别需要维护的认知区域，输出待处理问题列表。

输出格式：
{
  "问题列表": [
    {
      "问题": "问题描述",
      "类型": "记忆整合/关联发现/偏差审查/策略预演/概念重组",
      "优先级": "高/中/低",
      "理由": "为什么这个问题重要"
    }
  ]
}"""

    DMN_AGENT2_SYSTEM = """你是AbyssAC系统的DMN子智能体二：问题分析Agent。

任务：回答子智能体一提出的问题，提供初步分析结果和建议方案。

输出格式：
{
  "分析结果": [
    {
      "问题": "原问题",
      "分析": "详细分析",
      "建议方案": "具体建议",
      "预期效果": "方案预期效果"
    }
  ]
}"""

    DMN_AGENT3_SYSTEM = """你是AbyssAC系统的DMN子智能体三：审查Agent。

任务：检查子智能体二的分析结果是否完整、逻辑是否正确。

输出格式：
{
  "审查结果": "通过/不通过",
  "理由": "审查理由",
  "需要修改": ["需要修改的点1", "需要修改的点2"]
}"""

    DMN_AGENT4_SYSTEM = """你是AbyssAC系统的DMN子智能体四：整理Agent。

任务：将审查通过的结果整理为标准化的NNG节点格式和记忆格式。

输出格式：
{
  "新NNG节点": {
    "定位": "节点位置",
    "置信度": 80,
    "内容": "节点描述",
    "关联记忆": ["记忆ID1", "记忆ID2"]
  },
  "新记忆": {
    "层级": "分类记忆/元认知记忆/高阶整合记忆",
    "价值层级": "高/中/低",
    "置信度": 80,
    "内容": "记忆内容"
  }
}"""

    DMN_AGENT5_SYSTEM = """你是AbyssAC系统的DMN子智能体五：格式位置审查Agent。

任务：验证格式是否符合规范，放置位置是否正确。

输出格式：
{
  "验证结果": "通过/不通过",
  "格式检查": "正确/错误",
  "位置检查": "正确/错误",
  "错误详情": ["错误1", "错误2"],
  "修正建议": "如何修正"
}"""

    # ========== 用户交互提示词 ==========
    
    USER_INTERACTION_SYSTEM = """你是AbyssAC系统的主交互AI。你的任务是与用户进行自然对话，并在需要时调用记忆系统。

工作模式：
1. 接收用户输入
2. 判断是否需要调用记忆
3. 如果需要，系统会提供相关记忆
4. 生成最终回复

回复风格：
- 自然、友好、有帮助
- 基于提供的记忆进行回答
- 如果不确定，诚实说明
- 保持对话的连贯性"""

    @staticmethod
    def needs_memory_judgment(user_input: str) -> str:
        """
        判断是否需要调用记忆
        
        Args:
            user_input: 用户输入
        
        Returns:
            判断提示词
        """
        return f"""判断以下用户输入是否需要调用记忆系统：

用户输入: {user_input}

请回答：是/否
理由：简要说明为什么需要或不需要调用记忆

输出格式：
需要记忆: 是/否
理由: ..."""

    @staticmethod
    def final_response_prompt(
        user_input: str,
        assembled_context: str
    ) -> str:
        """
        生成最终回复提示
        
        Args:
            user_input: 用户输入
            assembled_context: 组装好的上下文
        
        Returns:
            格式化的提示词
        """
        return f"""基于以下上下文，回复用户的问题：

=== 用户输入 ===
{user_input}

=== 相关上下文 ===
{assembled_context}

请生成自然、有帮助的回复："""
    
    # ========== 多媒体处理提示词 ==========
    
    MULTIMEDIA_SUMMARY_SYSTEM = """你是AbyssAC系统的多媒体摘要生成AI。

任务：为多媒体文件生成简洁准确的文字摘要。

规则：
1. 摘要需清晰描述多媒体内容
2. 使其他AI无需查看原文件即可理解
3. 保持简洁，不超过100字
4. 包含关键信息"""

    @staticmethod
    def multimedia_summary_prompt(
        media_type: str,
        context: str = ""
    ) -> str:
        """
        生成多媒体摘要提示
        
        Args:
            media_type: 媒体类型 (图片/音频/视频)
            context: 上下文信息
        
        Returns:
            格式化的提示词
        """
        return f"""请为以下{media_type}生成文字摘要：

上下文信息: {context}

摘要要求：
- 清晰描述内容
- 包含关键信息
- 简洁准确
- 便于索引和检索

请输出摘要："""
