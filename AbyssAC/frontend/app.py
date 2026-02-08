"""
AbyssAC Gradio前端界面
"""
import gradio as gr
import json
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.system import get_system, AbyssACSystem


class AbyssACUI:
    """AbyssAC Gradio界面"""
    
    def __init__(self):
        self.system = get_system()
        self.chat_history = []
    
    def initialize_system(self, provider, base_url, model, api_key, temperature):
        """初始化系统"""
        llm_config = {
            "provider": provider,
            "base_url": base_url,
            "model": model,
            "api_key": api_key,
            "temperature": float(temperature)
        }
        
        success = self.system.initialize(llm_config)
        
        if success:
            # 测试LLM连接
            if self.system.test_llm_connection():
                return "✅ 系统初始化成功，LLM连接正常"
            else:
                return "⚠️ 系统初始化成功，但LLM连接测试失败，请检查配置"
        else:
            return "❌ 系统初始化失败"
    
    def chat(self, message, history, enable_sandbox):
        """处理聊天消息"""
        if not self.system.is_initialized:
            return "请先初始化系统", history
        
        response = self.system.chat(message, enable_sandbox=enable_sandbox)
        
        # 更新历史
        history.append([message, response.content])
        
        return "", history
    
    def get_status(self):
        """获取系统状态"""
        status = self.system.get_system_status()
        return json.dumps(status, ensure_ascii=False, indent=2)
    
    def get_nng_structure(self):
        """获取NNG结构"""
        structure = self.system.get_nng_structure()
        return json.dumps(structure, ensure_ascii=False, indent=2)
    
    def get_working_memory(self):
        """获取工作记忆"""
        memories = self.system.get_working_memory_list(limit=20)
        result = f"=== 工作记忆 (共{len(memories)}条) ===\n\n"
        for mem in memories:
            result += f"[{mem['id']}] {mem['timestamp']}\n{mem['content']}\n\n"
        return result
    
    def clear_working_memory(self):
        """清空工作记忆"""
        if self.system.clear_working_memory():
            return "✅ 工作记忆已清空"
        return "❌ 清空失败"
    
    def manual_dmn(self, task_type):
        """手动触发DMN"""
        if not self.system.is_initialized:
            return "请先初始化系统"
        
        success, logs = self.system.manual_dmn(task_type)
        return logs
    
    def create_ui(self):
        """创建Gradio界面"""
        with gr.Blocks(title="AbyssAC - 人工意识系统", css="""
            .container { max-width: 1200px; margin: 0 auto; }
            .chatbot { height: 500px; }
            .logs { font-family: monospace; font-size: 12px; }
        "") as demo:
            
            gr.Markdown("""
            # 🧠 AbyssAC - 基于NNG导航的人工意识系统
            
            一个具有长期记忆能力的AI系统，通过NNG（导航节点图）组织知识，支持三层沙盒记忆调取。
            """)
            
            with gr.Tab("💬 对话"):
                with gr.Row():
                    with gr.Column(scale=2):
                        chatbot = gr.Chatbot(
                            label="对话历史",
                            elem_classes=["chatbot"]
                        )
                        with gr.Row():
                            msg_input = gr.Textbox(
                                label="输入消息",
                                placeholder="请输入消息...",
                                scale=4
                            )
                            send_btn = gr.Button("发送", scale=1, variant="primary")
                        
                        enable_sandbox = gr.Checkbox(
                            label="启用三层沙盒",
                            value=True
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 系统状态")
                        status_text = gr.Textbox(
                            label="状态",
                            value="未初始化",
                            interactive=False
                        )
                        refresh_status_btn = gr.Button("刷新状态")
                        
                        gr.Markdown("### DMN控制")
                        dmn_task = gr.Dropdown(
                            label="DMN任务类型",
                            choices=["记忆整合", "关联发现", "偏差审查", "策略预演", "概念重组"],
                            value="记忆整合"
                        )
                        dmn_btn = gr.Button("手动触发DMN", variant="secondary")
                        dmn_logs = gr.Textbox(
                            label="DMN日志",
                            lines=10,
                            elem_classes=["logs"]
                        )
            
            with gr.Tab("⚙️ 系统配置"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### LLM配置")
                        provider = gr.Dropdown(
                            label="Provider",
                            choices=["ollama", "lmstudio", "openai"],
                            value="ollama"
                        )
                        base_url = gr.Textbox(
                            label="Base URL",
                            value="http://localhost:11434"
                        )
                        model = gr.Textbox(
                            label="Model",
                            value="qwen2.5"
                        )
                        api_key = gr.Textbox(
                            label="API Key (可选)",
                            type="password"
                        )
                        temperature = gr.Slider(
                            label="Temperature",
                            minimum=0.0,
                            maximum=2.0,
                            value=0.7,
                            step=0.1
                        )
                        init_btn = gr.Button("初始化系统", variant="primary")
                        init_result = gr.Textbox(label="初始化结果")
            
            with gr.Tab("📊 记忆查看"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### NNG结构")
                        nng_structure = gr.Textbox(
                            label="NNG导航图",
                            lines=15,
                            elem_classes=["logs"]
                        )
                        refresh_nng_btn = gr.Button("刷新NNG结构")
                    
                    with gr.Column():
                        gr.Markdown("### 工作记忆")
                        working_mem = gr.Textbox(
                            label="工作记忆内容",
                            lines=15,
                            elem_classes=["logs"]
                        )
                        with gr.Row():
                            refresh_wm_btn = gr.Button("刷新工作记忆")
                            clear_wm_btn = gr.Button("清空工作记忆", variant="stop")
            
            # 事件绑定
            init_btn.click(
                self.initialize_system,
                inputs=[provider, base_url, model, api_key, temperature],
                outputs=init_result
            )
            
            send_btn.click(
                self.chat,
                inputs=[msg_input, chatbot, enable_sandbox],
                outputs=[msg_input, chatbot]
            )
            
            msg_input.submit(
                self.chat,
                inputs=[msg_input, chatbot, enable_sandbox],
                outputs=[msg_input, chatbot]
            )
            
            refresh_status_btn.click(
                self.get_status,
                outputs=status_text
            )
            
            refresh_nng_btn.click(
                self.get_nng_structure,
                outputs=nng_structure
            )
            
            refresh_wm_btn.click(
                self.get_working_memory,
                outputs=working_mem
            )
            
            clear_wm_btn.click(
                self.clear_working_memory,
                outputs=working_mem
            )
            
            dmn_btn.click(
                self.manual_dmn,
                inputs=dmn_task,
                outputs=dmn_logs
            )
        
        return demo


def main():
    """主函数"""
    ui = AbyssACUI()
    demo = ui.create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()
