# AI_INTEGRATION_GUIDE · 如何接入衡垠世界知识库

> 本仓库是纯静态知识库。**没有网站、没有 HTTP API、没有数据库、没有后端服务。** AI 通过读取 Markdown、TXT、JSON、SVG 文件获取资料。

## 1. 推荐接入方式

### 方式 A：直接读取 GitHub 仓库

1. 打开 `https://github.com/koishi520786/hengyin-world`。
2. 先读根目录 `AI_START_HERE.md`，再按其中顺序读取。
3. 对支持 GitHub 连接器的 AI，可直接让它读取仓库；对只支持网页读取的 AI，使用 GitHub 文件页面或下载 ZIP。

### 方式 B：下载 ZIP

1. 在仓库页点击 **Code → Download ZIP**。
2. 解压后把 `AI_START_HERE.md` 作为第一份输入。
3. 按 `AI_START_HERE.md` 的读取顺序加载文件。

### 方式 C：Git 克隆

```bash
git clone https://github.com/koishi520786/hengyin-world.git
```

## 2. 读取顺序

```text
README.md
→ AI_START_HERE.md
→ 知识库/README.md
→ 知识库/World/DATA_SCHEMA.md
→ 知识库/World/world-index.json
→ 知识库/World/entities/*.json
→ 知识库/World/relationships.json
→ 知识库/World/gazetteers/*.md
→ 知识库/衡垠知识库/README.md
→ 知识库/衡垠知识库/Indexes/gu-index.json / beast-index.json / move-index.json / relationship-index.json
→ 对应 content_file 的 Markdown
→ Audit/ 与 World/reports/
```

不要一次性读取全部 1,200 多份 Markdown。先用索引定位 `id`，再按需读取正文；长文可按章节分段。

## 3. 文件职责

| 路径 | 用途 |
|---|---|
| `知识库/World/world-index.json` | 世界层总索引，1,483 条实体 |
| `知识库/World/entities/geography.json` | 地理、行政区、城市、地点 |
| `知识库/World/entities/organizations.json` | 组织 |
| `知识库/World/entities/realms.json` | 秘境 |
| `知识库/World/entities/gu.json` | 717 条蛊虫 + 460 条杀招的结构化索引 |
| `知识库/World/entities/beasts.json` | 89 条妖兽索引 |
| `知识库/World/entities/beasts_relations.json` | 妖兽生态关系的详细机制 |
| `知识库/World/relationships.json` | 世界层 220 条关系边 |
| `知识库/World/gazetteers/*.md` | 世界、城市、城区、街道、社区、秘境的地方志正文 |
| `知识库/World/rules/*.md` | 编号、状态、蛊道、秘境、妖兽携蛊、跑团规则 |
| `知识库/World/sources/*.md` | 来源、版本、统计口径、未编号实体 |
| `知识库/World/reports/*.md` | 冲突、缺失、待确认报告 |
| `知识库/衡垠知识库/Indexes/*.json` | 蛊虫、妖兽、杀招、关系、来源、扩展、秘境索引 |
| `知识库/衡垠知识库/Gu/`、`Beasts/`、`Related/` | 逐实体 Markdown 档案 |
| `知识库/衡垠知识库/Audit/` | 导入、覆盖、重复、冲突、不完整、核验报告 |
| `05_研究草稿/` | 未合并的专题研究与候选方案 |
| `06_参考资料/` | 与正式设定无关的外部写作参考 |

## 4. 给 AI 的字段约定

- `id`：唯一主键；跨文件引用一律用编号。
- `status`：`existing` / `proposed` / `uncertain` / `revised`。
- `coverage`：`full` / `summary` / `index` / `missing`。
- `content_file`：详细正文路径；`知识库/World/` 中的相对路径以该目录为基准，`知识库/衡垠知识库/` 中的路径以该目录为基准。
- `record_file`：结构化记录文件路径。
- 关系边的 `from` / `to` 必须指向已存在的实体 ID；关系类型必须按实际语义使用。
- 网站专属字段 `route` / `entity_route` 已移除；不要再依赖页面路由。

## 5. 更新流程

1. 只修改原始资料或对应实体档案，不直接批量改写索引。
2. 需要重建档案索引时，运行 `知识库/衡垠知识库/Tools/` 下的脚本；先读 `Tools/README.md`。
3. 世界层 JSON 改动后，跑一遍引用完整性检查：`content_file` / `record_file` 是否存在，`relationships` 的端点是否存在。
4. 把变更写入 `知识库/World/sources/01_版本与状态.md` 或对应审计报告。
5. 提交到 Git；不要在公开仓库中放入 `.workbuddy/`、本地缓存或密钥。

## 6. 边界

- 本仓库不提供在线查询、不托管网页、不运行 JavaScript。
- R-B 只是参考物种，不是衡垠世界实存生物。
- O-B 妖兽不能修炼蛊道、不能主动催蛊；携带蛊虫不等于控制。
- 未确认的能力、消耗、炼化条件保留“未知/待考证”，不得用推测补全。
- 未登记进索引的新候选档案一律视为草稿，不视为正式实体。
