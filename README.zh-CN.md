# 经管 Meta 分析 Skill

`econ-management-meta-skill` 是面向经济学、管理学、创新、创业、营销和信息系统研究的 fail-closed、file-first 工作流。

## 当前版本

**0.2.0** 已形成可执行的**证据获取与双人编码工作流**，包括：

- 可调用的根 `SKILL.md` 与分阶段 Skill；
- 受 Schema 约束的领域 Profile；
- 确定性项目初始化、状态转换和 SHA-256 完整性锁；
- 不可覆盖的协议版本和分类修订记录；
- 检索批次溯源，以及 CSV、RIS、BibTeX、EndNote XML 导入；
- 保留全部来源记录的报告级去重；
- 双人独立筛选、一致性统计、冲突仲裁与共识导出；
- 报告族、研究族的人工核验映射；
- 双人独立提取、冲突检测、人工仲裁和仅核验数据导出；
- Claude Code、Codex 与通用 Agent 适配说明；
- 初始 `ai-innovation` Profile。

**投稿级完整工作流尚未实现**。在线数据库检索、主动学习筛选、PDF自动提取、构念与 estimand 仲裁、效应量计算、R统计综合、缺失证据模型、Quarto稿件生成和 clean-room 复现属于后续阶段。

## 快速开始

```bash
uv sync --dev
uv run emm validate-profile profiles/ai-innovation
uv run emm init "AI and innovation" --profile profiles/ai-innovation --output demo-project
uv run emm validate-project demo-project
```

创建协议：

```bash
uv run emm protocol create demo-project 1.0 protocol.yaml --actor principal-investigator
uv run emm protocol validate demo-project/01_protocol/protocol-v1.0.yaml
```

登记并导入检索结果：

```bash
uv run emm search register demo-project search-run.yaml --actor information-specialist
uv run emm search import demo-project SEARCH_RUN_ID export.ris --format ris --actor information-specialist
uv run emm search deduplicate demo-project --actor review-lead
```

双人筛选、报告族映射和双人提取分别使用 `emm screen`、`emm report-family` 和 `emm extract`。精确参数见 `uv run emm --help`。

## Agent 调用与权限边界

加载仓库根目录的 [`SKILL.md`](SKILL.md)。AI可以提出候选内容，但不能被登记为最终筛选者、仲裁者、提取者或协议批准者。0.2.0 未实现的功能必须返回 `UNAVAILABLE_IN_VERSION`，不得伪造结果。

## 开发与测试

```bash
uv sync --dev
uv run pytest -v
```

已批准设计规格和实施计划位于 `docs/superpowers/`。
