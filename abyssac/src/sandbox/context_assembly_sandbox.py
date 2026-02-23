"""上下文组装沙盒模块"""

from typing import Dict, Any, List

class ContextAssemblySandbox:
    """上下文组装沙盒类"""
    
    def __init__(self, llm_integration, config_manager=None):
        """初始化上下文组装沙盒"""
        self.llm_integration = llm_integration
        self.config_manager = config_manager
        
        self.max_length = 8192
    
    def process(self, memory_context: Dict[str, Any]) -> Dict[str, Any]:
        """处理记忆上下文"""
        prompt = self._generate_prompt(memory_context)
        
        response = self.llm_integration.generate(prompt)
        
        final_context = {
            'user_input': memory_context['user_input'],
            'nng_paths': memory_context['nng_paths'],
            'nng_contents': memory_context['nng_contents'],
            'memory_paths': memory_context['memory_paths'],
            'memory_contents': memory_context['memory_contents'],
            'response': response,
            'notes': memory_context.get('notes', ''),
            'confidence_assessment': self._assess_confidence(memory_context),
            'context_length': len(response) if response else 0
        }
        
        return final_context
    
    def _generate_prompt(self, context: Dict[str, Any]) -> str:
        """生成提示词"""
        user_input = context['user_input']
        nng_contents = context['nng_contents']
        memory_contents = context['memory_contents']
        notes = context.get('notes', '')
        
        nng_count = len([c for c in nng_contents.values() if isinstance(c, dict) and 'error' not in c])
        memory_count = len([c for c in memory_contents.values() if isinstance(c, dict) and 'error' not in c])
        
        prompt = f"""你是AbyssAC系统的上下文组装模块。请根据收集到的NNG节点和记忆文件，回答用户的问题。

【用户问题】
{user_input}

【收集到的NNG节点】（{nng_count}个）
{self._format_nng_contents(nng_contents)}

【收集到的记忆文件】（{memory_count}个）
{self._format_memory_contents(memory_contents)}

【导航笔记】
{notes if notes else '无'}

【输出要求】
1. 直接回答用户的问题，不要提及NNG或记忆文件的存在
2. 如果收集到的信息足够，给出完整、准确的回答
3. 如果信息不足，基于已有信息回答，并说明可能需要更多信息
4. 如果完全无法回答，诚实地说明原因
5. 回答要自然流畅，像正常对话一样

请直接回答用户的问题："""
        
        return prompt
    
    def _format_nng_contents(self, nng_contents: Dict[str, Any]) -> str:
        if not nng_contents:
            return "（无NNG节点）"
        
        formatted = []
        for path, content in nng_contents.items():
            if isinstance(content, dict) and 'error' not in content:
                content_str = str(content.get('内容', '无内容'))
                confidence = content.get('置信度', 0.0)
                location = content.get('定位', '')
                
                formatted.append(f"【{location}】置信度:{confidence:.2f}\n{content_str}")
        
        return '\n\n'.join(formatted) if formatted else "（无有效内容）"
    
    def _format_memory_contents(self, memory_contents: Dict[str, Any]) -> str:
        if not memory_contents:
            return "（无记忆文件）"
        
        formatted = []
        for path, content in memory_contents.items():
            if isinstance(content, dict) and 'error' not in content:
                core = content.get('核心内容', {})
                user_in = core.get('用户输入', '')
                ai_out = core.get('AI响应', '')
                confidence = content.get('置信度', 0.0)
                
                formatted.append(f"【历史对话】置信度:{confidence:.2f}\n用户: {user_in}\nAI: {ai_out}")
        
        return '\n\n'.join(formatted) if formatted else "（无有效内容）"
    
    def _assess_confidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """评估整体置信度"""
        nng_contents = context.get('nng_contents', {})
        memory_contents = context.get('memory_contents', {})
        
        nng_confidences = []
        for content in nng_contents.values():
            if isinstance(content, dict) and '置信度' in content:
                nng_confidences.append(content['置信度'])
        
        memory_confidences = []
        for content in memory_contents.values():
            if isinstance(content, dict) and '置信度' in content:
                memory_confidences.append(content['置信度'])
        
        avg_nng_confidence = sum(nng_confidences) / len(nng_confidences) if nng_confidences else 0
        avg_memory_confidence = sum(memory_confidences) / len(memory_confidences) if memory_confidences else 0
        
        total_count = len(nng_confidences) + len(memory_confidences)
        if total_count > 0:
            overall_confidence = (avg_nng_confidence * len(nng_confidences) + avg_memory_confidence * len(memory_confidences)) / total_count
        else:
            overall_confidence = 0
        
        thresholds = self._get_confidence_thresholds()
        
        if overall_confidence >= thresholds.get('high', 0.90):
            level = '高'
            strategy = 'direct_use'
        elif overall_confidence >= thresholds.get('medium_high', 0.70):
            level = '中高'
            strategy = 'use_with_other_info'
        elif overall_confidence >= thresholds.get('medium', 0.50):
            level = '中'
            strategy = 'use_after_verification'
        elif overall_confidence >= thresholds.get('medium_low', 0.30):
            level = '中低'
            strategy = 'use_with_caution'
        else:
            level = '低'
            strategy = 'do_not_use'
        
        return {
            'overall_confidence': overall_confidence,
            'nng_confidence': avg_nng_confidence,
            'memory_confidence': avg_memory_confidence,
            'nng_count': len(nng_confidences),
            'memory_count': len(memory_confidences),
            'level': level,
            'strategy': strategy
        }
    
    def _get_confidence_thresholds(self) -> Dict[str, float]:
        if self.config_manager:
            return self.config_manager.get_confidence_thresholds()
        return {
            'high': 0.90,
            'medium_high': 0.70,
            'medium': 0.50,
            'medium_low': 0.30,
            'low': 0.00
        }
    
    def get_context_summary(self, final_context: Dict[str, Any]) -> str:
        """获取上下文摘要"""
        summary_parts = []
        
        user_input = final_context.get('user_input', '')
        summary_parts.append(f"用户问题: {user_input[:100]}...")
        
        nng_count = len(final_context.get('nng_paths', []))
        memory_count = len(final_context.get('memory_paths', []))
        summary_parts.append(f"NNG节点: {nng_count}个")
        summary_parts.append(f"记忆文件: {memory_count}个")
        
        confidence = final_context.get('confidence_assessment', {})
        summary_parts.append(f"置信度: {confidence.get('level', '未知')} ({confidence.get('overall_confidence', 0):.2f})")
        
        return '\n'.join(summary_parts)
