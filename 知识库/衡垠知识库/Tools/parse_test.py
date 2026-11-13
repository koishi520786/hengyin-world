# -*- coding: utf-8 -*-
"""核心资料解析计数测试（修正版），不写正式档案。"""
import re, io, collections

BASE = r"D:\study\跑团\01_最终版"

def read(p):
    return io.open(p, encoding="utf-8").read()

CG = read(BASE + r"\蛊道资料库_v3.0\蛊真人蛊虫合集_v3.0.md").splitlines()
entries = []
cur = None
for i, ln in enumerate(CG):
    m = re.match(r"^### (C-G-\d{3})\s+(.*)$", ln)
    if m:
        cur = {"id": m.group(1), "name": m.group(2).strip(), "start": i, "body": []}
        entries.append(cur)
    elif cur and (ln.startswith("### ") or ln.startswith("## ")):
        cur = None
    elif cur is not None:
        cur["body"].append(ln)

RANGES = [(1, 1, 45), (2, 46, 77), (3, 78, 123), (4, 124, 159), (5, 160, 212),
          (6, 213, 248), (7, 249, 259), (8, 260, 266), (9, 267, 274), (10, 275, 275)]
def rank_of(cgid):
    n = int(cgid.split("-")[-1])
    for r, a, b in RANGES:
        if a <= n <= b:
            return r
    return None
print("CG entries:", len(entries), "empty body:", sum(1 for e in entries if not [x for x in e["body"] if x.strip()]))
print("rank dist:", collections.Counter(rank_of(e["id"]) for e in entries))
print("bullet dist:", collections.Counter(min(len([x for x in e["body"] if x.strip().startswith("-")]), 4) for e in entries))

OG = read(BASE + r"\蛊道资料库_v3.0\原创蛊虫图鉴.md").splitlines()
og_blocks = []
for i, ln in enumerate(OG):
    m = re.match(r"^# 【原创设定】(.+)$", ln)
    if m:
        og_blocks.append({"name": m.group(1).strip(), "start": i})
print("OG blocks:", len(og_blocks))
og_fields = []
for b in og_blocks:
    fields = {}
    for ln in OG[b["start"]:b["start"] + 30]:
        m = re.match(r"^\| (编号|名称|品阶|凡蛊或仙蛊|所属流派|核心用途|稀有程度|原创标识) \| (.+?) \|", ln)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    og_fields.append(fields)
print("OG missing id:", [x for x in og_fields if "编号" not in x])
print("OG ranks:", collections.Counter(x.get("品阶", "?") for x in og_fields))
print("OG sects:", collections.Counter(x.get("所属流派", "?") for x in og_fields))

OB = read(BASE + r"\妖兽图鉴\原创妖兽图鉴.md").splitlines()
ob_blocks = [(re.match(r"^## (O-B-\d{3}) 【原创设定】(.+)$", ln).group(1),
              re.match(r"^## (O-B-\d{3}) 【原创设定】(.+)$", ln).group(2), i)
             for i, ln in enumerate(OB) if re.match(r"^## (O-B-\d{3}) 【原创设定】(.+)$", ln)]
print("OB blocks:", len(ob_blocks), "sections:", len([x for x in OB[ob_blocks[0][2]:ob_blocks[1][2]] if re.match(r'^### ', x)]))

CB = read(BASE + r"\妖兽图鉴\原著兽类图鉴.md").splitlines()
start = next(i for i, ln in enumerate(CB) if ln.startswith("## 三、原著兽类逐条档案"))
cb_rows = [ln for ln in CB[start:] if re.match(r"^\| C-B-\d{3} \|", ln)]
print("CB detail rows:", len(cb_rows), "cells:", len(cb_rows[0].split("|")))

RB = read(BASE + r"\妖兽图鉴\跨作品妖兽参考库.md").splitlines()
rb = [ln for ln in RB if re.match(r"^## R-B-\d{3} ", ln)]
print("RB blocks:", len(rb))

CK = read(BASE + r"\蛊道资料库_v3.0\原著杀招百科.md").splitlines()
start = next(i for i, ln in enumerate(CK) if ln.startswith("## 二、快速索引表"))
end = next(i for i, ln in enumerate(CK) if ln.startswith("## 三、按品阶分类"))
ck_rows = [ln for ln in CK[start:end] if re.match(r"^\| C-K-\d{3} \|", ln)]
print("CK index rows:", len(ck_rows), "cells:", len(ck_rows[0].split("|")))
ck_a = [ln for ln in CK if re.match(r"^## C-K-", ln)]
ck_b = [ln for ln in CK if re.match(r"^#### C-K-", ln)]
print("CK A blocks:", len(ck_a), "B blocks:", len(ck_b), "A ids:", len(set(re.findall(r'C-K-\d{3}', '\n'.join(ck_a)))))
print("A rows:", sum(1 for x in ck_rows if x.split('|')[8].strip() == 'A'))

OK = read(BASE + r"\蛊道资料库_v3.0\原创杀招图鉴.md").splitlines()
ok = [ln for ln in OK if re.match(r"^# 【原创设定】", ln)]
print("OK blocks:", len(ok))

EXT = read(r"D:\study\跑团\01_最终版\跑团提示词\ll_蛊虫扩展名录.txt").splitlines()
ext_rows = [ln for ln in EXT if re.match(r"^G-\d+-\w+-\d+｜", ln)]
print("EXT rows:", len(ext_rows), "by rank:", collections.Counter(x.split("｜")[0].split("-")[1] for x in ext_rows))
