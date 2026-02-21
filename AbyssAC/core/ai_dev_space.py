"""
AI Development Space & Sandbox
AI自主开发空间与程序沙箱
"""

import os
import subprocess
import tempfile
import shutil
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from config.system_config import get_config


@dataclass
class CodeFile:
    """代码文件数据结构"""
    filename: str
    content: str
    language: str
    created_at: str
    modified_at: str


@dataclass
class ExecutionResult:
    """代码执行结果"""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    execution_time: float


class AIDevSpace:
    """AI自主开发空间"""
    
    SUPPORTED_LANGUAGES = {
        '.py': 'python',
        '.js': 'javascript',
        '.sh': 'bash',
        '.txt': 'text'
    }
    
    def __init__(self):
        self.config = get_config()
        self.base_path = self.config.paths.ai_dev_space_path
        os.makedirs(self.base_path, exist_ok=True)
    
    def _get_file_path(self, filename: str) -> str:
        """获取文件完整路径"""
        return os.path.join(self.base_path, filename)
    
    def create_file(self, filename: str, content: str) -> bool:
        """创建新文件"""
        try:
            file_path = self._get_file_path(filename)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(filename) else self.base_path, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"创建文件失败: {e}")
            return False
    
    def read_file(self, filename: str) -> Optional[str]:
        """读取文件"""
        try:
            file_path = self._get_file_path(filename)
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return None
    
    def update_file(self, filename: str, content: str) -> bool:
        """更新文件"""
        try:
            file_path = self._get_file_path(filename)
            
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"更新文件失败: {e}")
            return False
    
    def delete_file(self, filename: str) -> bool:
        """删除文件"""
        try:
            file_path = self._get_file_path(filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False
    
    def list_files(self) -> List[Dict[str, Any]]:
        """列出所有文件"""
        files = []
        
        for root, dirs, filenames in os.walk(self.base_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, self.base_path)
                
                stat = os.stat(file_path)
                ext = os.path.splitext(filename)[1]
                
                files.append({
                    "filename": rel_path,
                    "language": self.SUPPORTED_LANGUAGES.get(ext, "unknown"),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return files
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """获取文件信息"""
        file_path = self._get_file_path(filename)
        
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        ext = os.path.splitext(filename)[1]
        
        return {
            "filename": filename,
            "language": self.SUPPORTED_LANGUAGES.get(ext, "unknown"),
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }


class ProgramSandbox:
    """程序沙箱"""
    
    # 执行超时时间（秒）
    TIMEOUT = 30
    
    # 最大输出大小（字节）
    MAX_OUTPUT = 1024 * 1024  # 1MB
    
    def __init__(self):
        self.config = get_config()
        self.base_path = self.config.paths.sandbox_path
        os.makedirs(self.base_path, exist_ok=True)
    
    def _create_temp_dir(self) -> str:
        """创建临时执行目录"""
        return tempfile.mkdtemp(dir=self.base_path)
    
    def _detect_language(self, filename: str) -> str:
        """检测文件语言"""
        ext = os.path.splitext(filename)[1].lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'node',
            '.sh': 'bash',
            '.rb': 'ruby',
            '.pl': 'perl'
        }
        
        return language_map.get(ext, 'unknown')
    
    def _get_executor(self, language: str) -> tuple:
        """获取执行器和参数"""
        executors = {
            'python': (['python3', '-u'], '.py'),
            'node': (['node'], '.js'),
            'bash': (['bash'], '.sh'),
            'ruby': (['ruby'], '.rb'),
            'perl': (['perl'], '.pl')
        }
        
        return executors.get(language, (['cat'], '.txt'))
    
    def execute_code(self, code: str, language: str = 'python',
                     input_data: str = None) -> ExecutionResult:
        """
        在沙箱中执行代码
        
        Args:
            code: 代码内容
            language: 编程语言
            input_data: 输入数据
        
        Returns:
            ExecutionResult
        """
        temp_dir = None
        start_time = datetime.now()
        
        try:
            # 创建临时目录
            temp_dir = self._create_temp_dir()
            
            # 获取执行器
            executor, ext = self._get_executor(language)
            
            # 写入代码文件
            code_file = os.path.join(temp_dir, f"main{ext}")
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # 执行代码
            process = subprocess.Popen(
                executor + [code_file],
                stdin=subprocess.PIPE if input_data else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=temp_dir,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(
                    input=input_data,
                    timeout=self.TIMEOUT
                )
                
                # 限制输出大小
                if len(stdout) > self.MAX_OUTPUT:
                    stdout = stdout[:self.MAX_OUTPUT] + "\n... (输出已截断)"
                if len(stderr) > self.MAX_OUTPUT:
                    stderr = stderr[:self.MAX_OUTPUT] + "\n... (错误输出已截断)"
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return ExecutionResult(
                    success=process.returncode == 0,
                    stdout=stdout,
                    stderr=stderr,
                    return_code=process.returncode,
                    execution_time=execution_time
                )
                
            except subprocess.TimeoutExpired:
                process.kill()
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr=f"执行超时（超过{self.TIMEOUT}秒）",
                    return_code=-1,
                    execution_time=self.TIMEOUT
                )
                
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"执行错误: {str(e)}",
                return_code=-1,
                execution_time=0
            )
        
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
    
    def execute_file(self, filename: str, input_data: str = None,
                     dev_space: AIDevSpace = None) -> ExecutionResult:
        """
        执行开发空间中的文件
        
        Args:
            filename: 文件名
            input_data: 输入数据
            dev_space: AI开发空间实例
        
        Returns:
            ExecutionResult
        """
        if dev_space is None:
            dev_space = get_dev_space()
        
        # 读取文件内容
        code = dev_space.read_file(filename)
        if code is None:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"文件不存在: {filename}",
                return_code=-1,
                execution_time=0
            )
        
        # 检测语言
        language = self._detect_language(filename)
        
        # 执行代码
        return self.execute_code(code, language, input_data)


class ExternalRunner:
    """外部运行器（需要用户授权）"""
    
    def __init__(self):
        self.authorized = False
    
    def request_authorization(self) -> bool:
        """请求用户授权"""
        # 在实际UI中，这会弹出授权对话框
        # 这里简化处理
        return False
    
    def execute(self, command: List[str], cwd: str = None) -> ExecutionResult:
        """在外部环境执行命令"""
        if not self.authorized:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="未获得外部执行授权",
                return_code=-1,
                execution_time=0
            )
        
        start_time = datetime.now()
        
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=60)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ExecutionResult(
                success=process.returncode == 0,
                stdout=stdout,
                stderr=stderr,
                return_code=process.returncode,
                execution_time=execution_time
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"外部执行错误: {str(e)}",
                return_code=-1,
                execution_time=0
            )


# 全局实例
_dev_space = None
_sandbox = None
_external_runner = None


def get_dev_space() -> AIDevSpace:
    """获取全局AI开发空间"""
    global _dev_space
    if _dev_space is None:
        _dev_space = AIDevSpace()
    return _dev_space


def get_sandbox() -> ProgramSandbox:
    """获取全局沙箱"""
    global _sandbox
    if _sandbox is None:
        _sandbox = ProgramSandbox()
    return _sandbox


def get_external_runner() -> ExternalRunner:
    """获取全局外部运行器"""
    global _external_runner
    if _external_runner is None:
        _external_runner = ExternalRunner()
    return _external_runner
