# Contributing to enhantica

Thanks for your interest! The short version:

- **Every change lands through a pull request** — `main` is protected in all repositories
  (short-lived `feature/*`-style branches, squash merges, linear history).
- **One `[scope]` label per PR/issue is required** — it maps to the SemVer bump
  (`bug`/`maintenance` → patch, `enhancement` → minor, `significant` → major,
  `documentation` → docs-only). The issue/PR templates prompt for it.
- **Per-repository rules override these defaults.** Check the repository's own `README`,
  `CONTRIBUTING`, or contributor instructions (`AGENTS.md`) before starting; run its verify
  gate (usually `pixi run verify`) before opening the PR.
- **Proposing a bigger change?** Open a Discussion first — architectural decisions are recorded
  as ADRs and we're happy to talk before you invest time.

By contributing you agree that your contributions are licensed under the repository's license
(BSD-3-Clause unless stated otherwise).
