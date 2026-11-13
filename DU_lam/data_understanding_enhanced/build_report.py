#!/usr/bin/env python3
"""Ghép báo cáo từ _template/part*.md và các bảng trong reports/md/*.md."""
import re
from pathlib import Path
root = Path(__file__).resolve().parent
text = "\n".join((root / "_template" / f"part{i}.md").read_text(encoding="utf-8") for i in range(1, 5))
def inc(m):
    f = root / "reports" / "md" / f"{m.group(1)}.md"
    return f.read_text(encoding="utf-8") if f.exists() else f"*(thiếu bảng {m.group(1)})*"
out = re.sub(r"\{\{include:([a-z_]+)\}\}", inc, text)
(root / "data_understanding_report_enhanced.md").write_text(out, encoding="utf-8")
print("Đã ghi data_understanding_report_enhanced.md,", len(out.splitlines()), "dòng")
