> 镜像副本：正式文件是 `data/DATA_SCHEMA.md`，本文件由 `tools/build_kb.py` 自动生成，请勿在此修改。
> 给 AI 用的完整资料包是「衡垠AI资料包.zip」。

# DATA_SCHEMA · 衡垠世界知识库数据结构说明

> 生成时间：2026-11-13 20:22:03 +0800 ｜ 版本：2.0.0 ｜ 权威文件：`data/entities/*.json`

## 1. 文件分工（一份数据，两个方向）

```
data/
├─ world-index.json      ← 由 entities/*.json 生成的总索引（网页搜索/浏览用）
├─ relationships.json    ← 带类型的关联边
├─ manifest.json         ← 版本、文件清单、统计、校验结果
├─ entities/
│  ├─ geography.json     ← 地理、行政区、地点
│  ├─ gu.json            ← 蛊虫与杀招
│  ├─ beasts.json        ← 妖兽、原著兽类、参考物种
│  ├─ realms.json        ← 秘境
│  ├─ organizations.json ← 组织
│  ├─ beasts_render.json ← 第一版网页渲染用的原始妖兽数据结构（只读投影源）
│  ├─ beasts_relations.json
│  └─ beasts/O-B-*.md    ← 十二种原创妖兽二十节完整档案
├─ gazetteers/*.md       ← 地方志与页面正文（从第一版网页转写，文字未改写）
├─ rules/*.md            ← 世界规则与机制（导航式说明）
├─ sources/*.md          ← 来源、版本、统计口径、未编号实体清单
├─ reports/*.md          ← 冲突、缺失、待确认、路由校验报告
├─ AI_START_HERE.md
├─ AI_INTEGRATION_GUIDE.md
└─ README.md
```

**唯一正式数据源是 `data/entities/*.json` 与各 `.md` 文档。** `world-index.json`、`relationships.json`、`manifest.json`、网页里的 `#kb-data` 数据岛、以及 `衡垠AI资料包.zip`，全部由 `tools/build_kb.py` 投影生成，不允许手工另建一份。

## 2. 实体记录字段

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | string | **唯一编号**，全库不得重复；不同页面不得为同一实体另建编号 |
| `name` | string | 名称 |
| `type` | string | 英文类型键（city / district / street / place / realm / gu / kill_move / beast / organization …） |
| `type_label` | string | 中文类型名 |
| `category` | string | 大类：geography / gu / beast / realm / organization |
| `parent_id` | string 或 null | **父级关系**（行政／地理层级），与普通关联严格分开 |
| `parent_name` | string 或 null | 父级名称（便于阅读，不用于计算） |
| `status` | enum | `existing` / `proposed` / `uncertain` / `revised` |
| `coverage` | enum | `full` / `summary` / `index` / `missing` |
| `summary` | string | 简要介绍（索引级记录只写已确认字段） |
| `content_file` | string 或 null | 该实体完整正文的相对路径（相对资料包根） |
| `route` | string 或 null | 网站专题页 hash 路由（可空） |
| `entity_route` | string | 统一实体档案页 `#/entity/<id>`，每个实体都有有效页面 |
| `tags` | string[] | 检索标签 |
| `relations` | string[] | 关系 ID 列表或 `rule_ref:<文件>` 规则引用 |
| `source` | object[] | `{doc, version, section, note}`，尽量保留文件编号与章节 |
| `version` | string | 记录版本 |
| `attributes` | object | **按类型扩展**：城市有面积／人口／等级；秘境有 S/D/R/ST/DS；蛊虫有转数／流派；妖兽有威胁等级／栖息环境……不强制所有实体同构 |
| `note` | string 或 null | 冲突、口径、纪律说明 |

## 3. 状态枚举（AI 不得把拟定当事实）

| 值 | 含义 |
|---|---|
| `existing` | 原设定已有，来自 `01_最终版/` 原始资料，不得改写 |
| `proposed` | 新增拟定，含【原创设定】与网站补拟编号；**不是既定事实** |
| `uncertain` | 尚未确认，资料不足或存在互斥记载 |
| `revised` | 经过正式修订并留版本记录 |

## 4. 完整度枚举

| 值 | 含义 |
|---|---|
| `full` | 知识库内有完整档案正文 |
| `summary` | 有原文摘录或结构化概要 |
| `index` | 只有编号、名称与索引字段 |
| `missing` | 仅在总目录提及，尚未建档 |

## 5. 关联关系

`relationships.json` 每条边：

| 字段 | 含义 |
|---|---|
| `id` | `REL-00001` 起，唯一 |
| `from` / `to` | 必须是 `world-index.json` 中存在的 `id` |
| `type` | 关系类型，见文件的 `kinds` 字典（如 `part_of`、`located_in`、`habitat`、`predation`、`carries_gu`、`has_entrance`、`headquarters_in`） |
| `kind` | `hierarchy`（父级，由 `parent_id` 生成）或 `association`（普通关联），**两者分开** |
| `status` / `note` / `source` | 状态、说明、依据 |

一个实体可关联任意多个其他实体；蛊虫、妖兽、组织不强行塞进地理 `parent_id` 层级，它们通过 `association` 边连接。

## 6. 编号体系（沿用原设定，不重排）

`CONT` 大陆｜`OCEAN` 海洋｜`NAT` 国家｜`ADM` 一级行政区｜`CITY` 城市｜`DIST` 城区｜`LOC` 地点｜`REALM` 秘境｜`C-G` 原著蛊虫｜`C-K` 原著杀招｜`O-G` 原创蛊虫｜`O-K` 原创杀招｜`C-B` 原著兽类｜`R-B` 跨作品参考物种｜`O-B` 本世界原创妖兽｜`ORG` 组织。

`PLANET-000` 与 `NODE-101-001` 是**占位编号**，不是原编号体系里的正式前缀，见 `reports/待确认清单.md`。

## 7. 构建与同步

```
python tools/build_kb.py            # 重新从原始资料抽取 + 生成 + 注入网页
python tools/build_kb.py --sync     # 只依据现有 data/ 重新生成索引、ZIP 与网页数据岛
python tools/serve.py              # 本地 HTTP 服务（可选）
```

网页直接双击打开也能用：构建脚本把数据以数据岛内嵌进 HTML，`file://` 下无需 fetch。启动 HTTP 服务时，浏览器可直接浏览 `data/` 下的 JSON 与 Markdown。

---
字段有新增时，请同步修改本文件，并重新生成资料包。
