# AI_START_HERE · 衡垠世界知识库阅读入口

> 本文件是 AI 进入仓库的第一份说明。仓库是纯静态知识库；没有网站、没有 JSON API、没有后端。

## 1. 先读顺序

1. `README.md`：仓库定位、数据分层、目录和下载方式。
2. 本文件：读取顺序、状态口径、禁区。
3. `知识库/README.md`：知识库两层总入口。
4. `知识库/World/DATA_SCHEMA.md`：世界层 JSON 的字段定义。
5. `知识库/衡垠知识库/README.md`：蛊虫、妖兽、杀招档案层的结构和统计口径。

## 2. 两层数据，不要混用

| 层 | 入口 | 适合回答 |
|---|---|---|
| 世界层 | `知识库/World/world-index.json` | 世界、地理、城市、行政区、地点、组织、秘境、全实体索引 |
| 档案层 | `知识库/衡垠知识库/Indexes/gu-index.json`、`beast-index.json`、`move-index.json` | 蛊虫、妖兽、杀招的逐实体档案与正式编号 |
| 关系层 | `知识库/World/relationships.json`、`知识库/衡垠知识库/Indexes/relationship-index.json` | 地理层级与实体关联；先看关系类型，再判断语义 |

`知识库/World/entities/gu.json` 同时包含 `type=gu` 的 717 条蛊虫和 `type=kill_move` 的 460 条杀招；不要仅凭文件名把所有记录都当蛊虫。

## 3. 读取步骤

### 查世界、城市、秘境

1. 在 `知识库/World/world-index.json` 用 `id` 或 `name` 找到实体。
2. 读 `record_file` 指向的 `知识库/World/entities/*.json` 取得结构化字段。
3. 需要正文时读 `content_file`；地方志在 `知识库/World/gazetteers/`，秘境补充在 `知识库/World/entities/realms.json`。
4. 需要关系时在 `知识库/World/relationships.json` 按 `from` / `to` 过滤。

### 查蛊虫、妖兽、杀招

1. 在对应 `*-index.json` 用 `id` 定位。
2. 读 `content_file` 指向的独立 Markdown 档案；路径相对于 `知识库/衡垠知识库/`。
3. 需要关系时读 `relationship-index.json`，不要从正文提及自行推断“拥有/携带/组成”。
4. 需要来源与审计时读 `Audit/IMPORT_REPORT.md`、`Audit/CONFLICTS.md`、`Audit/DUPLICATES.md`、`Audit/INCOMPLETE.md`。

## 4. 回答时必须遵守

- **状态**：`existing` 才是既有设定；`proposed` 是新增拟定；`uncertain` 必须说明未确认；`revised` 要看修订记录。
- **完整度**：`full` 才是完整档案；`summary` 是摘要；`index` 只有索引；`missing` 未建档。不得把索引扩写成完整设定。
- **分区**：C-G/C-K 是《蛊真人》原著；O-G/O-K/O-B 是本世界原创；C-B 是原著兽类参照；R-B 是跨作品参考物种，**不是衡垠世界实存物种**。
- **O-B 规则**：O-B 妖兽不具备空窍、真元、蛊师修炼体系、主动炼蛊能力，不能像蛊师一样主动催动蛊虫；携带、寄生、共生、被动触发必须分开表述。
- **唯一性**：O-G-110 界隙蛊是 O-B-012 阈鹿携带的唯一野生仙蛊；不得重复生成、不得改挂给其他妖兽。
- **不补造**：原文未载的能力、消耗、炼化条件保留“未知/待考证”，不要补写。
- **不调和冲突**：遇到互相矛盾的记载，并列说明并指向 `Audit/CONFLICTS.md`，不要自行选一个。
- **候选档案**：`知识库/衡垠知识库/Gu/O-G/`、`Related/Killer_Moves/` 中未被索引登记的新候选，不是正式实体。

## 5. 快速定位表

| 用户问 | 先读 |
|---|---|
| 某个蛊虫是什么 | `知识库/衡垠知识库/Indexes/gu-index.json` → `content_file` |
| 某只妖兽的完整档案 | `知识库/衡垠知识库/Indexes/beast-index.json` → `content_file` |
| 某个杀招用了哪些蛊虫 | `知识库/衡垠知识库/Indexes/move-index.json` 的 `components`，再查关系索引 |
| 某座城市在哪里 | `知识库/World/world-index.json` → `知识库/World/entities/geography.json` / `知识库/World/gazetteers/` |
| 某个秘境的资料 | `知识库/World/entities/realms.json`；详细正文见 `知识库/World/gazetteers/REALM-*.md` |
| 某个实体与谁有关 | 对应关系 JSON，按 `id` 过滤，并读关系类型 |
| 尚未合并的黑暗蛊道研究 | `05_研究草稿/Dark_Gu_Research/README.md` |

## 6. 研究草稿与参考资料

- `05_研究草稿/` 是未合并的专题研究和候选方案，不是正式设定。
- `06_参考资料/` 是外部写作参考，不参与世界设定。
- 正式实体只以 `知识库/` 下的索引与档案为准。

## 7. 下载

在 GitHub 页面点击 **Code → Download ZIP**，或执行：

```bash
git clone https://github.com/koishi520786/hengyin-world.git
```

如需让 AI 读取，优先把整个仓库或 ZIP 交给它；不要提供 `localhost` 或旧网站地址，因为本项目已经没有网站服务。
