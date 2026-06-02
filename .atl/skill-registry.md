# Skill Registry — ScrapperGenerico

> Auto-generated. Last updated: 2026-06-02

## User-level Skills

| Skill | Source | Triggers |
|-------|--------|----------|
| go-testing | ~/.config/opencode/skiffs/go-testing/SKILL.md | Go tests, teatest, test coverage |
| skill-creator | ~/.config/opencode/skiffs/skill-creator/SKILL.md | Creating new AI skills |
| branch-pr | ~/.config/opencode/skiffs/branch-pr/SKILL.md | Creating pull requests |
| issue-creation | ~/.config/opencode/skiffs/issue-creation/SKILL.md | Creating issues |
| judgment-day | ~/.config/opencode/skiffs/judgment-day/SKILL.md | "judgment day", "dual review" |
| customize-opencode | ~/.config/opencode/skiffs/customize-opencode/SKILL.md | Editing opencode config |

## SDD Skills (always available)

- sdd-init, sdd-explore, sdd-propose, sdd-spec, sdd-design, sdd-tasks
- sdd-apply, sdd-verify, sdd-archive, sdd-onboard

## Project Conventions

- **AGENTS.md**: `~/.config/opencode/AGENTS.md` — global agent instructions
- **Project type**: Python package (src layout)
- **Testing**: pytest 7.4+ with asyncio support
- **Linting**: Ruff (select: E, F, I, N, W, UP, ANN, B, SIM, ARG, C4, RUF)
- **Typing**: mypy strict mode
- **Format**: Ruff formatter, 100 chars, double quotes
