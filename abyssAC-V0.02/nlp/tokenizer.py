import jieba
import jieba.posseg as pseg
import re
import logging
from typing import List, Tuple, Dict, Set
from pathlib import Path
from dataclasses import dataclass
from collections import Counter

@dataclass
class Token:
    """分词结果单元"""
    word: str
    pos: str  # 词性
    start: int  # 起始位置
    end: int    # 结束位置
    frequency: float = 1.0  # 词频/权重
    
    def __str__(self):
        return f"{self.word}/{self.pos}"

class AdvancedTokenizer:
    """高级中文分词器"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化jieba
        self._init_jieba()
        
        # 加载资源
        self.stopwords = self._load_stopwords()
        self.user_dict = self._load_user_dict()
        
        # 缓存频繁使用的词
        self.word_cache = {}
        self.cache_size = 1000
        
        # 统计信息
        self.stats = {
            "total_tokens": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def _init_jieba(self):
        """初始化jieba分词器"""
        # 设置词典路径
        if Path(self.config.kernel.dict_path).exists():
            jieba.load_userdict(self.config.kernel.dict_path)
            self.logger.info(f"已加载用户词典: {self.config.kernel.dict_path}")
        
        # 调整分词器参数
        jieba.dt.cache_file = None  # 禁用缓存文件
        jieba.dt.FREQ = {}  # 重置词频
        jieba.dt.total = 0
        
        # 启用并行分词
        jieba.enable_parallel(4)
    
    def _load_stopwords(self) -> Set[str]:
        """加载停用词表"""
        stopwords_path = Path(self.config.kernel.stopwords_path)
        stopwords = set()
        
        if stopwords_path.exists():
            try:
                with open(stopwords_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            stopwords.add(line)
                self.logger.info(f"已加载停用词表: {len(stopwords)} 个词")
            except Exception as e:
                self.logger.error(f"加载停用词表失败: {e}")
        
        # 添加默认停用词
        default_stopwords = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
            "都", "一", "个", "上", "也", "很", "到", "说", "要", "去"
        }
        stopwords.update(default_stopwords)
        
        return stopwords
    
    def _load_user_dict(self) -> Dict[str, float]:
        """加载用户词典"""
        user_dict = {}
        dict_path = Path(self.config.kernel.dict_path)
        
        if dict_path.exists():
            try:
                with open(dict_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split()
                            if len(parts) >= 1:
                                word = parts[0]
                                freq = float(parts[1]) if len(parts) > 1 else 10.0
                                user_dict[word] = freq
                self.logger.info(f"已加载用户词典: {len(user_dict)} 个词")
            except Exception as e:
                self.logger.error(f"加载用户词典失败: {e}")
        
        return user_dict
    
    def tokenize(self, text: str, 
                 use_pos: bool = True,
                 remove_stopwords: bool = True,
                 min_length: int = 1,
                 max_length: int = 20) -> List[Token]:
        """分词主函数"""
        
        # 检查缓存
        cache_key = f"{text}_{use_pos}_{remove_stopwords}_{min_length}_{max_length}"
        if cache_key in self.word_cache:
            self.stats["cache_hits"] += 1
            return self.word_cache[cache_key]
        
        self.stats["cache_misses"] += 1
        
        # 文本预处理
        text = self._preprocess_text(text)
        
        # 分词
        if use_pos:
            tokens = self._tokenize_with_pos(text)
        else:
            tokens = self._tokenize_simple(text)
        
        # 后处理
        tokens = self._postprocess_tokens(
            tokens, remove_stopwords, min_length, max_length
        )
        
        # 更新缓存
        if len(self.word_cache) >= self.cache_size:
            self.word_cache.pop(next(iter(self.word_cache)))
        self.word_cache[cache_key] = tokens
        
        self.stats["total_tokens"] += len(tokens)
        
        return tokens
    
    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        if not text or not isinstance(text, str):
            return ""
        
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符（保留中文、英文、数字、常用标点）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？；："\'、（）《》【】\s]', '', text)
        
        return text.strip()
    
    def _tokenize_with_pos(self, text: str) -> List[Token]:
        """带词性的分词"""
        tokens = []
        start = 0
        
        for word, pos in pseg.cut(text):
            end = start + len(word)
            token = Token(
                word=word,
                pos=pos,
                start=start,
                end=end,
                frequency=self.user_dict.get(word, 1.0)
            )
            tokens.append(token)
            start = end
        
        return tokens
    
    def _tokenize_simple(self, text: str) -> List[Token]:
        """简单分词"""
        tokens = []
        words = jieba.lcut(text)
        start = 0
        
        for word in words:
            end = start + len(word)
            token = Token(
                word=word,
                pos='',  # 空词性
                start=start,
                end=end,
                frequency=self.user_dict.get(word, 1.0)
            )
            tokens.append(token)
            start = end
        
        return tokens
    
    def _postprocess_tokens(self, tokens: List[Token], 
                           remove_stopwords: bool,
                           min_length: int,
                           max_length: int) -> List[Token]:
        """分词后处理"""
        filtered_tokens = []
        
        for token in tokens:
            # 长度过滤
            if len(token.word) < min_length or len(token.word) > max_length:
                continue
            
            # 停用词过滤
            if remove_stopwords and token.word in self.stopwords:
                continue
            
            # 数字过滤（纯数字）
            if token.word.isdigit():
                continue
            
            # 单字符过滤（除非是核心概念）
            if len(token.word) == 1 and token.word not in self.user_dict:
                continue
            
            filtered_tokens.append(token)
        
        return filtered_tokens
    
    def extract_keywords(self, text: str, 
                        top_k: int = 10,
                        use_tfidf: bool = False) -> List[Tuple[str, float]]:
        """提取关键词"""
        tokens = self.tokenize(text, use_pos=True, remove_stopwords=True)
        
        # 统计词频
        word_freq = Counter()
        for token in tokens:
            # 根据词性加权
            weight = self._get_pos_weight(token.pos) * token.frequency
            word_freq[token.word] += weight
        
        # 可选：使用TF-IDF（简化版）
        if use_tfidf:
            keywords = self._calculate_tfidf(word_freq, len(tokens))
        else:
            keywords = [(word, freq) for word, freq in word_freq.items()]
        
        # 排序并返回top_k
        keywords.sort(key=lambda x: x[1], reverse=True)
        return keywords[:top_k]
    
    def _get_pos_weight(self, pos: str) -> float:
        """根据词性分配权重"""
        pos_weights = {
            'n': 1.5,      # 名词
            'v': 1.2,      # 动词
            'a': 1.3,      # 形容词
            't': 1.1,      # 时间词
            's': 1.4,      # 处所词
            'nr': 1.6,     # 人名
            'ns': 1.5,     # 地名
            'nt': 1.4,     # 机构名
            'nz': 1.5,     # 其他专名
            'eng': 1.1,    # 英文
            'x': 0.5,      # 非语素字
            'm': 0.8,      # 数词
            'q': 0.8,      # 量词
            'd': 0.7,      # 副词
            'p': 0.6,      # 介词
            'c': 0.6,      # 连词
            'u': 0.5,      # 助词
            'e': 0.5,      # 叹词
            'y': 0.5,      # 语气词
            'o': 0.4,      # 拟声词
        }
        return pos_weights.get(pos, 1.0)
    
    def _calculate_tfidf(self, word_freq: Counter, total_words: int) -> List[Tuple[str, float]]:
        """计算TF-IDF（简化版）"""
        # 这里简化了IDF计算，实际应用中应该基于大语料库
        keywords = []
        for word, freq in word_freq.items():
            tf = freq / total_words if total_words > 0 else 0
            
            # 简化的IDF（假设常见词的IDF较低）
            word_length = len(word)
            if word_length <= 1:
                idf = 0.5
            elif word_length == 2:
                idf = 1.0
            else:
                idf = 1.5
            
            tfidf = tf * idf * 100  # 放大以便阅读
            keywords.append((word, tfidf))
        
        return keywords
    
    def segment_sentences(self, text: str) -> List[str]:
        """分句"""
        # 中文分句标点
        sentence_delimiters = r'[。！？；;!?\n]'
        sentences = re.split(sentence_delimiters, text)
        
        # 清理空句子
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "cache_size": len(self.word_cache),
            "stopwords_count": len(self.stopwords),
            "user_dict_count": len(self.user_dict)
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.word_cache.clear()
        self.stats["cache_hits"] = 0
        self.stats["cache_misses"] = 0

class TextAnalyzer:
    """文本分析器"""
    
    def __init__(self, tokenizer: AdvancedTokenizer):
        self.tokenizer = tokenizer
    
    def analyze_text(self, text: str) -> Dict:
        """综合分析文本"""
        # 分句
        sentences = self.tokenizer.segment_sentences(text)
        
        # 分词
        all_tokens = []
        sentence_tokens = []
        
        for sentence in sentences:
            tokens = self.tokenizer.tokenize(sentence)
            all_tokens.extend(tokens)
            sentence_tokens.append(tokens)
        
        # 提取关键词
        keywords = self.tokenizer.extract_keywords(text, top_k=15)
        
        # 计算文本特征
        features = {
            "char_count": len(text),
            "sentence_count": len(sentences),
            "token_count": len(all_tokens),
            "avg_sentence_length": len(all_tokens) / len(sentences) if sentences else 0,
            "unique_words": len(set(t.word for t in all_tokens)),
            "lexical_density": len(set(t.word for t in all_tokens)) / len(all_tokens) if all_tokens else 0,
        }
        
        # 词性分布
        pos_distribution = Counter(t.pos for t in all_tokens if t.pos)
        
        return {
            "sentences": sentences,
            "sentence_tokens": [[t.word for t in tokens] for tokens in sentence_tokens],
            "keywords": keywords,
            "features": features,
            "pos_distribution": dict(pos_distribution),
            "all_tokens": [t.word for t in all_tokens]
        }
    
    def calculate_text_complexity(self, text: str) -> float:
        """计算文本复杂度（0-1）"""
        analysis = self.analyze_text(text)
        
        # 基于多个特征计算复杂度
        features = analysis["features"]
        
        # 归一化特征
        char_complexity = min(features["char_count"] / 500, 1.0)
        lexical_complexity = min(features["lexical_density"] * 3, 1.0)
        sentence_complexity = min(features["sentence_count"] / 10, 1.0)
        
        # 加权平均
        complexity = (
            char_complexity * 0.3 +
            lexical_complexity * 0.4 +
            sentence_complexity * 0.3
        )
        
        return round(complexity, 3)
    
    def detect_core_concepts(self, text: str, core_concepts: Dict[str, List[str]]) -> Dict[str, float]:
        """检测核心概念匹配度"""
        analysis = self.analyze_text(text)
        text_words = set(analysis["all_tokens"])
        
        matches = {}
        for concept, keywords in core_concepts.items():
            # 计算匹配的关键词数量
            matched = sum(1 for kw in keywords if kw in text_words)
            matches[concept] = matched / len(keywords) if keywords else 0
        
        return matches