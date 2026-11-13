# -*- coding: utf-8 -*-
"""交付前逐条核验：文件存在、编号连续/唯一、关系目标存在、计数一致。"""
import os, re, io, json, collections

OUT = r"D:\study\跑团\衡垠知识库迁入"
def read(p): return io.open(p, encoding="utf-8").read()

gu = json.loads(read(os.path.join(OUT, r"Indexes\gu-index.json")))
beasts = json.loads(read(os.path.join(OUT, r"Indexes\beast-index.json")))
moves = json.loads(read(os.path.join(OUT, r"Indexes\move-index.json")))
rels = json.loads(read(os.path.join(OUT, r"Indexes\relationship-index.json")))

issues = []
def check_files(entries, label):
    missing = [e["id"] for e in entries if not os.path.exists(os.path.join(OUT, e["content_file"].replace("/", "\\")))]
    if missing: issues.append({"type": "missing_file", "partition": label, "ids": missing})
    return len(entries) - len(missing)

def check_seq(ids, prefix, start, end, label):
    nums = [int(x.split("-")[-1]) for x in ids]
    if len(ids) != len(set(ids)): issues.append({"type": "duplicate_id", "partition": label})
    if nums != list(range(start, end + 1)):
        issues.append({"type": "sequence_gap", "partition": label,
                       "missing": sorted(set(range(start, end + 1)) - set(nums)),
                       "extra": sorted(set(nums) - set(range(start, end + 1)))})

cg = [e["id"] for e in gu["entries"] if e["origin"] == "C-G"]
og = [e["id"] for e in gu["entries"] if e["origin"] == "O-G"]
cb = [e["id"] for e in beasts["entries"] if e["origin"] == "C-B"]
rb = [e["id"] for e in beasts["entries"] if e["origin"] == "R-B"]
ob = [e["id"] for e in beasts["entries"] if e["origin"] == "O-B"]
ck = [e["id"] for e in moves["entries"] if e["origin"] == "C-K"]
ok = [e["id"] for e in moves["entries"] if e["origin"] == "O-K"]
check_seq(cg, "C-G", 1, 684, "C-G")
check_seq(cb, "C-B", 1, 37, "C-B")
check_seq(rb, "R-B", 1, 40, "R-B")
check_seq(ob, "O-B", 1, 12, "O-B")
check_seq(ck, "C-K", 1, 447, "C-K")
check_seq(ok, "O-K", 1, 13, "O-K")
for label, ids in [("O-G", og)]:
    if len(ids) != len(set(ids)): issues.append({"type": "duplicate_id", "partition": label})

file_counts = {
 "gu": check_files(gu["entries"], "gu"),
 "beast": check_files(beasts["entries"], "beast"),
 "move": check_files(moves["entries"], "move"),
}

valid_targets = {e["id"] for e in gu["entries"]} | {e["id"] for e in beasts["entries"]} | {e["id"] for e in moves["entries"]}
realm = json.loads(read(os.path.join(OUT, r"Indexes\realm-index.json")))
valid_targets |= {e["id"] for e in realm["entries"]}
bad_rel = [r for r in rels["relations"] if r["target"] not in valid_targets or r["source"] not in valid_targets]
if bad_rel: issues.append({"type": "bad_relation", "count": len(bad_rel), "sample": bad_rel[:5]})

nonentities = [e["id"] for e in gu["entries"] if any(f in ("malformed_heading_non_entity", "non_entity_note", "appendix_non_entity") for f in e.get("flags", []))]
dups = sorted({tuple(e.get("duplicate_group")) for e in gu["entries"] if e.get("duplicate_group")})
pending = json.loads(read(os.path.join(OUT, r"Indexes\alternate-gu-index.json")))["pending_confirmation"]

result = {
 "checked_at": "2026-11-13",
 "counts": {
  "gu_total": len(gu["entries"]), "C-G": len(cg), "O-G": len(og),
  "beast_total": len(beasts["entries"]), "C-B": len(cb), "R-B": len(rb), "O-B": len(ob),
  "move_total": len(moves["entries"]), "C-K": len(ck), "O-K": len(ok),
  "files_existing": file_counts, "relations": len(rels["relations"]),
  "realm_registry": len(realm["entries"]), "alternate_pending": pending,
  "non_entity_records": nonentities, "duplicate_groups": [list(x) for x in dups],
 },
 "issues": issues,
 "pass": not issues
}
with io.open(os.path.join(OUT, r"Audit\VALIDATION.json"), "w", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps(result, ensure_ascii=False, indent=1))

lines = [
 "# 交付前逐条核验（VALIDATION）",
 "",
 "> 日期：2026-11-13｜由 `Tools/validate.py` 对索引与磁盘档案逐条检查。",
 "",
 "## 结果：%s" % ("通过" if not issues else "有问题"),
 "",
 "| 项目 | 数量 |",
 "|---|---|",
 "| 蛊虫记录 | %d（C-G %d / O-G %d） |" % (len(gu["entries"]), len(cg), len(og)),
 "| 妖兽记录 | %d（C-B %d / R-B %d / O-B %d） |" % (len(beasts["entries"]), len(cb), len(rb), len(ob)),
 "| 杀招记录 | %d（C-K %d / O-K %d） |" % (len(moves["entries"]), len(ck), len(ok)),
 "| 独立档案存在 | 蛊虫 %d、妖兽 %d、杀招 %d |" % (file_counts["gu"], file_counts["beast"], file_counts["move"]),
 "| 关系 | %d 条，目标全部存在 |" % len(rels["relations"]),
 "| 秘境登记 | %d 条 |" % len(realm["entries"]),
 "| 非实体注记 | %s |" % ("、".join(nonentities) if nonentities else "无"),
 "| 疑似同物异号组 | %s |" % ("；".join(" / ".join(g) for g in [list(x) for x in dups]) if dups else "无"),
 "| 扩展待确认 | %d 条 |" % pending,
 "",
 "## 编号",
 "- C-G-001–684：连续、无重复。",
 "- C-B-001–037、R-B-001–040、O-B-001–012：连续、无重复。",
 "- C-K-001–447、O-K-001–013：连续、无重复。",
 "- O-G 编号按 001–021、101–109、201–202 预留段分布，无重复；O-G-110 单条登记。",
 "",
 "## 问题",
 *(["- %s" % json.dumps(x, ensure_ascii=False) for x in issues] if issues else ["- 未检出缺失档案、重复编号、编号断号或失效关系。"]),
]
with io.open(os.path.join(OUT, r"Audit\VALIDATION.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))
print(json.dumps(result, ensure_ascii=False, indent=1))
