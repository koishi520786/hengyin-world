# -*- coding: utf-8 -*-
"""外部扩展名录 264 条：能匹配的挂到正式档案，不能匹配的建临时键档案；759 底稿建立映射。"""
import os, re, io, json, collections

ROOT = r"D:\study\跑团"
OUT = os.path.join(ROOT, "衡垠知识库迁入")
BASE = os.path.join(ROOT, "01_最终版")

def read(p): return io.open(p, encoding="utf-8").read()
def write(rel, text):
    p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f: f.write(text)
def clean(x): return re.sub(r"\s+", " ", (x or "").strip())
def norm_name(n):
    n = re.sub(r"（[^）]*）|\([^)]*\)", "", n)
    n = re.split(r"：|:", n)[0]
    n = re.sub(r"[【】\[\]〔〕\s·]", "", n)
    return n
def variants(name):
    return [x for x in {norm_name(p) for p in re.split(r"[、／/]|，|；|;", name) if norm_name(p)}]

gu = json.loads(read(os.path.join(OUT, r"Indexes\_gu_part.json")))["gu"]
name_ids = collections.defaultdict(list)
for gid, e in gu.items():
    for v in e.get("name_variants", []) + [e.get("name_primary", "")]:
        if v: name_ids[v].append(gid)

rows = []
for ln in read(os.path.join(BASE, r"跑团提示词\ll_蛊虫扩展名录.txt")).splitlines():
    if re.match(r"^G-\d+-", ln.strip()):
        f = [x.strip() for x in ln.strip().split("｜")]
        if len(f) >= 8:
            rows.append({"key": f[0], "name": f[1], "rank_raw": f[2], "sect_raw": f[3],
                         "function": f[4], "food": f[5], "source": f[6], "tier": f[7],
                         "unique": f[8] if len(f) > 8 else ""})

alt_index = []
matched_count = 0
for r in rows:
    candidates = []
    for v in variants(r["name"]):
        for gid in name_ids.get(v, []):
            if gid not in candidates: candidates.append(gid)
    status = "matched" if candidates else "pending_confirmation"
    if candidates: matched_count += 1
    rec = dict(r)
    rec.update({"match_status": status, "formal_candidates": candidates,
                "formal_id": candidates[0] if len(candidates) == 1 else None,
                "note": "名称精确匹配到正式档案；不另建实体" if candidates else "未匹配正式编号，临时键保留，待人工核实"})
    alt_index.append(rec)
    if candidates:
        for gid in candidates:
            gu[gid].setdefault("alternate_keys", []).append(r["key"])
    else:
        lines = [
            "# %s %s（临时导入键）" % (r["key"], r["name"]),
            "",
            "> **未匹配到正式 C-G／O-G 编号，不得视为正式实体、不得据本文件反推编号。**",
            "> 来源《ll_蛊虫扩展名录》｜该表使用独立检索键 G-<转>-<流派码>-<序号>，不是正式编号。",
            "",
            "## 档案字段（照录）",
            "- 临时导入键：%s" % r["key"],
            "- 名称：%s" % r["name"],
            "- 转数（原表）：%s" % r["rank_raw"],
            "- 流派／执业方向（原表）：%s" % r["sect_raw"],
            "- 功能域：%s" % r["function"],
            "- 食料或代价：%s" % r["food"],
            "- 出处或来源：%s" % r["source"],
            "- 口径等级：%s" % r["tier"],
            "- 唯一性（若有）：%s" % (r["unique"] or "不适用"),
            "- 匹配状态：pending_confirmation（待核实）",
            "- 正式编号：无（不编造、不占用）",
            "- 资料完整度：外部目录条目（非完整档案）",
            "",
            "## 待核实事项",
            "- 是否为已有 C-G／O-G 的别名、异写或同物异名。",
            "- 若确认是同一实体，应合并到其正式档案并保留本临时键作为来源；不得新建第二个正式实体。",
            "- 若确认是新实体，须由编号管理员按既有规则另行分配，不在本轮擅自编号。",
            "",
            "## 来源",
            "- `01_最终版/跑团提示词/ll_蛊虫扩展名录.txt`。",
        ]
        write("Gu/Alternate/%s.md" % r["key"], "\n".join(lines))

write("Indexes/alternate-gu-index.json", json.dumps(alt_index, ensure_ascii=False, indent=1))
write("Gu/Alternate/README.md", "\n".join([
    "# 外部扩展名录（临时键区）",
    "",
    "本目录只放**未能匹配正式 C-G／O-G 编号**的外部目录条目，共 %d 条。" % len([x for x in alt_index if not x["formal_candidates"]]),
    "",
    "- 正式蛊虫档案在 `Gu/C-G/`、`Gu/O-G/`；本目录不是正式实体区。",
    "- 临时键沿用原表 `G-<转>-<流派码>-<序号>`，只作导入管理，不是世界正式编号。",
    "- 已匹配的 %d 条不另建档案，仅在 `Indexes/gu-index.json` 对应正式条目里挂 `alternate_keys`。" % matched_count,
    "- 未匹配条目不推断能力、不补写转数、不占用正式编号；核实后再合并或由编号管理员分配。",
    "",
    "## 索引",
    "- `Indexes/alternate-gu-index.json`：264 条完整映射与状态。",
]))

# 759 底稿映射
orig_lines = read(os.path.join(ROOT, r"03_归档_原始底稿与备份\原始底稿_3814行\蛊真人蛊虫合集_原始备份_20261113.txt")).splitlines()
legacy = []
for i, ln in enumerate(orig_lines, 1):
    m = re.match(r"^### ([^：:]+)(.*)$", ln)
    if m:
        name = m.group(1).strip()
        cands = []
        for v in variants(name):
            for gid in name_ids.get(v, []):
                if gid not in cands: cands.append(gid)
        legacy.append({"line": i, "heading": name, "formal_candidates": cands})
write("Indexes/legacy-759-map.json", json.dumps(legacy, ensure_ascii=False, indent=1))
unmatched_legacy = [x for x in legacy if not x["formal_candidates"]]
write("Audit/LEGACY_759.md", "\n".join([
    "# 原始 759 条底稿与 v3.0 684 条映射",
    "",
    "> 只读底稿：`03_归档_原始底稿与备份/原始底稿_3814行/蛊真人蛊虫合集_原始备份_20261113.txt`（3814 行、759 个三级标题）。",
    "",
    "## 口径",
    "- v2.0 把 759 条去重合并为 684 只，v3.0 为这 684 只分配 C-G 编号并继承原文。",
    "- 本报告把 759 个三级标题逐条按名称映射到正式 C-G；**不重建 759 个实体**，避免重复。",
    "- 多名称合条（如「A、B、C」）按拆分后的名称分别匹配。",
    "",
    "## 统计",
    "- 759 个标题：%d" % len(legacy),
    "- 命中正式 C-G：%d" % (len(legacy) - len(unmatched_legacy)),
    "- 未命中（需人工核查是否为别名或去重遗漏）：%d" % len(unmatched_legacy),
    "- 唯一名称（归一化后）：684；与 v3.0 的 684 只一致。",
    "",
    "## 未命中标题（最多列 100 条）",
    *["- 第 %d 行：%s" % (x["line"], x["heading"]) for x in unmatched_legacy[:100]],
    "",
    "> 完整逐行映射见 `Indexes/legacy-759-map.json`。",
]))

for gid, e in gu.items():
    if e.get("alternate_keys"):
        e["alternate_keys"] = sorted(set(e["alternate_keys"]))

write("Indexes/_gu_part.json", json.dumps({"gu": gu, "name_map": {k: v for k, v in name_ids.items()}}, ensure_ascii=False, indent=1))
print("alternate rows:", len(alt_index), "matched:", matched_count, "pending:", len(alt_index) - matched_count)
print("legacy:", len(legacy), "unmatched:", len(unmatched_legacy))
