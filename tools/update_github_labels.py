# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Set/update GitHub labels for the crysta-family repositories.

Labels-as-code for the **EasyScience unified labeling system** (org discussions
easyscience#33 + easyscience#49). This is the **canonical copy**, kept in
``enhantica/.github`` and applied to the four project repos via the ``Label sync``
workflow; the standard itself is recorded in crysta **ADR-0046**. Adapted from
``easyscience/diffraction-lib:tools/update_github_labels.py`` — the scheme is shared;
this copy generalises the org guard to the ``enhantica`` repos and adds the
crysta-specific ``[bot] perf-accepted`` label.

Requires the ``gh`` CLI installed and ``gh auth login`` completed.

Usage:
  python tools/update_github_labels.py                       # current repo
  python tools/update_github_labels.py --dry-run
  python tools/update_github_labels.py --repo enhantica/crysta
  python tools/update_github_labels.py --all                 # all four project repos
  python tools/update_github_labels.py --all --dry-run
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess  # noqa: S404
from dataclasses import dataclass

# Orgs whose repos this scheme covers (ADR-0046). The upstream diffraction-lib copy
# restricts to easyscience; the project's four repos live under enhantica.
ALLOWED_ORGS = {'enhantica', 'easyscience'}

# The four project repositories the standard applies to (ADR-0046).
TARGET_REPOS = [
    'enhantica/crysta',
    'enhantica/edi',
    'enhantica/agent-os',
    'enhantica/templates',
]


# Data structures


@dataclass(frozen=True)
class Label:
    """A GitHub label with name, color, and description."""

    name: str
    color: str
    description: str = ''


@dataclass(frozen=True)
class LabelRename:
    """Mapping from old label name to new label name."""

    old: str
    new: str


class Colors:
    """Hex color codes for the label groups (easyscience#33 + easyscience#49)."""

    SCOPE = 'd73a4a'  # red
    MAINTAINER = '0e8a16'  # green
    PRIORITY = 'fbca04'  # yellow
    AREA = '1e90ff'  # sky blue (optional, project-specific — see ADR-0046)
    BOT = '5319e7'  # violet


LABEL_RENAMES = [
    # Default GitHub labels renamed into the scheme (if they exist)
    LabelRename('bug', '[scope] bug'),
    LabelRename('documentation', '[scope] documentation'),
    LabelRename('duplicate', '[maintainer] duplicate'),
    LabelRename('enhancement', '[scope] enhancement'),
    LabelRename('good first issue', '[maintainer] good first issue'),
    LabelRename('help wanted', '[maintainer] help wanted'),
    LabelRename('invalid', '[maintainer] invalid'),
    LabelRename('question', '[maintainer] question'),
    LabelRename('wontfix', '[maintainer] wontfix'),
    # Custom label renames (if they exist)
    LabelRename('[bot] pull request', '[bot] release'),
]

LABELS = [
    # Scope labels (red) — required on issues + PRs; reflect the SemVer bump
    Label('[scope] bug', Colors.SCOPE, 'Bug report or fix (major.minor.PATCH)'),
    Label(
        '[scope] documentation',
        Colors.SCOPE,
        'Documentation only changes (major.minor.patch.POST)',
    ),
    Label('[scope] enhancement', Colors.SCOPE, 'Adds/improves features (major.MINOR.patch)'),
    Label(
        '[scope] maintenance',
        Colors.SCOPE,
        'Code/tooling cleanup, no feature or bugfix (major.minor.PATCH)',
    ),
    Label('[scope] significant', Colors.SCOPE, 'Breaking or major changes (MAJOR.minor.patch)'),
    Label(
        '[scope] ⚠️ label needed',
        Colors.SCOPE,
        'Automatically added to issues and PRs without a [scope] label',
    ),
    # Maintainer labels (green) — optional; maintainer state/decisions
    Label('[maintainer] duplicate', Colors.MAINTAINER, 'Already reported or submitted'),
    Label(
        '[maintainer] good first issue',
        Colors.MAINTAINER,
        'Good entry-level issue for newcomers',
    ),
    Label(
        '[maintainer] help wanted',
        Colors.MAINTAINER,
        'Needs additional help to resolve or implement',
    ),
    Label('[maintainer] invalid', Colors.MAINTAINER, 'Invalid, incorrect or outdated'),
    Label(
        '[maintainer] question',
        Colors.MAINTAINER,
        'Needs clarification, discussion, or more information',
    ),
    Label('[maintainer] wontfix', Colors.MAINTAINER, 'Will not be fixed or continued'),
    # Priority labels (yellow) — required on issues
    Label('[priority] lowest', Colors.PRIORITY, 'Very low urgency'),
    Label('[priority] low', Colors.PRIORITY, 'Low importance'),
    Label('[priority] medium', Colors.PRIORITY, 'Normal/default priority'),
    Label('[priority] high', Colors.PRIORITY, 'Should be prioritized soon'),
    Label('[priority] highest', Colors.PRIORITY, 'Urgent. Needs attention ASAP'),
    Label(
        '[priority] ⚠️ label needed',
        Colors.PRIORITY,
        'Automatically added to issues without a [priority] label',
    ),
    # Bot labels (violet) — applied by automation
    Label(
        '[bot] release',
        Colors.BOT,
        'Automated release PR. Excluded from changelog/versioning',
    ),
    Label(
        '[bot] backmerge',
        Colors.BOT,
        'Automated backmerge master → develop failed due to conflicts',
    ),
]

# Per-repo extras layered on top of the shared LABELS (ADR-0046). `[bot] perf-accepted`
# is crysta-only: ci.yml's advisory A/B perf gate reads it to consciously accept a
# regression. NOTE: ci.yml currently matches the literal `perf-accepted`; the rename
# below must land together with a ci.yml update to `[bot] perf-accepted` (deferred to
# after C04-T14, which is editing ci.yml).
REPO_EXTRA_LABELS = {
    'enhantica/crysta': [
        Label(
            '[bot] perf-accepted',
            Colors.BOT,
            'Consciously accept the advisory A/B perf-gate regression (e.g. self-hosted noise)',
        ),
    ],
}

REPO_EXTRA_RENAMES = {
    'enhantica/crysta': [
        LabelRename('perf-accepted', '[bot] perf-accepted'),
    ],
}


# Helpers


@dataclass(frozen=True)
class CmdResult:
    """Result of a shell command execution."""

    returncode: int
    stdout: str
    stderr: str


def run_cmd(args: list[str], *, dry_run: bool, check: bool = True) -> CmdResult:
    """Run a command (or print it in dry-run mode)."""
    cmd_str = ' '.join(shlex.quote(a) for a in args)

    if dry_run:
        print(f'  [dry-run] {cmd_str}')
        return CmdResult(0, '', '')

    proc = subprocess.run(args=args, text=True, capture_output=True, check=False)
    result = CmdResult(proc.returncode, proc.stdout.strip(), proc.stderr.strip())

    if check and proc.returncode != 0:
        msg = f'Command failed ({proc.returncode}): {cmd_str}\n{result.stderr}'
        raise RuntimeError(msg)

    return result


def get_current_repo() -> str:
    """Get the current repository name in 'owner/repo' format."""
    result = subprocess.run(
        args=['gh', 'repo', 'view', '--json', 'nameWithOwner'],
        text=True,
        capture_output=True,
        check=True,
    )
    data = json.loads(result.stdout)
    name_with_owner = data.get('nameWithOwner', '')

    if '/' not in name_with_owner:
        msg = 'Could not determine current repository name'
        raise RuntimeError(msg)

    return name_with_owner


def rename_label(repo: str, rename: LabelRename, *, dry_run: bool) -> None:
    """Rename a label, silently skipping if it doesn't exist."""
    result = run_cmd(
        args=['gh', 'label', 'edit', rename.old, '--name', rename.new, '--repo', repo],
        dry_run=dry_run,
        check=False,
    )

    if dry_run or result.returncode == 0:
        print(f'  Rename: {rename.old!r} → {rename.new!r}')
    else:
        print(f'  Skip (not found): {rename.old!r}')


def upsert_label(repo: str, label: Label, *, dry_run: bool) -> None:
    """Create or update a label."""
    run_cmd(
        [
            'gh',
            'label',
            'create',
            label.name,
            '--color',
            label.color,
            '--description',
            label.description,
            '--force',
            '--repo',
            repo,
        ],
        dry_run=dry_run,
    )
    print(f'  Upsert: {label.name!r}')


def sync_repo(repo: str, *, dry_run: bool) -> None:
    """Apply renames + the label set (shared + per-repo extras) to one repo."""
    org = repo.partition('/')[0]
    if org.lower() not in ALLOWED_ORGS:
        msg = f'repository {repo!r} is not under {sorted(ALLOWED_ORGS)}'
        raise RuntimeError(msg)

    print(f'\nRepository: {repo}')

    print('  Renaming default/legacy labels...')
    for rename in [*LABEL_RENAMES, *REPO_EXTRA_RENAMES.get(repo, [])]:
        rename_label(repo, rename, dry_run=dry_run)

    print('  Upserting labels...')
    for label in [*LABELS, *REPO_EXTRA_LABELS.get(repo, [])]:
        upsert_label(repo, label, dry_run=dry_run)


# Main


def main() -> int:
    """Entry point: parse arguments and sync labels."""
    parser = argparse.ArgumentParser(
        description='Sync GitHub labels for the crysta-family repos (ADR-0046)'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--repo', help='Target a single repository (owner/name)')
    group.add_argument(
        '--all',
        action='store_true',
        help=f'Target all project repos: {", ".join(TARGET_REPOS)}',
    )
    parser.add_argument(
        '--dry-run', action='store_true', help='Print actions without applying changes'
    )
    args = parser.parse_args()

    if args.all:
        repos = TARGET_REPOS
    elif args.repo:
        repos = [args.repo]
    else:
        repos = [get_current_repo()]

    if args.dry_run:
        print('Mode: DRY-RUN (no changes will be made)')

    for repo in repos:
        sync_repo(repo, dry_run=args.dry_run)

    print('\nDone.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
