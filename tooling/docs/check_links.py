"""Verify repository-local Markdown links without making network requests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
IGNORED_PARTS = frozenset({".agents", ".codex", ".git", ".venv", "dist", "node_modules"})
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\((?P<target>[^)]+)\)")


@dataclass(frozen=True)
class LinkViolation:
    path: Path
    line: int
    message: str

    def render(self) -> str:
        relative = self.path.relative_to(REPOSITORY_ROOT)
        return f"{relative}:{self.line}: {self.message}"


def _markdown_paths() -> list[Path]:
    return sorted(
        path
        for path in REPOSITORY_ROOT.rglob("*.md")
        if not IGNORED_PARTS.intersection(path.relative_to(REPOSITORY_ROOT).parts)
    )


def _target_path(markdown_path: Path, raw_target: str) -> Path | None:
    target = raw_target.strip().strip("<>").split(maxsplit=1)[0]
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or target.startswith("#"):
        return None
    path_text = unquote(parsed.path)
    if not path_text:
        return None
    if path_text.startswith("/") or re.match(r"^[a-zA-Z]:[/\\]", path_text):
        return REPOSITORY_ROOT.parent / "__invalid_absolute_documentation_link__"
    return (markdown_path.parent / path_text).resolve()


def verify_markdown(path: Path) -> list[LinkViolation]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        return [LinkViolation(path, 1, f"Cannot read Markdown: {error}")]

    violations: list[LinkViolation] = []
    inside_fence = False
    for line_number, line in enumerate(lines, start=1):
        if line.lstrip().startswith(("```", "~~~")):
            inside_fence = not inside_fence
            continue
        if inside_fence:
            continue
        for match in LINK_PATTERN.finditer(line):
            target = _target_path(path, match.group("target"))
            if target is None:
                continue
            try:
                target.relative_to(REPOSITORY_ROOT)
            except ValueError:
                violations.append(
                    LinkViolation(path, line_number, f"Local link escapes repository: {target}")
                )
                continue
            if not target.exists():
                violations.append(
                    LinkViolation(path, line_number, f"Local link does not exist: {target}")
                )
    return violations


def find_violations() -> list[LinkViolation]:
    violations = [violation for path in _markdown_paths() for violation in verify_markdown(path)]
    return sorted(violations, key=lambda violation: (str(violation.path), violation.line))
