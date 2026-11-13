# World · 衡垠世界数据层

本目录保存《衡垠世界》的世界层资料：总索引、地理与行政区、组织、秘境、地方志、规则、来源、报告和静态地图。它不再是网站数据目录，供 AI 与人类直接读取。

## 数据规模

| 内容 | 数量 |
|---|---:|
| 全实体总索引 | 1,483 条 |
| 蛊虫与杀招 | 1,177 条（717 蛊虫 + 460 杀招） |
| 妖兽 | 89 条 |
| 地理与行政区 | 151 条 |
| 组织 | 2 条 |
| 秘境 | 64 条 |
| 世界关系 | 220 条 |
| 地方志 | 6 份 |
| 地图 | 2 份 SVG |

## 文件

- `world-index.json`：总索引，含 `id`、名称、类型、父级、状态、完整度、`content_file`、`record_file`。
- `relationships.json`：世界层关系边，含 `from`、`to`、`type`、`kind`、`status`、`source`。
- `entities/geography.json`：地理、行政区、城市、地点。
- `entities/organizations.json`：组织。
- `entities/realms.json`：秘境。
- `entities/gu.json`：蛊虫与杀招的结构化索引（`type=gu` / `type=kill_move`）。
- `entities/beasts.json`：妖兽索引。
- `entities/beasts_relations.json`：妖兽生态关系的详细机制。
- `gazetteers/`：世界、城市、城区、街道、社区、秘境的地方志正文。
- `rules/`：编号、状态、蛊道、秘境、妖兽携蛊、跑团规则。
- `sources/`：来源总表、版本状态、统计口径、未编号实体清单。
- `reports/`：编号冲突、资料缺失与待确认报告。
- `maps/`：从旧网站抽取并保留的两张 SVG 空间示意图，已去除网页交互层，仅保留几何与文字标注。

## 关系与路径

- `content_file` 与 `record_file` 均为相对于本目录的路径；O-B 正文指向 `../衡垠知识库迁入/Beasts/O-B/`。
- `world-index.json` 的 `record_file` 指向本目录下的 `entities/*.json`。
- 关系边的 `from` / `to` 必须存在于 `world-index.json`。
- 网站页面路由字段 `route` / `entity_route` 已删除；不要再用旧 `#/...` 地址。

## 不包含

- 网站 HTML、CSS、JavaScript、页面路由、构建脚本、部署配置。
- 网站预览截图和重复的网页渲染数据。
- `.workbuddy/` 内部工作数据。
