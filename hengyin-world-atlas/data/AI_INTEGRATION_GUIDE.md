# AI_INTEGRATION_GUIDE · 未来 AI 接入指南（本阶段只做兼容设计）

> 生成时间：2026-11-13 20:22:03 +0800 ｜ 版本：2.0.0

## 0. 先说清楚：现在没有什么

- 本网站**没有**部署到公网，**没有**后端，**没有**数据库，**没有**付费 API。
- 云端 AI（ChatGPT、DeepSeek、Claude 等）**无法自动读取**用户电脑上的本地网站，也无法读取 `localhost`。
- 本项目**没有**实现 HTTP 查询接口；下面第六节只是未来可扩展的设计，不是已经可用的功能。
- 本阶段交付的是「标准化、可导出的静态资料包」，不是「AI 自动联网」。

三种能力必须分开讲：

| 能力 | 说明 | 状态 |
|---|---|---|
| A. 本地网站浏览 | 人双击 `衡垠世界图集.html` 或运行 `启动网站.bat` 后用浏览器看 | ✅ 已实现 |
| B. 资料包导出供 AI 读取 | 网站「一键导出」生成 ZIP，用户手动上传给 AI | ✅ 已实现 |
| C. AI 实时查询接口 | 云端／本地 AI 通过 HTTP 按编号、关键词、地域、关系查询 | ❌ 未实现，仅预留设计 |

## 1. 现在就能用的 AI 工作流

1. 打开网站 → 「资料导出」页 → 点「一键导出 AI 资料包」。
2. 得到 `衡垠AI资料包.zip`（项目目录里也有一份由构建脚本生成的同名文件）。
3. 把 ZIP 上传给支持文件读取的 AI，或解压后把 `AI_START_HERE.md` 设为第一份投喂文件。
4. AI 按 `world-index.json` → `entities/` → `relationships.json` → `gazetteers/` 逐级读取。
5. 资料更新后，重新导出一份 ZIP 即可；不需要改 AI 那边的配置。

## 2. 为什么这样设计

- 零成本：纯 HTML/CSS/JS/JSON/Markdown/ZIP，Python 只用于本地构建脚本，不购买服务器或 API。
- 可离线：所有数据以数据岛内嵌在 HTML 中，`file://` 直接打开也能搜索、浏览、导出。
- 单一数据源：`data/entities/*.json` 是正式来源；网页数据岛与 ZIP 都由 `tools/build_kb.py` 投影生成，不存在两套手工维护的数据。

## 3. 数据层已预留的查询维度

`world-index.json` 每条记录都带：`id`、`type`、`type_label`、`category`、`parent_id`、`status`、`coverage`、`tags`、`route`、`content_file`、`record_file`。
`relationships.json` 每条边都带：`from`、`to`、`type`、`kind`、`status`、`note`、`source`。

因此以下查询在**纯静态 JSON 上**已经可以离线完成（只是目前由网页 JS 在浏览器里做，不通过 HTTP）：

- 按实体编号查：直接以 `id` 索引。
- 按关键词查：对 `name`／`id`／`tags`／`summary` 做包含匹配。
- 按地理区域过滤：沿 `parent_id` 向上追溯，或用 `relationships.json` 的 `part_of` 边求子树。
- 按实体关系查：过滤 `from` 或 `to`，按 `type` 区分关系类型。
- 按分类批量读：`entities/<category>.json` 已经按类型分文件。
- 给跑团 AI 提供资料：按 `category` + `status` + `coverage` 过滤后打包。

## 4. 未来接口设计（尚未实现，不要当真）

如将来需要 C 类能力，最小改动是在 `tools/serve.py` 上增加只读路由，数据仍来自同一份 `data/`：

| 建议路径 | 作用 | 返回 |
|---|---|---|
| `GET /api/entity?id=CITY-101` | 按编号查 | 单条完整实体记录 |
| `GET /api/search?q=云栖` | 关键词搜索 | 命中的索引项数组 |
| `GET /api/geo?region=DIST-101-03` | 按地理区域过滤 | 该节点子树内的实体 |
| `GET /api/relations?id=O-B-012` | 按关系查询 | 相关的边数组 |
| `GET /api/type?type=realm` | 按分类批量读 | 该分类实体数组 |
| `GET /api/tr?topic=开窍` | 跑团资料打包 | 规则 + 相关实体 + 状态说明 |
| `GET /api/manifest` | 版本与统计 | `manifest.json` 内容 |

约束：只读、无鉴权（仅本机 `127.0.0.1`）、不写库、不引入框架、不加付费依赖；所有响应带 `version` 与 `generated_at`，并保留 `status`／`coverage` 字段，避免 AI 把拟定内容当事实。

若要让**云端** AI 访问，则必须额外做公网部署与授权，这会产生托管成本，超出本项目"零付费依赖"的范围，本阶段不做，也不建议用户现在做。

## 5. 安全与口径提醒

- 不要把 `localhost` 地址贴给云端 AI，指望它能抓取；它抓不到。
- 接口若将来实现，也应返回 `status`／`coverage`，并在 `AI_START_HERE.md` 中同步说明。
- 任何新增字段都要写进 `DATA_SCHEMA.md`，并重新运行 `python tools/build_kb.py --sync` 生成新的 ZIP 与网页数据岛。

---
本文件只做兼容性设计与说明，不代表当前已具备 HTTP 查询能力。
