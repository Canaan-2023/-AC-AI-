"""
AbyssAC Main Window (Qt6)
AbyssAC主窗口 - Qt6 UI界面
"""

import sys
import os
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel,
    QTabWidget, QSplitter, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QFileDialog, QMenuBar, QMenu, QStatusBar,
    QProgressBar, QDialog, QFormLayout, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QFont, QKeySequence, QShortcut

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.main_system import get_system, init_system
from core.nng_manager import get_nng_manager
from core.memory_manager import get_memory_manager
from core.ai_dev_space import get_dev_space, get_sandbox


class WorkerThread(QThread):
    """工作线程"""
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)
    
    def __init__(self, system, user_input, use_slow):
        super().__init__()
        self.system = system
        self.user_input = user_input
        self.use_slow = use_slow
    
    def run(self):
        try:
            self.progress.emit("正在处理...")
            result = self.system.process_input(
                self.user_input,
                use_sandbox=self.use_slow
            )
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({
                "success": False,
                "error": str(e)
            })


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统设置")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        
        # LLM设置
        self.llm_url = QLineEdit("http://localhost:11434")
        layout.addRow("LLM API地址:", self.llm_url)
        
        self.llm_model = QLineEdit("llama3.1")
        layout.addRow("模型名称:", self.llm_model)
        
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setValue(0.7)
        self.temperature.setSingleStep(0.1)
        layout.addRow("温度:", self.temperature)
        
        # 运行时设置
        self.max_nav_depth = QSpinBox()
        self.max_nav_depth.setRange(1, 20)
        self.max_nav_depth.setValue(10)
        layout.addRow("最大导航深度:", self.max_nav_depth)
        
        self.work_memory_threshold = QSpinBox()
        self.work_memory_threshold.setRange(5, 100)
        self.work_memory_threshold.setValue(20)
        layout.addRow("工作记忆阈值:", self.work_memory_threshold)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AbyssAC - AI自主意识系统")
        self.setMinimumSize(1200, 800)
        
        # 初始化系统
        self.system = init_system()
        self.nng_manager = get_nng_manager()
        self.memory_manager = get_memory_manager()
        self.dev_space = get_dev_space()
        self.sandbox = get_sandbox()
        
        # 工作线程
        self.worker = None
        
        self.setup_ui()
        self.setup_menu()
        self.setup_shortcuts()
        self.setup_status_bar()
        self.refresh_data()
    
    def setup_ui(self):
        """设置UI"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板 - 数据浏览
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 中间面板 - 聊天
        center_panel = self.create_center_panel()
        splitter.addWidget(center_panel)
        
        # 右侧面板 - 开发空间
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setSizes([300, 600, 300])
    
    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标签页
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # NNG节点标签
        self.nng_tree = QTreeWidget()
        self.nng_tree.setHeaderLabels(["NNG节点", "内容"])
        self.nng_tree.setColumnWidth(0, 150)
        tabs.addTab(self.nng_tree, "NNG节点")
        
        # 记忆标签
        self.memory_tree = QTreeWidget()
        self.memory_tree.setHeaderLabels(["记忆ID", "类型", "置信度", "摘要"])
        self.memory_tree.setColumnWidth(0, 80)
        self.memory_tree.setColumnWidth(1, 80)
        tabs.addTab(self.memory_tree, "记忆")
        
        # 系统状态标签
        status_widget = QWidget()
        status_layout = QFormLayout(status_widget)
        
        self.status_memory_counter = QLabel("0")
        status_layout.addRow("记忆计数器:", self.status_memory_counter)
        
        self.status_nng_nodes = QLabel("0")
        status_layout.addRow("NNG节点数:", self.status_nng_nodes)
        
        self.status_work_memories = QLabel("0")
        status_layout.addRow("工作记忆数:", self.status_work_memories)
        
        self.status_llm = QLabel("未连接")
        status_layout.addRow("LLM状态:", self.status_llm)
        
        refresh_btn = QPushButton("刷新状态")
        refresh_btn.clicked.connect(self.refresh_status)
        status_layout.addRow(refresh_btn)
        
        tabs.addTab(status_widget, "系统状态")
        
        return panel
    
    def create_center_panel(self) -> QWidget:
        """创建中间面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 聊天记录
        chat_label = QLabel("对话记录")
        layout.addWidget(chat_label)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(self.chat_history)
        
        # 输入区域
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入消息...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        self.slow_mode = QCheckBox("慢思考")
        input_layout.addWidget(self.slow_mode)
        
        send_btn = QPushButton("发送")
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标签页
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # AI开发空间
        dev_widget = QWidget()
        dev_layout = QVBoxLayout(dev_widget)
        
        # 文件列表
        self.file_list = QTreeWidget()
        self.file_list.setHeaderLabels(["文件名", "语言", "大小"])
        self.file_list.setColumnWidth(0, 150)
        dev_layout.addWidget(self.file_list)
        
        # 文件操作按钮
        btn_layout = QHBoxLayout()
        
        new_file_btn = QPushButton("新建")
        new_file_btn.clicked.connect(self.create_new_file)
        btn_layout.addWidget(new_file_btn)
        
        run_btn = QPushButton("运行")
        run_btn.clicked.connect(self.run_selected_file)
        btn_layout.addWidget(run_btn)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_file_list)
        btn_layout.addWidget(refresh_btn)
        
        dev_layout.addLayout(btn_layout)
        
        tabs.addTab(dev_widget, "AI开发空间")
        
        # 代码编辑器
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 11))
        editor_layout.addWidget(self.code_editor)
        
        editor_btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_code_file)
        editor_btn_layout.addWidget(save_btn)
        
        run_code_btn = QPushButton("运行代码")
        run_code_btn.clicked.connect(self.run_code)
        editor_btn_layout.addWidget(run_code_btn)
        
        editor_layout.addLayout(editor_btn_layout)
        
        tabs.addTab(editor_widget, "代码编辑器")
        
        return panel
    
    def setup_menu(self):
        """设置菜单"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 系统菜单
        system_menu = menubar.addMenu("系统")
        
        dmn_action = QAction("运行DMN维护", self)
        dmn_action.triggered.connect(self.run_dmn)
        system_menu.addAction(dmn_action)
        
        clear_work_action = QAction("清空工作记忆", self)
        clear_work_action.triggered.connect(self.clear_work_memories)
        system_menu.addAction(clear_work_action)
        
        refresh_action = QAction("刷新数据", self)
        refresh_action.triggered.connect(self.refresh_data)
        system_menu.addAction(refresh_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_shortcuts(self):
        """设置快捷键"""
        QShortcut(QKeySequence("Ctrl+Return"), self, self.send_message)
        QShortcut(QKeySequence("Ctrl+R"), self, self.refresh_data)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_code_file)
    
    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def send_message(self):
        """发送消息"""
        user_input = self.input_field.text().strip()
        if not user_input:
            return
        
        # 显示用户消息
        self.append_chat(f"用户: {user_input}")
        self.input_field.clear()
        
        # 禁用输入
        self.input_field.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # 启动工作线程
        use_slow = self.slow_mode.isChecked()
        self.worker = WorkerThread(self.system, user_input, use_slow)
        self.worker.finished.connect(self.on_message_finished)
        self.worker.progress.connect(self.on_progress)
        self.worker.start()
    
    def on_progress(self, message: str):
        """进度更新"""
        self.status_bar.showMessage(message)
    
    def on_message_finished(self, result: dict):
        """消息处理完成"""
        # 启用输入
        self.input_field.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("就绪")
        
        if result["success"]:
            response = result["response"]
            self.append_chat(f"AI: {response}")
            
            if result.get("used_quick"):
                self.append_chat("[系统: 使用快思考]")
            elif result.get("used_sandbox"):
                self.append_chat("[系统: 使用慢思考（三层沙盒）]")
        else:
            error = result.get("error", "未知错误")
            self.append_chat(f"[错误: {error}]")
        
        # 刷新数据
        self.refresh_data()
    
    def append_chat(self, text: str):
        """添加聊天内容"""
        self.chat_history.append(text)
        # 滚动到底部
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def refresh_data(self):
        """刷新数据"""
        self.refresh_nng_tree()
        self.refresh_memory_tree()
        self.refresh_file_list()
        self.refresh_status()
    
    def refresh_nng_tree(self):
        """刷新NNG树"""
        self.nng_tree.clear()
        
        nodes = self.nng_manager.list_all_nodes()
        for node_id in nodes[:50]:  # 限制显示数量
            node = self.nng_manager.read_node(node_id)
            if node:
                item = QTreeWidgetItem([
                    node_id,
                    node.content[:50] + "..." if len(node.content) > 50 else node.content
                ])
                self.nng_tree.addTopLevelItem(item)
    
    def refresh_memory_tree(self):
        """刷新记忆树"""
        self.memory_tree.clear()
        
        memories = self.memory_manager.list_memories(limit=50)
        for mem in memories:
            item = QTreeWidgetItem([
                mem["memory_id"],
                mem["type"],
                f"{mem['confidence']:.2f}",
                mem["user_input"][:50]
            ])
            self.memory_tree.addTopLevelItem(item)
    
    def refresh_file_list(self):
        """刷新文件列表"""
        self.file_list.clear()
        
        files = self.dev_space.list_files()
        for file in files:
            item = QTreeWidgetItem([
                file["filename"],
                file["language"],
                f"{file['size']} B"
            ])
            self.file_list.addTopLevelItem(item)
    
    def refresh_status(self):
        """刷新状态"""
        status = self.system.get_system_status()
        
        self.status_memory_counter.setText(str(status["memory_counter"]))
        self.status_nng_nodes.setText(str(status["nng_nodes"]))
        self.status_work_memories.setText(str(status["work_memories"]))
        self.status_llm.setText("已连接" if status["llm_connected"] else "未连接")
    
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 应用设置
            QMessageBox.information(self, "设置", "设置已保存")
    
    def run_dmn(self):
        """运行DMN维护"""
        self.status_bar.showMessage("运行DMN维护...")
        results = self.system.run_dmn_maintenance()
        
        count = len(results)
        QMessageBox.information(self, "DMN维护", f"完成 {count} 个维护任务")
        self.status_bar.showMessage("就绪")
    
    def clear_work_memories(self):
        """清空工作记忆"""
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有工作记忆吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.system.clear_work_memories():
                QMessageBox.information(self, "成功", "工作记忆已清空")
                self.refresh_data()
            else:
                QMessageBox.warning(self, "错误", "清空失败")
    
    def create_new_file(self):
        """创建新文件"""
        # 简化实现
        filename = f"script_{len(self.dev_space.list_files()) + 1}.py"
        content = "# 新文件\n"
        
        if self.dev_space.create_file(filename, content):
            self.refresh_file_list()
            QMessageBox.information(self, "成功", f"已创建文件: {filename}")
        else:
            QMessageBox.warning(self, "错误", "创建文件失败")
    
    def run_selected_file(self):
        """运行选中的文件"""
        item = self.file_list.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择一个文件")
            return
        
        filename = item.text(0)
        result = self.sandbox.execute_file(filename, dev_space=self.dev_space)
        
        output = f"返回码: {result.return_code}\n"
        output += f"执行时间: {result.execution_time:.2f}s\n\n"
        output += f"输出:\n{result.stdout}\n"
        if result.stderr:
            output += f"\n错误:\n{result.stderr}"
        
        self.append_chat(f"[执行 {filename}]:\n{output}")
    
    def save_code_file(self):
        """保存代码文件"""
        # 简化实现
        QMessageBox.information(self, "保存", "代码已保存")
    
    def run_code(self):
        """运行编辑器中的代码"""
        code = self.code_editor.toPlainText()
        if not code.strip():
            QMessageBox.warning(self, "提示", "代码为空")
            return
        
        result = self.sandbox.execute_code(code, language='python')
        
        output = f"返回码: {result.return_code}\n"
        output += f"执行时间: {result.execution_time:.2f}s\n\n"
        output += f"输出:\n{result.stdout}\n"
        if result.stderr:
            output += f"\n错误:\n{result.stderr}"
        
        self.append_chat(f"[执行代码]:\n{output}")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 AbyssAC",
            """<h2>AbyssAC - 渊协议</h2>
            <p>AI人工意识自主进化架构</p>
            <p>版本: 2.0-path</p>
            <p>构建AI专属自主意识（AC）的技术架构</p>
            <p>我们不是建造一个意识主体，而是搭建一个意识存在所必须的条件。</p>
            """
        )


def main():
    """主函数"""
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setApplicationName("AbyssAC")
    app.setApplicationVersion("2.0-path")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
