#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AbyssAC 启动脚本
自动创建必要的目录和文件
"""

import os
import sys
import json

def ensure_directories():
    """确保所有必要的目录都存在"""
    base_dir = os.path.dirname(__file__)
    
    directories = [
        'storage',
        'storage/nng',
        'storage/Y层记忆库',
        'storage/Y层记忆库/分类记忆',
        'storage/Y层记忆库/元认知记忆',
        'storage/Y层记忆库/高阶整合记忆',
        'storage/Y层记忆库/工作记忆',
        'storage/working_memory',
        'storage/logs',
        'temp',
    ]
    
    for directory in directories:
        path = os.path.join(base_dir, directory)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            print(f"创建目录: {directory}")

def ensure_root_json():
    """确保root.json存在"""
    base_dir = os.path.dirname(__file__)
    root_path = os.path.join(base_dir, 'storage/nng/root.json')
    
    if not os.path.exists(root_path):
        root_content = {
            "一级节点": [],
            "更新时间": ""
        }
        with open(root_path, 'w', encoding='utf-8') as f:
            json.dump(root_content, f, ensure_ascii=False, indent=2)
        print("创建文件: storage/nng/root.json")

def main():
    print("=" * 60)
    print("AbyssAC 系统初始化")
    print("=" * 60)
    
    print("\n检查目录结构...")
    ensure_directories()
    
    print("\n检查必要文件...")
    ensure_root_json()
    
    print("\n初始化完成！")
    print("\n启动方式:")
    print("  - Studio模式: python main.py")
    print("  - CLI模式:    python main.py --cli")
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
