# 使用指南

## 安装后首次使用

安装并重启 Hermes 后，无需任何额外配置。系统自动生效。

### 验证插件是否加载

在 Hermes 会话中执行：

```python
from hermes_cli.plugins import discover_plugins, get_plugin_manager
discover_plugins(force=True)
pm = get_plugin_manager()
pl = pm._plugins.get("cn-skill-loader")
print(f"插件状态: {'✅ 已加载' if pl and pl.enabled else '❌ 未加载'}")
print(f"注册的 hooks: {pl.hooks_registered if pl else '无'}")
print(f"注册的工具: {pl.tools_registered if pl else '无'}")
```

预期输出：
```
插件状态: ✅ 已加载
注册的 hooks: ['pre_llm_call']
注册的工具: ['skill_search_cn']
```

### 测试自动加载

说一些中文指令，系统会自动加载对应技能：

```python
from hermes_cli.plugins import invoke_hook
results = invoke_hook("pre_llm_call", user_message="帮我爬电商数据")
for r in results:
    if r and "自动加载技能" in r:
        print(r[:500])
```

## pip 升级后的恢复

升级 hermes-agent 后，如果发现中文功能失效：

```bash
pip install --upgrade hermes-agent

# 恢复中文补丁
python path/to/hermes-cn-patches.py
```

### 查看补丁状态

```bash
python path/to/hermes-cn-patches.py --status
```

输出示例：
```
Hermes 安装路径: ~/.hermes/hermes-agent

agent/skill_utils.py       ✅   keywords_cn 提取函数
agent/skill_utils.py       ✅   60→200 字符截断
tools/skill_usage.py       ✅   移除 is_agent_created 过滤
agent/prompt_builder.py    ✅   prompt_builder 导入 keywords_cn
agent/prompt_builder.py    ✅   渐进披露（类目折叠）
agent/prompt_builder.py    ✅   中文匹配指导
tools/skills_tool.py       ✅   _find_all_skills 返回 keywords_cn

7/7 个补丁已应用
```

## 自定义配置

### 修改匹配阈值

编辑 `plugin/cn-skill-loader/__init__.py`，找到 `AUTO_LOAD_THRESHOLD = 30`（默认值），调整为需要的值。

- 提高（如 50）：减少误匹配，更精确
- 降低（如 20）：增加匹配量，更敏感

### 自定义研究守卫关键词

编辑 `_RESEARCH_KW` 列表，添加或移除触发词。

## 常见问题

### Q: 插件安装了但没效果？

检查 `agent.log`：

```bash
grep "cn-skill-loader" ~/.hermes/logs/agent.log
```

- 如果有 `"no register() function"` → 入口函数不是 `register`，检查 `__init__.py`
- 如果没有任何输出 → 插件可能未被 `plugins.enabled` 收录

### Q: pip 升级后中文描述又变回英文了？

运行 `hermes-cn-patches.py` 恢复。中文描述存储在 `skills/chinese-skill-index.json`（插件外），不会因为 pip 升级丢失。

### Q: 可以同时装多个中文插件吗？

可以。但只有第一个注册 `pre_llm_call` hook 的插件能生效（Hermes 按发现顺序调用）。建议只保留 cn-skill-loader。

### Q: 怎么卸载？

1. 从 `config.yaml` 的 `plugins.enabled` 中移除 `cn-skill-loader`
2. 删除 `plugins/cn-skill-loader/` 目录
3. 重启 Hermes
