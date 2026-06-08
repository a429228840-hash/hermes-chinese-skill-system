# 架构文档

## 概述

Hermes 中文技能系统通过 4 层防御体系，确保中文用户的自然语言指令能被正确理解并匹配到合适的技能。

## 四层架构

```
用户输入 (e.g. "审代码")
    │
    ├─ 层1: SOUL.md 决策树
    │   └─ Agent 读取决策树 → 自觉执行链式加载
    │   └─ 10 个节点 (审代码、API开发、数据库、爬虫等)
    │   └─ 11 条文件映射规则
    │
    ├─ 层2: cn-skill-loader 插件 (pre_llm_call hook)
    │   └─ 388 个技能逐一评分
    │   └─ 加载所有 ≥ 30 分的技能 (最多 3 个)
    │   └─ 60 秒 LRU 缓存
    │
    ├─ 层3: 研究守卫
    │   └─ 检测"研究/调研/对比"等词
    │   └─ 强制注入 web_search 指令
    │
    └─ 层4: skill_search_cn 工具 + 中文关键词索引
        └─ 387 个技能的中文关键词
        └─ 全文模糊搜索
```

## 评分算法

```
关键词精确匹配 (大小写不敏感)              +50 分
汉字重叠 ≥ 50%                           +15 分
关键词前 3 字连续子串匹配                 +25 分
关键词前 2 字连续子串匹配 (总分 ≤ 35 时)  +25 分
关键词前后 4 字截断匹配                    各 +30 分
技能名匹配                               +40 分
─────────────────────────────────
上限                                    100 分
阈值                                    ≥ 30 分自动加载
```

## 插件生命周期

```
Hermes 启动
    │
    ├─ discover_plugins() 扫描 $HERMES_HOME/plugins/
    │
    ├─ 发现 cn-skill-loader/plugin.yaml
    │
    ├─ 调用 register(ctx)
    │   ├─ ctx.register_hook("pre_llm_call", handler)
    │   └─ ctx.register_tool("skill_search_cn", schema, handler)
    │
    └─ 每轮对话:
        └─ invoke_hook("pre_llm_call") → handler fires
            ├─ 读取用户消息
            ├─ 检查研究关键词 → 注入 web_search 指令
            ├─ 检查技能匹配 → 注入技能上下文
            └─ 返回上下文 → 追加到用户消息前
```

## YAML 前端标记解析

`_parse_frontmatter()` 支持两种 SKILL.md 格式：

- **闭合式**：ECC 风格的 `---` … `---`（Hermes 官方格式）
- **开放式**：`---` 后遇到首个空行即为边界

解析优先级：`yaml.safe_load` → 手工行扫描降级

## 文件结构

```
profiles/<profile>/plugins/cn-skill-loader/
├── __init__.py          # 插件入口 (390+ 行)
├── plugin.yaml          # 插件清单
└── hermes-cn-patches.py # pip 升级恢复脚本

profiles/<profile>/skills/
└── <category>/
    └── <skill-name>/
        └── SKILL.md     # YAML frontmatter 含 description + keywords_cn
```

## 与 Hermes Agent 的集成点

| Hermes 模块 | 集成方式 |
|-------------|---------|
| `agent/conversation_loop.py` | pre_llm_call hook（已移除内联代码） |
| `agent/skill_utils.py` | 补丁：截断 60→200、keywords_cn 提取 |
| `agent/prompt_builder.py` | 补丁：关键词渲染、渐进披露、中文指导 |
| `tools/skills_tool.py` | 补丁：中文关键词索引 |
| `tools/skill_usage.py` | 补丁：记录所有技能用量 |
