# -*- coding: utf-8 -*-
"""扩展名录 264 条与正式蛊虫名称匹配统计（支持 8/9 字段行）。"""
import re, io, json

def norm(n):
    n = re.sub(r"（[^）]*）|\([^)]*\)", "", n)
    n = re.split(r"：|:", n)[0]
    n = re.sub(r"[【】\[\]〔〕\s·]", "", n)
    return n

def variants(name):
    return {norm(p) for p in re.split(r"[、／/]|，", name) if norm(p)}

CG = io.open(r"D:\study\跑团\01_最终版\蛊道资料库_v3.0\蛊真人蛊虫合集_v3.0.md", encoding="utf-8").read().splitlines()
cg = {}
for ln in CG:
    m = re.match(r"^### (C-G-\d{3})\s+(.*)$", ln)
    if m:
        for v in variants(m.group(2)):
            cg.setdefault(v, []).append(m.group(1))
OG = io.open(r"D:\study\跑团\01_最终版\蛊道资料库_v3.0\原创蛊虫图鉴.md", encoding="utf-8").read().splitlines()
og = {}
for ln in OG:
    m = re.match(r"^# 【原创设定】(.+)$", ln)
    if m:
        for v in variants(m.group(1)):
            og.setdefault(v, []).append("O-G")

rows = []
for ln in io.open(r"D:\study\跑团\01_最终版\跑团提示词\ll_蛊虫扩展名录.txt", encoding="utf-8").read().splitlines():
    if re.match(r"^G-\d+-", ln.strip()):
        f = [x.strip() for x in ln.strip().split("｜")]
        if len(f) >= 8:
            rows.append({"key": f[0], "name": f[1], "rank": f[2], "sect": f[3],
                         "func": f[4], "food": f[5], "src": f[6], "tier": f[7],
                         "unique": f[8] if len(f) > 8 else ""})

matched, unmatched = [], []
for r in rows:
    v = norm(r["name"])
    if v in cg:
        matched.append((r["key"], r["name"], cg[v]))
    elif v in og:
        matched.append((r["key"], r["name"], og[v]))
    else:
        unmatched.append((r["key"], r["name"]))
print("rows", len(rows), "matched", len(matched), "unmatched", len(unmatched))
for x in unmatched:
    print(x[0], x[1])
json.dump({"rows": rows, "matched": matched, "unmatched": unmatched},
          io.open(r"D:\study\跑团\衡垠知识库迁入\Audit\EXT_MATCH.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
