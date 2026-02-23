"""问题分类器模块"""

from typing import Dict, Any, Tuple, Optional
import re


class QuestionClassifier:
    """问题分类器 - 判断问题应该由快思考还是慢思考处理"""
    
    SIMPLE_PATTERNS = [
        r'^(什么|是|有|在|谁|哪|几|多少|怎样|如何)\s*[？?]?$',
        r'^(是|不是|对|不对|可以|不可以)\s*[？?]?$',
        r'^(定义|解释|说明|介绍)\s+.+$',
        r'^.+(是什么|是什么意思|怎么读|怎么写)\s*[？?]?$',
        r'^.+(在哪里|在哪儿|是谁|叫什么)\s*[？?]?$',
    ]
    
    COMPLEX_PATTERNS = [
        r'(分析|比较|评估|设计|创建|开发|实现|优化|改进)',
        r'(为什么|原因|原理|机制|流程)',
        r'(如何|怎么).*?(实现|设计|开发|构建)',
        r'(优缺点|利弊|对比|区别)',
        r'(建议|推荐|方案|策略)',
        r'(如果|假设|假如|设想)',
    ]
    
    CREATIVE_PATTERNS = [
        r'(创作|编写|设计|发明|创造|想象)',
        r'(故事|小说|诗歌|文章|代码)',
        r'(新|创新|独特|原创)',
    ]
    
    def __init__(self, llm_integration=None):
        """初始化问题分类器
        
        Args:
            llm_integration: LLM集成（可选，用于复杂分类）
        """
        self.llm_integration = llm_integration
    
    def classify(self, question: str) -> Tuple[str, str, float]:
        """分类问题
        
        Args:
            question: 用户问题
            
        Returns:
            (问题类型, 复杂度, 置信度)
        """
        question = question.strip()
        
        if not question:
            return ('unknown', 'simple', 0.0)
        
        if self._match_patterns(question, self.SIMPLE_PATTERNS):
            return ('factual', 'simple', 0.9)
        
        if self._match_patterns(question, self.CREATIVE_PATTERNS):
            return ('creative', 'complex', 0.9)
        
        if self._match_patterns(question, self.COMPLEX_PATTERNS):
            return ('analytical', 'complex', 0.8)
        
        if len(question) < 10:
            return ('factual', 'simple', 0.7)
        
        if len(question) > 100:
            return ('analytical', 'complex', 0.6)
        
        question_type, complexity = self._analyze_structure(question)
        
        return (question_type, complexity, 0.6)
    
    def _match_patterns(self, question: str, patterns: list) -> bool:
        """匹配模式"""
        for pattern in patterns:
            if re.search(pattern, question, re.IGNORECASE):
                return True
        return False
    
    def _analyze_structure(self, question: str) -> Tuple[str, str]:
        """分析问题结构"""
        has_question_mark = '？' in question or '?' in question
        
        words = question.split()
        word_count = len(words)
        
        if word_count <= 5:
            return ('factual', 'simple')
        elif word_count <= 15:
            return ('factual', 'medium')
        else:
            return ('analytical', 'complex')
    
    def should_use_quick_thinking(self, question: str, has_quick_answer: bool = False) -> Tuple[bool, str]:
        """判断是否应该使用快思考
        
        Args:
            question: 用户问题
            has_quick_answer: 是否有快速答案
            
        Returns:
            (是否使用快思考, 原因)
        """
        question_type, complexity, confidence = self.classify(question)
        
        if question_type == 'creative':
            return (False, '创造性问题需要慢思考')
        
        if complexity == 'complex':
            return (False, '复杂问题需要慢思考')
        
        if complexity == 'simple' and question_type == 'factual':
            if has_quick_answer:
                return (True, '简单事实性问题，有快速答案')
            else:
                return (False, '简单问题但无快速答案，需要慢思考生成')
        
        if complexity == 'medium':
            if has_quick_answer:
                return (True, '中等复杂度问题，有快速答案')
            else:
                return (False, '中等复杂度问题，无快速答案')
        
        return (False, '默认使用慢思考')
    
    def classify_with_llm(self, question: str) -> Tuple[str, str, float]:
        """使用LLM进行更精确的分类
        
        Args:
            question: 用户问题
            
        Returns:
            (问题类型, 复杂度, 置信度)
        """
        if not self.llm_integration:
            return self.classify(question)
        
        prompt = f"""分析以下问题的类型和复杂度。

问题：{question}

请输出：
问题类型：[factual/analytical/creative]
复杂度：[simple/medium/complex]
置信度：[0.0-1.0]

只输出一行，格式：类型,复杂度,置信度"""
        
        try:
            response = self.llm_integration.generate(prompt)
            parts = response.strip().split(',')
            
            if len(parts) >= 3:
                question_type = parts[0].strip()
                complexity = parts[1].strip()
                confidence = float(parts[2].strip())
                
                valid_types = ['factual', 'analytical', 'creative']
                valid_complexities = ['simple', 'medium', 'complex']
                
                if question_type not in valid_types:
                    question_type = 'factual'
                if complexity not in valid_complexities:
                    complexity = 'medium'
                if confidence < 0 or confidence > 1:
                    confidence = 0.5
                
                return (question_type, complexity, confidence)
        except Exception:
            pass
        
        return self.classify(question)
