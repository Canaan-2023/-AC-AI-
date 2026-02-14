"""
AbyssAC 主应用模块
FastAPI后端API
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import StorageManager
from llm_client import LLMClient
from sandbox import SandboxOrchestrator, SandboxState
from dmn import DMN, DMNTaskType
from session import session_manager


# 全局实例
llm_client = LLMClient()
sandbox_orchestrator = SandboxOrchestrator()
dmn = DMN()


# 请求模型
class ChatRequest(BaseModel):
    session_id: str
    input: str


class DMNTriggerRequest(BaseModel):
    task_type: str


class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    message_count: int


# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("AbyssAC 系统启动...")
    
    # 启动后台任务
    asyncio.create_task(dmn_monitor_task())
    
    yield
    
    # 关闭时清理
    print("AbyssAC 系统关闭...")


app = FastAPI(title="AbyssAC API", lifespan=lifespan)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")


# ============== 前端路由 ==============

@app.get("/", response_class=HTMLResponse)
async def root():
    """主页"""
    return FileResponse("static/index.html")


# ============== API路由 ==============

@app.post("/api/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    发送用户输入，启动沙盒流程
    
    请求体:
    {
        "session_id": "会话ID",
        "input": "用户输入"
    }
    
    返回:
    {
        "task_id": "任务ID",
        "status": "processing",
        "session_id": "会话ID"
    }
    """
    # 获取或创建会话
    session = session_manager.get_or_create_session(request.session_id)
    
    # 添加用户消息
    session_manager.add_message(request.session_id, "user", request.input)
    
    # 获取对话历史
    history = session_manager.get_history(request.session_id, 10)
    
    # 启动沙盒流程（异步）
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.session_id[:8]}"
    
    # 在后台执行沙盒流程
    background_tasks.add_task(
        execute_sandbox_flow,
        task_id,
        request.session_id,
        request.input,
        history
    )
    
    return {
        "task_id": task_id,
        "status": "processing",
        "session_id": request.session_id
    }


async def execute_sandbox_flow(task_id: str, session_id: str, 
                               user_input: str, history: List[Dict[str, str]]):
    """执行沙盒流程（后台任务）"""
    try:
        result = await sandbox_orchestrator.process(user_input, session_id, history)
        
        # 添加AI回复到会话
        if "final_response" in result:
            session_manager.add_message(
                session_id, 
                "assistant", 
                result["final_response"]
            )
        
        # 保存任务结果（可以存储到内存或数据库）
        # 这里简化处理，实际应该使用Redis等
        
    except Exception as e:
        print(f"沙盒流程执行失败: {e}")
        # 记录错误
        StorageManager.write_error_log({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "SANDBOX_EXECUTION_ERROR",
            "task_id": task_id,
            "session_id": session_id,
            "error": str(e)
        })


@app.get("/api/sandbox/status/{task_id}")
async def get_sandbox_status(task_id: str, session_id: str):
    """
    获取沙盒状态
    
    参数:
    - task_id: 任务ID
    - session_id: 会话ID
    
    返回沙盒当前层、中间数据等
    """
    # 获取会话的沙盒状态
    sandbox_state = session_manager.get_sandbox_state(session_id)
    
    if sandbox_state is None:
        # 如果没有状态，返回默认状态
        return {
            "task_id": task_id,
            "currentLayer": 1,
            "path": ["root"],
            "currentNode": "root",
            "completed": False,
            "selectedMemories": [],
            "selectedNNGs": []
        }
    
    return {
        "task_id": task_id,
        "currentLayer": sandbox_state.get("layer", 1),
        "path": sandbox_state.get("navigation_path", ["root"]),
        "currentNode": sandbox_state.get("current_position", "root"),
        "completed": sandbox_state.get("completed", False),
        "selectedMemories": sandbox_state.get("selected_memories", []),
        "selectedNNGs": sandbox_state.get("selected_nngs", []),
        "error": sandbox_state.get("error")
    }


@app.get("/api/session/history")
async def get_session_history(session_id: str, count: int = 10):
    """
    获取会话历史
    
    参数:
    - session_id: 会话ID
    - count: 返回消息数量（默认10）
    
    返回对话历史列表
    """
    history = session_manager.get_history(session_id, count)
    return {
        "session_id": session_id,
        "history": history,
        "count": len(history)
    }


@app.post("/api/session/new")
async def create_new_session():
    """
    创建新会话
    
    返回新会话ID
    """
    session = session_manager.create_session()
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat()
    }


@app.get("/api/session/list")
async def list_sessions():
    """
    列出所有会话
    
    返回会话列表
    """
    sessions = session_manager.list_sessions()
    return {
        "sessions": sessions,
        "count": len(sessions)
    }


@app.get("/api/nng/tree")
async def get_nng_tree():
    """
    获取NNG树结构
    
    返回树状结构
    """
    tree = StorageManager.list_nng_tree()
    return tree


@app.get("/api/nng/node/{node_id}")
async def get_nng_node(node_id: str):
    """
    获取NNG节点详情
    
    参数:
    - node_id: 节点ID（如 "1.2.3" 或 "root"）
    
    返回节点JSON数据
    """
    node_data = StorageManager.read_nng(node_id)
    
    if node_data is None:
        raise HTTPException(status_code=404, detail=f"节点 {node_id} 不存在")
    
    return {
        "node_id": node_id,
        "data": node_data
    }


@app.get("/api/memories/stats")
async def get_memory_stats():
    """
    获取记忆统计
    
    返回各类记忆数量
    """
    stats = StorageManager.get_memory_stats()
    return stats


@app.get("/api/dmn/status")
async def get_dmn_status():
    """
    获取DMN状态
    
    返回是否运行、当前任务、进度
    """
    return dmn.get_status()


@app.get("/api/dmn/logs")
async def get_dmn_logs(limit: int = 10):
    """
    获取DMN日志
    
    参数:
    - limit: 返回日志数量（默认10）
    
    返回最近任务日志
    """
    # 从日志目录读取
    from pathlib import Path
    logs_dir = Path("storage/logs/dmn")
    if not logs_dir.exists():
        return {"logs": [], "count": 0}
    
    log_files = sorted(logs_dir.glob("*.json"), reverse=True)[:limit]
    
    logs = []
    for log_file in log_files:
        try:
            import json
            with open(log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                logs.append(log_data)
        except Exception:
            continue
    
    return {
        "logs": logs,
        "count": len(logs)
    }


@app.post("/api/dmn/trigger")
async def trigger_dmn(request: DMNTriggerRequest):
    """
    手动触发DMN任务
    
    请求体:
    {
        "task_type": "memory/assoc/bias/strategy/concept"
    }
    
    返回任务启动结果
    """
    # 映射任务类型
    task_type_map = {
        "memory": DMNTaskType.MEMORY_INTEGRATION,
        "assoc": DMNTaskType.ASSOCIATION_DISCOVERY,
        "bias": DMNTaskType.BIAS_REVIEW,
        "strategy": DMNTaskType.STRATEGY_REHEARSAL,
        "concept": DMNTaskType.CONCEPT_RECOMBINATION
    }
    
    task_type = task_type_map.get(request.task_type)
    if task_type is None:
        raise HTTPException(status_code=400, detail=f"无效的任务类型: {request.task_type}")
    
    # 获取上下文
    context = {
        "work_memories": [],  # 实际应该获取工作记忆
        "navigation_failures": 0,  # 实际应该获取导航失败次数
        "timestamp": datetime.now().isoformat()
    }
    
    # 运行DMN任务（同步）
    result = dmn.run_task(task_type, context)
    
    return {
        "task_type": request.task_type,
        "status": "started" if "error" not in result else "failed",
        "result": result
    }


@app.get("/api/system/status")
async def get_system_status():
    """
    获取系统整体状态
    
    返回系统状态概览
    """
    memory_stats = StorageManager.get_memory_stats()
    session_stats = session_manager.get_stats()
    dmn_status = dmn.get_status()
    
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "memory": memory_stats,
        "sessions": session_stats,
        "dmn": dmn_status
    }


# ============== 后台任务 ==============

async def dmn_monitor_task():
    """DMN监控任务（定期检查是否需要触发DMN）"""
    while True:
        try:
            # 获取统计信息
            memory_stats = StorageManager.get_memory_stats()
            working_memory_count = memory_stats.get("working", 0)
            
            # 获取导航失败次数（简化处理，实际应该读取日志）
            navigation_failures = 0
            
            # 检查是否需要触发DMN
            task_type = dmn.check_auto_trigger(
                working_memory_count,
                navigation_failures,
                datetime.now()  # 简化处理
            )
            
            if task_type and not dmn.get_status()["is_running"]:
                context = {
                    "work_memories": [],
                    "navigation_failures": navigation_failures,
                    "timestamp": datetime.now().isoformat()
                }
                
                # 在后台运行DMN任务
                asyncio.create_task(run_dmn_task_async(task_type, context))
            
            # 每分钟检查一次
            await asyncio.sleep(60)
        
        except Exception as e:
            print(f"DMN监控任务异常: {e}")
            await asyncio.sleep(60)


async def run_dmn_task_async(task_type: DMNTaskType, context: Dict[str, Any]):
    """异步运行DMN任务"""
    # 使用线程池运行同步的DMN任务
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, dmn.run_task, task_type, context)
    print(f"DMN任务 {task_type.value} 完成: {result.get('status', 'unknown')}")


# ============== 启动 ==============

if __name__ == "__main__":
    import uvicorn
    
    # 确保存储目录存在
    os.makedirs("storage/nng", exist_ok=True)
    os.makedirs("storage/Y层记忆库", exist_ok=True)
    os.makedirs("storage/logs", exist_ok=True)
    os.makedirs("prompts", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )
