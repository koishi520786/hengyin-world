# 衡垠世界 AI 资料包 · README

> 生成时间：2026-11-13 20:22:03 +0800 ｜ 版本：2.0.0

这是给 AI 读取的静态资料包，**不是网站程序**。

- 人类看的网站：项目根目录的 `衡垠世界图集.html`（双击即可）或 `启动网站.bat`。
- AI 看的第一份文件：`AI_START_HERE.md`。
- 导入入口：`world-index.json`；关联：`relationships.json`；规则：`rules/`；地方志：`gazetteers/`；来源：`sources/`；缺口与冲突：`reports/`。

**纪律**：`status=proposed` 不是既定事实；`coverage=index` 不是完整档案；R-B 不是本世界物种；冲突并列保留、不调和、不编造。

本包与网页共用 `data/entities/*.json` 这一份数据源，由 `tools/build_kb.py` 生成。
