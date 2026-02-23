"""提示词管理器模块"""

import os
import json
from typing import Dict, Any, Optional

class PromptManager:
    """提示词管理器类"""
    
    def __init__(self, prompts_file: str = 'prompts.json'):
        """初始化提示词管理器
        
        Args:
            prompts_file: 提示词配置文件路径
        """
        self.prompts_file = prompts_file
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, Any]:
        """加载提示词配置"""
        try:
            if os.path.exists(self.prompts_file):
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        
        return self._get_default_prompts()
    
    def _get_default_prompts(self) -> Dict[str, Any]:
        """获取默认提示词"""
        return {
            "system_prompt": "",
            "sandbox": {},
            "agents": {}
        }
    
    def save_prompts(self):
        """保存提示词配置"""
        try:
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return self.prompts.get('system_prompt', '')
    
    def set_system_prompt(self, prompt: str):
        """设置系统提示词"""
        self.prompts['system_prompt'] = prompt
        self.save_prompts()
    
    def get_sandbox_prompt(self, sandbox_type: str) -> Dict[str, Any]:
        """获取沙盒提示词
        
        Args:
            sandbox_type: 沙盒类型（nng_navigation/memory_filtering/context_assembly）
        """
        return self.prompts.get('sandbox', {}).get(sandbox_type, {})
    
    def get_agent_prompt(self, agent_type: str) -> Dict[str, Any]:
        """获取Agent提示词
        
        Args:
            agent_type: Agent类型
        """
        return self.prompts.get('agents', {}).get(agent_type, {})
    
    def build_sandbox_prompt(self, sandbox_type: str, context: str = "") -> str:
        """构建沙盒提示词
        
        Args:
            sandbox_type: 沙盒类型
            context: 上下文信息
        """
        prompt_config = self.get_sandbox_prompt(sandbox_type)
        
        if not prompt_config:
            return context
        
        role = prompt_config.get('role', '')
        task = prompt_config.get('task', '')
        output_format = prompt_config.get('output_format', '')
        rules = prompt_config.get('rules', [])
        
        prompt = f"""{role}

【任务】
{task}

【输出格式】
{output_format}

【规则】
"""
        for i, rule in enumerate(rules, 1):
            prompt += f"{i}. {rule}\n"
        
        if context:
            prompt += f"\n【上下文】\n{context}\n"
        
        return prompt
    
    def build_agent_prompt(self, agent_type: str, context: str = "") -> str:
        """构建Agent提示词
        
        Args:
            agent_type: Agent类型
            context: 上下文信息
        """
        prompt_config = self.get_agent_prompt(agent_type)
        
        if not prompt_config:
            return context
        
        role = prompt_config.get('role', '')
        task = prompt_config.get('task', '')
        output_format = prompt_config.get('output_format', '')
        rules = prompt_config.get('rules', [])
        
        prompt = f"""{role}

【任务】
{task}

【输出格式】
{output_format}

【规则】
"""
        for i, rule in enumerate(rules, 1):
            prompt += f"{i}. {rule}\n"
        
        if context:
            prompt += f"\n【上下文】\n{context}\n"
        
        return prompt
    
    def update_sandbox_prompt(self, sandbox_type: str, prompt_config: Dict[str, Any]):
        """更新沙盒提示词"""
        if 'sandbox' not in self.prompts:
            self.prompts['sandbox'] = {}
        self.prompts['sandbox'][sandbox_type] = prompt_config
        self.save_prompts()
    
    def update_agent_prompt(self, agent_type: str, prompt_config: Dict[str, Any]):
        """更新Agent提示词"""
        if 'agents' not in self.prompts:
            self.prompts['agents'] = {}
        self.prompts['agents'][agent_type] = prompt_config
        self.save_prompts()
    
    def get_all_prompts(self) -> Dict[str, Any]:
        """获取所有提示词"""
        return self.prompts
    
    def reset_to_default(self):
        """重置为默认提示词"""
        self.prompts = self._get_default_prompts()
        self.save_prompts()
