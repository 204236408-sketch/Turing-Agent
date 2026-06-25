from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class ChunkConfig:
    strategy: str = "hierarchical"
    target_chars: int = 800
    max_chars: int = 2000
    min_chars: int = 200
    overlap_chars: int = 150
    respect_paragraph: bool = True

    def __post_init__(self):
        assert self.strategy in ("hierarchical", "sliding_window", "fixed_size")


@dataclass
class Chunk:
    document_id: str
    text: str
    metadata: dict[str, Any]
    content_hash: str = ""


FRONTMATTER_KEYS = {"subject", "knowledge_point", "section", "chapter", "keywords"}
SUBJECT_NAMES = {"数据结构", "计算机组成原理", "操作系统", "计算机网络"}


class ChunkOptimizer:
    def __init__(self, config: ChunkConfig | None = None):
        self.config = config or ChunkConfig()

    def parse_markdown(self, fp: Path) -> list[Chunk]:
        text = fp.read_text(encoding="utf-8")
        if not text.strip():
            return []

        subject_from_path, kp_from_path = self._parse_subject_kp_from_path(fp)
        strategy = self._select_strategy(text)

        if strategy == "sliding_window":
            return self._sliding_window_chunk(text, fp, subject_from_path, kp_from_path)
        return self._hierarchical_chunk(text, fp, subject_from_path, kp_from_path)

    def _select_strategy(self, text: str) -> str:
        if self.config.strategy != "hierarchical":
            return self.config.strategy
        lines = text.splitlines()
        has_headers = any(line.startswith("## ") for line in lines)
        return "hierarchical" if has_headers else "sliding_window"

    def _sliding_window_chunk(
        self, text: str, fp: Path, subject: str, kp: str
    ) -> list[Chunk]:
        seen: set[str] = set()
        chunks: list[Chunk] = []
        target = self.config.target_chars
        overlap = self.config.overlap_chars
        paragraphs = self._split_paragraphs(text)

        windows = self._build_sliding_windows(paragraphs, target, overlap)

        for idx, window_text in enumerate(windows):
            h = hashlib.md5(window_text.encode()).hexdigest()[:12]
            if h in seen:
                continue
            seen.add(h)

            chunks.append(Chunk(
                document_id=f"sw_{fp.stem}_{idx}_{h}",
                text=window_text,
                metadata=self._build_meta(fp, subject, kp, {
                    "chunk_index": idx,
                    "total_chunks": len(windows),
                    "strategy": "sliding_window",
                    "file": fp.name,
                }),
                content_hash=h,
            ))

        return chunks

    def _hierarchical_chunk(
        self, text: str, fp: Path, subject_from_path: str, kp_from_path: str
    ) -> list[Chunk]:
        h1_sections = re.split(r'\n(?=# )', text)
        chunks: list[Chunk] = []
        seen: set[str] = set()

        for h1_idx, h1_section in enumerate(h1_sections):
            h1_section = h1_section.strip()
            if not h1_section:
                continue

            lines = h1_section.splitlines()
            h1_title = ""
            if lines and lines[0].startswith("# ") and not lines[0].startswith("## "):
                h1_title = lines[0][2:].strip()
                lines = lines[1:]

            frontmatter, body_start = self._extract_frontmatter(lines)
            body_lines = lines[body_start:]

            subject = frontmatter.get("subject", "") or subject_from_path
            knowledge_point = frontmatter.get("knowledge_point", "") or kp_from_path
            section = frontmatter.get("section", frontmatter.get("chapter", ""))

            body_text = "\n".join(body_lines)
            h2_sections = re.split(r'\n(?=## )', body_text)

            parsed_h2s: list[dict] = []
            for h2_section in h2_sections:
                h2_section = h2_section.strip()
                if not h2_section or h2_section.startswith("---"):
                    continue

                h2_lines = h2_section.splitlines()
                h2_title = ""
                if h2_lines and h2_lines[0].startswith("## "):
                    h2_title = h2_lines[0][3:].strip()
                    h2_lines = h2_lines[1:]

                content = "\n".join(h2_lines).strip()
                if not content:
                    continue
                parsed_h2s.append({"title": h2_title, "content": content})

            merged = self._merge_small_h2s(parsed_h2s)

            for h2_idx, block in enumerate(merged):
                h2_titles = block["titles"]
                content = block["content"]
                section_label = h2_titles[0] if h2_titles else ""
                titles_str = " / ".join(h2_titles) if len(h2_titles) > 1 else h2_titles[0] if h2_titles else ""

                base_meta = {
                    "h1_title": h1_title,
                    "h2_title": titles_str,
                    "h1_index": h1_idx,
                    "h2_index": h2_idx,
                    "subject": subject,
                    "knowledge_point": knowledge_point,
                    "section": section or section_label,
                    "file": fp.name,
                    "merged_h2_count": len(h2_titles),
                    "strategy": "hierarchical",
                }

                sub_chunks = self._split_long_section(
                    content, h1_title, titles_str, base_meta,
                    fp, h1_idx, h2_idx,
                )
                for sc in sub_chunks:
                    if sc.content_hash not in seen:
                        seen.add(sc.content_hash)
                        chunks.append(sc)

        return chunks

    def _merge_small_h2s(self, h2s: list[dict]) -> list[dict]:
        if not h2s:
            return []
        min_chars = self.config.min_chars
        merged: list[dict] = []
        current: list[dict] = []
        current_len = 0

        for h2 in h2s:
            h2_len = len(h2["content"])
            if current_len + h2_len > self.config.max_chars and current:
                merged.append(self._merge_block(current))
                current = []
                current_len = 0

            if h2_len < min_chars and current:
                current.append(h2)
                current_len += h2_len
            elif h2_len < min_chars and not current:
                current.append(h2)
                current_len += h2_len
            else:
                if current:
                    merged.append(self._merge_block(current))
                current = [h2]
                current_len = h2_len

        if current:
            merged.append(self._merge_block(current))

        return merged

    def _merge_block(self, block: list[dict]) -> dict:
        titles = [h2["title"] for h2 in block if h2["title"]]
        combined_parts = []
        for h2 in block:
            if h2["title"]:
                combined_parts.append(f"## {h2['title']}")
            combined_parts.append(h2["content"])
        return {
            "titles": titles,
            "content": "\n".join(combined_parts),
        }

    def _split_long_section(
        self, content: str,
        h1_title: str, h2_title: str,
        base_meta: dict,
        fp: Path, h1_idx: int, h2_idx: int,
    ) -> list[Chunk]:
        max_chars = self.config.max_chars
        min_chars = self.config.min_chars

        if len(content) <= max_chars:
            full = self._format_chunk_text(h1_title, h2_title, content)
            h = hashlib.md5(full.encode()).hexdigest()[:12]
            return [Chunk(
                document_id=f"md_{fp.stem}_{h1_idx}_{h2_idx}_{h}",
                text=full,
                metadata={**base_meta, "chunk_index": 0, "total_chunks": 1},
                content_hash=h,
            )]

        paragraphs = self._split_paragraphs(content)
        sub_chunks: list[Chunk] = []
        current: list[str] = []
        current_len = 0

        for para in paragraphs:
            para_len = len(para)
            if current_len + para_len > max_chars and current:
                chunk_text = "\n\n".join(current)
                if len(chunk_text) < min_chars and sub_chunks:
                    sub_chunks[-1].text += "\n\n" + chunk_text
                    sub_chunks[-1].content_hash = hashlib.md5(
                        sub_chunks[-1].text.encode()
                    ).hexdigest()[:12]
                else:
                    self._add_sub_chunk(sub_chunks, chunk_text, base_meta,
                                        fp, h1_idx, h2_idx, h1_title, h2_title)
                current = []
                current_len = 0

            current.append(para)
            current_len += para_len

        if current:
            chunk_text = "\n\n".join(current)
            self._add_sub_chunk(sub_chunks, chunk_text, base_meta,
                                fp, h1_idx, h2_idx, h1_title, h2_title)

        for i, c in enumerate(sub_chunks):
            c.metadata["chunk_index"] = i
            c.metadata["total_chunks"] = len(sub_chunks)

        return sub_chunks

    def _add_sub_chunk(
        self, sub_chunks: list[Chunk], text: str,
        base_meta: dict, fp: Path,
        h1_idx: int, h2_idx: int,
        h1_title: str, h2_title: str,
    ):
        full = self._format_chunk_text(h1_title, h2_title, text)
        h = hashlib.md5(full.encode()).hexdigest()[:12]
        sub_chunks.append(Chunk(
            document_id=f"md_{fp.stem}_{h1_idx}_{h2_idx}_{len(sub_chunks)}_{h}",
            text=full,
            metadata={**base_meta},
            content_hash=h,
        ))

    def _add_overlap_between_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        if len(chunks) <= 1 or self.config.overlap_chars <= 0:
            return chunks

        result = [chunks[0]]
        for i in range(1, len(chunks)):
            prev = result[-1]
            curr = chunks[i]

            if prev.metadata.get("h1_index") != curr.metadata.get("h1_index"):
                result.append(curr)
                continue

            if prev.metadata.get("h2_index") != curr.metadata.get("h2_index"):
                result.append(curr)
                continue

            overlap_text = self._extract_overlap(prev.text, curr.text)
            if overlap_text:
                curr.text = overlap_text + "\n" + curr.text
                curr.content_hash = hashlib.md5(curr.text.encode()).hexdigest()[:12]
                curr.metadata["has_overlap"] = True

            result.append(curr)

        return result

    def _extract_overlap(self, prev_text: str, curr_text: str) -> str:
        overlap_chars = self.config.overlap_chars
        prev_lines = prev_text.splitlines()
        overlap_lines: list[str] = []
        collected = 0

        for line in reversed(prev_lines):
            line_len = len(line) + 1
            if collected + line_len > overlap_chars and collected > 0:
                break
            overlap_lines.insert(0, line)
            collected += line_len

        return "\n".join(overlap_lines)

    def _build_sliding_windows(
        self, paragraphs: list[str], target: int, overlap: int,
    ) -> list[str]:
        windows: list[str] = []
        current_window: list[str] = []
        current_len = 0

        for para in paragraphs:
            para_len = len(para)
            if current_len + para_len > target and current_window:
                windows.append("\n\n".join(current_window))
                overlap_text = self._get_window_overlap(current_window, overlap)
                current_window = [overlap_text] if overlap_text else []
                current_len = len(overlap_text) if overlap_text else 0

            current_window.append(para)
            current_len += para_len

        if current_window:
            windows.append("\n\n".join(current_window))

        return windows

    def _get_window_overlap(self, window: list[str], overlap_chars: int) -> str:
        collected: list[str] = []
        total = 0
        for text in reversed(window):
            if total + len(text) > overlap_chars and total > 0:
                break
            collected.insert(0, text)
            total += len(text)
        return "\n\n".join(collected)

    def _split_paragraphs(self, text: str) -> list[str]:
        raw = re.split(r'\n\s*\n', text.strip())
        result = []
        for p in raw:
            p = p.strip()
            if p:
                result.append(p)
        if not result:
            result = [text.strip()]
        return result

    def _format_chunk_text(self, h1: str, h2: str, content: str) -> str:
        if h2:
            return f"# {h1}\n## {h2}\n{content}"
        elif h1:
            return f"# {h1}\n{content}"
        return content

    def _extract_frontmatter(self, lines: list[str]) -> tuple[dict[str, str], int]:
        frontmatter: dict[str, str] = {}
        body_start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                if stripped.startswith("#"):
                    body_start = i
                    break
                continue
            if stripped.startswith("---"):
                continue
            if ":" in stripped and not stripped.startswith("- "):
                key, _, val = stripped.partition(":")
                key = key.strip().lower()
                if key in FRONTMATTER_KEYS:
                    frontmatter[key] = val.strip()
                    continue
            body_start = i
            break
        return frontmatter, body_start

    def _parse_subject_kp_from_path(self, fp: Path) -> tuple[str, str]:
        stem = fp.stem
        for subj in SUBJECT_NAMES:
            if stem.startswith(subj + "_"):
                return subj, stem[len(subj) + 1:]
        return "", ""

    def _build_meta(self, fp: Path, subject: str, kp: str,
                    extra: dict | None = None) -> dict:
        meta: dict[str, Any] = {
            "subject": subject,
            "knowledge_point": kp,
            "file": fp.name,
        }
        if extra:
            meta.update(extra)
        return {k: v for k, v in meta.items() if v}


def chunk_document(fp: Path, config: ChunkConfig | None = None) -> list[Chunk]:
    optimizer = ChunkOptimizer(config)
    return optimizer.parse_markdown(fp)


def batch_chunk(docs_dir: Path, config: ChunkConfig | None = None) -> list[Chunk]:
    optimizer = ChunkOptimizer(config)
    all_chunks: list[Chunk] = []
    for fp in sorted(docs_dir.rglob("*.md")):
        try:
            chunks = optimizer.parse_markdown(fp)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"  [warn] {fp.name}: {e}")
    return all_chunks


def chunk_statistics(chunks: list[Chunk]) -> dict:
    lengths = [len(c.text) for c in chunks]
    return {
        "total_chunks": len(chunks),
        "total_chars": sum(lengths),
        "avg_chars": round(sum(lengths) / len(lengths), 1) if lengths else 0,
        "min_chars": min(lengths) if lengths else 0,
        "max_chars": max(lengths) if lengths else 0,
        "by_subject": _count_by_meta(chunks, "subject"),
        "by_strategy": _count_by_meta(chunks, "strategy"),
    }


def _count_by_meta(chunks: list[Chunk], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in chunks:
        val = c.metadata.get(key, "unknown")
        counts[val] = counts.get(val, 0) + 1
    return counts
