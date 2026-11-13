# -*- coding: utf-8 -*-
"""生成 C-B / R-B / O-B 独立妖兽档案与索引片段。"""
import os, re, io, json, collections

ROOT = r"D:\study\跑团"
OUT = os.path.join(ROOT, "知识库", "衡垠知识库")
BASE = os.path.join(ROOT, "01_最终版")

def read(p): return io.open(p, encoding="utf-8").read()
def write(rel, text):
    p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f: f.write(text)
def clean(x): return re.sub(r"\s+", " ", (x or "").strip())
def strip_bold(x): return clean(re.sub(r"\*\*", "", x or ""))
def trunc(s, n=180):
    s = clean(s); return s if len(s) <= n else s[:n] + "…"
def esc(x): return clean(x).replace("|", "\\|")

# ============ C-B ============
cb_lines = read(os.path.join(BASE, r"妖兽图鉴\原著兽类图鉴.md")).splitlines()
start = next(i for i, ln in enumerate(cb_lines) if ln.startswith("## 三、原著兽类逐条档案"))
cb_rows = []
for ln in cb_lines[start:]:
    if ln.startswith("## ") and not ln.startswith("## 三"):
        break
    if re.match(r"^\| C-B-\d{3} \|", ln):
        f = [x.strip() for x in ln.split("|")]
        # ['', id, name, category, ability, events, source, cred, '']
        if len(f) >= 9:
            cb_rows.append(f[1:8])
print("CB rows:", len(cb_rows))
beasts = {}
for f in cb_rows:
    cid, name, cat, ability, events, source, cred = f
    e = {
        "id": cid, "name": name, "type": "beast", "origin": "C-B", "origin_label": "原著兽类",
        "partition": "C-B", "is_world_species": False, "world_status": "原著参照物种，不作为本世界实存物种",
        "category": cat, "danger_level": None, "size": None, "habitat": None,
        "ability_summary": trunc(ability), "behavior": None, "carries_gu": False,
        "carried_gu": [], "related_realms": [], "related_regions": [],
        "status": "existing", "completeness": "table_entry",
        "content_file": "Beasts/C-B/%s.md" % cid,
        "source_files": ["01_最终版/妖兽图鉴/原著兽类图鉴.md"],
        "credibility": cred, "flags": ["table_only"]
    }
    beasts[cid] = e
    refs = sorted(set(re.findall(r"C-G-\d{3}", ability + " " + events + " " + source)))
    e["relations"] = [{"type": "cites_gu", "target": x, "source_section": "逐条档案"} for x in refs]
    write(e["content_file"], "\n".join([
        "# %s %s" % (cid, name),
        "",
        "> C-B 原著兽类｜迁入自《原著兽类图鉴》。原卷为表格式逐条档案，无二十节正文；本档案照录该行全部字段，未补写能力数值。",
        "",
        "## 基础索引",
        "- 编号：%s" % cid,
        "- 名称：%s" % name,
        "- 分类来源：C-B（原著兽类）",
        "- 原著分类：%s" % cat,
        "- 本世界实存：否（仅规则参照；世界地理不得写成本地物种）",
        "- 危险等级：未知（原卷未设 C-B 威胁分级）",
        "- 体型：未知（原卷未载）",
        "- 栖息环境：未知（原卷未单列；见能力与表现）",
        "- 资料完整度：表格式条目（非完整物种档案）",
        "- 可信度：%s" % cred,
        "- 来源文件：`01_最终版/妖兽图鉴/原著兽类图鉴.md`",
        "- 设定状态：existing（原著区）",
        "",
        "## 原著记载",
        "| 项目 | 内容 |",
        "|---|---|",
        "| 原著名称 | %s |" % esc(name),
        "| 原著分类 | %s |" % esc(cat),
        "| 能力 | %s |" % esc(ability),
        "| 实力表现 | %s |" % esc(events),
        "| 出处或章节 | %s |" % esc(source),
        "| 可信度 | %s |" % esc(cred),
        "",
        "## 迁入备注",
        "- 原卷只在总表/逐条表中给出上述字段，没有独立长篇档案；不得视为二十节完整档案。",
        "- 表中「兽王」「荒兽」等是原著称谓，不等同本世界威胁等级；本档案不擅自换算。",
        "",
        "## 来源",
        "- `01_最终版/妖兽图鉴/原著兽类图鉴.md` 第三节逐条档案。",
    ]))

# ============ R-B ============
rb_lines = read(os.path.join(BASE, r"妖兽图鉴\跨作品妖兽参考库.md")).splitlines()
rb_blocks = []
for i, ln in enumerate(rb_lines):
    m = re.match(r"^## (R-B-\d{3}) (.+)$", ln)
    if m:
        rb_blocks.append({"id": m.group(1), "name": m.group(2).strip(), "line": i})
for bi, b in enumerate(rb_blocks):
    end = rb_blocks[bi + 1]["line"] if bi + 1 < len(rb_blocks) else next(
        (i for i, ln in enumerate(rb_lines) if ln.startswith("## 档案末尾说明")), len(rb_lines))
    body = "\n".join(rb_lines[b["line"]:end]).strip("\n")
    ref = ""
    for ln in rb_lines[b["line"]:min(end, b["line"] + 6)]:
        if ln.startswith("【参考资料】"):
            ref = ln.strip(); break
    e = {
        "id": b["id"], "name": b["name"], "type": "beast", "origin": "R-B", "origin_label": "跨作品参考物种",
        "partition": "R-B", "is_world_species": False,
        "world_status": "参考物种，非本世界实存；只提取设计理念，不进入世界生态",
        "category": "跨作品参考", "danger_level": None, "size": None, "habitat": None,
        "ability_summary": None, "behavior": None, "carries_gu": False,
        "carried_gu": [], "related_realms": [], "related_regions": [],
        "status": "existing", "completeness": "reference_dossier",
        "content_file": "Beasts/R-B/%s.md" % b["id"],
        "source_files": ["01_最终版/妖兽图鉴/跨作品妖兽参考库.md"],
        "credibility": "【参考资料】", "flags": ["reference_only"]
    }
    beasts[b["id"]] = e
    e["relations"] = []
    write(e["content_file"], "\n".join([
        "# %s %s" % (b["id"], b["name"]),
        "",
        "> R-B 跨作品参考物种｜**非衡垠世界实存物种**，只提取设计理念。迁入自《跨作品妖兽参考库》八节参考档案，原文保留。",
        "",
        "## 基础索引",
        "- 编号：%s" % b["id"],
        "- 名称：%s" % b["name"],
        "- 分类来源：R-B（跨作品参考物种）",
        "- 本世界实存：否（参考素材，不进世界生态、不作本地物种）",
        "- 危险等级：不适用",
        "- 资料来源：%s" % (ref or "见正文第八节"),
        "- 资料完整度：八节参考档案（设计参考，不是本世界物种档案）",
        "- 设定状态：existing（参考区）",
        "",
        "## 参考档案（原文）",
        "",
        body,
        "",
    ]))

# ============ O-B ============
ob_lines = read(os.path.join(BASE, r"妖兽图鉴\原创妖兽图鉴.md")).splitlines()
ob_blocks = []
for i, ln in enumerate(ob_lines):
    m = re.match(r"^## (O-B-\d{3}) 【原创设定】(.+)$", ln)
    if m:
        ob_blocks.append({"id": m.group(1), "name": m.group(2).strip(), "line": i})
ob_end = next((i for i, ln in enumerate(ob_lines) if ln.startswith("## 卷末")), len(ob_lines))
print("OB blocks:", len(ob_blocks))

# 22 号分布索引：O-B -> 主分布/生态区/关联秘境/威胁
dist = {}
for ln in read(os.path.join(BASE, r"现代蛊道世界_v1.0\22_妖兽地理分布索引.md")).splitlines():
    if re.match(r"^\| O-B-\d{3} \|", ln):
        f = [x.strip() for x in ln.split("|")]
        if len(f) >= 10:
            dist[f[1]] = {"name": f[2], "threat": strip_bold(f[3]), "region": f[4],
                          "eco": f[5], "realm": f[6], "carries": f[7], "resource": f[8]}

for bi, b in enumerate(ob_blocks):
    end = ob_blocks[bi + 1]["line"] if bi + 1 < len(ob_blocks) else ob_end
    block_lines = ob_lines[b["line"]:end]
    block = "\n".join(block_lines).strip("\n")
    fields = {}
    for ln in block_lines[:40]:
        m = re.match(r"^\| (编号|名称|别名|生物类别|起源类型|威胁等级|体型|栖息环境|分布区域|智慧程度|群居方式|主要食物|生态定位|资源价值|资料状态) \| (.+?) \|", ln)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    # 分节
    secs = collections.OrderedDict()
    cursec = None
    for ln in block_lines:
        m = re.match(r"^### (.+)$", ln)
        if m:
            cursec = m.group(1).strip(); secs[cursec] = []
        elif cursec:
            secs[cursec].append(ln)
    def sec_text(prefix):
        for k, v in secs.items():
            if k.startswith(prefix):
                return "\n".join(v)
        return ""

    # 携带：只认第八节表格中的编号，不把正文举例引用误当成携带
    carry_lines = sec_text("八、携带蛊虫档案").splitlines()
    gu_ids = []
    carry_rels = []
    carries_flag = False
    for ln in carry_lines:
        if not ln.strip().startswith("|"):
            continue
        cells = [x.strip() for x in ln.split("|")[1:-1]]
        if not cells:
            continue
        # 明细行：首列以编号开头
        if re.match(r"^\*{0,2}[CO]-[GK]-\d{3}", cells[0]):
            ids = re.findall(r"[CO]-[GK]-\d{3}", cells[0])
            relcell = cells[5] if len(cells) >= 8 else ""
        # 总表行：是否携带为首列
        elif re.match(r"^\*{0,2}(是|否)", cells[0]):
            ids = []
            for c in cells[:4]:
                ids += re.findall(r"[CO]-[GK]-\d{3}", c)
            relcell = cells[7] if len(cells) >= 13 else ""
            if cells[0].replace("*", "") == "是":
                carries_flag = True
        else:
            continue
        for gid in ids:
            if gid in gu_ids:
                continue
            gu_ids.append(gid)
            window = relcell + " " + " ".join(cells)
            if gid == "O-G-110":
                rtype, note = "parasitism", "体表寄生（被动）；妖兽不可催动"
            elif "体表寄生" in window:
                rtype, note = "parasitism", "体表寄生；携带不等于可控"
            elif "体内寄生" in window:
                rtype, note = "parasitism", "体内寄生；携带不等于可控"
            elif "共生" in window:
                rtype, note = "symbiosis", "正文标共生；携带不等于可控"
            elif "伴生" in window:
                rtype, note = "commensal", "正文标伴生"
            elif "人工" in window:
                rtype, note = "artificial", "人工附加"
            else:
                rtype, note = "carried_unclear", "正文提及携带，关系类型未明确"
            carry_rels.append({"type": "beast_carries_gu", "target": gid, "relation": rtype,
                               "note": note, "source_section": "八、携带蛊虫档案"})
    if gu_ids:
        carries_flag = True
    elif not carries_flag:
        # 总表「否」或明确契约不携带
        carries_flag = False
    # 秘境
    realms = sorted(set(re.findall(r"REALM-\d{3}", block)))
    d = dist.get(b["id"], {})
    if d.get("realm"):
        for num in re.findall(r"(\d{3})", d["realm"]):
            if "REALM-" + num not in realms and 1 <= int(num) <= 64:
                realms.append("REALM-" + num)
    # 相关妖兽：第十五节
    eco_text = sec_text("十五、生态关系")
    related_beasts = sorted(set(x for x in re.findall(r"O-B-\d{3}", eco_text) if x != b["id"]))
    # 代表组合中的杀招
    combo_text = sec_text("十三、代表性实战组合")
    moves = sorted(set(re.findall(r"[CO]-K-\d{3}", combo_text)))
    e = {
        "id": b["id"], "name": b["name"], "type": "beast", "origin": "O-B", "origin_label": "原创妖兽",
        "partition": "O-B", "is_world_species": True, "world_status": "本世界实存原创物种",
        "category": fields.get("生物类别"), "danger_level": strip_bold(fields.get("威胁等级")),
        "size": fields.get("体型"), "habitat": fields.get("栖息环境"),
        "ability_summary": trunc(fields.get("生态定位")), "behavior": trunc(fields.get("群居方式")),
        "carries_gu": carries_flag, "carried_gu": gu_ids, "related_realms": realms,
        "related_regions": [d.get("region")] if d.get("region") else [],
        "status": "existing", "completeness": "complete_structured",
        "content_file": "Beasts/O-B/%s.md" % b["id"],
        "source_files": ["01_最终版/妖兽图鉴/原创妖兽图鉴.md",
                         "01_最终版/现代蛊道世界_v1.0/22_妖兽地理分布索引.md"],
        "credibility": "【原创设定】", "flags": ["original_setting", "twenty_sections", "no_control_rules"]
    }
    e["relations"] = carry_rels
    for rid in realms:
        e["relations"].append({"type": "beast_habitat_realm", "target": rid, "note": "正文／22 号索引登记", "source_section": "十七、现代社会与秘境分布"})
    for oid in related_beasts:
        e["relations"].append({"type": "beast_ecological_link", "target": oid, "note": "生态关系跨组引用", "source_section": "十五、生态关系"})
    for mid in moves:
        e["relations"].append({"type": "beast_vs_killer_move", "target": mid, "note": "代表性实战组合／评估", "source_section": "十三、代表性实战组合"})
    beasts[b["id"]] = e

    lines = [
        "# %s %s" % (b["id"], b["name"]),
        "",
        "> 【原创设定】本世界实存原创妖兽｜迁入自《原创妖兽图鉴 v1.1》二十节完整档案，原文保留。",
        "> **O-B 硬规则**：不具备空窍、真元、蛊师修炼体系、主动炼蛊能力，不能像蛊师一样主动催动蛊虫；携带蛊虫 ≠ 控制蛊虫。",
        "",
        "## 基础索引",
        "- 编号：%s" % b["id"],
        "- 名称：%s" % b["name"],
        "- 分类来源：O-B（原创妖兽，本世界实存）",
        "- 生物类别：%s" % (fields.get("生物类别", "未知")),
        "- 威胁等级：%s" % (fields.get("威胁等级", "未知")),
        "- 体型：%s" % (fields.get("体型", "未知")),
        "- 栖息环境：%s" % (fields.get("栖息环境", "未知")),
        "- 分布区域：%s" % (fields.get("分布区域", "未知")),
        "- 携带蛊虫：%s" % ("是（" + "、".join(gu_ids) + "）" if gu_ids else "否（按档案总表）"),
        "- 关联秘境：%s" % ("、".join(realms) if realms else "未登记"),
        "- 资料完整度：二十节完整档案",
        "- 设定状态：existing（原创区）",
        "",
        "## 原始档案（二十节）",
        "",
        block,
        "",
    ]
    write(e["content_file"], "\n".join(lines))

write("Indexes/_beast_part.json", json.dumps({"beasts": beasts, "dist": dist}, ensure_ascii=False, indent=1))
print("C-B:", len([x for x in beasts.values() if x["origin"] == "C-B"]),
      "R-B:", len([x for x in beasts.values() if x["origin"] == "R-B"]),
      "O-B:", len([x for x in beasts.values() if x["origin"] == "O-B"]))
