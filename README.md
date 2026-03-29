# AbyssAC

纯文件维持的LLM记忆系统。

## 定位

纯文件维持的LLM记忆系统，通过MCP协议为AI提供持久化记忆能力。

## 使用要求

需要具备文件读写能力。

## 核心特性

- **纯文件存储**：无需数据库，所有记忆以文件形式存储
- **NNG导航网络**：层级化节点结构，快速定位记忆
- **三级记忆体系**：元认知/高阶整合/分类，按价值分层
- **MCP协议**：标准化的指令模板，AI只需执行
- **Reviewer验证**：红黄绿三级检查，确保流程正确


## 安装配置

下载mcp_workflow.py和mcp.json在对应‘ABYSSAC记忆MCP’文件夹

### 环境要求

- Python 3.10+
- 支持MCP协议的IDE（如Trae、Claude Desktop等）

### 配置MCP

将 `mcp.json` 中的配置添加到你的IDE的MCP设置中，将 `{ABYSSAC_ROOT}` 替换为实际路径：

```json
{
  "mcpServers": {
    "abyssac-memory": {
      "command": "python",
      "args": ["mcp_workflow.py"],
      "cwd": "{ABYSSAC_ROOT}/ABYSSAC记忆MCP",
      "env": {
        "ABYSSAC_ROOT": "{ABYSSAC_ROOT}",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```


## 规则

本项目所有使用行为需遵守 **GNU AGPLv3** 开源协议（详见项目根目录 LICENSE 文件）；

若需豁免 AGPLv3 义务（如闭源商用、企业内网部署却不开源、不向用户提供源码）：**必须联系作者获取书面授权**（唯一渠道：CanaanMonika@foxmail.com），未经授权不得豁免义务商用。

## 免责声明

- 本协议仅提供技术参考，使用风险自负，作者不承担连带责任；
- 商用授权细节（费用/范围/权益）双方协商，无预设标准；
- 最终解释权归作者所有。
