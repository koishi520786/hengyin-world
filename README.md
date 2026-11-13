# 衡垠世界 · 官方知识库

《衡垠世界》是一个现代都市蛊道跑团世界设定项目。本仓库是整个项目的正式知识库，以 Markdown、TXT、JSON 和 SVG 保存世界设定、实体档案、索引、关系、来源与审计记录，供人类阅读和 AI 检索。

> **网站已正式移除。** 本项目不再提供独立网站、HTML 页面、前端路由、构建脚本或部署配置。仓库只保留可持续维护的知识库数据。

## 两层数据

### 1. `World/` — 世界层

面向地理、城市、地方志、组织、秘境和全实体总索引：

| 内容 | 数量 / 文件 |
|---|---|
| 全实体总索引 | 1,483 条，`World/world-index.json` |
| 蛊虫与杀招 | 1,177 条（717 蛊虫 + 460 杀招），`World/entities/gu.json` |
| 妖兽 | 89 条，`World/entities/beasts.json` |
| 地理与行政区 | 151 条，`World/entities/geography.json` |
| 组织 | 2 条，`World/entities/organizations.json` |
| 秘境 | 64 条，`World/entities/realms.json` |
| 世界关系 | 220 条，`World/relationships.json` |
| 地方志 | 6 份，`World/gazetteers/` |
| 规则、来源、报告 | `World/rules/`、`World/sources/`、`World/reports/` |
| 地图 | 2 份 SVG，`World/maps/` |

### 2. `衡垠知识库迁入/` — 档案层

面向逐实体 Markdown 档案与正式编号索引：

| 内容 | 数量 |
|---|---:|
| 蛊虫档案 | 717（C-G 684 + O-G 33） |
| 妖兽档案 | 89（C-B 37 + R-B 40 + O-B 12） |
| 杀招档案 | 460（C-K 447 + O-K 13） |
| 实体档案合计 | 1,266 份 |
| 关系 | 912 条，0 条失效目标 |

C-G 的 684 条记录中含 3 条非实体注记（C-G-274、C-G-462、C-G-643），有效候选 681 条；另有 4 组疑似同物异号，保留原编号、未合并。R-B 是跨作品参考物种，不代表衡垠世界实存妖兽。

## 目录

```text
hengyin-world/
├── README.md
├── AI_START_HERE.md
├── AI_INTEGRATION_GUIDE.md
├── 00_工作区总导航.md
├── World/                 世界层：总索引、地理、地方志、组织、秘境、规则、来源、地图
├── 衡垠知识库迁入/        档案层：蛊虫、妖兽、杀招、索引、关系、审计
├── 01_最终版/             当前生效的原始资料
├── 02_归档_历史版本/      只读历史版本
├── 03_归档_原始底稿与备份/ 只读原始底稿
├── 04_归档_拼装中间稿/    只读拼装稿
└── .workbuddy/            本地内部工作数据，不进入 Git 仓库
```

## 快速开始

- 先读 `AI_START_HERE.md`，再按其中的读取顺序进入 `World/` 或 `衡垠知识库迁入/`。
- 查蛊虫：`衡垠知识库迁入/Indexes/gu-index.json`。
- 查妖兽：`衡垠知识库迁入/Indexes/beast-index.json`。
- 查杀招：`衡垠知识库迁入/Indexes/move-index.json`。
- 查实体关系：`衡垠知识库迁入/Indexes/relationship-index.json`。
- 查世界、城市、秘境：`World/world-index.json`、`World/entities/`、`World/gazetteers/`。
- 查来源与审计：`衡垠知识库迁入/Audit/`、`World/sources/`、`World/reports/`。

## 下载与克隆

- 在 GitHub 仓库页点击 **Code → Download ZIP** 获取完整知识库。
- 或执行：

```bash
git clone https://github.com/koishi520786/hengyin-world.git
```

## 给 AI 的读取原则

1. **先索引，后正文**：先用 `id` 定位，再读 `content_file` 指向的 Markdown。
2. **状态优先**：`status=existing` 才是既有设定；`proposed` 是新增拟定；`uncertain` 必须说明未确认。
3. **完整度优先**：`coverage=full` 才是完整档案；`summary` 是概要；`index` 只有索引。
4. **分区不可混**：C-G/C-K 是原著；O-G/O-K/O-B 是原创；C-B 是原著兽类；R-B 是参考物种，不是本世界实存物种。
5. **携带 ≠ 控制**：妖兽携带蛊虫不等于能控制、催动或组成杀招；O-B 妖兽不具备空窍、真元、蛊师修炼或主动炼蛊能力。
6. **编号是主键**：引用实体一律使用 `id`，不要用名称替代主键。
7. **未知保留未知**：没有可靠资料的能力、消耗、炼化条件不补写，不把待考证写成确定。

## 版权与边界

本项目包含《蛊真人》相关设定摘录、同人整理与跑团资料。原著及相关素材版权归原作者所有；本仓库公开用于个人跑团、设定研究与资料索引，不构成对原著的授权再分发。如权利人认为有不适合公开的内容，可提出移除。

原创设定、整理文本与数据结构权利归项目作者。仓库不包含 `.workbuddy/` 内部工作数据。
