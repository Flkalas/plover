"""Minimal YAML loader for hwsim config (stdlib only, no PyYAML)."""

from __future__ import annotations

import re
from typing import Any


def load(text: str) -> Any:
    lines = text.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return {}
    base_indent = _leading(lines[0])
    if lines[0].lstrip().startswith("- "):
        return _parse_list(lines, base_indent)
    return _parse_mapping(lines, base_indent)


def load_file(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return load(f.read())


def _leading(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return line[:i].rstrip()
    return line.rstrip()


def _scalar(raw: str) -> Any:
    s = raw.strip()
    if not s:
        return ""
    if s in ("true", "True", "yes", "Yes"):
        return True
    if s in ("false", "False", "no", "No"):
        return False
    if s in ("null", "Null", "~"):
        return None
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"0[xX][0-9a-fA-F]+", s):
        return int(s, 16)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def _parse_mapping(lines: list[str], indent: int) -> dict[str, Any]:
    out: dict[str, Any] = {}
    i = 0
    while i < len(lines):
        line = _strip_comment(lines[i])
        if not line.strip():
            i += 1
            continue
        cur = _leading(line)
        if cur < indent:
            break
        if cur > indent:
            raise ValueError(f"Unexpected indent at line {i + 1}: {line!r}")
        content = line.strip()
        if ":" not in content:
            raise ValueError(f"Expected key: value at line {i + 1}: {line!r}")
        key, rest = content.split(":", 1)
        key = key.strip()
        rest = rest.strip()
        if rest:
            if rest.startswith("{") and rest.endswith("}"):
                out[key] = _parse_inline_map(rest)
            elif rest.startswith("[") and rest.endswith("]"):
                out[key] = _parse_inline_list(rest)
            else:
                out[key] = _scalar(rest)
            i += 1
            continue
        i += 1
        if i >= len(lines):
            out[key] = None
            break
        nxt = _strip_comment(lines[i])
        if not nxt.strip():
            out[key] = None
            continue
        nxt_indent = _leading(nxt)
        if nxt_indent <= indent:
            out[key] = None
            continue
        if nxt.lstrip().startswith("- "):
            block, i = _collect_list_block(lines, i, nxt_indent)
            out[key] = block
        else:
            block, i = _collect_mapping_block(lines, i, nxt_indent)
            out[key] = block
    return out


def _parse_list(lines: list[str], indent: int) -> list[Any]:
    items, _ = _collect_list_block(lines, 0, indent)
    return items


def _collect_list_block(lines: list[str], start: int, indent: int) -> tuple[list[Any], int]:
    items: list[Any] = []
    i = start
    while i < len(lines):
        line = _strip_comment(lines[i])
        if not line.strip():
            i += 1
            continue
        cur = _leading(line)
        if cur < indent:
            break
        if cur > indent:
            raise ValueError(f"Bad list indent line {i + 1}")
        body = line.strip()
        if not body.startswith("- "):
            break
        body = body[2:].strip()
        if body.startswith("{") and body.endswith("}"):
            items.append(_parse_inline_map(body))
            i += 1
            continue
        if ":" not in body:
            items.append(_scalar(body))
            i += 1
            continue
        item_lines = [" " * (indent + 2) + body]
        i += 1
        while i < len(lines):
            nxt = _strip_comment(lines[i])
            if not nxt.strip():
                i += 1
                continue
            ni = _leading(nxt)
            if ni <= indent:
                break
            if ni == indent and nxt.lstrip().startswith("- "):
                break
            item_lines.append(nxt)
            i += 1
        items.append(_parse_mapping(item_lines, indent + 2))
    return items, i


def _collect_mapping_block(lines: list[str], start: int, indent: int) -> tuple[dict[str, Any], int]:
    block_lines: list[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if not _strip_comment(line).strip():
            block_lines.append(line)
            i += 1
            continue
        cur = _leading(line)
        if cur < indent:
            break
        block_lines.append(line)
        i += 1
    return _parse_mapping(block_lines, indent), i


def _parse_inline_map(text: str) -> dict[str, Any]:
    inner = text.strip()[1:-1].strip()
    if not inner:
        return {}
    out: dict[str, Any] = {}
    for part in _split_commas(inner):
        if ":" not in part:
            continue
        k, v = part.split(":", 1)
        out[k.strip()] = _scalar(v.strip())
    return out


def _parse_inline_list(text: str) -> list[Any]:
    inner = text.strip()[1:-1].strip()
    if not inner:
        return []
    return [_scalar(p.strip()) for p in _split_commas(inner)]


def _split_commas(s: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    in_quote = None
    for ch in s:
        if in_quote:
            buf.append(ch)
            if ch == in_quote:
                in_quote = None
            continue
        if ch in "\"'":
            in_quote = ch
            buf.append(ch)
            continue
        if ch in "{[":
            depth += 1
            buf.append(ch)
            continue
        if ch in "}]":
            depth -= 1
            buf.append(ch)
            continue
        if ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return parts
