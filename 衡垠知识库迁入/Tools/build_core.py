# -*- coding: utf-8 -*-
"""
衡垠知识库迁入 · 核心构建
- 逐条生成蛊虫/妖兽独立 Markdown 档案
- 生成 JSON 索引与关系索引
- 原始资料只读，不覆盖、不删除
"""
import os, re, io, json, collections

ROOT = r"D:\study\跑团"
OUT = os.path.join(ROOT, "衡垠知识库迁入")
BASE = os.path.join(ROOT, "01_最终版")

def read(p):
    return io.open(p, encoding="utf-8").read()

def write(rel, text):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def clean(x):
    return re.sub(r"\s+", " ", (x or "").strip())

def norm_name(n):
    n = re.sub(r"（[^）]*）|\([^)]*\)", "", n)
    n = re.split(r"：|:", n)[0]
    n = re.sub(r"[【】\[\]〔〕\s·]", "", n)
    return n

def variants(name):
    return [x for x in {norm_name(p) for p in re.split(r"[、／/]|，", name) if norm_name(p)}]

def trunc(s, n=180):
    s = clean(s)
    return s if len(s) <= n else s[:n] + "…"

# ============ 1. C-G ============
cg_lines = read(os.path.join(BASE, r"蛊道资料库_v3.0\蛊真人蛊虫合集_v3.0.md")).splitlines()
cg_entries = []
cur = None
for i, ln in enumerate(cg_lines):
    m = re.match(r"^### (C-G-\d{3})\s+(.*)$", ln)
    if m:
        cur = {"id": m.group(1), "name": m.group(2).strip(), "line": i, "body": []}
        cg_entries.append(cur)
    elif cur and (ln.startswith("### ") or ln.startswith("## ")):
        cur = None
    elif cur is not None:
        cur["body"].append(ln)

RANGES = [(1, 1, 45), (2, 46, 77), (3, 78, 123), (4, 124, 159), (5, 160, 212),
          (6, 213, 248), (7, 249, 259), (8, 260, 266), (9, 267, 274), (10, 275, 275)]
def cg_rank(cgid):
    n = int(cgid.split("-")[-1])
    for r, a, b in RANGES:
        if a <= n <= b:
            return r
    return None

CN_NUM = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10}
def explicit_rank(text):
    m = re.search(r"([一二三四五六七八九十])\s*转", text)
    return CN_NUM.get(m.group(1)) if m else None

def explicit_sect(text):
    m = re.search(r"([\u4e00-\u9fa5]{1,2})道(?=仙蛊|凡蛊|蛊虫|蛊|杀招)", text)
    return (m.group(1) + "道") if m else None

def cg_class(rank, text):
    if rank and rank <= 5: return "凡蛊"
    if rank and rank >= 6: return "仙蛊"
    if "仙蛊" in text: return "仙蛊"
    if "凡蛊" in text: return "凡蛊"
    if "蛊屋" in text: return "蛊屋"
    if "战阵" in text: return "战阵"
    return "未定"

cg_index = {}
cg_name_map = collections.defaultdict(list)
cg_files = []
for e in cg_entries:
    raw_name = e["name"]
    body = "\n".join(e["body"]).strip("\n")
    bullets = [x.strip()[1:].strip() for x in e["body"] if x.strip().startswith("-")]
    sec_rank = cg_rank(e["id"])
    body_rank = explicit_rank(raw_name + "\n" + "\n".join(e["body"][:3]))
    rank = sec_rank if sec_rank else body_rank
    rank_basis = "合集章节归类" if sec_rank else ("正文自述" if body_rank else "未标注")
    rank_raw = (str(rank) + "转") if rank else "未知"
    cls = cg_class(rank, raw_name + "\n" + body)
    sect = explicit_sect(raw_name + "\n" + body)
    ability = None
    for b in bullets:
        if re.match(r"^[一二三四五六七八九十]+转", b): continue
        if len(b) <= 3: continue
        if b in ("凡蛊", "仙蛊", "花蛊", "草蛊", "蛊屋", "战阵"): continue
        ability = b; break
    if ability is None and bullets:
        ability = bullets[0]
    completeness = "index_only" if not body.strip() else ("brief" if len(bullets) <= 1 else "descriptive")
    entry = {
        "id": e["id"], "name": raw_name, "name_primary": norm_name(raw_name.split("，")[0]),
        "type": "gu", "origin": "C-G", "origin_label": "原著蛊虫",
        "rank": rank, "rank_raw": rank_raw, "rank_basis": rank_basis,
        "class": cls, "sect": sect, "sect_raw": sect,
        "ability_summary": trunc(ability) if ability else None,
        "use_summary": None, "limits": None,
        "status": "existing", "completeness": completeness,
        "content_file": "Gu/C-G/%s.md" % e["id"],
        "source_files": ["01_最终版/蛊道资料库_v3.0/蛊真人蛊虫合集_v3.0.md",
                         "03_归档_原始底稿与备份/整合版v2基线/蛊真人蛊虫合集.txt"],
        "name_variants": variants(raw_name),
        "flags": []
    }
    if e["id"] == "C-G-274": entry["flags"].append("malformed_heading_non_entity")
    if e["id"] == "C-G-245": entry["flags"].append("heading_contains_description")
    if not rank: entry["flags"].append("rank_unknown")
    if not sect: entry["flags"].append("sect_unknown")
    cg_index[e["id"]] = entry
    for v in entry["name_variants"]:
        cg_name_map[v].append(e["id"])

    lines = [
        "# %s %s" % (e["id"], raw_name),
        "",
        "> 迁入自《蛊真人蛊虫合集 v3.0》｜原文逐行保留，未改写名称、编号、转数与能力。",
        "",
        "## 基础索引",
        "- 编号：%s" % e["id"],
        "- 名称：%s" % raw_name,
        "- 来源类别：C-G（原著蛊虫）",
        "- 转数：%s" % (rank_raw if rank else "未知（原文未标注，未擅自推断）"),
        "- 蛊类：%s" % cls,
        "- 流派：%s" % (sect or "未知（原文未明确）"),
        "- 主要能力：%s" % (trunc(ability) if ability else "未知（原文未载）"),
        "- 核心用途：未知（原文未单列）",
        "- 关键限制：未知（原文未单列）",
        "- 关联杀招：见关系索引",
        "- 关联蛊方：未发现",
        "- 来源文件：`01_最终版/蛊道资料库_v3.0/蛊真人蛊虫合集_v3.0.md`；基线 `03_归档_原始底稿与备份/整合版v2基线/蛊真人蛊虫合集.txt`",
        "- 资料完整度：%s" % {"index_only":"仅索引/无正文","brief":"一段式条目","descriptive":"多段条目"}[completeness],
        "- 设定状态：existing（原著区）",
        "",
        "## 原始记载",
        "",
        body if body.strip() else "（原文件该条目无正文；仅存标题行，已按原样保留。）",
        "",
        "## 迁入备注",
    ]
    if e["id"] == "C-G-274":
        lines.append("- 该标题为一句喂养规则残句，未含蛊虫名与正文，疑为底稿误立条目；保留原编号，不删不改，标为待核查。")
    elif e["id"] == "C-G-245":
        lines.append("- 标题行同时包含名称与能力描述，原文无独立正文；名称字段照录标题，不作拆分改写。")
    else:
        lines.append("- 该条目只有原始摘录，无结构化七节档案；资料完整度按原文实际标注。")
    write(entry["content_file"], "\n".join(lines))

# ============ 2. O-G ============
og_lines = read(os.path.join(BASE, r"蛊道资料库_v3.0\原创蛊虫图鉴.md")).splitlines()
og_blocks = []
for i, ln in enumerate(og_lines):
    m = re.match(r"^# 【原创设定】(.+)$", ln)
    if m:
        og_blocks.append({"name": m.group(1).strip(), "line": i})
for bi, b in enumerate(og_blocks):
    end = og_blocks[bi + 1]["line"] if bi + 1 < len(og_blocks) else len(og_lines)
    block = "\n".join(og_lines[b["line"]:end]).strip("\n")
    fields = {}
    for ln in og_lines[b["line"]:min(end, b["line"] + 30)]:
        m = re.match(r"^\| (编号|名称|品阶|凡蛊或仙蛊|所属流派|核心用途|稀有程度|原创标识) \| (.+?) \|", ln)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    oid = fields.get("编号")
    if not oid:
        continue
    rank = explicit_rank(fields.get("品阶", ""))
    sect = fields.get("所属流派")
    cls = "凡蛊" if "凡蛊" in fields.get("凡蛊或仙蛊", "") else ("仙蛊" if "仙蛊" in fields.get("凡蛊或仙蛊", "") else ("特殊蛊" if "特殊" in fields.get("凡蛊或仙蛊", "") else "未定"))
    entry = {
        "id": oid, "name": fields.get("名称", b["name"]), "type": "gu", "origin": "O-G",
        "origin_label": "原创蛊虫", "rank": rank, "rank_raw": fields.get("品阶", "未知"),
        "rank_basis": "档案基本资料", "class": cls, "sect": sect, "sect_raw": sect,
        "ability_summary": fields.get("核心用途"), "use_summary": fields.get("核心用途"),
        "limits": None, "status": "existing", "completeness": "complete_structured",
        "content_file": "Gu/O-G/%s.md" % oid,
        "source_files": ["01_最终版/蛊道资料库_v3.0/原创蛊虫图鉴.md"],
        "name_variants": variants(fields.get("名称", b["name"])) + variants(b["name"]),
        "flags": ["original_setting"]
    }
    cg_index[oid] = entry
    # O-G 关系：抓 O-G / O-K / C-G 编号
    rel = []
    for m in re.finditer(r"([CO])-([GK])-(\d{3})", block):
        t = "%s-%s-%s" % (m.group(1), m.group(2), m.group(3))
        if t != oid and t not in [r["target"] for r in rel]:
            rel.append({"type": "related", "target": t, "source_section": "七、搭配关系"})
    entry["relations"] = rel
    lines = [
        "# %s %s" % (oid, entry["name"]),
        "",
        "> 【原创设定】迁入自《原创蛊虫图鉴 v3.0》｜七节完整档案，原文保留。与原著 C-G 严格分区。",
        "",
        "## 基础索引",
        "- 编号：%s" % oid,
        "- 名称：%s" % entry["name"],
        "- 来源类别：O-G（原创蛊虫）",
        "- 转数：%s" % fields.get("品阶", "未知"),
        "- 蛊类：%s" % fields.get("凡蛊或仙蛊", cls),
        "- 流派：%s" % (sect or "未知"),
        "- 核心用途：%s" % fields.get("核心用途", "未知"),
        "- 稀有程度：%s" % fields.get("稀有程度", "未知"),
        "- 关联杀招：见关系索引",
        "- 来源文件：`01_最终版/蛊道资料库_v3.0/原创蛊虫图鉴.md`",
        "- 资料完整度：七节完整档案",
        "- 设定状态：existing（原创区）",
        "",
        "## 原始档案",
        "",
        block,
        "",
    ]
    write(entry["content_file"], "\n".join(lines))

# O-G-110 单条登记（不在 32 只七节档案内）
og110 = {
    "id": "O-G-110", "name": "界隙蛊", "type": "gu", "origin": "O-G",
    "origin_label": "原创蛊虫（野生仙蛊登记）", "rank": 6, "rank_raw": "六转·宇道",
    "rank_basis": "仙蛊唯一性登记表", "class": "仙蛊", "sect": "宇道",
    "sect_raw": "宇道", "ability_summary": "登记表未载能力效果；仅登记为 O-B-012 阈鹿体表被动寄生的野生仙蛊。",
    "use_summary": None, "limits": "妖兽不可催动；自主护主存疑；宿主死亡后是否留存未知；能力／消耗／炼化均待考证。",
    "status": "existing", "completeness": "registration",
    "content_file": "Gu/O-G/O-G-110.md",
    "source_files": ["01_最终版/妖兽图鉴/仙蛊唯一性登记表.md"],
    "name_variants": ["界隙蛊"], "flags": ["original_setting", "registration_only", "reserved_segment_extension"],
    "relations": [{"type": "parasitizes", "target": "O-B-012", "relation": "体表寄生（被动）", "source_section": "登记表 C 组"}]
}
cg_index["O-G-110"] = og110
write("Gu/O-G/O-G-110.md", "\n".join([
    "# O-G-110 界隙蛊",
    "",
    "> 【原创设定】单条仙蛊登记，非七节完整档案。来源《仙蛊唯一性登记表》C 组；占用 v3.0 预留段 O-G-110，属顺延追加，不改动 v3.0 任何文件。",
    "",
    "## 基础索引",
    "- 编号：O-G-110",
    "- 名称：界隙蛊",
    "- 来源类别：O-G（原创蛊虫／野生仙蛊登记）",
    "- 转数：六转",
    "- 流派：宇道",
    "- 蛊类：仙蛊",
    "- 宿主：O-B-012 阈鹿（体表寄生，被动）",
    "- 控制状态：妖兽不可催动；自主护主存疑；宿主死亡后是否留存未知",
    "- 资料完整度：单条登记（能力效果、消耗、炼化条件均未载）",
    "- 设定状态：existing／【原创设定】",
    "",
    "## 登记原文（12 字段）",
    "",
    "| 编号 | 名称 | 转数 | 来源 | 原持有者 | 当前所在地 | 是否炼化 | 是否封印 | 宿主关系 | 控制状态 | 状态变更记录 | 可信度 |",
    "|---|---|---|---|---|---|---|---|---|---|---|---|",
    "| **O-G-110** | **界隙蛊** | **六转·宇道** | **【原创设定】**（本轮新增，非原著蛊虫，不进原著区） | **无**（本轮首次登记，从未被他人持有） | **O-B-012 阈鹿体表**（被动寄生）；阈值／界隙具体位置【位置或归属待核实】 | **未被炼化** | **未被封印** | **体表寄生（被动）**，宿主为本世界原创妖兽 **O-B-012 阈鹿** | **妖兽不可催动**；**自主护主存疑**；宿主死亡后是否留存**未知**；能否控制／是否自主活动／是否形成配合均【存疑／未知】 | ① 本轮首次登记；② 占用 v3.0 已声明的「**O-G-110 起预留段**」，属**顺延追加**；③ **不改动 v3.0 任何文件**；④ 预留段冲突处置见 4.3 | **【原创设定】** |",
    "",
    "## 唯一性与边界",
    "- 仙蛊同名天下唯一，不得重复生成、不得重新安排给别的妖兽。",
    "- 妖兽携带 ≠ 控制 ≠ 催动；O-B-012 不因携此蛊而获得空窍、真元、炼蛊或催动能力。",
    "- 登记表未载的能力效果、消耗、炼化条件一律【待考证】，不得由本条登记升格为能力描述。",
    "",
    "## 来源",
    "- `01_最终版/妖兽图鉴/仙蛊唯一性登记表.md` 第四节 C 组。",
]))

# 落盘中间索引（供总装脚本读取）
write("Indexes/_gu_part.json", json.dumps({
    "gu": cg_index,
    "name_map": {k: v for k, v in cg_name_map.items()},
}, ensure_ascii=False, indent=1))
print("C-G:", len([x for x in cg_index.values() if x["origin"] == "C-G"]),
      "O-G:", len([x for x in cg_index.values() if x["origin"] == "O-G"]))
