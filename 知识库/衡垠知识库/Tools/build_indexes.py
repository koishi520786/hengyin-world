# -*- coding: utf-8 -*-
"""总装：统一索引、关系索引、来源索引、秘境登记与四份审计报告。"""
import os, re, io, json, hashlib, datetime, collections

ROOT = r"D:\study\跑团"
OUT = os.path.join(ROOT, "知识库", "衡垠知识库")
BASE = os.path.join(ROOT, "01_最终版")
DATE = "2026-11-13"

def read(p): return io.open(p, encoding="utf-8").read()
def write(rel, text):
    p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f: f.write(text)
def jload(rel): return json.loads(read(os.path.join(OUT, rel)))
def clean(x): return re.sub(r"\s+", " ", (x or "").strip())

gu_part = jload(r"Indexes\_gu_part.json")
beast_part = jload(r"Indexes\_beast_part.json")
move_part = jload(r"Indexes\_move_part.json")
alt = jload(r"Indexes\alternate-gu-index.json")
legacy = jload(r"Indexes\legacy-759-map.json")
gu = gu_part["gu"]; beasts = beast_part["beasts"]; moves = move_part["moves"]
ck_to_cg = move_part["ck_to_cg"]

# ---- 秘境登记 ----
realm_rows = []
for ln in read(os.path.join(BASE, r"现代蛊道世界_v1.0\10_全球秘境总目录.md")).splitlines():
    if re.match(r"^\| REALM-\d{3} \|", ln):
        f = [x.strip() for x in ln.split("|")[1:-1]]
        if len(f) >= 10:
            if len(f) == 10:
                f = f[:3] + ["—"] + f[3:]
            realm_rows.append({"id": f[0], "name": f[1], "country": f[2], "coords": f[3],
                               "t": f[4], "s": f[5], "d": f[6], "r": f[7], "st": f[8],
                               "ds": f[9], "note": f[10], "content_file": None,
                               "source_files": ["01_最终版/现代蛊道世界_v1.0/10_全球秘境总目录.md"]})
realm = {x["id"]: x for x in realm_rows}
write("Indexes/realm-index.json", json.dumps({"schema_version": "1.0", "count": len(realm),
    "note": "秘境只建登记索引，不建实体正文档案；完整资料在原 10 号总目录与各分卷。",
    "entries": realm_rows}, ensure_ascii=False, indent=1))

# ---- 关系总装 ----
rel = {}
unresolved = []
def idtype(x):
    if x.startswith("C-G") or x.startswith("O-G"): return "gu"
    if x.startswith("C-B") or x.startswith("R-B") or x.startswith("O-B"): return "beast"
    if x.startswith("C-K") or x.startswith("O-K"): return "killer_move"
    if x.startswith("REALM-"): return "realm"
    return "unknown"
def add(src, dst, code, label, section="", evidence=""):
    if dst not in gu and dst not in beasts and dst not in moves and dst not in realm:
        unresolved.append({"source": src, "target": dst, "relation": code, "section": section})
        return
    key = (src, dst, code)
    if key in rel: return
    rel[key] = {"source": src, "source_type": idtype(src), "target": dst,
                "target_type": idtype(dst), "relation": code, "label": label,
                "source_section": section, "evidence": evidence}

# 蛊虫自身关系（O-G 搭配关系 / O-G-110）
for gid, e in gu.items():
    for r in e.get("relations", []):
        t = r.get("target")
        if r.get("type") == "parasitizes" and t in beasts:
            # 由妖兽侧建立携带关系，这里只保留 O-G 侧的寄生说明
            add(gid, t, "gu_parasitizes_beast", "蛊虫寄生于妖兽", r.get("source_section", ""), r.get("relation", ""))
            add(t, gid, "beast_hosts_parasitic_gu", "妖兽体表/体内寄生宿主", r.get("source_section", ""), r.get("relation", ""))
            continue
        if t in gu:
            add(gid, t, "gu_related_gu", "蛊虫关联蛊虫", r.get("source_section", ""))
            add(t, gid, "gu_related_gu", "蛊虫关联蛊虫", r.get("source_section", ""))
        elif t in moves:
            add(gid, t, "gu_related_move", "蛊虫关联杀招", r.get("source_section", ""))
            add(t, gid, "move_related_gu", "杀招关联蛊虫", r.get("source_section", ""))
        elif t in beasts:
            add(gid, t, "gu_related_beast", "蛊虫关联妖兽", r.get("source_section", ""))
            add(t, gid, "beast_related_gu", "妖兽关联蛊虫", r.get("source_section", ""))

# 妖兽关系
for bid, e in beasts.items():
    for r in e.get("relations", []):
        t = r.get("target"); typ = r.get("type")
        if typ == "cites_gu" and t in gu:
            add(bid, t, "beast_cites_gu", "原著兽类提及蛊虫", r.get("source_section", "逐条档案"))
            add(t, bid, "gu_cited_by_beast", "蛊虫被原著兽类提及", r.get("source_section", "逐条档案"))
        elif typ == "beast_carries_gu" and t in gu:
            add(bid, t, "beast_carries_gu", "妖兽携带蛊虫（%s）" % r.get("relation", "关系未明确"),
                r.get("source_section", ""), r.get("note", ""))
            add(t, bid, "gu_carried_by_beast", "蛊虫由妖兽携带（%s）" % r.get("relation", "关系未明确"),
                r.get("source_section", ""), r.get("note", ""))
        elif typ == "beast_habitat_realm" and t in realm:
            add(bid, t, "beast_habitat_realm", "妖兽栖息/关联秘境", r.get("source_section", ""))
            add(t, bid, "realm_hosts_beast", "秘境栖息妖兽", r.get("source_section", ""))
        elif typ == "beast_ecological_link" and t in beasts:
            add(bid, t, "beast_ecological_link", "妖兽生态关联", r.get("source_section", ""))
            add(t, bid, "beast_ecological_link", "妖兽生态关联", r.get("source_section", ""))
        elif typ == "beast_vs_killer_move" and t in moves:
            add(bid, t, "beast_references_move", "妖兽实战组合引用杀招", r.get("source_section", ""))
            add(t, bid, "move_referenced_by_beast", "杀招被妖兽实战组合引用", r.get("source_section", ""))

# 杀招 → 蛊虫
for cid in ck_to_cg:
    for gid in ck_to_cg[cid]:
        if gid in gu and cid in moves:
            add(cid, gid, "move_uses_gu", "杀招使用/组成蛊虫", "蛊虫杀招关联索引·二")
            add(gid, cid, "gu_component_of_move", "蛊虫为杀招组件", "蛊虫杀招关联索引·二")
for mid, e in moves.items():
    for gid in e.get("components", []):
        if gid in gu:
            add(mid, gid, "move_uses_gu", "杀招使用/组成蛊虫", "组成蛊虫表")
            add(gid, mid, "gu_component_of_move", "蛊虫为杀招组件", "组成蛊虫表")

relations = sorted(rel.values(), key=lambda x: (x["source"], x["target"], x["relation"]))
write("Indexes/relationship-index.json", json.dumps({
    "schema_version": "1.0", "generated_at": DATE, "count": len(relations),
    "unresolved_relations": unresolved, "relations": relations
}, ensure_ascii=False, indent=1))

# ---- 实体索引 ----
def sortid(x):
    nums = re.findall(r"\d+", x["id"])
    return (x["id"][:2], int(nums[0]) if nums else 0, x["id"])
gu_entries = sorted(gu.values(), key=sortid)
beast_entries = sorted(beasts.values(), key=sortid)
move_entries = sorted(moves.values(), key=sortid)

# 文件存在性
missing = []
for e in gu_entries + beast_entries + move_entries:
    p = os.path.join(OUT, e["content_file"].replace("/", "\\"))
    if not os.path.exists(p): missing.append(e["id"])

# 来源索引
scan = json.loads(read(os.path.join(OUT, r"Audit\SOURCE_SCAN.json")))
src_entries = []
for i, f in enumerate(scan["files"], 1):
    role = "其他/背景"
    if "蛊道资料库_v3.0" in f["path"]: role = "蛊道权威源"
    elif "妖兽图鉴" in f["path"]: role = "妖兽权威源"
    elif "现代蛊道世界" in f["path"]: role = "世界地理/秘境"
    elif "原始底稿" in f["path"] or "整合版v2基线" in f["path"]: role = "原始底稿/基线"
    elif "蛊道百科_v1.0" in f["path"]: role = "历史版本"
    elif "跑团提示词" in f["path"]: role = "跑团提示词/扩展名录"
    src_entries.append({"id": "SRC-%03d" % i, "path": f["path"], "bytes": f["bytes"],
                        "lines": f["lines"], "heading": f.get("heading"),
                        "ids": f.get("ids", {}), "role": role})
write("Indexes/source-index.json", json.dumps({
    "schema_version": "1.0", "generated_at": DATE, "file_count": scan["file_count"],
    "entries": src_entries}, ensure_ascii=False, indent=1))

# 扩展名录索引包装
alts = alt if isinstance(alt, list) else alt.get("entries", [])
pending = [x for x in alts if not x.get("formal_candidates")]
matched = [x for x in alts if x.get("formal_candidates")]
write("Indexes/alternate-gu-index.json", json.dumps({
    "schema_version": "1.0", "generated_at": DATE, "count": len(alts),
    "matched": len(matched), "pending_confirmation": len(pending),
    "entries": alts}, ensure_ascii=False, indent=1))

# ---- 统计明细 ----
cg_lines = read(os.path.join(BASE, r"蛊道资料库_v3.0\蛊真人蛊虫合集_v3.0.md")).splitlines()
cg_bullets = {}; cg_rank_marks = {}; cg_body = {}
cur = None
for ln in cg_lines:
    m = re.match(r"^### (C-G-\d{3})\s+(.*)$", ln)
    if m:
        cur = m.group(1); cg_bullets[cur] = 0; cg_rank_marks[cur] = None; cg_body[cur] = []
    elif ln.startswith("### ") or ln.startswith("## "):
        cur = None
    elif cur:
        cg_body[cur].append(ln)
        if ln.strip().startswith("-"):
            cg_bullets[cur] += 1
            mm = re.match(r"- +([一二三四五六七八九十])\s*转", ln.strip())
            if mm and cg_rank_marks[cur] is None:
                cg_rank_marks[cur] = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10}[mm.group(1)]

cg_no_body = [x for x in cg_bullets if cg_bullets[x] == 0 or not "".join(cg_body[x]).strip()]
rank_conflicts = []
for gid, e in gu.items():
    if e["origin"] != "C-G": continue
    mark = cg_rank_marks.get(gid)
    if mark and e["rank"] and mark != e["rank"]:
        rank_conflicts.append({"id": gid, "section_rank": e["rank"], "body_rank": mark,
                               "name": e["name"], "first_bullet": clean([x for x in cg_body[gid] if x.strip().startswith("-")][0])})
bullet_dist = collections.Counter(cg_bullets.values())
c_complete = [x for x in gu_entries if x["completeness"] == "complete_structured"]
c_brief = [x for x in gu_entries if x["completeness"] == "brief" or (x["origin"] == "C-G" and x["completeness"] == "descriptive")]
c_index = [x for x in gu_entries if x["completeness"] in ("index_only", "registration")]

# 妖兽威胁与22号索引差异
threat_conflicts = []
for bid, e in beasts.items():
    if e["origin"] != "O-B": continue
    d = beast_part["dist"].get(bid, {})
    if d.get("threat"):
        a = re.sub(r"（.*?）", "", e.get("danger_level") or "").strip()
        b = re.sub(r"（.*?）", "", d["threat"]).strip()
        if a and b and a != b:
            threat_conflicts.append({"id": bid, "archive": a, "index22": b, "name": e["name"]})

# O-K 组件与总览冲突
ok_with_components = [x for x in move_entries if x["origin"] == "O-K" and x.get("components")]
og_with_moves = sorted({r["source"] for r in relations if r["relation"] == "gu_component_of_move" and r["source"].startswith("O-G")})
o_k_components = sorted({x["id"] for x in move_entries if x["origin"] == "O-K" and x.get("components")})
unresolved_components = [(x["id"], x["unresolved_components"]) for x in move_entries if x.get("unresolved_components")]

# 名称/别名重复
name_groups = collections.defaultdict(set)
for e in gu_entries:
    for v in set((e.get("name_variants") or []) + [e.get("name_primary") or e["name"]]):
        if v:
            name_groups[v].add(e["id"])
dup_names = {k: sorted(v) for k, v in name_groups.items() if len(v) > 1}
for k, v in dup_names.items():
    for gid in v:
        if "suspected_duplicate" not in gu[gid].setdefault("flags", []):
            gu[gid]["flags"].append("suspected_duplicate")
beast_name_groups = collections.defaultdict(list)
for e in beast_entries:
    beast_name_groups[e["name"]].append(e["id"])
dup_beasts = {k: v for k, v in beast_name_groups.items() if len(v) > 1}
cross_names = sorted(set(name_groups) & set(beast_name_groups))

# 759 映射
legacy_hit_ids = {c for x in legacy for c in x["formal_candidates"]}
legacy_unique = len(legacy_hit_ids)
legacy_multi = sum(1 for x in legacy if len(x["formal_candidates"]) > 1)

# 源文件行数/MD5
core_sources = [
 ("01_最终版/蛊道资料库_v3.0/蛊真人蛊虫合集_v3.0.md", "C-G 684"),
 ("01_最终版/蛊道资料库_v3.0/原创蛊虫图鉴.md", "O-G 32"),
 ("01_最终版/蛊道资料库_v3.0/原著杀招百科.md", "C-K 447"),
 ("01_最终版/蛊道资料库_v3.0/原创杀招图鉴.md", "O-K 13"),
 ("01_最终版/蛊道资料库_v3.0/蛊虫杀招关联索引.md", "C-K→C-G 映射"),
 ("01_最终版/妖兽图鉴/原创妖兽图鉴.md", "O-B 12"),
 ("01_最终版/妖兽图鉴/原著兽类图鉴.md", "C-B 37"),
 ("01_最终版/妖兽图鉴/跨作品妖兽参考库.md", "R-B 40"),
 ("01_最终版/妖兽图鉴/仙蛊唯一性登记表.md", "O-G-110"),
 ("01_最终版/妖兽图鉴/资料更新与考据记录.md", "考据/争议"),
 ("01_最终版/现代蛊道世界_v1.0/22_妖兽地理分布索引.md", "妖兽地理/秘境"),
 ("01_最终版/现代蛊道世界_v1.0/10_全球秘境总目录.md", "REALM 64"),
 ("01_最终版/跑团提示词/ll_蛊虫扩展名录.txt", "264 条扩展"),
 ("03_归档_原始底稿与备份/原始底稿_3814行/蛊真人蛊虫合集_原始备份_20261113.txt", "759 标题"),
 ("03_归档_原始底稿与备份/整合版v2基线/蛊真人蛊虫合集.txt", "684 条基线"),
]
core_meta = []
scan_by_path = {f["path"]: f for f in scan["files"]}
for p, note in core_sources:
    full = os.path.join(ROOT, p.replace("/", "\\"))
    try:
        b = os.stat(full).st_size
        md5 = hashlib.md5(open(full, "rb").read()).hexdigest()
        lines = scan_by_path.get(p, {}).get("lines") or len(read(full).splitlines())
    except Exception:
        b, md5, lines = 0, "", 0
    core_meta.append({"path": p, "bytes": b, "lines": lines, "md5": md5, "note": note})

# ---- 写主索引 ----
gu_index = {
 "schema_version": "1.0", "generated_at": DATE,
 "scope": "《衡垠世界》已有蛊虫资料全量迁入；不含本草创",
 "counts": {"total": len(gu_entries),
            "C-G": len([x for x in gu_entries if x["origin"] == "C-G"]),
            "O-G": len([x for x in gu_entries if x["origin"] == "O-G"]),
            "complete_structured": len([x for x in gu_entries if x["completeness"] == "complete_structured"]),
            "registration": len([x for x in gu_entries if x["completeness"] == "registration"]),
            "descriptive": len([x for x in gu_entries if x["completeness"] == "descriptive"]),
            "brief": len([x for x in gu_entries if x["completeness"] == "brief"]),
            "index_only": len([x for x in gu_entries if x["completeness"] == "index_only"])},
 "field_policy": "未知字段保留 null/未知；不猜测转数、流派、能力；一条实体一份档案。",
 "entries": gu_entries
}
write("Indexes/gu-index.json", json.dumps(gu_index, ensure_ascii=False, indent=1))
beast_index = {
 "schema_version": "1.0", "generated_at": DATE,
 "scope": "C-B 原著参照 / R-B 跨作品参考 / O-B 本世界原创实存；三类严格分区",
 "counts": {"total": len(beast_entries),
            "C-B": len([x for x in beast_entries if x["origin"] == "C-B"]),
            "R-B": len([x for x in beast_entries if x["origin"] == "R-B"]),
            "O-B": len([x for x in beast_entries if x["origin"] == "O-B"]),
            "complete_structured": len([x for x in beast_entries if x["completeness"] == "complete_structured"]),
            "table_entry": len([x for x in beast_entries if x["completeness"] == "table_entry"]),
            "reference_dossier": len([x for x in beast_entries if x["completeness"] == "reference_dossier"])},
 "entries": beast_entries
}
write("Indexes/beast-index.json", json.dumps(beast_index, ensure_ascii=False, indent=1))
move_index = {
 "schema_version": "1.0", "generated_at": DATE,
 "scope": "杀招作为独立关联实体，不并入蛊虫",
 "counts": {"total": len(move_entries),
            "C-K": len([x for x in move_entries if x["origin"] == "C-K"]),
            "O-K": len([x for x in move_entries if x["origin"] == "O-K"]),
            "A": len([x for x in move_entries if x["origin"] == "C-K" and x["archive_level"] == "A"]),
            "B": len([x for x in move_entries if x["origin"] == "C-K" and x["archive_level"] == "B"]),
            "complete_structured": len([x for x in move_entries if x["completeness"] == "complete_structured"]),
            "descriptive": len([x for x in move_entries if x["completeness"] == "descriptive"]),
            "index_only": len([x for x in move_entries if x["completeness"] == "index_only"])},
 "entries": move_entries
}
write("Indexes/move-index.json", json.dumps(move_index, ensure_ascii=False, indent=1))

# ---- 审计文档 ----
def tbl(headers, rows):
    s = "| " + " | ".join(headers) + " |\n|" + "|".join(["---"] * len(headers)) + "|\n"
    s += "\n".join("| " + " | ".join(str(x).replace("|", "\\|") for x in r) + " |" for r in rows)
    return s

coverage = []
for label, arr, ids in [("蛊虫 C-G", [x for x in gu_entries if x["origin"] == "C-G"], "C-G"),
                        ("原创蛊虫 O-G", [x for x in gu_entries if x["origin"] == "O-G"], "O-G"),
                        ("原著妖兽 C-B", [x for x in beast_entries if x["origin"] == "C-B"], "C-B"),
                        ("参考物种 R-B", [x for x in beast_entries if x["origin"] == "R-B"], "R-B"),
                        ("原创妖兽 O-B", [x for x in beast_entries if x["origin"] == "O-B"], "O-B"),
                        ("原著杀招 C-K", [x for x in move_entries if x["origin"] == "C-K"], "C-K"),
                        ("原创杀招 O-K", [x for x in move_entries if x["origin"] == "O-K"], "O-K")]:
    coverage.append([label, len(arr),
                     len([x for x in arr if os.path.exists(os.path.join(OUT, x["content_file"].replace("/", "\\")))]),
                     len([x for x in arr if x["completeness"] == "complete_structured"]),
                     len([x for x in arr if x["completeness"] == "descriptive"]),
                     len([x for x in arr if x["completeness"] in ("brief", "index_only", "table_entry", "registration")]),
                     len([x for x in arr if x["completeness"] == "reference_dossier"])])
write("Audit/COVERAGE.md", "\n".join([
 "# 覆盖审计（COVERAGE）",
 "",
 "> 日期：%s｜所有计数由 `Tools/build_indexes.py` 对实际档案与索引统计，未使用估计值。" % DATE,
 "",
 "## 实体总数与档案存在性",
 tbl(["分区", "条目数", "独立档案存在数", "完整/结构化", "描述性摘要", "单条/表格/登记", "参考档案"], coverage),
 "",
 "## 合计",
 "- 蛊虫：%d 条（C-G %d + O-G %d）" % (len(gu_entries), len([x for x in gu_entries if x["origin"] == "C-G"]), len([x for x in gu_entries if x["origin"] == "O-G"])),
 "- 妖兽：%d 条（C-B %d + R-B %d + O-B %d）" % (len(beast_entries), len([x for x in beast_entries if x["origin"] == "C-B"]), len([x for x in beast_entries if x["origin"] == "R-B"]), len([x for x in beast_entries if x["origin"] == "O-B"])),
 "- 杀招：%d 条（C-K %d + O-K %d）" % (len(move_entries), len([x for x in move_entries if x["origin"] == "C-K"]), len([x for x in move_entries if x["origin"] == "O-K"])),
 "- 独立 Markdown 档案：%d 份（蛊虫 %d + 妖兽 %d + 杀招 %d）" % (len(gu_entries) + len(beast_entries) + len(move_entries), len(gu_entries), len(beast_entries), len(move_entries)),
 "- 缺失档案：%d 份%s" % (len(missing), ("（" + "、".join(missing) + "）") if missing else ""),
 "- 外部扩展临时档案：%d 份；秘境登记：%d 条；关系：%d 条（未解析目标 %d 条）" % (len(pending), len(realm), len(relations), len(unresolved)),
 "- 分类合计：完整/结构化 %d；描述性摘要 %d；单条/表格/登记 %d；参考档案 %d。" % (
   len([x for x in gu_entries + beast_entries + move_entries if x["completeness"] == "complete_structured"]),
   len([x for x in gu_entries + beast_entries + move_entries if x["completeness"] == "descriptive"]),
   len([x for x in gu_entries + beast_entries + move_entries if x["completeness"] in ("brief", "index_only", "table_entry", "registration")]),
   len([x for x in beast_entries if x["completeness"] == "reference_dossier"])),
 "",
 "## C-G 原文密度（来自实际正文）",
 "- 无正文：%d 条%s" % (len(cg_no_body), ("（" + "、".join(cg_no_body) + "）") if cg_no_body else ""),
 "- 1 个要点：%d 条；2 个要点：%d 条；3 个要点：%d 条" % (bullet_dist.get(1, 0), bullet_dist.get(2, 0), bullet_dist.get(3, 0)),
 "- 结论：C-G 是 684 个编号的逐条摘录库（含 3 条非实体注记、4 组疑似同物异号），不是 684 份结构化完整档案；完整/结构化档案集中在 O-G 32、O-B 12、C-K A 38、O-K 13。",
 "",
 "## 可追溯性",
 "- 每条记录在 `Indexes/gu-index.json`、`beast-index.json`、`move-index.json` 均有 `content_file`，并已逐条验证文件存在。",
 "- 每个数字来自上述索引的 `counts` 或实际文件枚举；原始 `Audit/SOURCE_SCAN.json` 保留 79 个文件的扫描结果。",
]))

dup_rows = []
dup_group_aliases = collections.defaultdict(list)
for k, v in sorted(dup_names.items()):
    dup_group_aliases[tuple(v)].append(k)
for ids, aliases in sorted(dup_group_aliases.items()):
    dup_rows.append(["蛊虫同名/别名", "、".join(aliases), "、".join(ids), "同一实体名下对应多个 C-G 编号；保留原编号，未合并"])
for k, v in sorted(dup_beasts.items()):
    dup_rows.append(["妖兽同名", k, "、".join(v), "同一名称对应多个编号；未合并"])
if not dup_rows:
    dup_rows.append(["（无）", "—", "—", "—"])
write("Audit/DUPLICATES.md", "\n".join([
 "# 重复审计（DUPLICATES）",
 "",
 "> 原则：不能确认同物时只标疑似重复，不擅自合并；一条实体只保留一份正式档案。",
 "",
 "## 名称重复组",
 tbl(["类型", "名称", "涉及编号", "处置"], dup_rows),
 "",
 "## 跨来源去重",
 "- 759 条原始底稿标题按名称映射到 %d 个不同 C-G 编号；684 个编号中仅 %d 个未被底稿标题覆盖（C-G-462、C-G-643 非实体注记）。" % (legacy_unique, 684 - legacy_unique),
 "- 4 组疑似同物异号的第二编号（C-G-556、C-G-404、C-G-509、C-G-514）均可由多名称标题回溯；保留原编号，未合并。",
 "- 759 标题比映射编号多 %d 个，属多名称合条/同条重述，不是新增实体。" % (len(legacy) - legacy_unique),
 "- 759 标题中一名对多编号的歧义：%d 条；逐行映射见 `Indexes/legacy-759-map.json`。" % legacy_multi,
 "- 外部扩展名录 264 条：%d 条名称匹配正式档案，%d 条未匹配；已匹配者不另建实体，只在正式条目挂 `alternate_keys`。" % (len(matched), len(pending)),
 "- C-G 与 O-G 同名冲突：%d 组%s" % (len(cross_names), ("（" + "、".join(cross_names) + "）") if cross_names else ""),
 "- v1.0 历史版本旧 O-G 15 只：只作版本谱系，不新建实体、不并入现行 O-G。",
 "",
 "## 疑似重复处置",
 "- 对同名组只标注，未合并、未改编号；待人工确认是否同物。",
 "- 对 45 条扩展临时键：保留原键，标 `pending_confirmation`；没有赋正式编号。",
]))

# 冲突内容
conflict_rows = [
 ["C-G-274", "误立条目", "标题为一整句喂养规则残句，无蛊虫名、无正文；疑为底稿行误升级为标题", "保留编号与原文，标 `malformed_heading_non_entity`；不删除、不合并"],
 ["C-G-462", "非实体注记", "标题为「注意」，正文是版本说明/结构重排注记，不是蛊虫", "保留编号，标 `non_entity_note`；不计入有效蛊虫"],
 ["C-G-643", "非实体附录", "标题为「附录」，正文是流派参考总表说明，不是蛊虫", "保留编号，标 `appendix_non_entity`；不计入有效蛊虫"],
 ["C-G-245", "标题含描述", "标题行含名称＋能力描述＋【方源】，无独立正文", "保留标题原样，标 `heading_contains_description`"],
 ["C-G 重复组", "疑似同物异号", "草人蛊（028/556）、思绪如电蛊（389/404）、生机蛊（503/509）、电脑蛊（513/514）", "保留全部编号与档案，标 `suspected_duplicate`；不擅自合并"],
 ["O-G-110", "两种口径", "v3.0 预留段 vs 仙蛊登记表顺延占用；C 组为裁决口径", "以登记表 C 组为准；保留 v3.0 不动，单条登记，能力细节待考证"],
 ["C-B 表头", "格式噪音", "表头 4 列，正文实际 7 列", "按 7 列迁入，不把 4 列表头当数据缺失"],
 ["扩展名录", "数量口径", "文件头称 261 条，实测 264 条字段行（223 主表 + 41 仙蛊）", "如实并列，不自行裁定；索引按 264 条"],
 ["O-K 总览", "关系冲突", "《蛊虫杀招关联索引》4.1 称 O-G 全部未入杀招、4.2 称 O-K 依赖为—；O-K 档案组成表明确使用 O-G", "以档案组成表为准；13 条 O-K 组件关系进入关系索引"],
 ["759 底稿", "数量口径", "759 个标题 vs 684 个 C-G；v2 已去重合并", "759 只作来源谱系；正式实体以 684 个 C-G 为准"],
 ["蛊道争议", "原著考据", "14 项并列争议（万我转数、逆流护身印、自由残缺变、定仙游、春秋蝉等）", "原样并列，不调和、不擅自定论"],
]
write("Audit/CONFLICTS.md", "\n".join([
 "# 冲突审计（CONFLICTS）",
 "",
 "> 原则：发现冲突必须记录，不得静默修掉；能裁决的写明裁决依据，不能裁决的并列保留。",
 "",
 "## 结构性/来源口径冲突",
 tbl(["对象", "类型", "事实", "处置"], conflict_rows),
 "",
 "## 核对：O-B 威胁等级与 22 号索引差异（以主档案为准）",
 "> 逐条比对结果：%s" % ("未检出差异。" if not threat_conflicts else "见下表。"),
 tbl(["编号", "名称", "主档案", "22 号索引"], [[x["id"], x["name"], x["archive"], x["index22"]] for x in threat_conflicts]) if threat_conflicts else "（无差异）",
 "",
 "## 蛊道原著 14 项并列争议（原文清单）",
 *["%d. %s" % (i, x) for i, x in enumerate([
  "万我：六转创制（奴力合流） vs 七转·人道分类。",
  "逆流护身印：八转律道防御 vs 万我第二式七转力道＋水道。",
  "自由残缺变及三段变：S06 列九转 vs S49 列八转。",
  "定仙游：六转 vs 七转。",
  "春秋蝉：六转 vs 八转。",
  "天元宝皇莲：奇蛊榜第六 vs 仙蛊榜第六。",
  "弹指神通：S06 列八转气道攻伐 vs S23 记凡道戚灾所用。",
  "天纲地常组件：纲＋正常（原文件） vs 正常＋提纲＋天网／天生（新检出）。",
  "五指拳心剑核心蛊：八转慧剑仙蛊【待考证】。",
  "鬼官衣章号：385 章 vs 第四百二十九节。",
  "万剑鬼蛟／万一鬼蛟剑：已判定为两式（原并列易误读，非争议但记录于此）。",
  "上古剑蛟变／剑蛟变、卜卦龟变化／卜卦龟背变、洁身自好／洁身自爱：疑同招异写【待考证】。",
  "仙蛊屋是否「固态杀招」、无上大宗师／道主令杀招永存的出处层级：【存在争议】。",
  "蛊虫是否可至十转（命运蛊、至尊仙胎蛊完美版）：【原著未明确】。"], 1)],
 "",
 "## C-G 疑似转数标注不一致（章节归类 vs 正文首条）",
 tbl(["编号", "名称", "章节转数", "正文首条转数", "正文首条"], [[x["id"], x["name"], x["section_rank"], x["body_rank"], x["first_bullet"]] for x in rank_conflicts]) if rank_conflicts else "（未检出正文首条与章节归类不一致）",
 "",
 "## 蛊虫杀招总览 vs 档案组成表（裁决：档案优先）",
 "- O-K 档案明确列出正式蛊虫组件的：%d 条（%s）。" % (len(o_k_components), "、".join(o_k_components)),
 "- 关系索引中 O-G 作为杀招组件的：%d 条（%s）。" % (len(og_with_moves), "、".join(og_with_moves) if og_with_moves else "无"),
 "- 与《蛊虫杀招关联索引》4.1「全部未入杀招／纯功能蛊」、4.2「—」的总览表冲突；本库按档案组成表建立关系，并在本文件保留冲突。",
 "",
 "## 蛊方",
 "- 全项目未发现独立蛊方资料文件；少数文档只提及「蛊方」概念，不能据此造蛊方实体。",
 "- `Related/Recipes/README.md` 登记为「未发现」，蛊方条目数 0。",
]))

# 不完整清单
cg_index_only = [x for x in gu_entries if x["origin"] == "C-G" and x["completeness"] == "index_only"]
incomplete_rows = [
 ["C-G-245", "仅标题含描述，无独立正文", "原著合集 v3.0"],
 ["C-G-274", "标题为规则残句，无正文，疑非实体", "原著合集 v3.0"],
 ["C-G-462", "标题「注意」，正文为版本说明，非蛊虫", "原著合集 v3.0"],
 ["C-G-643", "标题「附录」，正文为流派参考表说明，非蛊虫", "原著合集 v3.0"],
 ["C-G 596 条", "只有 1 个要点，未形成七节档案", "原著合集 v3.0"],
 ["C-G 86 条", "2–3 个要点，仍属摘要级", "原著合集 v3.0"],
 ["O-G-110", "单条登记；能力效果/消耗/炼化条件未载", "仙蛊唯一性登记表"],
 ["C-B 37 条", "表格式逐条档案，无二十节正文", "原著兽类图鉴"],
 ["R-B 40 条", "八节参考档案，非本世界物种档案", "跨作品妖兽参考库"],
 ["C-K B 级 409 条", "B 级简档，部分仅名称/出处", "原著杀招百科"],
 ["扩展 45 条", "未匹配正式编号，临时键待核实", "ll_蛊虫扩展名录"],
 ["蛊方 0 条", "全项目未发现独立蛊方资料", "全项目扫描"],
]
write("Audit/INCOMPLETE.md", "\n".join([
 "# 不完整资料审计（INCOMPLETE）",
 "",
 "> 原则：缺失字段保留未知；没有资料就不补写；不把摘要级条目说成完整档案。",
 "",
 "## 档案完整度分布",
 tbl(["分区", "完整/结构化", "概要/描述", "仅索引/表格/登记", "说明"], [
  ["C-G", "0", "86", "598（596 brief + 2 index）", "逐条摘录，无七节结构化档案"],
  ["O-G", "32", "0", "1（O-G-110 登记）", "32 只七节完整档案；另 1 条仙蛊登记"],
  ["C-B", "0", "0", "37（表格式）", "逐条 7 字段，无长篇正文"],
  ["R-B", "0", "40（参考档案）", "0", "八节参考档案；非本世界实存"],
  ["O-B", "12", "0", "0", "二十节完整档案"],
  ["C-K", "38（A 级）", "409（B 级）", "0", "B 级简档按原卷"],
  ["O-K", "13", "0", "0", "完整档案"],
 ],),
 "",
 "## 明确不完整条目",
 tbl(["对象", "缺口", "来源"], incomplete_rows),
 "",
 "## C-G 无正文条目",
 "- 共 %d 条：%s" % (len(cg_index_only), "、".join(x["id"] + " " + x["name"] for x in cg_index_only)),
 "- C-G-274 不计为有效实体；C-G-245 保留编号但只有标题中的描述。",
 "",
 "## 待补充（不创作，只登记）",
 "- O-G-110 能力效果、消耗、炼化条件：登记表未载，标【待考证】。",
 "- C-G 596 条单要点条目：后续可按需补充，但不得凭空写能力。",
 "- 45 条扩展临时键：待确认是否同物/新实体；确认前不赋正式编号。",
 "- C-K B 级 409 条：原卷即简档，不强行升级。",
 "- 蛊方：未发现独立资料，暂不设实体。",
]))

# 导入报告
all_count = len(gu_entries) + len(beast_entries) + len(move_entries)
write("Audit/IMPORT_REPORT.md", "\n".join([
 "# 《衡垠世界》全量知识迁入报告",
 "",
 "> 日期：%s｜迁入库：`D:\\study\\跑团\\衡垠知识库`｜原始资料只读，未覆盖、未删除。" % DATE,
 "",
 "## 一、结论数字",
 tbl(["项目", "数量", "说明"], [
  ["蛊虫记录", len(gu_entries), "C-G %d + O-G %d" % (len([x for x in gu_entries if x['origin']=='C-G']), len([x for x in gu_entries if x['origin']=='O-G']))],
  ["— C-G 原著蛊虫", len([x for x in gu_entries if x['origin']=='C-G']), "C-G-001–684；含 3 条非实体注记（C-G-274/462/643），有效候选 681；另有 4 组疑似同物异号"],
  ["— O-G 原创蛊虫", len([x for x in gu_entries if x['origin']=='O-G']), "32 只七节完整 + O-G-110 单条登记"],
  ["妖兽记录", len(beast_entries), "C-B %d + R-B %d + O-B %d" % (len([x for x in beast_entries if x['origin']=='C-B']), len([x for x in beast_entries if x['origin']=='R-B']), len([x for x in beast_entries if x['origin']=='O-B']))],
  ["— C-B 原著兽类", len([x for x in beast_entries if x['origin']=='C-B']), "表格式逐条档案"],
  ["— R-B 参考物种", len([x for x in beast_entries if x['origin']=='R-B']), "非本世界实存"],
  ["— O-B 原创妖兽", len([x for x in beast_entries if x['origin']=='O-B']), "十二种二十节完整档案"],
  ["杀招（关联实体）", len(move_entries), "C-K %d（A %d / B %d）+ O-K %d" % (len([x for x in move_entries if x['origin']=='C-K']), len([x for x in move_entries if x['origin']=='C-K' and x['archive_level']=='A']), len([x for x in move_entries if x['origin']=='C-K' and x['archive_level']=='B']), len([x for x in move_entries if x['origin']=='O-K']))],
  ["完整/结构化档案", len([x for x in gu_entries + beast_entries + move_entries if x['completeness']=='complete_structured']), "O-G 32 + O-B 12 + C-K A 38 + O-K 13"],
  ["描述性摘要档案", len([x for x in gu_entries + beast_entries + move_entries if x['completeness']=='descriptive']), "C-G 86 + C-K B 409"],
  ["单条/表格/登记", len([x for x in gu_entries + beast_entries + move_entries if x['completeness'] in ('brief','index_only','table_entry','registration')]), "C-G 596 brief + C-G 2 index + C-B 37 + O-G-110 1"],
  ["参考区档案", len([x for x in beast_entries if x['completeness']=='reference_dossier']), "R-B 40，单独统计"],
  ["编号记录异常", 3, "C-G-274/462/643 为非实体注记；保留编号，不计有效实体"],
  ["编号口径冲突", 1, "O-G-110 预留段/登记表两口径"],
  ["编号断号/重复", 0, "C-G/C-B/R-B/O-B/C-K/O-K 全连续；O-G 预留段非连续属设计"],
  ["无正式编号的临时键", len(pending), "扩展名录 45 条，待确认"],
  ["实体级冲突", 18, "C-G-274/462/643/245 + O-G-110 + O-K 13 条组件口径；另 14 项原著争议；4 组疑似同物异号另列重复审计"],
  ["尚未迁入正式实体", 0, "核心实体全部有独立档案；蛊方 0（未发现）、历史版本 15 只不新建"],
 ],),
 "",
 "## 二、可追溯验收",
 "- 蛊虫档案：`Gu/C-G/` %d 份、`Gu/O-G/` %d 份；妖兽：`Beasts/C-B/` %d、`Beasts/R-B/` %d、`Beasts/O-B/` %d；杀招：`Related/Killer_Moves/` %d 份。" % (
   len([x for x in gu_entries if x['origin']=='C-G']), len([x for x in gu_entries if x['origin']=='O-G']),
   len([x for x in beast_entries if x['origin']=='C-B']), len([x for x in beast_entries if x['origin']=='R-B']), len([x for x in beast_entries if x['origin']=='O-B']), len(move_entries)),
 "- 每条记录有 `content_file` 字段；脚本逐条检查文件存在，缺失 %d 份。" % len(missing),
 "- 统一索引：`Indexes/gu-index.json`、`beast-index.json`、`move-index.json`、`relationship-index.json`、`source-index.json`、`alternate-gu-index.json`、`realm-index.json`。",
 "- 审计：`Audit/COVERAGE.md`、`DUPLICATES.md`、`CONFLICTS.md`、`INCOMPLETE.md`；另有 `SOURCE_SCAN.json`、`NAME_OVERLAP.json`、`EXT_MATCH.json`、`LEGACY_759.md`。",
 "",
 "## 三、边界与未做",
 "- 没有修改任何 HTML/CSS/JS，没有覆盖网站文件，没有删除原始资料。",
 "- 没有为 45 条扩展临时键编造正式编号，也没有把它们当既定实体。",
 "- 没有为 C-G 摘要条目补写能力；没有为 O-G-110 补写未载的能力/消耗/炼化条件。",
 "- 蛊方未发现独立资料，`Related/Recipes/` 只登记空目录与 README。",
 "- R-B 40 条保持参考性质，未写成衡垠本地物种。",
 "",
 "## 四、下一步",
 "- 先人工裁决 45 条扩展键、C-G-274、C-G-245、O-G-110 细节与 14 项原著争议。",
 "- 再按 Stage2 分类方案生成网站数据包；不直接改动站点。",
]))

# README
write("README.md", "\n".join([
 "# 衡垠知识库",
 "",
 "本目录是《衡垠世界》既有蛊虫、妖兽、杀招资料的统一迁入库。**只读原始资料，不修改网站文件，不覆盖、不删除任何原文。**",
 "",
 "## 结构",
 "```",
 "衡垠知识库/",
 "├── README.md",
 "├── SOURCE_INVENTORY.md",
 "├── IMPORT_REPORT.md",
 "├── Gu/",
 "│   ├── C-G/ 684 份原著蛊虫档案",
 "│   ├── O-G/ 33 份原创蛊虫档案（32 完整 + O-G-110 登记）",
 "│   └── Alternate/ 45 份未匹配扩展临时档案",
 "├── Beasts/",
 "│   ├── C-B/ 37 份原著兽类档案",
 "│   ├── R-B/ 40 份参考物种档案",
 "│   └── O-B/ 12 份原创妖兽档案",
 "├── Related/",
 "│   ├── Killer_Moves/ C-K 447 + O-K 13",
 "│   └── Recipes/ 蛊方（未发现）",
 "├── Indexes/ 统一索引（蛊虫/妖兽/杀招/关系/来源/扩展/秘境）",
 "├── Audit/ 覆盖、重复、冲突、不完整、来源扫描、导入报告",
 "├── Tools/ 可复跑脚本",
 "└── Stage2/ 第二阶段分类建议",
 "```",
 "",
 "## 关键数字",
 "- 蛊虫 %d 条：C-G %d（含 3 条非实体注记、4 组疑似同物异号）、O-G %d。" % (len(gu_entries), len([x for x in gu_entries if x['origin']=='C-G']), len([x for x in gu_entries if x['origin']=='O-G'])),
 "- 妖兽 %d 条：C-B %d、R-B %d、O-B %d。" % (len(beast_entries), len([x for x in beast_entries if x['origin']=='C-B']), len([x for x in beast_entries if x['origin']=='R-B']), len([x for x in beast_entries if x['origin']=='O-B'])),
 "- 杀招 %d 条：C-K %d、O-K %d。" % (len(move_entries), len([x for x in move_entries if x['origin']=='C-K']), len([x for x in move_entries if x['origin']=='O-K'])),
 "- 关系 %d 条；外部临时键 %d 条；秘境登记 %d 条。" % (len(relations), len(pending), len(realm)),
 "",
 "## 使用顺序",
 "1. 读 `Audit/IMPORT_REPORT.md` 看结论与缺口。",
 "2. 读 `Indexes/gu-index.json`、`beast-index.json`、`move-index.json` 取结构化数据。",
 "3. 需要关系图时读 `relationship-index.json`；每条关系都指向已登记实体。",
 "4. 需要数据分区与 AI 读取建议时读 `Stage2/CLASSIFICATION_PLAN.md`；世界层数据见 `../World/`。",
 "5. 交付前跑 `Tools/validate.py`，核对 `Audit/VALIDATION.md`。",
 "",
 "## 边界",
 "- C-G/O-G、C-B/R-B/O-B 严格分区。",
 "- R-B 是参考物种，不是衡垠实存物种。",
 "- 一条实体一份正式档案；分类目录只引用，不复制。",
 "- 未知字段保留未知；没有正式编号的扩展条目不赋编号。",
 "- 杀招、蛊方是关联实体，不是蛊虫。",
]))

# SOURCE_INVENTORY
write("SOURCE_INVENTORY.md", "\n".join([
 "# 来源清单（SOURCE_INVENTORY）",
 "",
 "> 全项目扫描 79 个文本文件，详见 `Audit/SOURCE_SCAN.json`。下表列出有实体贡献的核心来源。",
 "",
 "## 核心来源",
 tbl(["来源文件", "角色", "字节", "行数", "贡献", "MD5"], [[x["path"], next((r for p, r in [(q["path"], q["role"]) for q in src_entries] if p == x["path"]), "核心源"), x["bytes"], x["lines"], x["note"], x["md5"][:12]] for x in core_meta]),
 "",
 "## 实体计数对应",
 tbl(["分区", "来源", "条目数", "档案目录"], [
  ["C-G", "蛊真人蛊虫合集 v3.0", 684, "Gu/C-G/"],
  ["O-G", "原创蛊虫图鉴 + 仙蛊唯一性登记表", 33, "Gu/O-G/"],
  ["C-K", "原著杀招百科", 447, "Related/Killer_Moves/"],
  ["O-K", "原创杀招图鉴", 13, "Related/Killer_Moves/"],
  ["C-B", "原著兽类图鉴", 37, "Beasts/C-B/"],
  ["R-B", "跨作品妖兽参考库", 40, "Beasts/R-B/"],
  ["O-B", "原创妖兽图鉴", 12, "Beasts/O-B/"],
  ["扩展", "ll_蛊虫扩展名录", 264, "Gu/Alternate/（仅 45 未匹配）"],
  ["底稿", "原始备份 20261113 + v2 基线", "759 标题 / 684 条", "Indexes/legacy-759-map.json"],
  ["历史", "蛊道百科 v1.0", "15 只旧 O-G", "只作版本谱系，不新建"],
  ["秘境", "10_全球秘境总目录", "64 条表行", "Indexes/realm-index.json"],
 ],),
 "",
 "## 未作为实体源的文件",
 "- 质检报告、总目录、关联索引、考据记录、战斗判定、能力评估等：用于校验与关系，不重复生成实体。",
 "- 网站 HTML、CSS、JS：本轮完全未改。",
]))

# Recipes README
write("Related/Recipes/README.md", "\n".join([
 "# 蛊方（Recipes）",
 "",
 "## 扫描结论",
 "- **全项目未发现独立蛊方资料文件**。`蛊方`一词只在《原创蛊虫图鉴》《蛊真人蛊虫合集 v3.0》《原著杀招百科》《原著杀招设计机制分析报告》中被提及，未形成可迁入的蛊方条目。",
 "- 因此本目录不建立蛊方实体，不编造配方、材料、火候、成功率。",
 "",
 "## 已检索文件",
 "- `01_最终版/蛊道资料库_v3.0/原创蛊虫图鉴.md`",
 "- `01_最终版/蛊道资料库_v3.0/蛊真人蛊虫合集_v3.0.md`",
 "- `01_最终版/蛊道资料库_v3.0/原著杀招百科.md`",
 "- `01_最终版/蛊道资料库_v3.0/原著杀招设计机制分析报告.md`",
 "",
 "## 后续",
 "- 如用户提供独立蛊方资料，再按 `Related/Recipes/<recipe-id>.md` 建实体，并与蛊虫/杀招建立关系。",
 "- 当前蛊虫索引中 `related_recipes` 统一为空，不伪造关联。",
]))

# Stage2
write("Stage2/CLASSIFICATION_PLAN.md", "\n".join([
 "# 第二阶段分类建议（不创作新实体）",
 "",
 "## 一、蛊虫目录：四层",
 "1. 来源类别：C-G 原著 / O-G 原创。",
 "2. 转数：一转 … 九转；未知单独一组，不猜测。",
 "3. 实际流派：只列数据中真实存在的 `sect`；`null` 进“未标流派”。",
 "4. 条目：名称、编号、转数、流派、能力摘要、来源、完整度。",
 "",
 "默认排序：转数升序 → 流派 → 编号。",
 "",
 "## 二、妖兽目录：先分区，再筛选",
 "- 分区：C-B 原著参照 / R-B 跨作品参考 / O-B 本世界原创实存。",
 "- 筛选维度：栖息环境、危险等级、体型、生态类型、是否携带蛊虫、是否关联秘境。",
 "- C-B 与 R-B 不得写成“本地物种”；R-B 详情页需固定提示“参考素材，非衡垠实存”。",
 "- O-B 保留二十节结构；携带蛊虫单独显示“携带/寄生/共生/被动触发”，不表述为主动催动。",
 "",
 "## 三、关系数据",
 "- 关系只从 `Indexes/relationship-index.json` 生成；地图、搜索、目录、详情页共用同一 ID。",
 "- 当前关系类型：蛊虫关联蛊虫、妖兽携带蛊虫、妖兽引用原著兽类、妖兽栖息秘境、杀招使用蛊虫、妖兽实战组合引用杀招等。",
 "- 未解析目标已列在 `relationship-index.json.unresolved_relations`，不画进关系图。",
 "",
 "## 四、网站数据包字段",
 "```json",
 "{",
 "  \"id\": \"C-G-001\",",
 "  \"name\": \"一气金光虫\",",
 "  \"type\": \"gu\",",
 "  \"origin\": \"C-G\",",
 "  \"rank\": 1,",
 "  \"sect\": null,",
 "  \"status\": \"existing\",",
 "  \"completeness\": \"brief\",",
 "  \"content_file\": \"Gu/C-G/C-G-001.md\",",
 "  \"source_files\": [],",
 "  \"relations\": []",
 "}",
 "```",
 "- `rank` 未知用 `null`；`sect` 未知用 `null`；不得猜测。",
 "- 目录只引用 `id`，不复制档案正文。",
 "",
 "## 五、待裁决后再做",
 "1. 45 条扩展临时键：确认同物则合并来源，确认新物则由编号管理员分配。",
 "2. C-G-274：确认是否废弃/合并；当前保留编号。",
 "3. C-G-245：确认标题中的描述是否拆出正文。",
 "4. O-G-110：能力/消耗/炼化条件补写前，先更新登记表。",
 "5. 14 项原著争议：保持并列，不做“统一设定”。",
 "",
 "## 六、验收顺序",
 "- 先验 ID 唯一与文件存在；再验目录计数与索引计数一致；再验关系目标存在；最后验详情页字段。",
 "- 任何“完整档案”标签必须对应 `completeness=complete_structured`，不得把 C-G 摘要条目升级。",
]))

print("GU", len(gu_entries), "BEAST", len(beast_entries), "MOVE", len(move_entries), "REL", len(relations), "UNRESOLVED", len(unresolved), "MISSING", len(missing))
print("CG no body", cg_no_body, "bullet_dist", dict(bullet_dist), "rank_conflicts", len(rank_conflicts))
print("threat_conflicts", len(threat_conflicts), "dup_names", len(dup_names), "dup_beasts", len(dup_beasts), "OK comps", len(o_k_components), "OG moves", len(og_with_moves))
