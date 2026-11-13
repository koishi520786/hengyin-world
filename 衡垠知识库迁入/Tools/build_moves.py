# -*- coding: utf-8 -*-
"""生成 C-K / O-K 杀招档案与关联片段。"""
import os, re, io, json, collections

ROOT = r"D:\study\跑团"
OUT = os.path.join(ROOT, "衡垠知识库迁入")
BASE = os.path.join(ROOT, "01_最终版")

def read(p): return io.open(p, encoding="utf-8").read()
def write(rel, text):
    p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f: f.write(text)
def clean(x): return re.sub(r"\s+", " ", (x or "").strip())
def trunc(s, n=180):
    s = clean(s); return s if len(s) <= n else s[:n] + "…"

# 载入蛊虫名表
gu_part = json.loads(read(os.path.join(OUT, r"Indexes\_gu_part.json")))
gu = gu_part["gu"]
name_ids = collections.defaultdict(list)
for gid, e in gu.items():
    for v in e.get("name_variants", []) + [e.get("name_primary", "")]:
        if v: name_ids[v].append(gid)

def match_name(n):
    n = re.sub(r"【[^】]*】", "", n)
    n = re.sub(r"（[^）]*）|\([^)]*\)", "", n)
    n = re.split(r"[：:／/,，]", n)[0].strip()
    n = re.sub(r"^[\s·]*|[\s·]*$", "", n)
    ids = sorted(set(name_ids.get(n, [])))
    return ids[0] if len(ids) == 1 else None

def components_of(block):
    ids, unresolved = [], []
    in_sec = False
    for ln in block.splitlines():
        if re.match(r"^#{2,4}\s*[二三]、?组成蛊虫", ln) or "组成蛊虫" in ln and ln.startswith("#"):
            in_sec = True; continue
        if in_sec and re.match(r"^#{2,4}\s", ln):
            in_sec = False
        if not in_sec: continue
        if not ln.strip().startswith("|"): continue
        if re.match(r"^\|\s*(蛊虫名称|项目|编号)", ln): continue
        if re.match(r"^\|\s*-+", ln): continue
        found = re.findall(r"([CO])-([GK])-(\d{3})", ln)
        for m in found:
            t = "%s-%s-%s" % m
            if t not in ids: ids.append(t)
        if not found:
            first = ln.split("|")[1].strip() if "|" in ln else ""
            mid = match_name(first)
            if mid and mid not in ids:
                ids.append(mid)
            elif first and first not in ("", "—", "待考"):
                unresolved.append(first)
    return ids, unresolved

# ============ C-K 索引 ============
ck_lines = read(os.path.join(BASE, r"蛊道资料库_v3.0\原著杀招百科.md")).splitlines()
s2 = next(i for i, ln in enumerate(ck_lines) if ln.startswith("## 二、快速索引表"))
s3 = next(i for i, ln in enumerate(ck_lines) if ln.startswith("## 三、按品阶分类"))
ck_rows = {}
for ln in ck_lines[s2:s3]:
    if re.match(r"^\| C-K-\d{3} \|", ln):
        f = [x.strip() for x in ln.split("|")[1:-1]]
        if len(f) >= 8:
            ck_rows[f[0]] = {"id": f[0], "name": f[1], "rank_raw": f[2], "sect": f[3],
                             "function": f[4], "user": f[5], "credibility": f[6], "level": f[7]}
# A blocks
s9 = next(i for i, ln in enumerate(ck_lines) if ln.startswith("## 九、A 级"))
s10 = next(i for i, ln in enumerate(ck_lines) if ln.startswith("## 十、B 级"))
a_blocks = []
for i in range(s9, s10):
    if re.match(r"^## C-K-", ck_lines[i]):
        end = next((j for j in range(i + 1, s10) if re.match(r"^## C-K-", ck_lines[j])), s10)
        a_blocks.append((re.findall(r"C-K-\d{3}", ck_lines[i]), "\n".join(ck_lines[i:end]).strip("\n")))
a_map = {}
for ids, block in a_blocks:
    for cid in ids: a_map[cid] = (block, ids)
# B blocks
b_map = {}
i = s10
while i < len(ck_lines):
    if re.match(r"^#### C-K-", ck_lines[i]):
        m = re.match(r"^#### (C-K-\d{3})", ck_lines[i])
        end = i + 1
        while end < len(ck_lines) and not re.match(r"^#### C-K-", ck_lines[end]) and not re.match(r"^## ", ck_lines[end]):
            end += 1
        b_map[m.group(1)] = "\n".join(ck_lines[i:end]).strip("\n")
        i = end
    else:
        i += 1
print("CK index", len(ck_rows), "A", len(a_map), "B", len(b_map))

moves = {}
ck_to_cg = collections.defaultdict(list)
for cid, row in ck_rows.items():
    detail = None; level = row["level"]
    if cid in a_map: detail, ids = a_map[cid]; level = "A"
    elif cid in b_map: detail = b_map[cid]; level = "B"
    comps, unresolved = components_of(detail) if detail else ([], [])
    e = {
        "id": cid, "name": row["name"], "type": "killer_move", "origin": "C-K",
        "origin_label": "原著杀招", "rank_raw": row["rank_raw"],
        "rank_value": ({"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}.get(re.search(r"([一二三四五六七八九])转", row["rank_raw"]).group(1)) if re.search(r"([一二三四五六七八九])转", row["rank_raw"]) else None),
        "sect": row["sect"], "function": row["function"], "user": row["user"],
        "credibility": row["credibility"], "archive_level": level,
        "status": "existing",
        "completeness": "complete_structured" if level == "A" else ("descriptive" if detail else "index_only"),
        "content_file": "Related/Killer_Moves/%s.md" % cid,
        "source_files": ["01_最终版/蛊道资料库_v3.0/原著杀招百科.md"],
        "components": comps, "unresolved_components": unresolved,
        "flags": [] if level == "A" else (["B_level_brief"] if detail else ["index_only"])
    }
    moves[cid] = e
    write(e["content_file"], "\n".join([
        "# %s %s" % (cid, row["name"]),
        "",
        "> C-K 原著杀招｜迁入自《原著杀招百科》。档案级别 %s；详细程度按原卷，不补写缺失组件与消耗。" % level,
        "",
        "## 索引字段",
        "- 编号：%s" % cid,
        "- 名称：%s" % row["name"],
        "- 分类来源：C-K（原著杀招）",
        "- 品阶：%s" % row["rank_raw"],
        "- 主要流派：%s" % row["sect"],
        "- 功能：%s" % row["function"],
        "- 使用者／创造者：%s" % row["user"],
        "- 可信度：%s" % row["credibility"],
        "- 档案级别：%s" % level,
        "- 资料完整度：%s" % ("十节完整档案" if level == "A" else ("B 级简档" if detail else "仅索引")),
        "- 来源文件：`01_最终版/蛊道资料库_v3.0/原著杀招百科.md`",
        "",
        "## 详细档案" if detail else "## 详细档案",
        "",
        detail if detail else "（原卷仅有索引行，未建详细档案；不编造组件、发动条件与消耗。）",
        "",
    ]))

# ============ C-K → C-G 映射（关联索引第二节）============
rel_lines = read(os.path.join(BASE, r"蛊道资料库_v3.0\蛊虫杀招关联索引.md")).splitlines()
in_sec = False
for ln in rel_lines:
    if ln.startswith("## 二、原著杀招"):
        in_sec = True; continue
    if in_sec and ln.startswith("## "):
        break
    if in_sec and re.match(r"^\| C-K-\d{3} \|", ln):
        f = [x.strip() for x in ln.split("|")[1:-1]]
        if len(f) >= 3:
            cid = f[0]
            for gid in re.findall(r"C-G-\d{3}", f[2]):
                if gid in gu and gid not in ck_to_cg[cid]:
                    ck_to_cg[cid].append(gid)

# ============ O-K ============
ok_lines = read(os.path.join(BASE, r"蛊道资料库_v3.0\原创杀招图鉴.md")).splitlines()
ok_blocks = []
for i, ln in enumerate(ok_lines):
    m = re.match(r"^# 【原创设定】(.+)$", ln)
    if m: ok_blocks.append({"name": m.group(1).strip(), "line": i})
for bi, b in enumerate(ok_blocks):
    end = ok_blocks[bi + 1]["line"] if bi + 1 < len(ok_blocks) else next(
        (i for i, ln in enumerate(ok_lines) if ln.startswith("## 文末自检")), len(ok_lines))
    block = "\n".join(ok_lines[b["line"]:end]).strip("\n")
    fields = {}
    for ln in ok_lines[b["line"]:min(end, b["line"] + 40)]:
        m = re.match(r"^\| (杀招编号|名称|杀招类别|品阶|所属流派|功能类型|创造者|主要使用者|首次出现章节|信息可信度|主要用途) \| (.+?) \|", ln)
        if m: fields[m.group(1)] = m.group(2).strip()
    oid = fields.get("杀招编号")
    if not oid: continue
    comps, unresolved = components_of(block)
    rank = re.search(r"([一二三四五六七八九])转", fields.get("品阶", ""))
    e = {
        "id": oid, "name": fields.get("名称", b["name"]), "type": "killer_move", "origin": "O-K",
        "origin_label": "原创杀招", "rank_raw": fields.get("品阶", "未知"),
        "rank_value": ({"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}.get(rank.group(1)) if rank else None),
        "sect": fields.get("所属流派"), "function": fields.get("功能类型"),
        "user": fields.get("主要使用者"), "credibility": "【原创设定】", "archive_level": "完整",
        "status": "existing", "completeness": "complete_structured",
        "content_file": "Related/Killer_Moves/%s.md" % oid,
        "source_files": ["01_最终版/蛊道资料库_v3.0/原创杀招图鉴.md"],
        "components": comps, "unresolved_components": unresolved, "flags": ["original_setting"]
    }
    moves[oid] = e
    write(e["content_file"], "\n".join([
        "# %s %s" % (oid, e["name"]),
        "",
        "> 【原创设定】O-K 原创杀招｜迁入自《原创杀招图鉴 v3.0》，完整档案，原文保留。",
        "",
        "## 基础索引",
        "- 编号：%s" % oid,
        "- 名称：%s" % e["name"],
        "- 分类来源：O-K（原创杀招）",
        "- 杀招类别：%s" % fields.get("杀招类别", "未知"),
        "- 品阶：%s" % fields.get("品阶", "未知"),
        "- 所属流派：%s" % fields.get("所属流派", "未知"),
        "- 功能类型：%s" % fields.get("功能类型", "未知"),
        "- 创造者：%s" % fields.get("创造者", "未知"),
        "- 主要使用者：%s" % fields.get("主要使用者", "未知"),
        "- 主要用途：%s" % fields.get("主要用途", "未知"),
        "- 资料完整度：完整档案",
        "- 设定状态：existing（原创区）",
        "",
        "## 原始档案",
        "",
        block,
        "",
        "## 组件索引备注",
        "- 已解析到正式蛊虫编号：%s" % ("、".join(comps) if comps else "无"),
        "- 名称未能唯一匹配的组件：%s" % ("、".join(unresolved) if unresolved else "无"),
        "- 仅按组成表与正式名称做保守匹配；未匹配不推断编号。",
        "",
    ]))

write("Indexes/_move_part.json", json.dumps({
    "moves": moves, "ck_to_cg": ck_to_cg
}, ensure_ascii=False, indent=1))
print("C-K:", len([x for x in moves.values() if x["origin"] == "C-K"]),
      "O-K:", len([x for x in moves.values() if x["origin"] == "O-K"]))
