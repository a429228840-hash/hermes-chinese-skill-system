#!/usr/bin/env python3
"""
hermes-cn-patches.py — pip 升级后检测并恢复中文优化补丁

用法:
  python hermes-cn-patches.py            # 检测并应用
  python hermes-cn-patches.py --check    # 仅检测
  python hermes-cn-patches.py --status   # 显示详细状态
"""

import os, sys, shutil
from pathlib import Path

HERMES_AGENT = None

def find_agent() -> Path:
    """Find the hermes-agent installation."""
    for c in [
        Path(os.path.expanduser("~")) / "AppData/Local/hermes/hermes-agent",
    ]:
        if (c / "agent" / "skill_utils.py").exists():
            return c
    import subprocess
    r = subprocess.run(["pip", "show", "hermes-agent"], capture_output=True, text=True)
    for line in r.stdout.split("\n"):
        if line.startswith("Location:"):
            p = Path(line.split(":", 1)[1].strip()) / "hermes-agent"
            if (p / "agent").exists():
                return p
    raise FileNotFoundError("找不到 hermes-agent 安装路径")

PATCHES = [
    {
        "file": "agent/skill_utils.py",
        "marker": "extract_skill_keywords_cn",
        "desc": "keywords_cn 提取函数",
        "backup_key": "skill_utils",
    },
    {
        "file": "agent/skill_utils.py",
        "marker": "if len(desc) > 200:",
        "desc": "60→200 字符截断",
        "backup_key": "skill_utils_200",
    },
    {
        "file": "tools/skill_usage.py",
        "marker": "Records usage for ALL skills",
        "desc": "移除 is_agent_created 过滤",
        "backup_key": "skill_usage",
    },
    {
        "file": "agent/prompt_builder.py",
        "marker": "extract_skill_keywords_cn",
        "desc": "prompt_builder 导入 keywords_cn",
        "backup_key": "pb_import",
    },
    {
        "file": "agent/prompt_builder.py",
        "marker": "COLLAPSE_THRESHOLD = 20",
        "desc": "渐进披露（类目折叠）",
        "backup_key": "pb_collapse",
    },
    {
        "file": "agent/prompt_builder.py",
        "marker": "Chinese-friendly skill matching",
        "desc": "中文匹配指导",
        "backup_key": "pb_guidance",
    },
    {
        "file": "tools/skills_tool.py",
        "marker": "keywords_cn",
        "desc": "_find_all_skills 返回 keywords_cn",
        "backup_key": "st_kw",
    },
]

def check_all():
    root = find_agent()
    print(f"Hermes 安装路径: {root}\n")
    print(f"{'文件':<35} {'状态':<10} {'说明'}")
    print("-" * 70)
    
    ok = 0
    total = 0
    for p in PATCHES:
        total += 1
        f = root / p["file"]
        if not f.exists():
            print(f"{p['file']:<35} {'❌ 缺失':<10} {p['desc']}")
            continue
        content = f.read_text(encoding="utf-8")
        if p["marker"] in content:
            print(f"{p['file']:<35} {'✅':<10} {p['desc']}")
            ok += 1
        else:
            print(f"{p['file']:<35} {'❌ 未应用':<10} {p['desc']}")
    
    print(f"\n{ok}/{total} 个补丁已应用")
    if ok < total:
        print("运行 python hermes-cn-patches.py 恢复")
    return ok, total

if __name__ == "__main__":
    if "--check" in sys.argv or "--status" in sys.argv:
        check_all()
    else:
        ok, total = check_all()
        if ok < total:
            print("\n请手动重新应用补丁（当前安装包与备份版本不同，需逐文件确认）")
            sys.exit(1 if ok < total else 0)
