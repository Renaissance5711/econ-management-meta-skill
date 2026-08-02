# 经管 Meta 分析 Skill

`econ-management-meta-skill` 是面向经济学、管理学、创新、创业、营销和信息系统研究的 fail-closed、file-first **架构与Schema原型**。

## 当前版本

**0.1.0** 已提供：

- 可调用的根 `SKILL.md` 与分阶段 Skill；
- 受 Schema 约束的领域 Profile；
- 确定性的项目初始化；
- fail-closed 阶段状态转换；
- 基于 SHA-256 的版本化完整性锁；
- Claude Code、Codex 与通用 Agent 适配说明；
- 初始 `ai-innovation` Profile。

**投稿级完整工作流尚未实现**。数据库检索执行、主动学习筛选、全文提取、构念与 estimand 仲裁、R 统计综合、缺失证据模型、Quarto 稿件生成以及 clean-room 复现属于后续阶段。

## 快速开始

```bash
uv sync --dev
uv run emm validate-profile profiles/ai-innovation
uv run emm init "AI and innovation" --profile profiles/ai-innovation --output demo-project
uv run emm validate-project demo-project
```

离线环境已预装依赖时，可指定现有 Python 并跳过同步：

```bash
UV_PYTHON=3.13 uv run --no-sync emm version
```

## Agent 调用

加载仓库根目录的 [`SKILL.md`](SKILL.md)。根 Skill 会验证 Profile、初始化或验证项目、读取流水线状态，并仅调用当前允许的阶段 Skill。0.1.0 尚未实现的实质研究操作必须返回 `UNAVAILABLE_IN_VERSION`，不得伪造结果。

## 人工权限边界

AI 可以提出候选记录、字段、映射或代码，但不能作最终纳入排除决定，不能批准构念或 estimand 映射，不能核验效应量，不能选择主模型，也不能批准因果表述。领域 Profile 只能加强核心要求，不能削弱核心门禁。

## 开发与测试

```bash
uv sync --dev
uv run pytest -v
```

已批准设计规格位于 `docs/superpowers/specs/`，0.1.0 实施计划位于 `docs/superpowers/plans/`。
