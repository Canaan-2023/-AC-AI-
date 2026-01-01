#!/usr/bin/env python3
"""
自定义异常模块
"""

class AbyssError(Exception):
    """渊协议基础异常"""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ConfigError(AbyssError):
    """配置错误"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "CONFIG_ERROR", details)

class ValidationError(AbyssError):
    """验证错误"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {"field": field, "value": value}
        super().__init__(message, "VALIDATION_ERROR", details)

class MemoryError(AbyssError):
    """记忆系统错误"""
    def __init__(self, message: str, memory_id: str = None, layer: int = None):
        details = {"memory_id": memory_id, "layer": layer}
        super().__init__(message, "MEMORY_ERROR", details)

class KernelError(AbyssError):
    """认知内核错误"""
    def __init__(self, message: str, kernel_status: dict = None):
        details = {"kernel_status": kernel_status}
        super().__init__(message, "KERNEL_ERROR", details)

class AIError(AbyssError):
    """AI模型错误"""
    def __init__(self, message: str, model_type: str = None, api_response: dict = None):
        details = {"model_type": model_type, "api_response": api_response}
        super().__init__(message, "AI_ERROR", details)

class TopologyError(AbyssError):
    """拓扑错误"""
    def __init__(self, message: str, path_id: str = None, quality: float = None):
        details = {"path_id": path_id, "quality": quality}
        super().__init__(message, "TOPOLOGY_ERROR", details)

class EvaluationError(AbyssError):
    """评估错误"""
    def __init__(self, message: str, session_id: str = None, score: float = None):
        details = {"session_id": session_id, "score": score}
        super().__init__(message, "EVALUATION_ERROR", details)

class IterationError(AbyssError):
    """迭代错误"""
    def __init__(self, message: str, iteration_id: str = None, root_cause: str = None):
        details = {"iteration_id": iteration_id, "root_cause": root_cause}
        super().__init__(message, "ITERATION_ERROR", details)

class ResourceError(AbyssError):
    """资源错误（内存、磁盘等）"""
    def __init__(self, message: str, resource_type: str = None, usage_percent: float = None):
        details = {"resource_type": resource_type, "usage_percent": usage_percent}
        super().__init__(message, "RESOURCE_ERROR", details)

class TimeoutError(AbyssError):
    """超时错误"""
    def __init__(self, message: str, timeout_seconds: float = None, operation: str = None):
        details = {"timeout_seconds": timeout_seconds, "operation": operation}
        super().__init__(message, "TIMEOUT_ERROR", details)

class CacheError(AbyssError):
    """缓存错误"""
    def __init__(self, message: str, cache_type: str = None, key: str = None):
        details = {"cache_type": cache_type, "key": key}
        super().__init__(message, "CACHE_ERROR", details)

class IntegrityError(AbyssError):
    """数据完整性错误"""
    def __init__(self, message: str, data_type: str = None, corruption_details: dict = None):
        details = {"data_type": data_type, "corruption_details": corruption_details}
        super().__init__(message, "INTEGRITY_ERROR", details)

class RecoveryError(AbyssError):
    """恢复错误"""
    def __init__(self, message: str, recovery_type: str = None, backup_path: str = None):
        details = {"recovery_type": recovery_type, "backup_path": backup_path}
        super().__init__(message, "RECOVERY_ERROR", details)

class RateLimitError(AbyssError):
    """速率限制错误"""
    def __init__(self, message: str, limit: int = None, remaining: int = None):
        details = {"limit": limit, "remaining": remaining}
        super().__init__(message, "RATE_LIMIT_ERROR", details)

class SecurityError(AbyssError):
    """安全错误"""
    def __init__(self, message: str, threat_type: str = None, severity: str = "MEDIUM"):
        details = {"threat_type": threat_type, "severity": severity}
        super().__init__(message, "SECURITY_ERROR", details)

class ErrorHandler:
    """错误处理器"""
    
    @staticmethod
    def handle_error(error: Exception, context: dict = None) -> dict:
        """处理错误并返回标准化的错误响应"""
        context = context or {}
        
        # 如果是渊协议异常，直接使用其属性
        if isinstance(error, AbyssError):
            return {
                "success": False,
                "error": {
                    "code": error.error_code,
                    "message": error.message,
                    "details": error.details,
                    "type": error.__class__.__name__
                },
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
        
        # 对于其他异常，进行包装
        return {
            "success": False,
            "error": {
                "code": "UNEXPECTED_ERROR",
                "message": str(error),
                "details": {
                    "exception_type": error.__class__.__name__,
                    "traceback": ErrorHandler.get_traceback(error)
                },
                "type": "UnexpectedError"
            },
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_traceback(error: Exception) -> str:
        """获取异常的traceback"""
        import traceback
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    
    @staticmethod
    def should_retry(error: Exception, retry_count: int) -> bool:
        """判断是否应该重试"""
        if retry_count >= 3:  # 最大重试次数
            return False
        
        # 某些错误应该重试
        retryable_errors = [
            TimeoutError,
            RateLimitError,
            AIError  # AI错误有时是暂时的
        ]
        
        for error_type in retryable_errors:
            if isinstance(error, error_type):
                return True
        
        # 网络相关错误
        error_str = str(error).lower()
        network_keywords = ["timeout", "connection", "network", "socket", "retry"]
        for keyword in network_keywords:
            if keyword in error_str:
                return True
        
        return False
    
    @staticmethod
    def log_error(error: Exception, logger=None, level: str = "ERROR"):
        """记录错误"""
        if logger:
            error_response = ErrorHandler.handle_error(error)
            log_message = f"错误: {error_response['error']['code']} - {error_response['error']['message']}"
            
            if level == "ERROR":
                logger.error(log_message)
            elif level == "WARNING":
                logger.warning(log_message)
            else:
                logger.info(log_message)

# 全局错误处理器实例
error_handler = ErrorHandler()