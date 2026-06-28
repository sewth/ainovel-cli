#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# python3 scripts/merge_markdown_folder.py <章节目录> 
"""Merge all Markdown files in a folder into one reading-friendly file."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def natural_sort_key(path: Path) -> list[object]:
    """Sort paths like 01.md, 2.md, 10.md in human order."""
    parts = re.split(r"(\d+)", path.stem)
    key: list[object] = []
    for part in parts:
        if not part:
            continue
        key.append(int(part) if part.isdigit() else part.lower())
    key.append(path.suffix.lower())
    return key


def collect_markdown_files(folder: Path, output_path: Path) -> list[Path]:
    files = []
    for path in folder.iterdir():
        if not path.is_file() or path.suffix.lower() != ".md":
            continue
        if path.resolve() == output_path.resolve():
            continue
        files.append(path)
    return sorted(files, key=natural_sort_key)


def build_merged_content(files: list[Path], title: str | None) -> str:
    lines: list[str] = []

    if title:
        lines.append(f"# {title}")
        lines.append("")

    for index, file_path in enumerate(files, start=1):
        content = file_path.read_text(encoding="utf-8").strip()
        lines.append(f"<!-- source: {file_path.name} -->")
        lines.append("")

        first_line = content.splitlines()[0].strip() if content else ""
        if not first_line.startswith("#"):
            lines.append(f"# {file_path.stem}")
            lines.append("")

        lines.append(content)

        if index != len(files):
            lines.append("")
            lines.append("\n---\n")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def default_output_path(folder: Path) -> Path:
    return folder / f"{folder.name}-汇总.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将一个文件夹下的所有 Markdown 文件按顺序合并为一个汇总文件。"
    )
    parser.add_argument("folder", help="要合并的 Markdown 文件夹路径")
    parser.add_argument(
        "output",
        nargs="?",
        help="输出文件路径；不传时默认输出到目标文件夹下的“文件夹名-汇总.md”",
    )
    parser.add_argument(
        "--title",
        help="可选，总文件顶部标题；不传则不额外添加总标题",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    folder = Path(args.folder).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        print(f"错误：文件夹不存在或不是目录：{folder}", file=sys.stderr)
        return 1

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else default_output_path(folder).resolve()
    )
    files = collect_markdown_files(folder, output_path)

    if not files:
        print(f"错误：目录下没有可合并的 Markdown 文件：{folder}", file=sys.stderr)
        return 1

    merged = build_merged_content(files, args.title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(merged, encoding="utf-8")

    print(f"已合并 {len(files)} 个文件 -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
