"""
AbyssAC Gradio前端界面
"""
import os
import sys
import json
import gradio as gr
from pathlib import Path
from typing import List, Tuple, Optional

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.abyssac import AbyssAC
from core.config import get_config, SystemConfig


class AbyssACUI:
    """AbyssAC Gradio界面"""
    
    def __init__(self):
        self.abyssac: Optional[AbyssAC] = None
        self.chat_history: List[Tuple[str, str]] = []
        
    def initialize_system(self, use_local: bool, 
                          ollama_model: str,
                          ollama_url: str) -> str:
        """初始化系统"""
        try:
            # 加载配置
            config = get_config()
            config.llm.use_local = use_local
            config.llm.ollama_model = ollama_model
            config.llm.ollama_base_url = ollama_url
            
            # 初始化AbyssAC
            self.abyssac = AbyssAC(config)
            
            status = self.abyssac.get_system_status()
            
            return f"""✅ 系统初始化成功！

📊 系统状态:
- Bootstrap阶段: {status['bootstrap_stage']}
- LLM提供商: {status['llm_provider']}
- LLM模型: {status['llm_model']}
- 工作记忆数: {status['working_memory_count']}
- NNG节点数: {status['nng_node_count']}
- 导航失败: {status['navigation_failures']}
"""
        except Exception as e:
            return f"❌ 初始化失败: {str(e)}"
    
    def chat(self, message: str, history: List[Tuple[str, str]]) -> Tuple[str, List[Tuple[str, str]]]:
        """处理聊天消息"""
        if self.abyssac is None:
            return "请先初始化系统", history
        
        if not message.strip():
            return "", history
        
        try:
            # 调用AbyssAC
            response = self.abyssac.chat(message)
            
            # 更新历史
            history.append((message, response))
            
            return "", history
            
        except Exception as e:
            return f"错误: {str(e)}", history
    
    def get_system_status(self) -> str:
        """获取系统状态"""
        if self.abyssac is None:
            return "系统未初始化"
        
        status = self.abyssac.get_system_status()
        
        return f"""📊 系统状态

🔄 Bootstrap阶段: {status['bootstrap_stage']}
💬 对话总数: {status['total_conversations']}
🧠 工作记忆: {status['working_memory_count']}
🗺️ NNG节点: {status['nng_node_count']}
❌ 导航失败: {status['navigation_failures']}
⏰ 最后DMN: {status['last_dmn_time'] or '未执行'}
🏃 DMN运行中: {'是' if status['dmn_running'] else '否'}

🤖 LLM配置:
- 提供商: {status['llm_provider']}
- 模型: {status['llm_model']}
"""
    
    def trigger_dmn(self, task_type: str) -> str:
        """手动触发DMN"""
        if self.abyssac is None:
            return "系统未初始化"
        
        return self.abyssac.manual_trigger_dmn(task_type)
    
    def clear_memory(self) -> str:
        """清空工作记忆"""
        if self.abyssac is None:
            return "系统未初始化"
        
        return self.abyssac.clear_working_memory()
    
    def create_ui(self) -> gr.Blocks:
        """创建Gradio界面"""
        
        with gr.Blocks(title="AbyssAC - 人工意识系统", theme=gr.themes.Soft()) as demo:
            
            gr.Markdown("""
            # 🧠 AbyssAC - 人工意识系统
            
            基于NNG导航和Y层记忆的AI操作系统
            """)
            
            with gr.Tab("💬 对话"):
                chatbot = gr.Chatbot(
                    label="对话历史",
                    height=500,
                    bubble_full_width=False
                )
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        label="输入消息",
                        placeholder="输入你的问题...",
                        scale=8
                    )
                    send_btn = gr.Button("发送", scale=1, variant="primary")
                
                with gr.Row():
                    clear_btn = gr.Button("清空对话")
                    status_btn = gr.Button("查看状态")
                
                status_text = gr.Textbox(label="系统状态", interactive=False)
                
                # 事件绑定
                send_btn.click(
                    self.chat,
                    inputs=[msg_input, chatbot],
                    outputs=[msg_input, chatbot]
                )
                
                msg_input.submit(
                    self.chat,
                    inputs=[msg_input, chatbot],
                    outputs=[msg_input, chatbot]
                )
                
                clear_btn.click(lambda: ([], None), outputs=[chatbot, msg_input])
                status_btn.click(self.get_system_status, outputs=status_text)
            
            with gr.Tab("⚙️ 系统设置"):
                with gr.Group():
                    gr.Markdown("### LLM配置")
                    
                    use_local = gr.Checkbox(
                        label="使用本地模型(Ollama)",
                        value=True
                    )
                    
                    ollama_url = gr.Textbox(
                        label="Ollama服务地址",
                        value="http://localhost:11434"
                    )
                    
                    ollama_model = gr.Dropdown(
                        label="Ollama模型",
                        choices=[
                            "qwen2.5:7b",
                            "qwen2.5:14b",
                            "llama3.1:8b",
                            "llama3.2:3b",
                            "mistral:7b",
                            "gemma2:9b",
                            "deepseek-coder:6.7b"
                        ],
                        value="qwen2.5:7b"
                    )
                    
                    init_btn = gr.Button("初始化系统", variant="primary")
                    init_output = gr.Textbox(label="初始化结果", interactive=False, lines=10)
                    
                    init_btn.click(
                        self.initialize_system,
                        inputs=[use_local, ollama_model, ollama_url],
                        outputs=init_output
                    )
            
            with gr.Tab("🔧 DMN维护"):
                with gr.Group():
                    gr.Markdown("### 手动触发DMN任务")
                    
                    task_type = gr.Dropdown(
                        label="任务类型",
                        choices=[
                            ("记忆整合", "memory_integration"),
                            ("关联发现", "association_discovery"),
                            ("偏差审查", "bias_review"),
                            ("策略预演", "strategy_rehearsal"),
                            ("概念重组", "concept_recombination"),
                            ("NNG优化", "nng_optimization")
                        ],
                        value="memory_integration"
                    )
                    
                    dmn_btn = gr.Button("执行DMN任务", variant="primary")
                    dmn_output = gr.Textbox(label="执行结果", interactive=False)
                    
                    dmn_btn.click(self.trigger_dmn, inputs=task_type, outputs=dmn_output)
                
                with gr.Group():
                    gr.Markdown("### 内存管理")
                    clear_btn = gr.Button("清空工作记忆", variant="stop")
                    clear_output = gr.Textbox(label="操作结果", interactive=False)
                    
                    clear_btn.click(self.clear_working_memory, outputs=clear_output)
            
            with gr.Tab("📚 使用帮助"):
                gr.Markdown("""
                ## 使用指南
                
                ### 1. 初始化系统
                - 进入"系统设置"标签页
                - 选择Ollama模型（默认qwen2.5:7b）
                - 点击"初始化系统"
                
                ### 2. 开始对话
                - 进入"对话"标签页
                - 输入消息并发送
                - 系统会自动管理记忆
                
                ### 3. DMN维护
                - 当工作记忆超过20条时，DMN会自动触发
                - 也可以手动触发DMN任务
                - DMN会整合记忆、优化NNG结构
                
                ### 4. Bootstrap阶段
                - **阶段1**: NNG为空，直接回复
                - **阶段2**: 首次DMN触发，创建初始结构
                - **阶段3**: 正常使用X层三层沙盒
                
                ### 系统架构
                - **X层**: 三层沙盒（导航→筛选→组装）
                - **Y层**: 记忆库（元认知/高阶整合/分类/工作）
                - **NNG**: 导航节点图
                - **DMN**: 动态维护网络（5个子智能体）
                """)
            
            gr.Markdown("""
            ---
            📝 AbyssAC v1.0 | 基于NNG导航的AI记忆系统
            """)
        
        return demo


def main():
    """主函数"""
    ui = AbyssACUI()
    demo = ui.create_ui()
    
    # 启动Gradio
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()
