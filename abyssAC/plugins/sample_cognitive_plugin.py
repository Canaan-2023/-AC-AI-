#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例认知插件

展示如何实现一个认知插件来增强系统的认知能力。
"""

from abyss_mcp_plugin.plugins.plugin_base import CognitivePlugin, PluginInfo, PluginType


class SampleCognitivePlugin(CognitivePlugin):
    """示例认知插件"""
    
    # 插件信息
    PLUGIN_INFO = {
        "name": "SampleCognitive",
        "version": "1.0.0",
        "description": "示例认知插件，增强关键词提取和激活",
        "author": "AbyssAC Team",
        "type": "cognitive",
        "dependencies": []
    }
    
    def __init__(self, info: PluginInfo):
        super().__init__(info)
        self.custom_keywords = {
            "AI": ["人工智能", "机器学习", "深度学习", "神经网络"],
            "哲思": ["意识", "认知", "思维", "反思", "元认知"],
            "技术": ["算法", "模型", "系统", "架构", "协议"]
        }
    
    def initialize(self, kernel, config: dict = None):
        """初始化插件"""
        self.kernel = kernel
        self.logger.info("示例认知插件初始化完成")
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("示例认知插件清理完成")
    
    def process_activation(self, text: str, activations: dict) -> dict:
        """处理认知激活"""
        # 增强激活结果
        enhanced_activations = activations.copy()
        
        # 检查文本中是否包含自定义关键词
        for category, keywords in self.custom_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    # 增强相关关键词的激活强度
                    enhanced_activations[keyword] = min(
                        enhanced_activations.get(keyword, 0) + 0.2,
                        1.0
                    )
        
        return enhanced_activations
    
    def enhance_tokenization(self, tokens: list) -> list:
        """增强分词结果"""
        enhanced_tokens = tokens.copy()
        
        # 添加相关词
        for token in tokens:
            for category, keywords in self.custom_keywords.items():
                if token in keywords:
                    # 添加同类别的其他关键词
                    for related in keywords:
                        if related not in enhanced_tokens and related != token:
                            enhanced_tokens.append(related)
        
        return enhanced_tokens