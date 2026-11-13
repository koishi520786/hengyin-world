# -*- coding: utf-8 -*-
"""补充非实体注记与疑似同物异号的标记；只改迁入库自己的档案，不动原始资料。"""
import io, os, json, collections, re

OUT = r"D:\study\跑团\知识库\衡垠知识库"
GU = json.loads(io.open(os.path.join(OUT, r"Indexes\_gu_part.json"), encoding="utf-8").read())
entries = GU["gu"]

notes = {
 "C-G-028": "- 疑似与 C-G-556 为同一实体（同名、同条能力原文）；保留两份编号与档案，未合并，待人工核查。",
 "C-G-556": "- 疑似与 C-G-028 为同一实体（同名、同条能力原文）；保留两份编号与档案，未合并，待人工核查。",
 "C-G-462": "- 该标题为版本说明/结构重排注记，不是蛊虫名，正文也不是蛊虫能力；保留原编号，标为非实体注记，不计入有效蛊虫数。",
 "C-G-643": "- 该标题为附录标签，不是蛊虫名；保留原编号，标为非实体附录，不计入有效蛊虫数。",
 "C-G-503": "- 该标题为多名称合条（玄冰蛊、冰墙蛊、华玉蛊、缓更蛊、生机蛊）；其中「生机蛊」另见 C-G-509，疑似同物异号，保留两处，未合并。",
 "C-G-509": "- 该条「生机蛊」与 C-G-503 多名称合条中的「生机蛊」疑似同物异号；保留两处编号与档案，未合并。",
 "C-G-513": "- 该条「电脑蛊」与 C-G-514 多名称合条中的「电脑蛊」疑似同物异号；保留两处编号与档案，未合并。",
 "C-G-514": "- 该标题为多名称合条（电脑蛊、智脑蛊、光脑蛊）；其中「电脑蛊」另见 C-G-513，疑似同物异号，保留两处，未合并。",
 "C-G-389": "- 该条「思绪如电蛊」与 C-G-404 多名称合条中的「思绪如电蛊」同名但能力记载不同，疑似同物异号/同条重述；保留两处编号与档案，未合并。",
 "C-G-404": "- 该标题为多名称合条（才思蛊、彗心蛊、玲珑蛊、思绪如电蛊）；其中「思绪如电蛊」另见 C-G-389，能力记载不同，疑似同物异号/同条重述；保留两处，未合并。",
}
flags = {
 "C-G-462": "non_entity_note",
 "C-G-643": "appendix_non_entity",
}
for gid, flag in flags.items():
    entries[gid].setdefault("flags", [])
    if flag not in entries[gid]["flags"]:
        entries[gid]["flags"].append(flag)

# 非实体条目不保留从残句/说明文字误推的蛊类与转数
nonentity_meta = {
 "C-G-274": ("malformed_heading_non_entity", "未知（规则残句，非蛊名）", "非实体（疑误立条目）"),
 "C-G-462": ("non_entity_note", "未知（版本说明，非蛊名）", "非实体注记"),
 "C-G-643": ("appendix_non_entity", "未知（附录标签，非蛊名）", "非实体附录"),
}
for gid, (flag, rank_raw, klass) in nonentity_meta.items():
    e = entries[gid]
    e["rank"] = None
    e["rank_raw"] = rank_raw
    e["class"] = klass
    e["rank_basis"] = "不适用（非实体）"
    e["ability_summary"] = "不适用（非实体条目）"

# 按别名建立疑似同物组
alias = collections.defaultdict(set)
for gid, e in entries.items():
    if e["origin"] != "C-G": continue
    for v in set((e.get("name_variants") or []) + [e.get("name_primary") or e["name"]]):
        if v: alias[v].add(gid)
groups = {}
for v, ids in alias.items():
    if len(ids) > 1:
        groups.setdefault(tuple(sorted(ids)), []).append(v)
for ids, names in groups.items():
    for gid in ids:
        entries[gid].setdefault("flags", [])
        if "suspected_duplicate" not in entries[gid]["flags"]:
            entries[gid]["flags"].append("suspected_duplicate")
        entries[gid]["duplicate_group"] = list(ids)
    print("duplicate group", ids, names)

for gid, note in notes.items():
    p = os.path.join(OUT, ("Gu/C-G/%s.md" % gid))
    s = io.open(p, encoding="utf-8").read()
    if note in s:
        continue
    s = s.rstrip("\n") + "\n" + note + "\n"
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("noted", gid)

# 同步非实体档案的基础索引行
for gid, (flag, rank_raw, klass) in nonentity_meta.items():
    p = os.path.join(OUT, ("Gu/C-G/%s.md" % gid))
    s = io.open(p, encoding="utf-8").read()
    s = re.sub(r"^- 转数：.*$", "- 转数：%s" % rank_raw, s, count=1, flags=re.MULTILINE)
    s = re.sub(r"^- 蛊类：.*$", "- 蛊类：%s" % klass, s, count=1, flags=re.MULTILINE)
    s = s.replace("- 来源类别：C-G（原著蛊虫）", "- 来源类别：C-G（原著条目，非实体）", 1)
    s = re.sub(r"^- 主要能力：.*$", "- 主要能力：不适用（非实体条目）", s, count=1, flags=re.MULTILINE)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)

with io.open(os.path.join(OUT, r"Indexes\_gu_part.json"), "w", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps(GU, ensure_ascii=False, indent=1))
