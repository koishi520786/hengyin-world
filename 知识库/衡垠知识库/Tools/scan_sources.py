# -*- coding: utf-8 -*-
"""扫描项目内所有文本资料，统计实体编号与文件角色。只读，不改动源文件。"""
import os, re, json, io

ROOT = r"D:\study\跑团"
OUT = r"D:\study\跑团\知识库\衡垠知识库\Audit\SOURCE_SCAN.json"
SKIP_DIRS = {".git", "node_modules", "衡垠知识库", ".workbuddy"}
EXTS = (".md", ".txt", ".json", ".csv")
ID_RE = re.compile(r"\b(C-G|O-G|C-B|R-B|O-B|C-K|O-K)-(\d{3})\b")
HEAD_RE = re.compile(r"^(?:#{1,4}\s*)?(C-G|O-G|C-B|R-B|O-B|C-K|O-K)-(\d{3})\b", re.M)

def read_text(p):
    try:
        raw = open(p, "rb").read()
    except Exception:
        return None
    for enc in ("utf-8-sig", "gb18030"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return None

files = []
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in SKIP_DIRS]
    for n in fn:
        if not n.lower().endswith(EXTS):
            continue
        p = os.path.join(dp, n)
        try:
            size = os.path.getsize(p)
        except Exception:
            continue
        if size > 8 * 1024 * 1024:
            continue
        s = read_text(p)
        if s is None:
            continue
        ids = {}
        for m in ID_RE.finditer(s):
            k = m.group(1)
            ids.setdefault(k, set()).add(m.group(2))
        heads = {}
        for m in HEAD_RE.finditer(s):
            heads.setdefault(m.group(1), set()).add(m.group(2))
        lines = len(s.splitlines())
        first = ""
        for ln in s.splitlines():
            if ln.strip().startswith("#"):
                first = ln.strip()[:120]
                break
        files.append({
            "path": os.path.relpath(p, ROOT).replace("\\", "/"),
            "bytes": size,
            "lines": lines,
            "heading": first,
            "ids": {k: len(v) for k, v in sorted(ids.items())},
            "heads": {k: len(v) for k, v in sorted(heads.items()) if len(v) >= 3},
        })

files.sort(key=lambda x: (-sum(x["ids"].values()), x["path"]))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8") as f:
    json.dump({"root": ROOT, "file_count": len(files), "files": files}, f, ensure_ascii=False, indent=1)

print("files:", len(files))
for f in files[:25]:
    print(f["bytes"], f["lines"], f["path"], f["ids"], f["heading"][:60])
