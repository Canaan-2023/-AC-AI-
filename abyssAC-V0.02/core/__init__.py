#!/usr/bin/env python3
"""
渊协议核心模块
"""

from .cognitive_kernel import CognitiveKernelV12
from .memex import MemexA
from .ai_interface import ExtendedAIInterface
from .x_layer import XLayer
from .topology import CognitiveTopologyManager
from .evaluator import AC100Evaluator
from .iteration import EndogenousIterationEngine
from .abyss_core import AbyssAC

__all__ = [
    "CognitiveKernelV12",
    "MemexA", 
    "ExtendedAIInterface",
    "XLayer",
    "CognitiveTopologyManager", 
    "AC100Evaluator",
    "EndogenousIterationEngine",
    "AbyssAC"
]