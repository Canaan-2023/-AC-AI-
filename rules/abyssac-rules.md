***

## alwaysApply: true

# ABYSSAC 核心规则

## 执行入口

1. ProjectCache文件夹（我的记忆）
2. 根据用户需求，从记忆中选择对应文件注入上下文
3. 对话产生新知识 → 运行abyssac-memory的SKILL

## 记忆选择

- 根据用户问题，从ProjectCache中选择最相关的记忆

## ProjectCache（我的记忆）

- 路径：ProjectCache/{项目名}.cache.md
- 需要时加载
- 后续对话直接注入

## 什么时候调用SKILL

| IF                         | 调用SKILL        |
| -------------------------- | -------------- |
| 检索/存储知识/ProjectCache需要更多记忆 | abyssac-memory |
| 其他需求                       | 调用对应SKILL      |

##

