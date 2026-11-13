# -*- coding: utf-8 -*-
"""比对 C-G / 扩展名录 / 原始759底稿 / v1.0 的名称重叠。只读。"""
import re, io, json

CG = r"D:\study\跑团\01_最终版\蛊道资料库_v3.0\蛊真人蛊虫合集_v3.0.md"
EXT = r"D:\study\跑团\01_最终版\跑团提示词\ll_蛊虫扩展名录.txt"
ORIG = r"D:\study\跑团\03_归档_原始底稿与备份\原始底稿_3814行\蛊真人蛊虫合集_原始备份_20261113.txt"

def norm(n):
    n = n.strip()
    n = re.sub(r"（[^）]*）|\([^)]*\)", "", n)
    n = re.split(r"：|:", n)[0]
    n = re.sub(r"[【】\[\]〔〕\s·]", "", n)
    return n

def variants(name):
    parts = re.split(r"[、／/]|，", name)
    out = set()
    for p in parts:
        b = norm(p)
        if b:
            out.add(b)
    return out

s = io.open(CG, encoding="utf-8").read().splitlines()
cg = []
cur = None
for ln in s:
    m = re.match(r"^### (C-G-\d{3})\s+(.*)$", ln)
    if m:
        cur = {"id": m.group(1), "raw": m.group(2), "names": variants(m.group(2)), "body": []}
        cg.append(cur)
    elif cur is not None:
        if ln.startswith("### ") or ln.startswith("## "):
            cur = None
        else:
            cur["body"].append(ln)

print("C-G headings:", len(cg), "ids:", len({x['id'] for x in cg}))
cg_names = set()
for x in cg:
    cg_names |= x["names"]

# 扩展名录
ext = []
for ln in io.open(EXT, encoding="utf-8").read().splitlines():
    m = re.match(r"^(G-\d+-\w+-\d+)｜([^｜]+)｜([^｜]+)｜([^｜]+)｜([^｜]+)｜([^｜]+)｜([^｜]+)｜([^｜]*)$", ln.strip())
    if m:
        ext.append({"key": m.group(1), "name": m.group(2).strip(), "rank": m.group(3).strip(),
                    "sect": m.group(4).strip(), "func": m.group(5).strip(),
                    "food": m.group(6).strip(), "src": m.group(7).strip(), "tier": m.group(8).strip()})
print("EXT rows:", len(ext))
ext_names = {norm(e["name"]) for e in ext}
ext_match = sorted([e["name"] for e in ext if norm(e["name"]) in cg_names])
ext_un = sorted([e["name"] for e in ext if norm(e["name"]) not in cg_names])
print("EXT matched:", len(ext_match), "unmatched:", len(ext_un), ext_un[:60])

# 原始759
h3 = []
for i, ln in enumerate(io.open(ORIG, encoding="utf-8").read().splitlines(), 1):
    m = re.match(r"^### ([^：:]+)", ln)
    if m:
        h3.append(m.group(1).strip())
print("ORIG h3:", len(h3), "unique base:", len({norm(x) for x in h3}))
orig_un = sorted({norm(x) for x in h3} - cg_names)
print("ORIG unmatched:", len(orig_un))
print(orig_un[:100])

json.dump({"cg_count": len(cg), "ext_count": len(ext), "ext_unmatched": ext_un,
           "orig_h3": len(h3), "orig_unmatched": orig_un},
          io.open(r"D:\study\跑团\衡垠知识库迁入\Audit\NAME_OVERLAP.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
