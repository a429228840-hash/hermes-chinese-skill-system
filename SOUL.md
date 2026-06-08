# Hermes 中文技能决策树

将此文件放置于 Hermes profile 目录（`~/.hermes/profiles/<profile>/SOUL.md`），
Agent 会在会话开始时读取并应用其中的决策规则。

---
## Skill Decision Tree

Before responding to any user request, evaluate which category it falls into and load ALL associated skills via skill_view(). Do NOT pick just one — load the full chain.

### 1. 代码审查 / 安全检查
触发条件：用户说"审代码"、"审查"、"安全审计"、"code review"
链式加载：
  - 先从 ecc-agents 加载 ecc-code-reviewer
  - 再从 ecc-skills 加载 security-review
  - 语言相关的审查规则（如存在对应 skill）

### 2. API 开发 / 后端服务
触发条件：用户说"写 API"、"写接口"、"后端"、"Django"、"FastAPI"、"Spring Boot"
链式加载：
  - api-design（API 设计规范）
  - 框架对应 skill（django-patterns / fastapi-patterns / springboot-patterns）
  - postgres-patterns 或 mysql-patterns（涉及数据库时）
  - security-review（涉及认证时）

### 3. 数据库 / SQL 优化
触发条件：用户说"SQL"、"查询慢"、"数据库"、"PostgreSQL"、"MySQL"、"调优"
链式加载：
  - postgres-patterns 或 mysql-patterns
  - 涉及数据库迁移时加载 database-migrations

### 4. 爬虫 / 数据采集
触发条件：用户说"爬虫"、"抓取"、"采集"、"scrape"、"京东"、"淘宝"
链式加载：
  - data-scraper-agent
  - scraper-safety-guardrails
  - browser-automation-safety（涉及浏览器操作时）

### 5. 前端开发 / UI
触发条件：用户说"前端"、"React"、"Vue"、"页面"、"组件"、"UI"
链式加载：
  - frontend-patterns
  - react-patterns（如涉及 React）
  - react-performance（如涉及性能）
  - accessibility（如涉及无障碍）
  - popular-web-designs（如涉及设计）

### 6. 容器化 / 部署
触发条件：用户说"Docker"、"Dockerfile"、"容器"、"部署"、"Compose"、"K8s"
链式加载：
  - docker-patterns
  - deployment-patterns（涉及 CI/CD 时）

### 7. 性能优化
触发条件：用户说"性能"、"优化"、"慢"、"加载速度"、"响应时间"
链式加载：
  - benchmark（基准测试方法论）
  - 根据上下文加载 react-performance / postgres-patterns 等

### 8. 测试
触发条件：用户说"测试"、"TDD"、"单元测试"、"pytest"
链式加载：
  - tdd-workflow
  - 对应语言的测试 skill（python-testing / react-testing 等）
  - verification-loop（开发完成后的验证）

### 9. 研究 / 调研 / 对比
触发条件：用户说"研究"、"调研"、"对比"、"调查"、"deep dive"
执行流程：
  1. 先用 web_search 搜索至少 3 个不同关键词
  2. 对核心结果用 browser_navigate 深读
  3. 综合输出带来源引用的报告
  ★ 禁止只靠训练数据回答问题

### 10. 日常开发（兜底）
未匹配到上述分类时，使用 skill_search('用户需求关键词') 搜索相关技能，
然后调用 auto-loader 的平铺匹配逻辑。

## File→Skill Mapping

当用户正在编辑或引用特定文件时，额外加载对应技能：

| 文件模式 | 加载技能 |
|---------|---------|
| *.py, **/python/** | python-patterns |
| *django*, **/django/** | django-patterns, django-security |
| *fastapi* | fastapi-patterns |
| *spring*, *java* | springboot-patterns, springboot-security |
| *.sql, */sql/** | postgres-patterns or mysql-patterns |
| *.tsx, *.jsx, **/components/** | react-patterns, react-testing |
| *Dockerfile*, *docker-compose* | docker-patterns |
| *test_*, *_test.py, *_test.go | 对应语言的 testing skill |
| *.html, *.css | frontend-patterns |
| *terraform*, */terraform/** | terraform-patterns |
| *.yaml, *.yml (K8s) | deployment-patterns |

## Skill Loading Rules

1. **Chain loading**: 不要只加载一个技能。同一节点下的所有 skill 都要加载。
2. **Order matters**: 按表格顺序依次 skill_view，全部内容注入上下文。
3. **Don't skip the file mapping**: 如果用户给了文件名或代码，先检查 File→Skill Mapping 再检查决策树。
4. **Fallback**: 决策树和文件映射都未命中时，用 skill_search 搜。搜不到再用自动加载器兜底。