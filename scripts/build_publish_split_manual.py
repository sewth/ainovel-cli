#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def read_blocks(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8").strip("\n")
    return text.split("\n\n")


def slice_block(blocks: list[str], start: int, end: int) -> str:
    return "\n\n".join(blocks[start : end + 1]).strip("\n")


def compose_body(file_map: dict[str, list[str]], segments: list[tuple[str, int, int]]) -> str:
    blocks = [slice_block(file_map[name], start, end) for name, start, end in segments]
    return "\n\n".join(blocks).strip("\n") + "\n"


def count_cjk(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def count_fanqie_like(text: str) -> int:
    return len("".join(text.split()))


def write_chapter(path: Path, chapter_no: int, title: str, body: str) -> None:
    path.write_text(f"# 第{chapter_no}章 {title}\n\n{body}", encoding="utf-8")


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    if args.project_root is not None:
        project_root = args.project_root
        return project_root / "output" / "novel" / "chapters", project_root / "chapters_publish_split"

    if args.source_dir is None or args.output_dir is None:
        raise SystemExit("Either provide project_root, or both --source-dir and --output-dir.")

    return args.source_dir, args.output_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build content-aware publish splits for markdown chapters."
    )
    parser.add_argument("project_root", nargs="?", type=Path)
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    source_dir, output_dir = resolve_paths(args)
    output_dir.mkdir(parents=True, exist_ok=True)

    for existing in output_dir.iterdir():
        if existing.is_file():
            existing.unlink()

    file_map = {
        name: read_blocks(source_dir / name)
        for name in [
            "01.md",
            "02.md",
            "03.md",
            "04.md",
            "05.md",
        ]
    }

    splits = [
        (1, "夜半快递", [("01.md", 0, 125)]),
        (2, "土地公上门", [("01.md", 127, 267)]),
        (3, "先把直播开起来", [("02.md", 0, 92)]),
        (4, "你有预约吗", [("02.md", 93, 185)]),
        (5, "供桌一拍", [("03.md", 0, 71)]),
        (6, "三倍罚款", [("03.md", 72, 116), ("04.md", 0, 29)]),
        (7, "香火账本", [("04.md", 30, 94)]),
        (8, "德柱文化", [("04.md", 95, 175)]),
        (9, "香火赔付款", [("04.md", 176, 187), ("05.md", 0, 52)]),
        (10, "人事科归档", [("05.md", 53, 126)]),
        (11, "转正培训通知", [("05.md", 127, 207)]),
    ]

    stats: list[tuple[int, str, int, int]] = []
    for chapter_no, title, segments in splits:
        body = compose_body(file_map, segments)
        chapter_path = output_dir / f"{chapter_no:02d}.md"
        write_chapter(chapter_path, chapter_no, title, body)
        full_text = chapter_path.read_text(encoding="utf-8")
        stats.append((chapter_no, title, count_fanqie_like(full_text), count_cjk(body)))

    stats_lines = ["chapter\ttitle\tfanqie_like_count\tcjk_count"]
    stats_lines.extend(
        f"{no:02d}\t{title}\t{fanqie_count}\t{cjk_count}"
        for no, title, fanqie_count, cjk_count in stats
    )
    (output_dir / "chapter_stats.tsv").write_text("\n".join(stats_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
