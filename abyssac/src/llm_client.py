"""
AbyssAC LLM客户端模块
处理与LLM的通信
"""

import httpx
import yaml
from typing import Optional, Dict, Any, List, AsyncGenerator
import json
import re

# 获取项目根目录
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent

# 加载配置
config_path = PROJECT_ROOT / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        CONFIG = yaml.safe_load(f)
else:
    CONFIG = {
        "llm": {
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "qwen2.5:14b",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 30
        },
        "sandbox": {
            "max_navigation_depth": 10,
            "navigation_timeout": 30,
            "max_retries": 1
        }
    }

LLM_CONFIG = CONFIG["llm"]


class LLMClient:
    """LLM客户端"""
    
    def __init__(self):
        self.provider = LLM_CONFIG["provider"]
        self.base_url = LLM_CONFIG["base_url"]
        self.model = LLM_CONFIG["model"]
        self.temperature = LLM_CONFIG["temperature"]
        self.max_tokens = LLM_CONFIG["max_tokens"]
        self.timeout = LLM_CONFIG["timeout"]
    
    async def chat(self, messages: List[Dict[str, str]], 
                   temperature: Optional[float] = None) -> str:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表，格式 [{"role": "user/system/assistant", "content": "..."}]
            temperature: 可选的温度参数
        
        Returns:
            LLM的回复文本
        """
        temp = temperature if temperature is not None else self.temperature
        
        if self.provider == "ollama":
            return await self._chat_ollama(messages, temp)
        elif self.provider == "openai":
            return await self._chat_openai(messages, temp)
        else:
            raise ValueError(f"不支持的LLM provider: {self.provider}")
    
    async def _chat_ollama(self, messages: List[Dict[str, str]], 
                           temperature: float) -> str:
        """使用Ollama API"""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")
            except httpx.TimeoutException:
                return "ERROR:TIMEOUT"
            except Exception as e:
                return f"ERROR:{str(e)}"
    
    async def _chat_openai(self, messages: List[Dict[str, str]], 
                           temperature: float) -> str:
        """使用OpenAI API"""
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
            except httpx.TimeoutException:
                return "ERROR:TIMEOUT"
            except Exception as e:
                return f"ERROR:{str(e)}"
    
    async def chat_stream(self, messages: List[Dict[str, str]], 
                          temperature: Optional[float] = None) -> AsyncGenerator[str, None]:
        """流式聊天请求"""
        temp = temperature if temperature is not None else self.temperature
        
        if self.provider == "ollama":
            async for chunk in self._chat_ollama_stream(messages, temp):
                yield chunk
        else:
            # 非流式回退
            response = await self.chat(messages, temp)
            yield response
    
    async def _chat_ollama_stream(self, messages: List[Dict[str, str]], 
                                  temperature: float) -> AsyncGenerator[str, None]:
        """Ollama流式API"""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue


class PromptLoader:
    """提示词加载器"""
    
    @staticmethod
    def load_prompt(prompt_name: str, **kwargs) -> str:
        """
        加载并格式化提示词
        
        Args:
            prompt_name: 提示词文件名（不含.txt）
            **kwargs: 占位符替换值
        
        Returns:
            格式化后的提示词
        """
        prompt_file = PROJECT_ROOT / f"prompts/{prompt_name}.txt"
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt = f.read()
            
            # 替换占位符
            for key, value in kwargs.items():
                placeholder = f"{{{key}}}"
                prompt = prompt.replace(placeholder, str(value))
            
            return prompt
        except FileNotFoundError:
            # 返回默认提示词
            return PromptLoader._get_default_prompt(prompt_name, **kwargs)
    
    @staticmethod
    def _get_default_prompt(prompt_name: str, **kwargs) -> str:
        """获取默认提示词"""
        defaults = {
            "sandbox_layer1": """你是AbyssAC系统的第一层沙盒，负责在NNG结构中导航定位。

【当前状态】
用户输入：{user_input}
当前位置：{current_position}
导航路径：{navigation_path}
当前深度：{depth}/10

【当前节点内容】
{nng_content}

【可用指令】
- GOTO(节点ID)：进入某个子节点
  示例：GOTO(2) 进入节点2
- STAY：停留在当前节点，结束导航
- BACK：返回上一层
- ROOT：回到根目录
- NNG节点ID,STAY：直接定位到指定节点
  示例：NNG2.3.5,STAY

【重要规则】
1. 节点ID是动态的，根据实际NNG结构决定
2. 不要硬编码任何具体的节点ID
3. 只输出一条指令，不要附加解释

请输出你的决策：""",
            
            "sandbox_layer2": """你是AbyssAC系统的第二层沙盒，负责筛选相关记忆。

【当前状态】
用户输入：{user_input}
当前NNG节点：{current_nng}

【候选记忆摘要】
{memories_list}

【可用指令】
- 记忆ID,STAY：选中指定记忆并进入下一沙盒
  示例：记忆1856,STAY
- 记忆ID1,记忆ID2,STAY：选中多个记忆
  示例：记忆1856,记忆1888,STAY
- STAY：不选任何记忆，直接进入下一沙盒

请输出你的决策：""",
            
            "sandbox_layer3": """你是AbyssAC系统的第三层沙盒，负责组装上下文。

【当前状态】
用户输入：{user_input}

【选中的记忆内容】
{selected_memories}

【当前对话上下文】
{context_history}

【任务】
1. 分析记忆与用户输入的关联性
2. 将记忆内容自然地整合到回复上下文中
3. 生成结构化的上下文供最终回复使用

请输出整合后的上下文（无需生成最终回复）：""",
            
            "dmn_agent1": """你是AbyssAC DMN的问题输出智能体。

【当前状态】
任务类型：{task_type}
工作记忆数量：{working_memory_count}
导航失败次数：{navigation_failures}

【工作记忆摘要】
{work_memories}

【任务】
根据当前工作记忆和系统状态，识别需要维护的认知区域，输出待处理问题列表。

请输出问题列表（每条一行）：""",
            
            "dmn_agent2": """你是AbyssAC DMN的问题分析智能体。

【任务类型】
{task_type}

【待处理问题】
{questions}

【工作记忆】
{work_memories}

【任务】
分析问题并给出初步分析结果和建议方案。

请输出分析结果：""",
            
            "dmn_agent3": """你是AbyssAC DMN的审查智能体。

【任务类型】
{task_type}

【分析结果】
{analysis_result}

【审查标准】
1. 分析是否完整？
2. 逻辑是否正确？
3. 建议是否可行？

【输出格式】
- 如果完整正确：输出 "APPROVED"
- 如果有问题：输出 "REJECTED: 具体问题说明"

请输出审查结果：""",
            
            "dmn_agent4": """你是AbyssAC DMN的整理智能体。

【任务类型】
{task_type}

【审查通过的分析结果】
{analysis_result}

【任务】
将结果整理为标准格式：
1. NNG JSON格式（如需新增/修改NNG）
2. 记忆文件格式（如需新增记忆）

可用指令：
- 新增NNG<节点ID> ...
- 修改NNG<节点ID> ...
- 新增记忆 <记忆类型>/<价值层级> ...

请输出整理后的内容：""",
            
            "dmn_agent5": """你是AbyssAC DMN的格式审查智能体。

【任务类型】
{task_type}

【整理输出】
{formatted_output}

【审查标准】
1. JSON格式是否正确？
2. 文件路径是否符合规范？
3. 所有必填字段是否存在？

【输出格式】
- 如果格式正确：输出 "VERIFIED"
- 如果有问题：输出 "REJECTED: 具体问题说明"

请输出审查结果："""
        }
        
        prompt = defaults.get(prompt_name, "请执行任务。")
        
        # 替换占位符
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            prompt = prompt.replace(placeholder, str(value))
        
        return prompt


class InstructionParser:
    """指令解析器"""
    
    @staticmethod
    def parse_layer1_instruction(response: str) -> Dict[str, Any]:
        """
        解析第一层沙盒指令
        
        Returns:
            {"type": "GOTO/STAY/BACK/ROOT/DIRECT", "target": "...", "multiple": [...]}
        """
        response = response.strip().upper()
        
        # 检查多节点直接定位
        if "NNG" in response and "," in response and "STAY" in response:
            # 格式: NNG1.2,NNG2.3,STAY
            nodes = []
            parts = response.replace("STAY", "").split(",")
            for part in parts:
                part = part.strip()
                if part.startswith("NNG"):
                    nodes.append(part[3:])
            return {"type": "DIRECT", "multiple": nodes}
        
        # 单节点直接定位
        if response.startswith("NNG"):
            target = response[3:].strip()
            return {"type": "DIRECT", "target": target}
        
        # GOTO指令
        match = re.match(r'GOTO\(([^)]+)\)', response)
        if match:
            return {"type": "GOTO", "target": match.group(1)}
        
        # STAY指令
        if response == "STAY":
            return {"type": "STAY"}
        
        # BACK指令
        if response == "BACK":
            return {"type": "BACK"}
        
        # ROOT指令
        if response == "ROOT":
            return {"type": "ROOT"}
        
        # 默认STAY
        return {"type": "STAY"}
    
    @staticmethod
    def parse_layer2_instruction(response: str) -> Dict[str, Any]:
        """
        解析第二层沙盒指令
        
        Returns:
            {"type": "SELECT/STAY", "memory_ids": [...]}
        """
        response = response.strip()
        
        # 检查多记忆选择
        if "记忆" in response and "STAY" in response:
            memory_ids = []
            parts = response.replace("STAY", "").split(",")
            for part in parts:
                part = part.strip()
                if part.startswith("记忆"):
                    memory_ids.append(part[2:].strip())
            return {"type": "SELECT", "memory_ids": memory_ids}
        
        # 单记忆选择
        if response.startswith("记忆"):
            memory_id = response[2:].strip()
            return {"type": "SELECT", "memory_ids": [memory_id]}
        
        # 默认STAY（不选记忆）
        return {"type": "STAY", "memory_ids": []}
    
    @staticmethod
    def parse_dmn_instruction(response: str) -> List[Dict[str, Any]]:
        """
        解析DMN指令
        
        Returns:
            指令列表
        """
        instructions = []
        lines = response.strip().split('\n')
        
        current_instruction = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # 新增NNG
            if line.startswith("新增NNG"):
                if current_instruction:
                    current_instruction["content"] = '\n'.join(current_content)
                    instructions.append(current_instruction)
                
                nng_id = line[5:].strip()
                current_instruction = {"action": "ADD_NNG", "nng_id": nng_id}
                current_content = []
            
            # 修改NNG
            elif line.startswith("修改NNG"):
                if current_instruction:
                    current_instruction["content"] = '\n'.join(current_content)
                    instructions.append(current_instruction)
                
                nng_id = line[5:].strip()
                current_instruction = {"action": "MODIFY_NNG", "nng_id": nng_id}
                current_content = []
            
            # 删除NNG
            elif line.startswith("删除NNG"):
                if current_instruction:
                    current_instruction["content"] = '\n'.join(current_content)
                    instructions.append(current_instruction)
                
                nng_id = line[5:].strip()
                instructions.append({"action": "DELETE_NNG", "nng_id": nng_id})
                current_instruction = None
                current_content = []
            
            # 新增记忆
            elif line.startswith("新增记忆"):
                if current_instruction:
                    current_instruction["content"] = '\n'.join(current_content)
                    instructions.append(current_instruction)
                
                parts = line[5:].strip().split('/')
                mem_type = parts[0].strip() if parts else "分类记忆"
                value_tier = parts[1].strip() if len(parts) > 1 else None
                current_instruction = {
                    "action": "ADD_MEMORY", 
                    "memory_type": mem_type,
                    "value_tier": value_tier
                }
                current_content = []
            
            # JSON内容或其他
            elif current_instruction is not None:
                current_content.append(line)
        
        # 处理最后一个指令
        if current_instruction:
            current_instruction["content"] = '\n'.join(current_content)
            instructions.append(current_instruction)
        
        return instructions
