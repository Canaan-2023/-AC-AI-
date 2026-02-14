FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p storage/nng \
    storage/Y层记忆库/分类记忆/高价值 \
    storage/Y层记忆库/分类记忆/中价值 \
    storage/Y层记忆库/分类记忆/低价值 \
    storage/Y层记忆库/高阶整合记忆 \
    storage/Y层记忆库/元认知记忆 \
    storage/Y层记忆库/工作记忆 \
    storage/logs/navigation \
    storage/logs/error \
    storage/logs/dmn

# 初始化文件
RUN echo "0" > storage/memory_counter.txt && \
    echo '{"一级节点": [], "更新时间": "2026-02-14 00:00:00"}' > storage/nng/root.json

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "start.py"]
