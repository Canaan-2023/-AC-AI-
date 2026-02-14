#!/usr/bin/env python3
"""
AbyssAC 启动脚本
"""

import os
import sys

# 设置工作目录为脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# 确保目录存在
os.makedirs("storage/nng", exist_ok=True)
os.makedirs("storage/Y层记忆库/分类记忆/高价值", exist_ok=True)
os.makedirs("storage/Y层记忆库/分类记忆/中价值", exist_ok=True)
os.makedirs("storage/Y层记忆库/分类记忆/低价值", exist_ok=True)
os.makedirs("storage/Y层记忆库/高阶整合记忆", exist_ok=True)
os.makedirs("storage/Y层记忆库/元认知记忆", exist_ok=True)
os.makedirs("storage/Y层记忆库/工作记忆", exist_ok=True)
os.makedirs("storage/logs/navigation", exist_ok=True)
os.makedirs("storage/logs/error", exist_ok=True)
os.makedirs("storage/logs/dmn", exist_ok=True)
os.makedirs("prompts", exist_ok=True)
os.makedirs("static", exist_ok=True)

# 初始化memory_counter.txt
if not os.path.exists("storage/memory_counter.txt"):
    with open("storage/memory_counter.txt", "w") as f:
        f.write("0")

# 初始化root.json
if not os.path.exists("storage/nng/root.json"):
    with open("storage/nng/root.json", "w", encoding="utf-8") as f:
        f.write('{"一级节点": [], "更新时间": "2026-02-14 00:00:00"}')

# 启动应用
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("AbyssAC 人工意识系统")
    print("=" * 50)
    print("\n系统正在启动...")
    print("访问地址: http://localhost:8080")
    print("\n按 Ctrl+C 停止系统\n")
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )
