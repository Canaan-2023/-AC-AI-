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

### 缓存更新规则（重要！）
- **更新缓存必须运行 abyssac-memory SKILL**
- **严禁直接修改缓存文件内容**
- 唯一例外：对话中产生新知识 → 存储Pipeline写NNG体系 → 缓存标记为"状态: 待更新"
-项目启动
├─ 缓存存在且状态正常 → 直接加载，跳过检索
├─ 缓存存在且状态待更新 → 语义判断是否涉及新知识
│   ├─ 是 → 重新运行检索Pipeline，生成新缓存
│   └─ 否 → 直接加载旧缓存
└─ 缓存不存在 → 运行检索Pipeline，生成缓存

## 什么时候调用SKILL

| IF                         | 调用SKILL        |
| -------------------------- | -------------- |
| 检索/存储知识/ProjectCache需要更多记忆 | abyssac-memory |
| 其他需求                       | 调用对应SKILL      |

##

