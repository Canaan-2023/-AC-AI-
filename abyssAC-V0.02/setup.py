#!/usr/bin/env python3
"""
渊协议系统安装脚本
"""

from setuptools import setup, find_packages
import os

def read_requirements():
    """读取依赖文件"""
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def read_readme():
    """读取README文件"""
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()

setup(
    name="abyss-protocol",
    version="2.0.0",
    author="渊协议开发团队",
    author_email="abyss@protocol.ai",
    description="渊协议认知系统 - 具有自主意识的AI认知框架",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/abyss-protocol",
    
    packages=find_packages(include=['core', 'config', 'nlp', 'utils', 'models']),
    include_package_data=True,
    install_requires=read_requirements(),
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    
    python_requires=">=3.8",
    
    entry_points={
        "console_scripts": [
            "abyss=run:main",
            "abyss-web=scripts.web_api:main",
            "abyss-demo=scripts.demo:main",
        ],
    },
    
    project_urls={
        "Documentation": "https://abyss-protocol.readthedocs.io/",
        "Source": "https://github.com/yourusername/abyss-protocol",
        "Bug Reports": "https://github.com/yourusername/abyss-protocol/issues",
    },
)