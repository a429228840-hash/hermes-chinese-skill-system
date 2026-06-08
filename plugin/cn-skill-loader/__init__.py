"""
cn-skill-loader plugin — Chinese skill auto-loader.

Replaces the inline auto-loader in conversation_loop.py with a
profile-scoped plugin that survives pip upgrade.

Hooks:
  - pre_llm_call: skill matching + chain loading + research guard

Tools:
  - skill_search_cn: Chinese-friendly skill search
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Module-level skill index cache ──────────────────────────────────────
# Keyed by skills_root path so profile switches invalidate the cache.
_cache: Dict[str, List[Tuple[str, str, List[str]]]] = {}
_cache_at: Dict[str, float] = {}
_CACHE_TTL = 60  # seconds before rebuild

# Reverse index: YAML registered name → directory name (for skill_view fallback)
_dir_by_name: Dict[str, str] = {}

# Research keywords — only clearly research-intent phrases.
# Avoid high-frequency daily words (最新, 现状, 趋势) that trigger
# false positives on queries like "最新的Python版本有什么特性".
_RESEARCH_KW = [
    "研究", "调研", "对比", "调查", "deep dive",
    "竞品", "市场",
]

SKILL_SEARCH_SCHEMA = {
    "name": "skill_search_cn",
    "description": "用中文搜索技能。支持模糊匹配中文关键词。",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词，支持中文（如 '审代码', '做爬虫', '写API'）",
            },
        },
        "required": ["query"],
    },
}


# ── Cache management ────────────────────────────────────────────────────

def _resolve_skills_root() -> Optional[str]:
    """Find the active skills directory (platform-aware)."""
    for env_key in ("HERMES_PROFILE_SKILLS", "HERMES_HOME"):
        base = os.environ.get(env_key, "")
        if base:
            candidate = os.path.join(base, "skills")
            if os.path.isdir(candidate):
                return candidate
    # Fallback: dynamic profile resolution
    try:
        from agent.file_safety import _resolve_active_profile_name
        profile = _resolve_active_profile_name()
    except Exception:
        profile = "default"
    home = os.path.expanduser("~")
    # Try standard Hermes home paths across platforms
    candidates = [
        os.path.join(home, ".hermes", "profiles", profile, "skills"),
    ]
    if sys.platform == "win32":
        candidates.append(
            os.path.join(home, "AppData", "Local", "hermes", "profiles", profile, "skills"),
        )
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None


def _parse_frontmatter(raw: str) -> Optional[Dict[str, Any]]:
    """Extract and parse YAML frontmatter from SKILL.md content.

    Tries ``yaml.safe_load`` first (handles multi-line values, nested
    keys).  Falls back to manual line-scanning when ``yaml`` is not
    available (minimal dependency surface).

    Supports both closed (``---`` … ``---``) and open-ended (``---``
    until first blank line) frontmatter styles.
    """
    lines = raw.split("\n")
    if not lines or lines[0].strip() != "---":
        return None

    # Find frontmatter end boundary
    end_idx = None

    # 1) Look for explicit closing ---
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        # 2) No closing ---: stop at the first blank line after line 1
        for i in range(2, min(len(lines), 30)):
            if not lines[i].strip():
                end_idx = i
                break
    if end_idx is None:
        # 3) No blank line either — treat the whole file as frontmatter
        end_idx = len(lines) - 1

    if end_idx < 2:
        return None

    fm_text = "\n".join(lines[1:end_idx])

    # Try full YAML parser first
    try:
        import yaml  # type: ignore[import-untyped]
        data = yaml.safe_load(fm_text)
        if isinstance(data, dict):
            return data
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: manual line-by-line scanning
    data: Dict[str, Any] = {}
    in_meta = False
    in_hermes = False
    for line in fm_text.split("\n"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("name:"):
            data["name"] = s.split(":", 1)[1].strip()
        elif s.startswith("description:"):
            data["description"] = s.split(":", 1)[1].strip()
        elif s == "metadata:":
            in_meta = True
        elif in_meta and s == "hermes:":
            in_hermes = True
        elif in_hermes and "keywords_cn:" in s:
            kw_raw = s.split(":", 1)[1].strip()
            try:
                data["keywords_cn"] = json.loads(kw_raw)
            except Exception:
                data["keywords_cn"] = []
            break
    return data


def _build_cache(skills_root: str) -> List[Tuple[str, str, List[str]]]:
    """Scan all SKILL.md files and build a (name, desc, keywords) index.

    Uses ``_parse_frontmatter`` which supports both full YAML parsing
    and a manual fallback.
    """
    index: List[Tuple[str, str, List[str]]] = []
    for root, dirs, files in os.walk(skills_root, followlinks=True):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules")]
        if "SKILL.md" not in files:
            continue
        fpath = os.path.join(root, "SKILL.md")
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                raw = f.read()
        except Exception:
            continue

        fallback_name = os.path.basename(os.path.dirname(fpath))
        fm = _parse_frontmatter(raw)

        if fm:
            name = fm.get("name") or fallback_name
            desc = fm.get("description") or ""
            # Record dir_name reverse index
            if name != fallback_name:
                _dir_by_name[name] = fallback_name
            kw: List[str] = []
            # keywords_cn lives under metadata → hermes → keywords_cn
            meta = fm.get("metadata")
            if isinstance(meta, dict):
                hermes_meta = meta.get("hermes")
                if isinstance(hermes_meta, dict):
                    kw = hermes_meta.get("keywords_cn") or []
            # Fallback: direct keywords_cn key (simpler frontmatter layouts)
            if not kw:
                kw = fm.get("keywords_cn") or []
        else:
            name = fallback_name
            desc = ""
            kw = []

        index.append((name, desc, kw))
    return index


def _get_cache(skills_root: str) -> List[Tuple[str, str, List[str]]]:
    """Get cache, rebuild if stale."""
    now = time.time()
    if skills_root not in _cache or now - _cache_at.get(skills_root, 0) > _CACHE_TTL:
        _cache[skills_root] = _build_cache(skills_root)
        _cache_at[skills_root] = now
    return _cache[skills_root]


# ── Scoring ─────────────────────────────────────────────────────────────

def _score_skill(name: str, kw: List[str], user_msg: str) -> int:
    """Score a single skill against the user message. Returns 0-100."""
    msg_lower = user_msg.lower().strip()
    s = 0
    for k in kw:
        kl = k.lower()
        if kl in msg_lower or k in msg_lower:
            s += 50
        elif k:
            # Character overlap
            kw_chars = {c for c in k if '\u4e00' <= c <= '\u9fff'}
            msg_chars = {c for c in msg_lower if '\u4e00' <= c <= '\u9fff'}
            if kw_chars and msg_chars:
                shared = len(kw_chars & msg_chars)
                if shared / len(kw_chars) >= 0.5:
                    s += int(15 * shared / len(kw_chars))
            # Substring matches
            if len(k) >= 4:
                if kl[:4] in msg_lower:
                    s += 30
                if kl[-4:] in msg_lower:
                    s += 30
                # 3-char sliding window
                for pos in range(len(k) - 2):
                    sub = k[pos:pos+3].lower()
                    if sub in msg_lower:
                        s += 25
                        break
                if s <= 35:
                    for pos in range(len(k) - 1):
                        sub2 = k[pos:pos+2].lower()
                        if sub2 in msg_lower:
                            s += 25
                            break
    # Name match
    if name.lower() in msg_lower or msg_lower in name.lower():
        s += 40
    return min(s, 100)


# ── pre_llm_call hook ───────────────────────────────────────────────────

def pre_llm_call(**kwargs: Any) -> Optional[str]:
    """
    pre_llm_call hook handler.

    Returns skill context string to inject, or None.
    """
    user_msg = kwargs.get("user_message") or ""
    if not user_msg or len(user_msg) >= 500:
        return None

    msg_lower = user_msg.lower().strip()
    contexts: List[str] = []

    # ── Resolve skills root ──────────────────────────────────────────
    skills_root = _resolve_skills_root()
    if not skills_root:
        return None

    try:
        index = _get_cache(skills_root)

        # ── Research guard ───────────────────────────────────────────
        # Fire BEFORE skill loading — research is a higher-priority intercept
        is_research = False
        matched_rk = ""
        for rk in _RESEARCH_KW:
            if rk in user_msg:
                is_research = True
                matched_rk = rk
                break

        if is_research:
            contexts.append(
                "## ⚠️ 系统指令：研究类任务必须调用 web_search\n"
                f"检测到用户消息包含研究关键词「{matched_rk}」。\n"
                "在执行任何其他操作之前，必须先进行以下步骤：\n"
                "1. 用 web_search 搜索至少 3 个不同关键词\n"
                "2. 对核心结果用 browser_navigate 深读\n"
                "3. 综合输出带来源引用的报告\n"
                "**禁止只靠训练数据回答问题。**"
            )

        # ── Skill chain loading ──────────────────────────────────────
        scored = [(s, n) for n, d, kw in index
                   if (s := _score_skill(n, kw, msg_lower)) >= 30]
        scored.sort(key=lambda x: -x[0])

        if scored:
            loaded = []
            for score, name in scored[:3]:
                try:
                    from tools.skills_tool import skill_view
                    raw = skill_view(name)
                    data = json.loads(raw) if isinstance(raw, str) else {}
                    if not (isinstance(data, dict) and data.get("success")):
                        # Fallback: skill_view by YAML name failed (directory name
                        # may differ, e.g. YAML name "ecc-code-reviewer" but dir
                        # "code-reviewer"). Try resolving by directory name.
                        dir_name = _dir_by_name.get(name)
                        if dir_name and dir_name != name:
                            logger.debug(
                                "skill_view('%s') failed, trying dir name '%s'",
                                name, dir_name,
                            )
                            raw = skill_view(dir_name)
                            data = json.loads(raw) if isinstance(raw, str) else {}
                    if isinstance(data, dict) and data.get("success"):
                        content = data.get("content", "")
                        if content:
                            loaded.append(
                                f"## 自动加载技能：{name}（匹配度 {score} 分）\n{content[:2000]}"
                            )
                            # Track usage
                            try:
                                from tools.skill_usage import bump_view, bump_use
                                bump_view(str(name))
                                bump_use(str(name))
                            except Exception:
                                pass
                            logger.info(
                                "Plugin auto-loaded '%s' (score=%s)", name, score
                            )
                except Exception as e:
                    logger.debug("Plugin skill load failed: %s: %s", name, e)

            if loaded:
                total = len(scored)
                shown = len(loaded)
                header = (
                    f"系统自动加载了 {shown} 个相关技能（共匹配 {total} 个）。\n\n"
                    if total > shown
                    else f"系统自动加载了 {shown} 个相关技能。\n\n"
                )
                contexts.append(header + "\n\n".join(loaded))

    except Exception as e:
        logger.warning("cn-skill-loader error in pre_llm_call: %s", e)

    return "\n\n".join(contexts) if contexts else None


# ── skill_search_cn tool handler ────────────────────────────────────────

def skill_search_cn_handler(args: Dict[str, Any], **kw: Any) -> str:
    """Handle skill_search_cn tool call."""
    query = (args.get("query") or "").strip()
    if not query:
        return json.dumps({"success": False, "error": "query is required"})

    skills_root = _resolve_skills_root()
    if not skills_root:
        return json.dumps({"success": False, "error": "no skills directory found"})

    try:
        index = _get_cache(skills_root)
        results = [(s, n) for n, d, kw in index
                    if (s := _score_skill(n, kw, query)) >= 20]
        results.sort(key=lambda x: -x[0])

        skills = [
            {"name": n, "relevance": s}
            for s, n in results[:15]
        ]
        return json.dumps({
            "success": True,
            "query": query,
            "skills": skills,
            "count": len(skills),
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# ── Plugin entry point ──────────────────────────────────────────────────

def register(ctx):
    """Plugin registration entry point (Hermes plugin system calls register())."""
    ctx.register_hook("pre_llm_call", pre_llm_call)
    ctx.register_tool(
        name="skill_search_cn",
        toolset="skills",
        schema=SKILL_SEARCH_SCHEMA,
        handler=skill_search_cn_handler,
        description="用中文搜索技能。支持模糊匹配中文关键词。",
        emoji="🔍",
    )
    logger.info("cn-skill-loader plugin loaded: auto-loader + research guard + skill_search registered")
