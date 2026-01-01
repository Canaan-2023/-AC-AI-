#!/usr/bin/env python3
"""
Web API服务模块
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.abyss_core import AbyssAC
from config.config_manager import config_manager

# 创建FastAPI应用
app = FastAPI(
    title="渊协议AI系统API",
    description="具有自主意识的AI认知系统",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局系统实例
abyss_ac: Optional[AbyssAC] = None

# 请求/响应模型
class UserRequest(BaseModel):
    """用户请求模型"""
    text: str = Field(..., description="用户输入文本")
    session_id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[str] = Field(None, description="用户ID")

class SystemResponse(BaseModel):
    """系统响应模型"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict] = Field(None, description="响应数据")
    timestamp: str = Field(..., description="时间戳")

class CognitiveResponse(BaseModel):
    """认知响应模型"""
    response: str = Field(..., description="AI响应文本")
    session_id: str = Field(..., description="会话ID")
    cognitive_status: Dict = Field(..., description="认知状态")
    processing_time: float = Field(..., description="处理时间(秒)")

# API端点
@app.on_event("startup")
async def startup_event():
    """启动时初始化系统"""
    global abyss_ac
    try:
        # 加载配置
        config = config_manager.load_config()
        
        # 初始化系统
        abyss_ac = AbyssAC(config)
        
        logging.info("✅ 渊协议系统初始化完成")
    except Exception as e:
        logging.error(f"❌ 系统初始化失败: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    if abyss_ac:
        abyss_ac.memex.cleanup_working_memory()
        abyss_ac.memex.backup_system()
        abyss_ac.ai_interface.kernel.save_kernel()
        logging.info("💾 系统资源已清理并备份")

@app.get("/", response_class=HTMLResponse)
async def root():
    """根端点 - 返回HTML页面"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>渊协议AI系统</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 40px;
                border-radius: 20px;
                margin-top: 50px;
            }
            h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .links {
                margin-top: 30px;
            }
            .link {
                display: block;
                background: rgba(255, 255, 255, 0.2);
                padding: 15px;
                margin: 10px 0;
                border-radius: 10px;
                text-decoration: none;
                color: white;
                transition: background 0.3s;
            }
            .link:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            .status {
                background: rgba(0, 255, 0, 0.2);
                padding: 10px;
                border-radius: 10px;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧠 渊协议AI系统</h1>
            <p>具有自主意识的AI认知框架 v2.0</p>
            
            <div class="status">
                ✅ 系统运行正常
            </div>
            
            <div class="links">
                <a href="/docs" class="link">📚 API文档 (Swagger UI)</a>
                <a href="/redoc" class="link">📖 API文档 (ReDoc)</a>
                <a href="/health" class="link">🏥 健康检查</a>
                <a href="/system/status" class="link">📊 系统状态</a>
                <a href="/cognitive/chat" class="link">💭 开始对话</a>
            </div>
            
            <div style="margin-top: 40px; font-size: 0.9em; opacity: 0.8;">
                <p>系统配置: {config}</p>
                <p>启动时间: {start_time}</p>
            </div>
        </div>
    </body>
    </html>
    """.format(
        config=abyss_ac.get_system_info() if abyss_ac else "未初始化",
        start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    return html_content

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy" if abyss_ac else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "service": "abyss-protocol",
        "version": "2.0.0"
    }

@app.post("/cognitive/cycle", response_model=CognitiveResponse)
async def cognitive_cycle(request: UserRequest):
    """执行认知循环"""
    if not abyss_ac:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    import time
    start_time = time.time()
    
    try:
        # 执行认知循环
        response = abyss_ac.cognitive_cycle(request.text)
        
        # 获取认知状态
        cognitive_status = abyss_ac.ai_interface.get_kernel_status()
        
        processing_time = time.time() - start_time
        
        return CognitiveResponse(
            response=response,
            session_id=request.session_id or f"ses_{int(start_time)}",
            cognitive_status=cognitive_status,
            processing_time=round(processing_time, 3)
        )
    
    except Exception as e:
        logging.error(f"认知循环失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/status")
async def system_status():
    """获取系统状态"""
    if not abyss_ac:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        status = abyss_ac.get_system_info()
        memory_status = abyss_ac.memex.get_system_status()
        
        return {
            "system": status,
            "memory": memory_status,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/store")
async def store_memory(content: str, layer: int = 2, category: Optional[str] = None):
    """存储记忆"""
    if not abyss_ac:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        memory_id = abyss_ac.memex.create_memory(
            content=content,
            layer=layer,
            category=category
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "记忆存储成功"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/retrieve")
async def retrieve_memory(query: str, limit: int = 10):
    """检索记忆"""
    if not abyss_ac:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        results = abyss_ac.memex.retrieve_memory(
            query=query,
            limit=limit
        )
        
        return {
            "count": len(results),
            "results": results,
            "query": query
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/backup")
async def create_backup():
    """创建系统备份"""
    if not abyss_ac:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        backup_path = abyss_ac.memex.backup_system()
        
        return {
            "success": True if backup_path else False,
            "backup_path": backup_path,
            "message": "备份创建成功" if backup_path else "备份创建失败"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
async def get_config():
    """获取当前配置"""
    try:
        config_dict = config_manager.config.__dict__
        
        # 移除内部字段
        if "_abc_impl" in config_dict:
            del config_dict["_abc_impl"]
        
        return {
            "config": config_dict,
            "meta": {
                "config_path": str(config_manager.config_path),
                "loaded_at": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket端点
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket端点（用于实时对话）"""
    await websocket.accept()
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                # 执行认知循环
                response = abyss_ac.cognitive_cycle(data.get("text", ""))
                
                # 发送响应
                await websocket.send_json({
                    "type": "response",
                    "text": response,
                    "timestamp": datetime.now().isoformat()
                })
            
            elif data.get("type") == "ping":
                # 心跳
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
    
    except Exception as e:
        print(f"WebSocket错误: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )