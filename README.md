<p align="center">
  <img src="docs/logo.svg" width="120" alt="hermes-cn logo">
</p>

<h1 align="center">Hermes 中文技能系统</h1>

<p align="center">
  <strong>让 AI Agent 听懂中文 —— 为 Hermes Agent 提供中文自然语言技能匹配、自动加载和智能搜索</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <a href="https://github.com/a429228840-hash/hermes-chinese-skill-system"><img src="https://img.shields.io/badge/status-beta-orange" alt="Beta"></a>
</p>

---

## 📖 简介

**Hermes 中文技能系统** 是一个为 [Hermes Agent](https://hermes-agent.nousresearch.com) 提供中文支持的插件 + 工具集。

核心能力：

- 🎯 **中文自然语言自动加载** — 你说"帮我写个 Django API"，自动加载 Django 和 API 设计技能
- 🔍 **中文技能搜索** — 用"爬虫 数据库 安全"这种中文关键词就能找到对应技能
- 🛡️ **研究守卫** — 检测到"研究/调研/对比"等词时，强制调用 web_search 而不是凭训练数据回答
- 🌏 **387 个技能的中文描述** — 覆盖 ECC 全部技能的中文说明和中文搜索关键词
- 🔧 **pip 升级不丢失** — 插件化架构，升级 hermes-agent 后中文功能依然保留

### 适用于谁

- 中文 Hermes 用户，用自然语言驱动 Agent 做开发、爬虫、运维
- 不熟悉英文技能名的用户
- 希望 Hermes 更好地理解中文指令的任何人

---

## 🚀 快速安装

### 前置条件

- 已安装 [Hermes Agent](https://hermes-agent.nousresearch.com)
- Hermes 版本 ≥ 3.0（支持插件系统）

### 方式一：一键安装（推荐）

```bash
git clone https://github.com/a429228840-hash/hermes-chinese-skill-system.git
cd hermes-chinese-skill-system
chmod +x scripts/install.sh
./scripts/install.sh
```

### 方式二：手动安装

1. 复制插件到 Hermes profile 插件目录：

```bash
cp -r plugin/cn-skill-loader ~/.hermes/plugins/cn-skill-loader/
```

2. 在 Hermes 配置 `~/.hermes/config.yaml` 中启用插件：

```yaml
plugins:
  enabled:
    - cn-skill-loader
```

3. 重启 Hermes 会话。

### 方式三：Windows

```powershell
# PowerShell (管理员)
Copy-Item -Recurse plugin\cn-skill-loader $env:USERPROFILE\.hermes\plugins\cn-skill-loader\
```

然后在 `%USERPROFILE%\.hermes\config.yaml` 中添加 `plugins.enabled: [cn-skill-loader]`。

---

## 📦 项目结构

```
hermes-chinese-skill-system/
├── plugin/
│   └── cn-skill-loader/        # Hermes 插件 — 核心自动加载器
│       ├── __init__.py          # 插件入口：pre_llm_call hook + skill_search_cn 工具
│       └── plugin.yaml          # 插件清单
├── scripts/
│   ├── hermes-cn-patches.py     # pip 升级后恢复中文补丁的脚本
│   └── install.sh               # 安装脚本
├── skills/
│   └── chinese-skill-index.json # 387 个技能的中文描述和关键词索引
├── docs/
│   ├── architecture.md          # 架构文档
│   └── usage.md                 # 使用指南
├── SOUL.md                      # 决策树 — 供 Agent 读取的中文匹配规则
├── README.md
├── LICENSE                      # MIT
└── CONTRIBUTING.md
```

---

## 🎮 使用指南

### 自动加载（无需手动操作）

安装后即生效。系统会在每轮对话前分析你的消息，自动加载匹配的技能：

| 你说 | 自动加载 |
|------|---------|
| "写一个 Django 的 API 接口" | `api-design`, `fastapi-patterns`, `api-connector-builder` |
| "帮我爬京东的商品数据" | `jd-spy-data-enrichment`, `data-scraper-agent` |
| "数据库查询太慢了" | `postgres-patterns`, `mysql-patterns` |
| "写个 Dockerfile 部署" | `deployment-patterns`, `docker-patterns` |
| "审一下这段代码" | `ecc-code-reviewer`, `requesting-code-review` |
| "性能优化怎么做" | `benchmark`, `benchmark-optimization-loop` |

### 研究守卫

当消息包含「研究/调研/对比/调查/竞品/市场」等词时，系统会自动注入指令，强制 Agent 先调 web_search 搜索再回答，避免只靠训练数据输出。

### 中文技能搜索

```python
# 在 Hermes 会话中调用
skill_search_cn(query="爬虫 数据库 安全")
```

---

## 🧩 架构原理

```
用户说"审代码"
    │
    ├─ 层1：SOUL.md 决策树 — Agent 自觉执行（文档级路线图）
    │
    ├─ 层2：cn-skill-loader 插件 — 代码级兜底（无选择权）
    │     388 技能评分 → 加载 ≥ 30 分的技能（最多 3 个）
    │
    ├─ 层3：研究守卫 — 检测研究意图 → 强制调 web_search
    │
    └─ 层4：skill_search_cn 工具 + 中文关键词索引
```

详见 [docs/architecture.md](docs/architecture.md)。

---

## 🔧 补丁恢复

`pip install --upgrade hermes-agent` 后会覆盖以下核心文件中的中文补丁：

| 文件 | 补丁内容 |
|------|---------|
| `agent/skill_utils.py` | 描述截断 60→200 字符、keywords_cn 提取 |
| `agent/prompt_builder.py` | 渐进披露(类目折叠)、中文关键词渲染、中文匹配指导 |
| `tools/skill_usage.py` | 记录所有技能用量（不限 bundle 技能） |
| `tools/skills_tool.py` | 中文关键词索引 |

升级后运行恢复脚本：

```bash
python scripts/hermes-cn-patches.py
```

脚本会自动检测补丁状态并恢复。使用 `--check` 或 `--status` 查看详情。

---

## 🤝 贡献指南

欢迎贡献！参见 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 可以贡献的方向

- 补充更多中文关键词（keywords_cn）
- 改进技能的 Chinese description 翻译
- 优化自动加载器的评分算法
- 增加对其他 Agent 平台（Claude Code、Codex）的支持
- 修复 bug 和改进文档

---

## 📄 许可证

[MIT](LICENSE)

本项目包含的 ECC 技能中文描述和关键词是对 [ECC（Everything Claude Code）](https://github.com/nicholasgriffintn/ECC) 项目的 MIT 许可技能的中文翻译衍生作品。

---

## ⚠️ 免责声明

本项目的核心补丁（`hermes-cn-patches.py`）会修改 Hermes Agent 的安装文件。这些修改是向前的兼容性适配，但建议在升级 hermes-agent 后重新运行恢复脚本以确保功能正常。本项目与 Nous Research 无关，非 Hermes Agent 官方出品。
