# DATA_SCHEMA · 衡垠世界知识库数据结构

> 本文件描述 `World/` 下的静态数据结构。知识库不含网站、后端、数据库或 HTTP 查询接口。

## 1. 文件分工

```text
World/
├── world-index.json          总索引：1,483 条实体
├── relationships.json        220 条带类型的关系边
├── entities/
│   ├── geography.json        151 条地理、行政区、城市、地点
│   ├── organizations.json    2 条组织
│   ├── realms.json           64 条秘境
│   ├── gu.json               717 条蛊虫 + 460 条杀招
│   ├── beasts.json           89 条妖兽
│   └── beasts_relations.json 36 条妖兽生态关系机制
├── gazetteers/*.md           地方志正文
├── rules/*.md                规则说明
├── sources/*.md              来源、版本、统计口径
├── reports/*.md              冲突、缺失、待确认报告
├── maps/*.svg                静态空间示意图
└── DATA_SCHEMA.md            本文件
```

`world-index.json` 是总索引；`entities/*.json` 是分类记录；两者通过 `record_file` 关联。详细实体 Markdown 仍以 `衡垠知识库迁入/` 为准。

## 2. 实体字段

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | string | 唯一编号，全库不重复 |
| `name` | string | 名称 |
| `type` | string | 类型键：`admin_region` / `city` / `district` / `street` / `place` / `realm` / `gu` / `kill_move` / `beast` / `organization` 等 |
| `type_label` | string | 中文类型名 |
| `category` | string | 大类：`geography` / `gu` / `beast` / `realm` / `organization` |
| `parent_id` | string 或 null | 行政／地理父级；普通关联不写入此字段 |
| `parent_name` | string 或 null | 父级名称，仅供阅读 |
| `status` | enum | `existing` / `proposed` / `uncertain` / `revised` |
| `coverage` | enum | `full` / `summary` / `index` / `missing` |
| `summary` | string | 索引级简介 |
| `content_file` | string 或 null | 详细正文路径，相对于 `World/` |
| `record_file` | string 或 null | 结构化分类记录路径，相对于 `World/` |
| `tags` | string[] | 检索标签 |
| `relations` | string[] | 关系 ID，对应 `relationships.json.edges[].id` |
| `source` | object[] | 来源：`doc`、`version`、`section`、`note` |
| `version` | string | 记录版本 |
| `attributes` | object | 按类型扩展的字段（面积、人口、S/D/R/ST/DS、转数、流派、威胁等级等） |
| `note` | string 或 null | 冲突、口径或限制说明 |

网站专用的 `route` / `entity_route` 字段已移除。

## 3. 状态与完整度

### status

| 值 | 含义 |
|---|---|
| `existing` | 原设定已有，来自 `01_最终版/` 或既有资料 |
| `proposed` | 新增拟定／原创设定，不是既定事实 |
| `uncertain` | 资料不足或存在互斥记载，尚未确认 |
| `revised` | 经过正式修订并留有版本记录 |

### coverage

| 值 | 含义 |
|---|---|
| `full` | 有完整实体档案正文 |
| `summary` | 有原文摘录或结构化概要 |
| `index` | 只有编号、名称与索引字段 |
| `missing` | 仅在目录提及，尚未建档 |

## 4. 关系边

`relationships.json` 的 `edges` 每项包含：

| 字段 | 含义 |
|---|---|
| `id` | 关系 ID，`REL-00001` 起 |
| `from` / `to` | 必须是 `world-index.json` 中存在的实体 `id` |
| `type` | 关系类型，如 `part_of`、`located_in`、`habitat`、`predation`、`carries_gu`、`has_entrance`、`headquarters_in` |
| `kind` | `hierarchy`（父级）或 `association`（普通关联） |
| `status` | 关系状态 |
| `note` | 关系说明 |
| `source` | 依据文件或字段 |

关系类型只在语义允许时使用：`carries_gu` 表示携带，不等于控制或催动；`part_of` 表示层级归属，不等于生态关联。

## 5. 编号前缀

`CONT` 大陆｜`OCEAN` 海洋｜`NAT` 国家｜`ADM` 一级行政区｜`CITY` 城市｜`DIST` 城区｜`LOC` 地点｜`REALM` 秘境｜`C-G` 原著蛊虫｜`C-K` 原著杀招｜`O-G` 原创蛊虫｜`O-K` 原创杀招｜`C-B` 原著兽类｜`R-B` 跨作品参考物种｜`O-B` 本世界原创妖兽｜`ORG` 组织。

编号沿用原设定，不重排、不复用；新增只能顺延追加。

## 6. 路径规则

- `content_file` / `record_file` 相对于 `World/`。
- O-B 的 `content_file` 指向 `../衡垠知识库迁入/Beasts/O-B/O-B-*.md`。
- 地方志正文在 `gazetteers/`。
- 不再有 `localhost`、`#/` 路由或网站页面路径。
