# 知识库总入口

本目录是《衡垠世界》的正式数据层，分成两个同级子库：

```text
知识库/
├── World/          世界层：总索引、地理、地方志、组织、秘境、规则、来源、地图
└── 衡垠知识库/     档案层：蛊虫、妖兽、杀招、索引、关系、审计
```

## 读取顺序

1. 先读根目录 `README.md` 和 `AI_START_HERE.md`。
2. 查世界、城市、秘境：`World/world-index.json` → `World/entities/` → `World/gazetteers/`。
3. 查蛊虫、妖兽、杀招：`衡垠知识库/Indexes/` → `content_file` 指向的 Markdown。
4. 查关系：`World/relationships.json` 与 `衡垠知识库/Indexes/relationship-index.json`。

## 边界

- 网站已移除；本目录只含静态 Markdown、JSON、SVG。
- `World/` 与 `衡垠知识库/` 是两份互补数据：前者是世界实体与地方志，后者是逐实体档案与编号索引。
- 未写入索引的候选档案、研究稿不算正式实体；研究草稿放在根目录 `05_研究草稿/`。
- 原始资料与归档仍在根目录 `01_最终版/`、`02_`、`03_`、`04_`，不并入本目录。
