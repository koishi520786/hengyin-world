# 网站移除与知识库化报告

- 日期：2026-11-13
- 仓库：`https://github.com/koishi520786/hengyin-world`
- 分支：`main`
- 清理基线：`7421bced226654156a3af081154ffb5e168bd9b4`
- 提交信息：`chore: remove website and keep knowledge base`
- 原则：删除网站，保留世界；不修改正式设定内容，不覆盖其他 Agent 的提交，不使用强制推送。

## 一、结果

独立网站已从工作区移除。网站中仍有资料价值的世界数据先迁入 `World/`，再删除原网站目录；旧网站文件可从 Git 历史恢复，但不再属于当前知识库结构。

## 二、删除内容

删除整个 `hengyin-world-atlas/`，包括：

- 网站页面：`衡垠世界图集.html`、`衡垠世界图集_备份_接入妖兽前_20261113.html`、`index.html`。
- 启动与构建：`启动网站.bat`、`重新生成资料.bat`、`tools/build_kb.py`、`tools/patch_site.py`、`tools/serve.py`。
- 网站预览与资料包：`预览_生灵图鉴页.png`、`预览_阈鹿档案页.png`、`衡垠AI资料包.zip`。
- 网站专属说明：`使用说明.md`、`本次修改记录.md`、`数据结构说明.md`，以及 `data/README.md`、`data/AI_START_HERE.md`、`data/AI_INTEGRATION_GUIDE.md`。
- 网站专属数据：`data/manifest.json`、`data/entities/beasts_render.json`、`data/reports/链接与路由校验报告.md`。
- 网站首页与建设状态：`data/gazetteers/00_首页.md`、`data/gazetteers/BUILD_建设状态.md`、`data/gazetteers/GU_蛊道索引.md`。
- 网站内重复的 O-B 档案副本：`data/entities/beasts/O-B-001.md` 至 `O-B-012.md`（正文已保留在 `衡垠知识库迁入/Beasts/O-B/`）。
- 网站 IA 交接文档：`衡垠知识库迁入/Stage2/WEB_IA_HANDOFF.md`。
- 空目录 `衡垠世界_世界地图集/`。

Git 初始提交中 `hengyin-world-atlas/` 共 67 个跟踪文件；其中 31 个世界数据文件已先复制到 `World/` 并保留，原网站路径随目录删除。删除的预览图是网站 UI 截图，不是原始地图。

## 三、保留与迁入

### 世界层 `World/`（32 个文件）

- `world-index.json`：1,483 条实体，ID 唯一。
- `relationships.json`：220 条关系，端点全部有效。
- `entities/geography.json`：151 条。
- `entities/organizations.json`：2 条。
- `entities/realms.json`：64 条。
- `entities/gu.json`：1,177 条（717 蛊虫 + 460 杀招）。
- `entities/beasts.json`：89 条。
- `entities/beasts_relations.json`：36 条带机制的生态关系（保留，因为包含网站关系索引没有的细节）。
- `gazetteers/`：6 份地方志正文。
- `rules/`：6 份规则。
- `sources/`：5 份来源与口径。
- `reports/`：3 份既有报告（编号冲突、待确认、资料缺失与完整度）。
- `maps/`：2 份从旧网页抽取的 SVG 地图，已补 `xmlns`、去除网页交互层：
  - `云栖花园_空间示意.svg`
  - `云栖生活圈_示意.svg`
- `README.md`、`DATA_SCHEMA.md`：世界层说明与字段规范。

### 档案层 `衡垠知识库迁入/`

- 蛊虫 717 份：C-G 684、O-G 33。
- 妖兽 89 份：C-B 37、R-B 40、O-B 12。
- 杀招 460 份：C-K 447、O-K 13。
- 实体档案合计 1,266 份。
- 关系索引 912 条。
- 原始归档 `01_最终版/`、`02_归档_历史版本/`、`03_归档_原始底稿与备份/`、`04_归档_拼装中间稿/` 全部保留。

### 灰色文件处理

- `World/entities/gu.json`、`beasts.json` 被 `world-index.json` 的 `record_file` 引用，保留。
- `World/entities/beasts_relations.json` 保留，作为妖兽生态机制补充。
- `World/reports/` 与 `World/sources/` 中的历史 `#/entity` 文字属于旧审计证据，不是活跃路由字段；未改写原文。
- 用途不明且无法判断的文件：无。

## 四、文档更新

- 根 `README.md`：重写为纯知识库入口，明确网站已移除。
- 根 `AI_START_HERE.md`：新增 AI 读取顺序、状态口径和禁区。
- 根 `AI_INTEGRATION_GUIDE.md`：新增静态知识库接入、更新流程和边界。
- `World/README.md`、`World/DATA_SCHEMA.md`：改为世界层静态数据说明，删除网站路由字段说明。
- `00_工作区总导航.md`：加入 `World/` 与 `衡垠知识库迁入/`，记录网站已移除。
- `衡垠知识库迁入/README.md`：删除网页 IA 引用，修正 `Audit/IMPORT_REPORT.md` 路径。
- `Stage2/CLASSIFICATION_PLAN.md`：网站数据包改为 AI 数据包，保留分类建议。
- `Tools/build_indexes.py`、`Tools/scan_sources.py`：移除旧网站路径引用。

## 五、校验结果

### 世界层

- 实体：1,483 条，ID 唯一，重复 0。
- 关系：220 条，失效端点 0。
- `content_file` / `record_file` 缺失路径：0。
- `World` 下残留 `route` / `entity_route` 字段：0。
- `World` 文件：32 个（8 JSON、22 Markdown、2 SVG）。

### 档案层

- `gu-index.json`：717 条，C-G 684、O-G 33；全部有 `content_file`，缺失 0。
- `beast-index.json`：89 条，C-B 37、R-B 40、O-B 12；全部有 `content_file`，缺失 0。
- `move-index.json`：460 条，C-K 447、O-K 13；全部有 `content_file`，缺失 0。
- 实体文件：C-G 684、O-G 33、C-B 37、R-B 40、O-B 12、Killer_Moves 460，合计 1,266。
- 关系索引：912 条；其中 20 条是指向 `REALM-*` 的跨层关系，目标全部存在于 `World/world-index.json` 的 64 条秘境中；其余端点均在 gu/beast/move 索引内。
- `relationship-index.json` 的 `unresolved_relations`：0。

### 目录

- `hengyin-world-atlas/`：已不存在。
- `衡垠世界_世界地图集/`：已不存在。
- `Stage2/WEB_IA_HANDOFF.md`：已不存在。
- 根 `README.md`、`AI_START_HERE.md`、`AI_INTEGRATION_GUIDE.md`：存在。

## 六、未完成与待确认

- 本轮是网站清理与数据结构校验，不是全量质量审计；C-G 的 3 条非实体注记、4 组疑似同物异号、O-G-110 登记状态等既有问题未在本轮修改。
- `World/reports/`、`World/sources/` 中少数历史审计文字仍提到旧 `#/entity` 路由；保留为历史证据，当前 JSON 已无该字段。
- 网站删除不涉及正式设定内容；如未来需要恢复网站文件，从 Git 历史中的 `7421bce` 提交取回。
