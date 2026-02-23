#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import threading
import subprocess
from datetime import datetime

try:
    import customtkinter as ctk
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "customtkinter", "-q"])
    import customtkinter as ctk

ctk.set_appearance_mode("dark")

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.path_parser import PathParser
from core.parallel_io import ParallelIOManager
from sandbox.nng_navigation_sandbox import NNGNavigationSandbox
from sandbox.memory_filtering_sandbox import MemoryFilteringSandbox
from sandbox.context_assembly_sandbox import ContextAssemblySandbox
from nng.nng_manager import NNGManager
from memory.memory_manager import MemoryManager
from dmn.dmn_manager import DMNManager
from llm.llm_integration import LLMIntegration
from config.config_manager import ConfigManager


class AbyssACStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("AbyssAC")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        self.configure(fg_color="#0d0d0d")
        
        self.config = self._load_config()
        self._init_components()
        
        self.running = True
        self.processing = False
        self.sessions = []
        self.current_session = None
        self.work_folder = None
        self.sidebar_visible = True
        self.current_view = "chat"
        
        self._create_ui()
        self._start_services()
    
    def _load_config(self):
        try:
            with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _init_components(self):
        self.config_manager = ConfigManager(self.config)
        self.path_parser = PathParser()
        self.parallel_io = ParallelIOManager()
        
        base_dir = os.path.dirname(__file__)
        nng_root = os.path.join(base_dir, self.config.get('paths', {}).get('nngrootpath', 'storage/nng/'))
        memory_root = os.path.join(base_dir, self.config.get('paths', {}).get('memoryrootpath', 'storage/Y层记忆库/'))
        
        self.nng_manager = NNGManager(nng_root)
        self.memory_manager = MemoryManager(memory_root)
        self.llm_integration = LLMIntegration(self.config_manager.get_config('llm') or {})
        
        self.nng_sandbox = NNGNavigationSandbox(self.nng_manager, self.llm_integration, self.path_parser, self.parallel_io, self.config_manager)
        self.memory_sandbox = MemoryFilteringSandbox(self.memory_manager, self.llm_integration, self.path_parser, self.parallel_io, self.config_manager)
        self.context_sandbox = ContextAssemblySandbox(self.llm_integration, self.config_manager)
        self.dmn_manager = DMNManager(self.nng_manager, self.memory_manager, self.llm_integration)
        
        from utils.prompt_manager import PromptManager
        self.prompt_manager = PromptManager(os.path.join(base_dir, 'prompts.json'))
    
    def _create_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_sidebar()
        self._create_main()
    
    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#141414", border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(1, weight=1)
        self.sidebar.grid_propagate(False)
        
        header = ctk.CTkFrame(self.sidebar, height=50, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        
        new_btn = ctk.CTkButton(header, text="+  新对话", height=40, corner_radius=8, fg_color="#1a1a1a", hover_color="#252525", text_color="#a0a0a0", font=("Microsoft YaHei", 11), command=self._new_session)
        new_btn.pack(fill="x")
        
        self.sessions_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.sessions_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        
        footer = ctk.CTkFrame(self.sidebar, height=80, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=12, pady=12)
        
        settings_btn = ctk.CTkButton(footer, text="设置", height=36, corner_radius=8, fg_color="transparent", hover_color="#1a1a1a", text_color="#666666", font=("Microsoft YaHei", 10), command=lambda: self._switch_view("settings"))
        settings_btn.pack(fill="x", pady=2)
        
        self.status_label = ctk.CTkLabel(footer, text="", font=("Microsoft YaHei", 9), text_color="#404040")
        self.status_label.pack(pady=5)
    
    def _create_main(self):
        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color="#0d0d0d", border_width=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)
        
        self._create_header()
        self._create_content_area()
    
    def _create_header(self):
        header = ctk.CTkFrame(self.main, height=52, corner_radius=0, fg_color="#141414", border_width=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(2, weight=1)
        
        toggle_btn = ctk.CTkButton(header, text="三", width=44, height=36, corner_radius=0, fg_color="transparent", hover_color="#1a1a1a", text_color="#505050", font=("Segoe UI", 14), command=self._toggle_sidebar)
        toggle_btn.grid(row=0, column=0, padx=4, pady=8)
        
        tab_frame = ctk.CTkFrame(header, fg_color="transparent")
        tab_frame.grid(row=0, column=1, padx=10, pady=8)
        
        self.chat_tab = ctk.CTkButton(tab_frame, text="对话", width=60, height=32, corner_radius=6, fg_color="#1e3a5f", hover_color="#254a75", text_color="#a0a0a0", font=("Microsoft YaHei", 10), command=lambda: self._switch_view("chat"))
        self.chat_tab.pack(side="left", padx=2)
        
        self.sandbox_tab = ctk.CTkButton(tab_frame, text="沙盒", width=60, height=32, corner_radius=6, fg_color="transparent", hover_color="#1a1a1a", text_color="#505050", font=("Microsoft YaHei", 10), command=lambda: self._switch_view("sandbox"))
        self.sandbox_tab.pack(side="left", padx=2)
        
        right_frame = ctk.CTkFrame(header, fg_color="transparent")
        right_frame.grid(row=0, column=2, padx=12, pady=8, sticky="e")
        
        self.model_btn = ctk.CTkButton(right_frame, text="模型", width=70, height=32, corner_radius=6, fg_color="transparent", hover_color="#1a1a1a", text_color="#505050", font=("Microsoft YaHei", 10), command=lambda: self._switch_view("model"))
        self.model_btn.pack(side="right", padx=3)
        
        prompt_btn = ctk.CTkButton(right_frame, text="提示词", width=70, height=32, corner_radius=6, fg_color="transparent", hover_color="#1a1a1a", text_color="#505050", font=("Microsoft YaHei", 10), command=lambda: self._switch_view("prompt"))
        prompt_btn.pack(side="right", padx=3)
    
    def _create_content_area(self):
        self.content_frame = ctk.CTkFrame(self.main, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        self._create_chat_view()
        self._create_sandbox_view()
        self._create_settings_view()
        self._create_model_view()
        self._create_prompt_view()
        
        self._switch_view("chat")
    
    def _create_chat_view(self):
        self.chat_view = ctk.CTkFrame(self.content_frame, corner_radius=0, fg_color="transparent")
        self.chat_view.grid(row=0, column=0, sticky="nsew")
        self.chat_view.grid_columnconfigure(0, weight=1)
        self.chat_view.grid_rowconfigure(0, weight=1)
        
        self.chat_display = ctk.CTkTextbox(self.chat_view, corner_radius=0, fg_color="transparent", text_color="#b0b0b0", font=("Microsoft YaHei", 11), wrap="word", border_width=0, border_spacing=25)
        self.chat_display.grid(row=0, column=0, sticky="nsew")
        self.chat_display.configure(state="disabled")
        
        input_frame = ctk.CTkFrame(self.chat_view, height=90, corner_radius=0, fg_color="#141414", border_width=0)
        input_frame.grid(row=1, column=0, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        inner_input = ctk.CTkFrame(input_frame, corner_radius=10, fg_color="#1a1a1a", border_width=0)
        inner_input.grid(row=0, column=0, sticky="ew", padx=25, pady=18)
        inner_input.grid_columnconfigure(0, weight=1)
        
        self.input_text = ctk.CTkTextbox(inner_input, height=45, corner_radius=10, fg_color="#1a1a1a", text_color="#b0b0b0", font=("Microsoft YaHei", 11), wrap="word", border_width=0)
        self.input_text.grid(row=0, column=0, sticky="ew", padx=12, pady=10)
        self.input_text.bind('<Control-Return>', lambda e: self._send())
        self.input_text.bind('<Return>', self._on_enter)
        
        self.send_btn = ctk.CTkButton(inner_input, text="发送", width=65, height=38, corner_radius=8, fg_color="#1e3a5f", hover_color="#254a75", text_color="#c0c0c0", font=("Microsoft YaHei", 10), command=self._send)
        self.send_btn.grid(row=0, column=1, padx=10, pady=10)
    
    def _create_sandbox_view(self):
        self.sandbox_view = ctk.CTkFrame(self.content_frame, corner_radius=0, fg_color="transparent")
        self.sandbox_view.grid(row=0, column=0, sticky="nsew")
        self.sandbox_view.grid_columnconfigure(0, weight=1)
        self.sandbox_view.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkFrame(self.sandbox_view, height=50, corner_radius=0, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=25, pady=15)
        
        ctk.CTkLabel(header, text="三层沙盒流程", font=("Microsoft YaHei", 14, "bold"), text_color="#707070").pack(side="left")
        
        clear_btn = ctk.CTkButton(header, text="清空", width=50, height=28, corner_radius=6, fg_color="transparent", hover_color="#1a1a1a", text_color="#505050", font=("Microsoft YaHei", 9), command=self._clear_sandbox_logs)
        clear_btn.pack(side="right")
        
        content = ctk.CTkFrame(self.sandbox_view, corner_radius=0, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_columnconfigure(2, weight=1)
        content.grid_rowconfigure(0, weight=1)
        
        nng_frame = ctk.CTkFrame(content, corner_radius=10, fg_color="#141414")
        nng_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        nng_frame.grid_columnconfigure(0, weight=1)
        nng_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(nng_frame, text="1. NNG导航", font=("Microsoft YaHei", 11, "bold"), text_color="#3a7ca5").grid(row=0, column=0, padx=15, pady=12, sticky="w")
        
        self.nng_log = ctk.CTkTextbox(nng_frame, corner_radius=0, fg_color="transparent", text_color="#808080", font=("Consolas", 9), wrap="word", border_width=0)
        self.nng_log.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.nng_log.configure(state="disabled")
        
        mem_frame = ctk.CTkFrame(content, corner_radius=10, fg_color="#141414")
        mem_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        mem_frame.grid_columnconfigure(0, weight=1)
        mem_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(mem_frame, text="2. 记忆筛选", font=("Microsoft YaHei", 11, "bold"), text_color="#5a8a5a").grid(row=0, column=0, padx=15, pady=12, sticky="w")
        
        self.mem_log = ctk.CTkTextbox(mem_frame, corner_radius=0, fg_color="transparent", text_color="#808080", font=("Consolas", 9), wrap="word", border_width=0)
        self.mem_log.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.mem_log.configure(state="disabled")
        
        ctx_frame = ctk.CTkFrame(content, corner_radius=10, fg_color="#141414")
        ctx_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        ctx_frame.grid_columnconfigure(0, weight=1)
        ctx_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(ctx_frame, text="3. 上下文组装", font=("Microsoft YaHei", 11, "bold"), text_color="#8a5a8a").grid(row=0, column=0, padx=15, pady=12, sticky="w")
        
        self.ctx_log = ctk.CTkTextbox(ctx_frame, corner_radius=0, fg_color="transparent", text_color="#808080", font=("Consolas", 9), wrap="word", border_width=0)
        self.ctx_log.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.ctx_log.configure(state="disabled")
    
    def _create_settings_view(self):
        self.settings_view = ctk.CTkFrame(self.content_frame, corner_radius=0, fg_color="transparent")
        self.settings_view.grid(row=0, column=0, sticky="nsew")
        self.settings_view.grid_columnconfigure(0, weight=1)
        self.settings_view.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkFrame(self.settings_view, height=60, corner_radius=0, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=20)
        
        ctk.CTkLabel(header, text="设置", font=("Microsoft YaHei", 18, "bold"), text_color="#707070").pack(side="left")
        
        back_btn = ctk.CTkButton(header, text="返回", width=60, height=32, corner_radius=6, fg_color="transparent", hover_color="#1a1a1a", text_color="#505050", font=("Microsoft YaHei", 10), command=lambda: self._switch_view("chat"))
        back_btn.pack(side="right")
        
        content = ctk.CTkScrollableFrame(self.settings_view, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
        
        ctk.CTkLabel(content, text="工作目录", font=("Microsoft YaHei", 12), text_color="#505050").pack(anchor="w", pady=(15, 8))
        
        dir_frame = ctk.CTkFrame(content, fg_color="#141414", corner_radius=8, height=45)
        dir_frame.pack(fill="x", pady=5)
        dir_frame.pack_propagate(False)
        
        self.dir_label = ctk.CTkLabel(dir_frame, text=self.work_folder or "未选择", font=("Microsoft YaHei", 10), text_color="#404040")
        self.dir_label.pack(side="left", padx=15, pady=10)
        
        ctk.CTkButton(dir_frame, text="选择", width=55, height=30, corner_radius=6, fg_color="#1a1a1a", hover_color="#252525", text_color="#606060", font=("Microsoft YaHei", 9), command=self._select_dir).pack(side="right", padx=10, pady=7)
        
        ctk.CTkLabel(content, text="LLM设置", font=("Microsoft YaHei", 12), text_color="#505050").pack(anchor="w", pady=(30, 8))
        
        llm_frame = ctk.CTkFrame(content, fg_color="#141414", corner_radius=8)
        llm_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(llm_frame, text="API地址", font=("Microsoft YaHei", 10), text_color="#404040").pack(anchor="w", padx=15, pady=(12, 5))
        
        self.api_entry = ctk.CTkEntry(llm_frame, height=36, corner_radius=6, fg_color="#1a1a1a", text_color="#808080", border_width=0, placeholder_text="http://localhost:11434")
        self.api_entry.pack(fill="x", padx=15, pady=(0, 12))
        self.api_entry.insert(0, self.config.get('llm', {}).get('base_url', 'http://localhost:11434'))
        
        ctk.CTkLabel(content, text="系统维护", font=("Microsoft YaHei", 12), text_color="#505050").pack(anchor="w", pady=(30, 8))
        
        ctk.CTkButton(content, text="触发DMN维护", height=40, corner_radius=8, fg_color="#141414", hover_color="#1a1a1a", text_color="#505050", font=("Microsoft YaHei", 10), anchor="w", command=self._trigger_dmn).pack(fill="x", pady=3)
    
    def _create_model_view(self):
        self.model_view = ctk.CTkFrame(self.content_frame, corner_radius=0, fg_color="transparent")
        self.model_view.grid(row=0, column=0, sticky="nsew")
        self.model_view.grid_columnconfigure(0, weight=1)
        self.model_view.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkFrame(self.model_view, height=60, corner_radius=0, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=20)
        
        ctk.CTkLabel(header, text="模型选择", font=("Microsoft YaHei", 18, "bold"), text_color="#707070").pack(side="left")
        
        back_btn = ctk.CTkButton(header, text="返回", width=60, height=32, corner_radius=6, fg_color="transparent", hover_color="#1a1a1a", text_color="#505050", font=("Microsoft YaHei", 10), command=lambda: self._switch_view("chat"))
        back_btn.pack(side="right")
        
        self.model_list_frame = ctk.CTkScrollableFrame(self.model_view, fg_color="transparent")
        self.model_list_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
        
        self.model_var = ctk.StringVar(value=self.llm_integration.model_name or "")
        
        refresh_btn = ctk.CTkButton(self.model_list_frame, text="刷新模型列表", height=40, corner_radius=8, fg_color="#141414", hover_color="#1a1a1a", text_color="#505050", font=("Microsoft YaHei", 10), command=self._refresh_models)
        refresh_btn.pack(fill="x", pady=10)
        
        self.model_radio_frame = ctk.CTkFrame(self.model_list_frame, fg_color="transparent")
        self.model_radio_frame.pack(fill="x", pady=10)
    
    def _create_prompt_view(self):
        self.prompt_view = ctk.CTkFrame(self.content_frame, corner_radius=0, fg_color="transparent")
        self.prompt_view.grid(row=0, column=0, sticky="nsew")
        self.prompt_view.grid_columnconfigure(0, weight=1)
        self.prompt_view.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkFrame(self.prompt_view, height=60, corner_radius=0, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=20)
        
        ctk.CTkLabel(header, text="系统提示词", font=("Microsoft YaHei", 18, "bold"), text_color="#707070").pack(side="left")
        
        back_btn = ctk.CTkButton(header, text="返回", width=60, height=32, corner_radius=6, fg_color="transparent", hover_color="#1a1a1a", text_color="#505050", font=("Microsoft YaHei", 10), command=lambda: self._switch_view("chat"))
        back_btn.pack(side="right")
        
        content = ctk.CTkFrame(self.prompt_view, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        
        self.prompt_text = ctk.CTkTextbox(content, corner_radius=10, fg_color="#141414", text_color="#909090", font=("Microsoft YaHei", 11), wrap="word", border_width=0)
        self.prompt_text.grid(row=0, column=0, sticky="nsew")
        self.prompt_text.insert("1.0", self.prompt_manager.get_system_prompt())
        
        save_btn = ctk.CTkButton(content, text="保存", width=80, height=38, corner_radius=8, fg_color="#1e3a5f", hover_color="#254a75", text_color="#c0c0c0", font=("Microsoft YaHei", 10), command=self._save_prompt)
        save_btn.grid(row=1, column=0, pady=15)
    
    def _switch_view(self, view):
        self.chat_view.grid_remove()
        self.sandbox_view.grid_remove()
        self.settings_view.grid_remove()
        self.model_view.grid_remove()
        self.prompt_view.grid_remove()
        
        self.chat_tab.configure(fg_color="transparent", text_color="#505050")
        self.sandbox_tab.configure(fg_color="transparent", text_color="#505050")
        
        if view == "chat":
            self.chat_view.grid(row=0, column=0, sticky="nsew")
            self.chat_tab.configure(fg_color="#1e3a5f", text_color="#a0a0a0")
        elif view == "sandbox":
            self.sandbox_view.grid(row=0, column=0, sticky="nsew")
            self.sandbox_tab.configure(fg_color="#1e3a5f", text_color="#a0a0a0")
        elif view == "settings":
            self.settings_view.grid(row=0, column=0, sticky="nsew")
        elif view == "model":
            self.model_view.grid(row=0, column=0, sticky="nsew")
            self._refresh_models()
        elif view == "prompt":
            self.prompt_view.grid(row=0, column=0, sticky="nsew")
        
        self.current_view = view
    
    def _log_sandbox(self, stage, msg):
        t = datetime.now().strftime("%H:%M:%S")
        log_msg = "[" + t + "] " + msg + "\n"
        
        if stage == "nng":
            self.nng_log.configure(state="normal")
            self.nng_log.insert("end", log_msg)
            self.nng_log.see("end")
            self.nng_log.configure(state="disabled")
        elif stage == "mem":
            self.mem_log.configure(state="normal")
            self.mem_log.insert("end", log_msg)
            self.mem_log.see("end")
            self.mem_log.configure(state="disabled")
        elif stage == "ctx":
            self.ctx_log.configure(state="normal")
            self.ctx_log.insert("end", log_msg)
            self.ctx_log.see("end")
            self.ctx_log.configure(state="disabled")
    
    def _clear_sandbox_logs(self):
        for log in [self.nng_log, self.mem_log, self.ctx_log]:
            log.configure(state="normal")
            log.delete("1.0", "end")
            log.configure(state="disabled")
    
    def _refresh_models(self):
        for w in self.model_radio_frame.winfo_children():
            w.destroy()
        
        models = self.llm_integration.list_models() or []
        
        if not models:
            ctk.CTkLabel(self.model_radio_frame, text="未找到模型，请确保Ollama正在运行", font=("Microsoft YaHei", 11), text_color="#404040").pack(pady=20)
            return
        
        for m in models:
            is_selected = m == self.llm_integration.model_name
            fg = "#1e3a5f" if is_selected else "#141414"
            txt = "#a0a0a0" if is_selected else "#606060"
            
            btn = ctk.CTkButton(self.model_radio_frame, text=m, height=42, corner_radius=8, fg_color=fg, hover_color="#254a75", text_color=txt, font=("Microsoft YaHei", 11), anchor="w", command=lambda x=m: self._select_model(x))
            btn.pack(fill="x", pady=3)
    
    def _select_model(self, model):
        self.llm_integration.model_name = model
        self.model_btn.configure(text=model[:8])
        self._refresh_models()
    
    def _save_prompt(self):
        self.prompt_manager.set_system_prompt(self.prompt_text.get("1.0", "end").strip())
        self._switch_view("chat")
    
    def _toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.grid_remove()
            self.sidebar_visible = False
        else:
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            self.sidebar_visible = True
    
    def _new_session(self):
        self.current_session = {'title': '新对话', 'messages': []}
        self.sessions.append(self.current_session)
        self._refresh_sessions()
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self._switch_view("chat")
    
    def _refresh_sessions(self):
        for w in self.sessions_frame.winfo_children():
            w.destroy()
        
        for s in self.sessions[-20:]:
            title = s.get('title', '对话')[:20]
            btn = ctk.CTkButton(self.sessions_frame, text=title, height=34, corner_radius=6, fg_color="transparent", hover_color="#1a1a1a", text_color="#606060", font=("Microsoft YaHei", 10), anchor="w", command=lambda x=s: self._load_session(x))
            btn.pack(fill="x", pady=2)
    
    def _load_session(self, s):
        self.current_session = s
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        for m in s.get('messages', []):
            self._add_msg(m['role'], m['content'], save=False)
        self.chat_display.configure(state="disabled")
        self._switch_view("chat")
    
    def _on_enter(self, e):
        if e.state & 0x1:
            self.input_text.insert("insert", "\n")
            return "break"
    
    def _send(self):
        msg = self.input_text.get("1.0", "end").strip()
        if not msg or self.processing:
            return
        
        self._add_msg('user', msg)
        self.input_text.delete("1.0", "end")
        
        self.processing = True
        self.send_btn.configure(state="disabled", text="...")
        self.status_label.configure(text="处理中...")
        
        def run():
            try:
                self._log_sandbox("nng", "开始NNG导航...")
                self._log_sandbox("nng", "输入: " + msg[:50])
                nng = self.nng_sandbox.process(msg)
                paths = nng.get('nng_paths', [])
                self._log_sandbox("nng", "找到 " + str(len(paths)) + " 个节点")
                for p in paths[:5]:
                    self._log_sandbox("nng", "  -> " + p)
                
                self._log_sandbox("mem", "开始记忆筛选...")
                mem = self.memory_sandbox.process(nng)
                mem_paths = mem.get('memory_paths', [])
                self._log_sandbox("mem", "找到 " + str(len(mem_paths)) + " 个记忆文件")
                for p in mem_paths[:5]:
                    self._log_sandbox("mem", "  -> " + p)
                
                self._log_sandbox("ctx", "开始上下文组装...")
                final = self.context_sandbox.process(mem)
                self._log_sandbox("ctx", "组装完成")
                
                resp = final.get('response', '')
                self._add_msg('assistant', resp)
                self._log_sandbox("ctx", "响应长度: " + str(len(resp)) + " 字符")
            except Exception as e:
                self._add_msg('error', str(e))
                self._log_sandbox("ctx", "错误: " + str(e))
            finally:
                self.processing = False
                self.after(0, lambda: self.send_btn.configure(state="normal", text="发送"))
                self.after(0, lambda: self.status_label.configure(text=""))
        
        threading.Thread(target=run, daemon=True).start()
    
    def _add_msg(self, role, msg, save=True):
        t = datetime.now().strftime("%H:%M")
        self.chat_display.configure(state="normal")
        
        if role == 'user':
            self.chat_display.insert("end", "\n[" + t + "] 你\n", "user")
            self.chat_display.insert("end", msg + "\n")
        elif role == 'assistant':
            self.chat_display.insert("end", "\n[" + t + "] AbyssAC\n", "assistant")
            self.chat_display.insert("end", msg + "\n")
        elif role == 'error':
            self.chat_display.insert("end", "\n[" + t + "] 错误: " + msg + "\n", "error")
        
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        
        if save and self.current_session:
            self.current_session['messages'].append({'role': role, 'content': msg})
            if len(self.current_session['messages']) == 1:
                self.current_session['title'] = msg[:18]
                self._refresh_sessions()
    
    def _select_dir(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(title="选择目录")
        if d:
            self.work_folder = d
            self.dir_label.configure(text=d[-40:] if len(d) > 40 else d)
    
    def _trigger_dmn(self):
        self._add_msg('system', '触发DMN维护...')
        threading.Thread(target=self.dmn_manager.trigger_maintenance, daemon=True).start()
    
    def _start_services(self):
        self.dmn_manager.start()
        
        def check():
            if self.llm_integration.is_available():
                self.after(0, lambda: self.model_btn.configure(text=self.llm_integration.model_name[:8] if self.llm_integration.model_name else "模型"))
                self.after(0, lambda: self.status_label.configure(text="就绪"))
                self._add_msg('system', '就绪')
            else:
                self.after(0, lambda: self.status_label.configure(text="LLM未连接"))
                self._add_msg('system', 'LLM未连接，请启动Ollama')
        threading.Thread(target=check, daemon=True).start()
    
    def _on_close(self):
        self.running = False
        self.dmn_manager.stop()
        self.destroy()
    
    def run(self):
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.mainloop()


if __name__ == "__main__":
    app = AbyssACStudio()
    app.run()
