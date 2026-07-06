# enhantica/.github

Org-wide GitHub configuration for [enhantica](https://github.com/enhantica) — shared
defaults and automation that apply across the project repositories.

## Labels-as-code

A single source of truth for the **EasyScience unified labeling system** (org discussions
[easyscience#33](https://github.com/orgs/easyscience/discussions/33) +
[easyscience#49](https://github.com/orgs/easyscience/discussions/49)), applied identically
across the four project repos. The decision/standard is recorded in crysta **ADR-0046**.

**Label groups** (see `tools/update_github_labels.py` for the exact names/colors/descriptions):

| Group | Color | Enforcement | Purpose |
| --- | --- | --- | --- |
| `[scope]` | red `#d73a4a` | required on issues + PRs | maps to the SemVer bump (bug/maintenance → PATCH, enhancement → MINOR, significant → MAJOR, documentation → POST) |
| `[maintainer]` | green `#0e8a16` | optional | maintainer state/decisions (duplicate, wontfix, help wanted, …) |
| `[priority]` | yellow `#fbca04` | required on issues | lowest … highest |
| `[area]` | sky blue `#1e90ff` | optional, per-project | categorize by component (project-defined) |
| `[bot]` | violet `#5319e7` | automation-applied | `[bot] release`, `[bot] backmerge`, and crysta's `[bot] perf-accepted` |

The `⚠️ label needed` auto-labels (`[scope]` / `[priority]`) mark issues/PRs missing a
required group label.

### Target repos

`enhantica/crysta` · `enhantica/edi` · `enhantica/agent-os` · `enhantica/templates`
(per-repo extras — e.g. crysta's `[bot] perf-accepted` — live in `REPO_EXTRA_LABELS`).

### Apply the labels

**Via the workflow** (Actions → **Label sync** → *Run workflow*): leave `repo` blank to sync
all four, or name one; tick `dry_run` to preview. Requires the `LABELS_TOKEN` secret below.

**Locally:**

```bash
python tools/update_github_labels.py --all            # all four repos
python tools/update_github_labels.py --all --dry-run  # preview only
python tools/update_github_labels.py --repo enhantica/crysta
```

Needs the `gh` CLI authenticated (`gh auth login`) with permission to edit labels on the
target repos.

### `LABELS_TOKEN` secret (for the workflow)

A workflow's default `GITHUB_TOKEN` can only edit **this** repo's labels. To let the `Label
sync` workflow edit the sibling repos, add a repo (or org) secret **`LABELS_TOKEN`**: a
classic Personal Access Token with the **`repo`** scope (or a fine-grained token granting the
four repos **Issues / Metadata: Read & write**).
