# 贡献指南

欢迎贡献！这个项目是社区驱动的，任何形式的贡献都欢迎。

## 贡献方式

### 🐛 报告 Bug

- 通过 [GitHub Issues](https://github.com/a429228840-hash/hermes-chinese-skill-system/issues) 提交
- 请包含：Hermes 版本、操作系统、插件版本、复现步骤
- 如有可能，附上 `agent.log` 中的相关日志

### 💡 提交功能建议

同样通过 Issues 提交，标题加 `[提案]` 前缀。描述清楚使用场景和期望效果。

### 🔧 提交代码

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feat/your-feature`
3. 提交改动
4. 确保通过安全检查（无凭证泄露）
5. 创建 Pull Request

### 🌏 补充中文翻译

部分技能的描述和关键词翻译可能不完整或有改进空间。欢迎在 `skills/chinese-skill-index.json` 中补充或修正：

```json
{
  "skills": {
    "skill-name": {
      "description_cn": "更准确的中文描述",
      "keywords_cn": ["关键词1", "关键词2"]
    }
  }
}
```

### 📝 改进文档

README、架构文档、使用指南——任何你觉得不清楚的地方都可以改进。

## 开发指引

### 本地安装

```bash
git clone https://github.com/a429228840-hash/hermes-chinese-skill-system.git
cd hermes-chinese-skill-system
# 将插件链接到 Hermes profile
ln -s "$PWD/plugin/cn-skill-loader" ~/.hermes/plugins/cn-skill-loader
```

### 验证插件加载

```python
from hermes_cli.plugins import discover_plugins, get_plugin_manager
discover_plugins(force=True)
pm = get_plugin_manager()
pl = pm._plugins.get("cn-skill-loader")
assert pl and pl.enabled, "插件未加载"
```

## 行为准则

- 尊重他人，文明交流
- 所有贡献者，无论技术水平，都受到欢迎
