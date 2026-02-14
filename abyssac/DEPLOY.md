# AbyssAC 部署说明

## 系统要求

- Python 3.8+
- 支持的操作系统：Linux, macOS, Windows
- 内存：至少 2GB RAM
- 磁盘空间：至少 1GB 可用空间

## 部署步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 配置LLM

编辑 `config.yaml` 文件，配置您的LLM服务：

#### 使用Ollama（推荐）

```yaml
llm:
  provider: "ollama"
  base_url: "http://localhost:11434"
  model: "qwen2.5:14b"  # 或其他模型
  temperature: 0.7
  max_tokens: 4096
  timeout: 30
```

确保Ollama已安装并运行：
```bash
ollama run qwen2.5:14b
```

#### 使用OpenAI API

```yaml
llm:
  provider: "openai"
  base_url: "https://api.openai.com/v1"
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 4096
  timeout: 30
```

### 3. 启动系统

```bash
python start.py
```

系统将在 http://localhost:8080 启动

### 4. 访问系统

打开浏览器访问：http://localhost:8080

## Docker部署（可选）

### 构建镜像

```bash
docker build -t abyssac .
```

### 运行容器

```bash
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/storage:/app/storage \
  --name abyssac \
  abyssac
```

## 系统配置

### 沙盒配置

```yaml
sandbox:
  max_navigation_depth: 10    # 最大导航深度
  navigation_timeout: 30      # 导航超时时间（秒）
  max_retries: 1              # 最大重试次数
```

### DMN配置

```yaml
dmn:
  idle_trigger_seconds: 300   # 空闲触发时间（5分钟）
  max_working_memories: 20    # 工作记忆阈值
  max_navigation_failures: 5  # 导航失败阈值
```

## 目录权限

确保以下目录可写：
- `storage/`
- `storage/nng/`
- `storage/Y层记忆库/`
- `storage/logs/`

## 日志查看

系统日志位于：
- 导航日志：`storage/logs/navigation/`
- 错误日志：`storage/logs/error/`
- DMN日志：`storage/logs/dmn/`

## 故障排查

### 问题：LLM连接失败

**解决方案**：
1. 检查LLM服务是否运行
2. 检查 `config.yaml` 中的 `base_url` 配置
3. 检查网络连接

### 问题：文件权限错误

**解决方案**：
```bash
chmod -R 755 storage/
```

### 问题：端口被占用

**解决方案**：
修改 `start.py` 中的端口：
```python
uvicorn.run(
    "src.main:app",
    host="0.0.0.0",
    port=8081,  # 修改端口
    ...
)
```

## 生产环境部署

### 使用Gunicorn

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app -b 0.0.0.0:8080
```

### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 备份与恢复

### 备份

```bash
tar -czf abyssac_backup_$(date +%Y%m%d).tar.gz storage/
```

### 恢复

```bash
tar -xzf abyssac_backup_20260214.tar.gz
```

## 更新系统

1. 备份数据
2. 拉取最新代码
3. 更新依赖
4. 重启服务

```bash
# 备份
tar -czf backup.tar.gz storage/

# 更新
git pull
pip install -r requirements.txt

# 重启
python start.py
```
