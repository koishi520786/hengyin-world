# Tools · 复跑顺序

所有脚本只读 `D:\study\跑团` 原始资料，写入 `D:\study\跑团\衡垠知识库迁入`。

```text
1. scan_sources.py          扫描 79 个文本文件 -> Audit/SOURCE_SCAN.json
2. compare_names.py         C-G / 扩展 / 759 名称重叠 -> Audit/NAME_OVERLAP.json
3. match_ext.py             264 条扩展名录匹配 -> Audit/EXT_MATCH.json
4. build_core.py            C-G 684 + O-G 33 档案 -> Gu/**；_gu_part.json
5. build_beasts.py          C-B 37 + R-B 40 + O-B 12 档案 -> Beasts/**；_beast_part.json
6. build_moves.py           C-K 447 + O-K 13 档案 -> Related/Killer_Moves/**；_move_part.json
7. build_alternate.py       45 条未匹配扩展临时档案；759 底稿映射
8. mark_quality.py          非实体注记、疑似同物异号标记（只补本库档案）
9. build_indexes.py         统一索引 + 关系 + 来源 + 审计 + README + Stage2
10. validate.py             逐条核验 -> Audit/VALIDATION.json / VALIDATION.md
```

## 注意

- `build_core.py` 会重写 `Gu/C-G/**` 与 `Gu/O-G/**`；重跑后必须依次重跑 `build_alternate.py`、`mark_quality.py`、`build_indexes.py`，否则扩展键与质量标记会丢失。
- `build_alternate.py` 会读取并回写 `_gu_part.json` 的 `alternate_keys`；已做去重。
- 所有文件写入使用 `io.open(..., encoding="utf-8", newline="\n")`。
- 原始资料路径一律只读；脚本不会写入 `01_最终版`、`02_归档_历史版本`、`03_归档_原始底稿与备份` 或网站目录。
