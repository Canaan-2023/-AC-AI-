"""
AbyssAC - 人工意识系统

基于NNG导航和Y层记忆的AI操作系统
"""

__version__ = "1.0.0"
__author__ = "AbyssAC Team"

from core.abyssac import AbyssAC
from core.config import get_config, SystemConfig

__all__ = ['AbyssAC', 'get_config', 'SystemConfig']
