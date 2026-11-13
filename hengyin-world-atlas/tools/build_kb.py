# -*- coding: utf-8 -*-
"""
衡垠世界图集 · 统一知识库构建器（零依赖，Python 标准库）

用途
----
把「原始设定资料」与「第一版网页内容」抽取到 data/ 这一份正式数据源，
再由 data/ 生成：
  * data/world-index.json      实体总索引（网页搜索/浏览用）
  * data/relationships.json   带类型的关联关系
  * data/reports/*.md         编号冲突、资料缺失、路由校验等报告
  * 衡垠AI资料包.zip           供用户上传给 AI 的完整资料包
  * 网页内的数据岛（#kb-data / #ai-pack-b64 / #beasts-json）

用法
----
  python tools/build_kb.py            # 全量：重新抽取 + 生成 + 注入
  python tools/build_kb.py --sync     # 只依据现有 data/ 重新生成索引、包与网页数据岛

原则
----
  * data/entities/*.json 是实体资料的唯一正式来源；网页数据岛只是它的「投影」。
  * 原设定编号一字不改；新增拟定一律 status=proposed 并注明出处。
  * 只有索引的资料一律 coverage=index，不冒充完整档案。
"""
import sys, os, re, json, base64, zipfile, hashlib, html, io
from pathlib import Path
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
WS = ROOT.parent
SRC_WORLD = WS / "01_最终版" / "现代蛊道世界_v1.0"
SRC_GU = WS / "01_最终版" / "蛊道资料库_v3.0"
SRC_BEAST = WS / "01_最终版" / "妖兽图鉴"
DATA = ROOT / "data"
ENT = DATA / "entities"
HTML_FILE = ROOT / "衡垠世界图集.html"
PACK = ROOT / "衡垠AI资料包.zip"
NOW = datetime.now(timezone(timedelta(hours=8)))
STAMP = NOW.strftime("%Y-%m-%d %H:%M:%S %z")
VERSION = "2.0.0"

for d in (DATA, ENT, DATA / "gazetteers", DATA / "rules", DATA / "sources", DATA / "reports"):
    d.mkdir(parents=True, exist_ok=True)


def read(p):
    return Path(p).read_text(encoding="utf-8")


def write(p, s):
    Path(p).write_text(s, encoding="utf-8", newline="\n")


def jwrite(p, obj):
    write(p, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False) + "\n")


def write_if_missing(p, s):
    if not Path(p).exists():
        write(p, s)


def clean(s):
    s = re.sub(r"\*\*|`|〔[^〕]*〕", "", s or "")
    return html.unescape(s).strip()


def rows_of(path, id_pattern, start=0, end=None):
    """抽取 markdown 表格中以指定编号开头的行，返回单元格列表"""
    lines = read(path).splitlines()
    out = []
    for ln in lines[start:end]:
        if not ln.strip().startswith("|"):
            continue
        cells = [clean(c) for c in ln.strip().strip("|").split("|")]
        if cells and re.fullmatch(id_pattern, cells[0]):
            out.append(cells)
    return out


def E(id, name, type_, type_label, category, **kw):
    rec = {
        "id": id,
        "name": name,
        "type": type_,
        "type_label": type_label,
        "category": category,
        "parent_id": None,
        "parent_name": None,
        "status": "existing",
        "coverage": "index",
        "summary": "",
        "content_file": None,
        "route": None,
        "tags": [],
        "relations": [],
        "source": [],
        "version": "1.0",
        "attributes": {},
        "note": None,
    }
    rec.update(kw)
    return rec


def src(doc, section="", note="", version="v1.0"):
    return {"doc": doc, "version": version, "section": section, "note": note}


# ----------------------------------------------------------------------------
# 一、从原始资料抽取实体
# ----------------------------------------------------------------------------
def parse_planet_continent_ocean():
    out = []
    out.append(E("PLANET-000", "衡垠星", "planet", "行星", "geography",
                 summary="本世界所在行星；六大陆、六片海洋或内海，垠历 738 年，全球人口 81.2 亿。",
                 status="proposed", coverage="summary",
                 note="行星本身在原编号体系中无编号；PLANET-000 是为建立地理根节点而设的占位 ID，非正式编号。",
                 source=[src("00_世界观总目录.md", "第三节", "编号体系未为行星分配前缀"),
                         src("01_世界基础设定.md", "第一节")]))
    p = SRC_WORLD / "02_全球地理与大陆总览.md"
    for c in rows_of(p, r"CONT-\d{3}"):
        out.append(E(c[0], c[1], "continent", "大陆", "geography",
                     parent_id="PLANET-000", parent_name="衡垠星", coverage="summary",
                     summary=f"{c[1]}；面积 {c[2]} 万 km²；人口 {c[5]} 亿；国家数 {c[6]}；登记秘境 {c[7]} 处。",
                     attributes={"面积_万km2": c[2], "纬度": c[3], "经度": c[4], "人口_亿": c[5], "国家数": c[6], "登记秘境": c[7]},
                     source=[src("02_全球地理与大陆总览.md", "第一节 六大陆")]))
    for c in rows_of(p, r"OCEAN-\d{3}"):
        nm = c[1].replace("（内海，附属于赫兰大陆）", "")
        out.append(E(c[0], nm, "ocean", "海洋/内海", "geography",
                     parent_id="PLANET-000", parent_name="衡垠星", coverage="summary",
                     summary=f"{nm}；面积 {c[2]} 万 km²；{c[3]}。{c[4]}",
                     attributes={"面积_万km2": c[2], "位置": c[3], "特征": c[4], "用途": c[5] if len(c) > 5 else ""},
                     source=[src("02_全球地理与大陆总览.md", "第二节 海洋与内海")]))
    return out


def parse_nat():
    out, cont_map = [], {}
    p = SRC_WORLD / "04_全球国家总览.md"
    cur_cont = None
    for ln in read(p).splitlines():
        m = re.match(r"^### 2\.\d+ (.+?)（\d+）", ln.strip())
        if m:
            cur_cont = clean(m.group(1))
    # 重新按小节扫描（保留所属大陆）
    cur_cont = None
    for ln in read(p).splitlines():
        m = re.match(r"^### 2\.\d+ (.+?)（\d+）", ln.strip())
        if m:
            cur_cont = clean(m.group(1))
        if ln.strip().startswith("|") and "NAT-" in ln:
            c = [clean(x) for x in ln.strip().strip("|").split("|")]
            if re.fullmatch(r"NAT-\d{3}", c[0]):
                cont_map[c[0]] = cur_cont
    cont_by_name = {e["name"]: e["id"] for e in parse_planet_continent_ocean() if e["type"] == "continent"}
    for c in rows_of(p, r"NAT-\d{3}"):
        cont = cont_map.get(c[0])
        pid = cont_by_name.get(cont)
        out.append(E(c[0], c[1], "country", "国家/政治实体", "geography",
                     parent_id=pid, parent_name=cont, coverage="summary",
                     summary=f"{c[1]}；{c[2]}；首都 {c[3]}；面积 {c[4]} 万 km²；人口 {c[5]} 亿；等级 {c[7]}；主要产业 {c[8]}。",
                     attributes={"政体": c[2], "首都": c[3], "面积_万km2": c[4], "人口_亿": c[5],
                                 "GDP_万亿": c[6], "等级": c[7], "主要产业": c[8], "秘境数": c[9] if len(c) > 9 else "",
                                 "所属大陆": cont},
                     source=[src("04_全球国家总览.md", "第二节 分洲国家总览")]))
    # 首都城市编号（03 号）
    capitals = {c[0]: c[3] for c in rows_of(SRC_WORLD / "03_世界地图与坐标索引.md", r"NAT-\d{3}")}
    for e in out:
        if e["id"] in capitals:
            e["attributes"]["首都城市编号"] = capitals[e["id"]]
    return out


def parse_city(nats):
    out = []
    by_name = {n["name"]: n["id"] for n in nats}
    for c in rows_of(SRC_WORLD / "07_全球城市总索引.md", r"CITY-\d{3}"):
        country, grade, pop = c[2], c[6], c[5]
        pid = by_name.get(country)
        rec = E(c[0], c[1], "city", "城市", "geography",
                parent_id=pid, parent_name=country if pid else None,
                coverage="summary",
                summary=f"{c[1]}（{country}）；坐标 {c[3]}；垠格 {c[4]}；人口 {pop} 万；等级 {grade}。{c[7]}",
                attributes={"国家": country, "坐标": c[3], "垠格": c[4], "人口_万": pop, "等级": grade, "定位与产业": c[7]},
                source=[src("07_全球城市总索引.md", "第二节 城市总表", "07 声明 60 座，实际登记 59 行，缺 CITY-039，见 C-01")])
        out.append(rec)
    # 临江市挂到澜东州（09 号）
    for e in out:
        if e["id"] == "CITY-101":
            e["parent_id"] = "ADM-105"
            e["parent_name"] = "澜东州"
            e["coverage"] = "full"
            e["content_file"] = "gazetteers/CITY-101.md"
            e["route"] = "#/linjiang"
            e["attributes"].update({"面积_km2": 8240, "建成区_km2": 1186, "人口_万": 1180, "城区人口_万": 1064,
                                    "等级": "MET-2", "登记蛊师_万": 28.4, "蛊师密度": "2.4%"})
            e["source"].append(src("09_临江市城市档案.md", "第一节 基本资料 / 第四节 行政区划"))
    return out


def parse_admin():
    out = [E("ADM-105", "澜东州", "admin_region", "一级行政区", "geography",
             parent_id="NAT-005", parent_name="曜川联邦", coverage="index",
             summary="曜川联邦九州之一，临江市为其第二大市。",
             source=[src("06_曜川联邦国家档案.md", "第二节")])]
    return out


def parse_dist_street():
    out = []
    for c in rows_of(SRC_WORLD / "09_临江市城市档案.md", r"DIST-101-\d{2}"):
        e = E(c[0], c[1], "district", "城区", "geography",
              parent_id="CITY-101", parent_name="临江市", coverage="summary",
              summary=f"{c[1]}；面积 {c[2]} km²；人口 {c[3]} 万；{c[5]}；{c[6]}",
              attributes={"面积_km2": c[2], "人口_万": c[3], "区位": c[4], "功能": c[5], "空间特征": c[6]},
              source=[src("09_临江市城市档案.md", "§4.1 七城区")])
        if c[0] == "DIST-101-03":
            e["coverage"] = "full"
            e["content_file"] = "gazetteers/DIST-101-03.md"
            e["route"] = "#/beicheng"
        out.append(e)
    # 六街道（§4.2，编号 0301—0306）
    lines = read(SRC_WORLD / "09_临江市城市档案.md").splitlines()
    for ln in lines:
        if ln.strip().startswith("|") and re.search(r"\| LOC-101-030[1-6] \|", ln):
            c = [clean(x) for x in ln.strip().strip("|").split("|")]
            e = E(c[0], c[1], "street", "街道", "geography",
                  parent_id="DIST-101-03", parent_name="北城区", coverage="summary",
                  summary=f"{c[1]}；面积 {c[2]} km²；人口 {c[3]} 万；{c[4]}",
                  attributes={"面积_km2": c[2], "人口_万": c[3], "空间与生活": c[4]},
                  source=[src("09_临江市城市档案.md", "§4.2 北城区六街道")])
            if c[0] == "LOC-101-0301":
                e["coverage"] = "full"
                e["content_file"] = "gazetteers/LOC-101-0301.md"
                e["route"] = "#/yunqi"
                e["note"] = "原 09 号 §13 地点表把 0301 也用于「云栖街道办事处」，构成 C-04 冲突；本站保留街道编号为 0301，街道办事处改挂 0360（拟定）。"
            out.append(e)
    return out


LOC_TYPE = {"云栖花园": "住宅小区", "第二小学": "学校", "社区医院": "医疗", "大桥": "桥梁",
            "人行桥": "桥梁", "菜市场": "市场", "办事处": "政务", "枢纽": "交通",
            "公园": "公园", "中学": "学校", "港": "港口", "码头": "码头", "机场": "机场",
            "会展": "会展", "车站": "交通", "站": "交通", "广场": "公共空间", "仓": "仓储",
            "大学": "学校", "政府": "政务"}


def loc_type(name):
    for k, v in LOC_TYPE.items():
        if k in name:
            return v
    return "地点"


def parse_loc():
    """09 号 §13 LOC 表 23 行；与 §4.2 街道表重复的三个编号按 C-04 处理"""
    out = []
    lines = read(SRC_WORLD / "09_临江市城市档案.md").splitlines()
    seg = "\n".join(lines[271:306])
    seen = set()
    conflict = {"LOC-101-0301": ("云栖街道办事处", "LOC-101-0360"),
                "LOC-101-0302": ("云栖菜市场", "LOC-101-0361"),
                "LOC-101-0305": ("云栖河人行桥", "LOC-101-0362")}
    for ln in seg.splitlines():
        if not ln.strip().startswith("|"):
            continue
        c = [clean(x) for x in ln.strip().strip("|").split("|")]
        if not c or not re.fullmatch(r"LOC-101-\d{4}", c[0]):
            continue
        rid, name, where, coord, kind, hours = c[0], c[1], c[2], c[3], c[4], c[5]
        parent = None
        if "云栖街道" in where:
            parent = "LOC-101-0301"
        elif "北苑街道" in where:
            parent = "LOC-101-0302"
        elif "双桥街道" in where:
            parent = "LOC-101-0303"
        elif "江堤街道" in where:
            parent = "LOC-101-0304"
        elif "老站街道" in where:
            parent = "LOC-101-0305"
        elif "屏岭街道" in where:
            parent = "LOC-101-0306"
        elif "中城区" in where:
            parent = "DIST-101-01"
        elif "西陵区" in where:
            parent = "DIST-101-05"
        elif "南岸区" in where:
            parent = "DIST-101-02"
        elif "江东区" in where:
            parent = "DIST-101-04"
        elif "临港区" in where:
            parent = "DIST-101-06"
        elif "澜湾区" in where:
            parent = "DIST-101-07"
        elif "北城区" in where:
            parent = "DIST-101-03"
        elif "跨江" in where:
            parent = "CITY-101"
        if rid in conflict:
            # 该编号已归街道表；把 §13 里被挤掉的实体以 C-04 拟定编号登记
            alias, newid = conflict[rid]
            out.append(E(newid, alias, "place", loc_type(alias), "geography",
                         status="proposed", coverage="summary",
                         parent_id="LOC-101-0301", parent_name="云栖街道",
                         summary=f"{alias}；{where}；{coord}；{kind}；{hours}。",
                         attributes={"坐标": coord, "类别": kind, "开放": hours, "来源编号": rid},
                         note="C-04：09 号 §13 原用 " + rid + "，与 §4.2 街道表重复；本站按 C-04 改挂拟定编号，待用户确认。不是正式编号。",
                         source=[src("09_临江市城市档案.md", "§13 地图索引（LOC 表）", "C-04 冲突重挂")]))
            continue
        if rid in seen:
            continue
        seen.add(rid)
        e = E(rid, name, "place", loc_type(name), "geography",
              parent_id=parent, parent_name=where, coverage="index",
              summary=f"{name}；{where}；{coord}；{kind}；{hours}。",
              attributes={"坐标": coord, "类别": kind, "开放": hours, "原表位置": where},
              source=[src("09_临江市城市档案.md", "§13 地图索引（LOC 表）")])
        out.append(e)
    # 网页补充信息与专题路由
    extras = {
        "LOC-101-0312": dict(content_file="gazetteers/LOC-101-0312.md", coverage="full", route="#/garden",
                             summary="云栖花园，云栖路 118 号，2003 年建成，7 栋六层砖混、312 户、无电梯；3 号楼 602 为本次探索起点。",
                             attributes={"地址": "云栖路118号", "建成": 2003, "楼栋": 7, "户数": 312, "月租_曜元": 1850, "租户占比": "46%"}),
        "LOC-101-0318": dict(summary="临江市北城区第二小学，育才路 26 号，1987 年建校，42 个班、1,980 名学生。",
                             coverage="summary", route="#/garden"),
        "LOC-101-0340": dict(summary="蛊坊街，北城区·江堤街道，蛊虫零售与维修；父级是江堤街道 LOC-101-0304，不是云栖街道。",
                             coverage="summary", route="#/beicheng"),
        "LOC-101-0330": dict(summary="北城社区医院，8:00—20:00，常见病、儿童保健与开窍初检。", coverage="summary"),
        "LOC-101-0012": dict(summary="旧渠闸，REALM-012 临江地下层的入口，中城区江堤路 9 号，24 小时值守。", coverage="summary"),
    }
    for rid, kv in extras.items():
        for e in out:
            if e["id"] == rid:
                e.update(kv)
    # 网页上出现但 09 号 §13 没有编号的 POI：公交站
    out.append(E("NODE-101-001", "“云栖花园”公交站", "bus_stop", "交通节点", "geography",
                 status="proposed", coverage="summary",
                 parent_id="LOC-101-0301", parent_name="云栖街道",
                 summary="云栖路西侧，3 条线路停靠；早高峰 6:50—7:40 每 6—9 分钟一班。",
                 note="NODE 前缀在原编号体系中未定义；此编号来自第一版地图 POI，属拟定占位，待分配正式 LOC 编号。",
                 source=[src("衡垠世界图集.html", "云栖生活圈 SVG POI", "第一版已有")]))
    return out


def parse_realm():
    out = []
    p = SRC_WORLD / "10_全球秘境总目录.md"
    for c in rows_of(p, r"REALM-\d{3}"):
        # 2.1 表：编号 名称 国家/地区 坐标 类型 S D R ST DS 一句话
        # 2.2 表：编号 名称 位置 类型 S D R ST DS 一句话
        if len(c) < 10:
            continue
        e = E(c[0], c[1], "realm", "秘境", "realm",
              coverage="index",
              summary=f"{c[1]}；{c[2]}；{c[3]}；类型 {c[4]}；S/D/R {c[5]}/{c[6]}/{c[7]}；ST {c[8]}；DS {c[9]}。{c[10] if len(c)>10 else ''}",
              attributes={"位置": c[2], "坐标或区位": c[3], "类型": c[4], "S": c[5], "D": c[6], "R": c[7], "ST": c[8], "DS": c[9],
                          "一句话": c[10] if len(c) > 10 else ""},
              source=[src("10_全球秘境总目录.md", "第二节 64 座有名秘境")])
        if "临江" in c[2]:
            e["parent_id"] = "CITY-101"
            e["parent_name"] = "临江市"
        out.append(e)
    rich = {
        "REALM-012": dict(coverage="full", route="#/realms",
                          summary="临江地下层：中城区江堤路 9 号旧渠闸入口，地下 18—42 m，旧城管网与空间折叠区；S1/D3/R4、ST-1、DS-07，市政与 FRA 临江分局共管，限科研与特许探索。",
                          content_file="gazetteers/REALM-012.md",
                          attributes={"入口": "旧渠闸（LOC-101-0012）／江堤路9号", "S": "S1", "D": "D3", "R": "R4", "ST": "ST-1", "DS": "DS-07", "管理": "临江市政府＋FRA 临江分局"}),
        "REALM-061": dict(coverage="summary", route="#/realms"),
        "REALM-062": dict(coverage="summary", route="#/realms"),
        "REALM-063": dict(coverage="summary", route="#/realms"),
        "REALM-064": dict(coverage="summary", route="#/realms",
                          summary="云栖河水眼：北城区云栖河下游，S0/D1/R1、ST-1、DS-04，已登记未开发的小型水眼；周边存在地产争议与开发传言。"),
    }
    for rid, kv in rich.items():
        for e in out:
            if e["id"] == rid:
                e.update(kv)
    return out


def parse_cg():
    out = []
    p = SRC_GU / "蛊真人蛊虫合集_v3.0.md"
    rank = ""
    for ln in read(p).splitlines():
        m = re.match(r"^## (\d)转凡蛊", ln.strip()) or re.match(r"^## (\d)转仙蛊", ln.strip())
        if m:
            rank = m.group(1) + "转"
        m2 = re.match(r"^### (C-G-\d{3}) (.+)$", ln.strip())
        if m2:
            out.append({"id": m2.group(1), "name": clean(m2.group(2)), "rank": rank, "lines": []})
        elif out and ln.strip().startswith("- ") and len(out[-1]["lines"]) < 3:
            out[-1]["lines"].append(clean(ln.strip()[2:]))
    res = []
    for x in out:
        s = "；".join(x["lines"])[:180]
        res.append(E(x["id"], x["name"], "gu", "原著蛊虫", "gu",
                     coverage="summary", summary=s or f"{x['name']}（{x['rank']}）。",
                     tags=["C-G", "原著", x["rank"]],
                     attributes={"转数": x["rank"], "分区": "原著蛊虫"},
                     note="原文摘录来自 v3.0 合集；本站仅对 C-G-001、C-G-004 建有展示条目，其余为索引级记录。",
                     source=[src("蛊真人蛊虫合集_v3.0.md", "第一～三部分", "C-G 编号按 v2.0 条目顺序分配", "v3.0")]))
    for e in res:
        if e["id"] in ("C-G-001", "C-G-004"):
            e["route"] = "#/gu"
            e["coverage"] = "full"
    return res


def parse_ck():
    out = []
    p = SRC_GU / "原著杀招百科.md"
    for c in rows_of(p, r"C-K-\d{3}", start=45, end=510):
        if len(c) < 8:
            continue
        out.append(E(c[0], c[1], "kill_move", "原著杀招", "gu",
                     coverage="index",
                     summary=f"{c[1]}；流派 {c[3]}；类型 {c[4]}；{c[5]}；可信度 {c[6]}；档案级别 {c[7]}。",
                     tags=["C-K", "原著", c[3]],
                     attributes={"出处或待考": c[2], "流派": c[3], "类型": c[4], "备注": c[5], "可信度": c[6], "档案级别": c[7]},
                     note="仅导入快速索引行；A 级 36 份完整十节档案、B 级 409 条简档尚未导入本知识库，详情请查原著杀招百科.md。",
                     source=[src("原著杀招百科.md", "第二节 全量快速索引", "447 条", "v3.0")]))
    return out


def parse_og_ok():
    def scan(path, idkey, idpat):
        out, cur = [], None
        for ln in read(path).splitlines():
            if not ln.strip().startswith("|"):
                continue
            c = [clean(x) for x in ln.strip().strip("|").split("|")]
            if len(c) < 2:
                continue
            if re.fullmatch(idpat, c[1]) and c[0] in (idkey, "编号", "杀招编号"):
                cur = {"id": c[1]}
                out.append(cur)
            elif cur is not None:
                cur[c[0]] = c[1]
        return out
    res = []
    for r in scan(SRC_GU / "原创蛊虫图鉴.md", "编号", r"O-G-\d{3}"):
        res.append(E(r["id"], r.get("名称", ""), "gu", "原创蛊虫", "gu",
                     status="proposed", coverage="index",
                     summary=f"{r.get('名称','')}；{r.get('品阶','')}；{r.get('凡蛊或仙蛊','')}；流派 {r.get('所属流派','')}；用途 {r.get('核心用途','')}。",
                     tags=["O-G", "原创设定"],
                     attributes={k: v for k, v in r.items() if k != "id"},
                     note="【原创设定】本世界新增，不是《蛊真人》原著蛊虫；与原著 C-G 区严格分离。",
                     source=[src("原创蛊虫图鉴.md", "档案基本资料表", "原创区", "v3.0")]))
    for r in scan(SRC_GU / "原创杀招图鉴.md", "杀招编号", r"O-K-\d{3}"):
        res.append(E(r["id"], r.get("名称", ""), "kill_move", "原创杀招", "gu",
                     status="proposed", coverage="index",
                     summary=f"{r.get('名称','')}；{r.get('杀招类别','')}；{r.get('品阶','')}；流派 {r.get('所属流派','')}。",
                     tags=["O-K", "原创设定"],
                     attributes={k: v for k, v in r.items() if k != "id"},
                     note="【原创设定】本世界新增，不是原著杀招；与 C-K 区严格分离。",
                     source=[src("原创杀招图鉴.md", "档案基本资料表", "原创区", "v3.0")]))
    # 网站已展示条目
    for e in res:
        if e["id"] in ("O-G-001", "O-G-002"):
            e["route"] = "#/gu"
            e["coverage"] = "full"
    # O-G-110 界隙蛊：野生仙蛊登记，独立条目，不计入 32 只原创蛊虫
    res.append(E("O-G-110", "界隙蛊", "gu", "野生仙蛊（登记条目）", "gu",
                 status="proposed", coverage="summary",
                 summary="六转·宇道·野生仙蛊。当前所在地：O-B-012 阈鹿体表（被动寄生）。未被炼化、未被封印，妖兽不可催动；具体能力效果、消耗与限制登记表未载，一律【待考证】。同名仙蛊天下唯一。",
                 tags=["O-G", "仙蛊", "野生", "唯一性"],
                 attributes={"转数": "六转", "流派": "宇道", "宿主": "O-B-012", "可控性": "不可催动", "唯一性": "同名仙蛊天下唯一"},
                 route="#/beast/012",
                 note="出自《仙蛊唯一性登记表》第四节 C 组唯一新增条目，不在《原创蛊虫图鉴》32 只之内；引用一律以登记表为准。",
                 source=[src("仙蛊唯一性登记表.md", "第四节", "C 组唯一新增条目"),
                         src("原创妖兽图鉴.md", "O-B-012 阈鹿档案", "宿主关系")]))
    return res


def parse_beasts():
    """第一版网页的 beasts-json 数据岛 → 正式资料；同时保留原始渲染结构"""
    s = read(HTML_FILE)
    m = re.search(r'<script type="application/json" id="beasts-json">(.*?)</script>', s, re.S)
    if not m:
        raise RuntimeError("找不到 #beasts-json 数据岛")
    raw = json.loads(m.group(1))
    jwrite(ENT / "beasts_render.json", raw)      # 供网页重建数据岛，单一来源
    jwrite(ENT / "beasts_relations.json", raw.get("relations", []))
    out = []
    for b in raw["beasts"]:
        meta = b.get("meta", {}) or {}
        out.append(E(b["id"], b["name"], "beast", "原创妖兽", "beast",
                     status="proposed", coverage="full",
                     summary=f"{b['name']}（{b.get('alias','')}）；威胁 {b.get('threat','')}；栖息 {b.get('envFull') or b.get('env','')}；{meta.get('生态定位','')}。二十节完整档案已导入。",
                     route=f"#/beast/{b['num']}",
                     content_file=f"entities/beasts/{b['id']}.md",
                     tags=["O-B", "原创设定", b.get("envCode", "")],
                     attributes={"别名": b.get("alias", ""), "威胁等级": b.get("threat", ""),
                                 "栖息环境": b.get("envFull") or b.get("env", ""),
                                 "生物类别": meta.get("生物类别", ""), "生态定位": meta.get("生态定位", ""),
                                 "携带蛊虫": b.get("carry", ""), "资料状态": meta.get("资料状态", "")},
                     note="【原创设定】本世界原创妖兽；「携带蛊虫」不等于可控、可催动、可组杀招。",
                     source=[src("原创妖兽图鉴.md", b["id"] + " 二十节档案", "v1.1 收口版")]))
    # 二十节档案正文 → markdown（供 AI 资料包）
    bdir = ENT / "beasts"
    bdir.mkdir(exist_ok=True)
    for b in raw["beasts"]:
        lines = [f"# {b['id']} {b['name']}", "",
                 f"> 来源：《原创妖兽图鉴》v1.1 ｜ 状态：proposed（原创设定）｜ 分区：O-B", "",
                 "## 基本资料", ""]
        for k, v in (b.get("meta") or {}).items():
            lines.append(f"- **{k}**：{v}")
        lines += ["", "## 二十节档案", ""]
        for sec in b.get("sections", []):
            t = sec.get("title") or sec.get("name") or ""
            body = sec.get("body") or sec.get("content") or sec.get("text") or ""
            if isinstance(body, list):
                body = "\n".join(str(x) for x in body)
            lines += [f"### {t}", "", str(body), ""]
        write(bdir / (b["id"] + ".md"), "\n".join(lines).rstrip() + "\n")
    # C-B / R-B 索引
    for c in rows_of(SRC_BEAST / "原著兽类图鉴.md", r"C-B-\d{3}"):
        out.append(E(c[0], c[1], "beast_ref", "原著兽类（索引）", "beast",
                     coverage="index",
                     summary=f"{c[1]}；原著分类 {c[2]}；可信度 {c[3]}。",
                     tags=["C-B", "原著"],
                     attributes={"原著分类": c[2], "可信度": c[3]},
                     note="仅索引级记录：名称、分类与可信度已导入；完整档案未导入本知识库。C-B 不是本世界原创物种。",
                     source=[src("原著兽类图鉴.md", "第二节 总索引")]))
    for c in rows_of(SRC_BEAST / "跨作品妖兽参考库.md", r"R-B-\d{3}"):
        out.append(E(c[0], c[1], "reference_species", "跨作品参考物种（非本世界）", "beast",
                     coverage="index",
                     summary=f"{c[1]}；来源 {c[2]}；文化圈 {c[3]}；可信度 {c[4]}。",
                     tags=["R-B", "参考", "非本世界"],
                     attributes={"来源作品": c[2], "文化圈": c[3], "可信度": c[4]},
                     note="R-B 只是研究参考，不是本世界真实存在的物种；不得当作衡垠世界的生灵。",
                     source=[src("跨作品妖兽参考库.md", "总索引表")]))
    return out, raw


def parse_orgs():
    return [
        E("ORG-016", "临江炼蛊集团", "organization", "国企", "organization",
          parent_id="CITY-101", parent_name="临江市", coverage="index",
          summary="临江市国企，4.2 万人；凡蛊量产、蛊具；全球凡蛊量产排第十一。",
          attributes={"人数": "4.2 万", "业务": "凡蛊量产、蛊具", "总部": "临江市"},
          note="仅索引与概要，无完整组织档案。",
          source=[src("09_临江市城市档案.md", "§11 主要势力"), src("衡垠世界图集.html", "实体索引")]),
        E("ORG-017", "临江港务集团", "organization", "国企", "organization",
          parent_id="CITY-101", parent_name="临江市", coverage="index",
          summary="临江市国企，1.6 万人；港口与保税；临江港年吞吐 1.2 亿吨。",
          attributes={"人数": "1.6 万", "业务": "港口、保税", "总部": "临江市"},
          note="仅索引与概要，无完整组织档案。",
          source=[src("09_临江市城市档案.md", "§11 主要势力"), src("衡垠世界图集.html", "实体索引")]),
    ]


def build_entities():
    ents = []
    nats = parse_nat()
    ents += parse_planet_continent_ocean()
    ents += nats
    ents += parse_admin()
    ents += parse_city(nats)
    ents += parse_dist_street()
    ents += parse_loc()
    ents += parse_realm()
    ents += parse_cg()
    ents += parse_ck()
    ents += parse_og_ok()
    beasts, raw = parse_beasts()
    ents += beasts
    ents += parse_orgs()
    # 去重（同一编号只保留一条，保留信息更全者）
    byid = {}
    for e in ents:
        if e["id"] in byid:
            old = byid[e["id"]]
            if (e["coverage"] == "full" and old["coverage"] != "full") or len(json.dumps(e, ensure_ascii=False)) > len(json.dumps(old, ensure_ascii=False)):
                byid[e["id"]] = e
        else:
            byid[e["id"]] = e
    ents = list(byid.values())
    # 补充网页专名与路由
    site = {
        "NAT-005": dict(route="#/world"), "ADM-105": dict(route="#/world"),
        "DIST-101-03": dict(route="#/beicheng"), "LOC-101-0301": dict(route="#/yunqi"),
        "LOC-101-0312": dict(route="#/garden"),
        "LOC-101-0360": dict(route="#/garden?map"), "LOC-101-0361": dict(route="#/garden?map"),
        "LOC-101-0362": dict(route="#/garden?map"), "NODE-101-001": dict(route="#/garden?map"),
        "REALM-012": dict(route="#/realms"), "REALM-061": dict(route="#/realms"),
        "REALM-062": dict(route="#/realms"), "REALM-063": dict(route="#/realms"), "REALM-064": dict(route="#/realms"),
        "C-G-001": dict(route="#/gu"), "C-G-004": dict(route="#/gu"),
        "O-G-001": dict(route="#/gu"), "O-G-002": dict(route="#/gu"), "O-G-110": dict(route="#/beast/012"),
        "ORG-016": dict(route="#/linjiang"), "ORG-017": dict(route="#/linjiang"),
    }
    for e in ents:
        if e["id"] in site and not e.get("route"):
            e.update(site[e["id"]])
        e["entity_route"] = "#/entity/" + e["id"]
        if not e["summary"]:
            e["summary"] = e["name"] + "（索引级记录，详情见原始资料）。"
    # 分类写入
    groups = {}
    for e in ents:
        groups.setdefault(e["category"], []).append(e)
    names = {"geography": "geography", "gu": "gu", "beast": "beasts", "realm": "realms", "organization": "organizations"}
    for cat, arr in groups.items():
        arr.sort(key=lambda x: x["id"])
        jwrite(ENT / (names.get(cat, cat) + ".json"), {"schema": "hengyin/entities/1.0", "category": cat, "count": len(arr), "entities": arr})
    return ents, raw


# ----------------------------------------------------------------------------
# 二、关联关系
# ----------------------------------------------------------------------------
KINDS = {
    "part_of": "隶属／包含（父级）",
    "located_in": "位于",
    "capital_of": "首都／驻地",
    "has_entrance": "出入口位于",
    "entrance_of": "是…的出入口",
    "managed_by": "由…管理",
    "headquarters_in": "总部位于",
    "habitat": "栖息地",
    "occasional": "偶入记录（非现存物种）",
    "predation": "捕食／被捕食",
    "symbiosis": "共生／伴生",
    "competition": "竞争",
    "ecology_other": "其他生态关系",
    "carries_gu": "携带蛊虫（不等于可控）",
    "host_of": "宿主／被动寄生",
    "traded_at": "交易场所",
    "produced_in": "产地／制造",
    "rule_ref": "规则依据",
}


def build_relations(ents, raw):
    byid = {e["id"]: e for e in ents}
    edges = []

    def add(f, t, typ, kind="association", note="", status="existing", source=""):
        if f not in byid or t not in byid:
            return
        edges.append({"id": "", "from": f, "to": t, "type": typ, "kind": kind,
                      "status": status, "note": note, "source": source})

    # 1) 父级层级（与普通关联分开）
    for e in ents:
        if e.get("parent_id") and e["parent_id"] in byid:
            add(e["id"], e["parent_id"], "part_of", "hierarchy",
                "由 parent_id 生成；" + (e.get("note") or ""), e["status"], "world-index.json / parent_id")
    # 2) 首都（03 号）
    for e in ents:
        cid = (e.get("attributes") or {}).get("首都城市编号")
        if cid and cid in byid:
            add(e["id"], cid, "capital_of", "association", "首都／驻地，据 03 号政治实体首都坐标表", "existing", "03_世界地图与坐标索引.md §3")
    # 3) 秘境出入口与管理
    add("REALM-012", "LOC-101-0012", "has_entrance", "association", "旧渠闸为中城区江堤路 9 号入口，24 小时值守。", "existing", "09_临江市城市档案.md §13 / 10_全球秘境总目录.md")
    add("LOC-101-0012", "REALM-012", "entrance_of", "association", "旧渠闸是临江地下层的登记入口。", "existing", "09_临江市城市档案.md §13")
    # 4) 蛊坊街父级明确到江堤街道
    add("LOC-101-0340", "LOC-101-0304", "located_in", "association", "蛊坊街在江堤街道，不在云栖街道；第一版部分链接误指向云栖街道，本阶段已修正。", "existing", "09_临江市城市档案.md §13")
    # 5) 蛊虫／交易／产业
    add("LOC-101-0340", "LOC-101-0208", "traded_at", "association", "蛊坊街为零售与小修；临江蛊虫交易市场在南岸区，二者不是同一地点。", "existing", "09_临江市城市档案.md §7")
    add("ORG-016", "CITY-101", "headquarters_in", "association", "总部临江市；凡蛊量产。", "existing", "09_临江市城市档案.md §11")
    add("ORG-017", "CITY-101", "headquarters_in", "association", "总部临江市；港口与保税。", "existing", "09_临江市城市档案.md §11")
    # 6) 生灵：生态关系（36 条，来自《妖兽分类与生态体系》7.1）
    rtype_map = {"捕食": "predation", "共生": "symbiosis", "竞争": "competition"}
    for r in raw.get("relations", []):
        sids = [x for x in r.get("subjIds", []) if x in byid]
        oids = [x for x in r.get("objIds", []) if x in byid]
        typ = "ecology_other"
        for k, v in rtype_map.items():
            if k in (r.get("type") or ""):
                typ = v
                break
        for a in sids:
            for b in oids:
                add(a, b, typ, "association", (r.get("mech") or "") + "（" + (r.get("type") or "") + "）",
                    "proposed", "妖兽分类与生态体系.md §7.1 / " + (r.get("rid") or ""))
    # 7) 阈鹿 ↔ 界隙蛊
    add("O-G-110", "O-B-012", "host_of", "association", "界隙蛊被动寄生于阈鹿体表；未被炼化、不可催动；同名仙蛊天下唯一。", "proposed", "仙蛊唯一性登记表.md §4 / 原创妖兽图鉴.md O-B-012")
    add("O-B-012", "O-G-110", "carries_gu", "association", "携带≠可控≠可催动；阈鹿不主动使用界隙蛊。", "proposed", "原创妖兽图鉴.md O-B-012")
    # 8) 檐鸮 ↔ REALM-012 仅为偶入记录
    add("O-B-001", "REALM-012", "occasional", "association", "仅偶入记录，不判定为云栖花园或该秘境的现存物种。", "proposed", "原创妖兽图鉴.md O-B-001")
    add("O-B-002", "REALM-012", "habitat", "association", "地下管廊与旧城地下管网为隧锈鼠主要栖息环境；REALM-012 属同类空间，按原文表述登记。", "proposed", "原创妖兽图鉴.md O-B-002")
    # 9) 规则文件引用
    for e in ents:
        if e["type"] in ("gu", "kill_move"):
            e["relations"].append("rule_ref:03_蛊道规则.md")
        if e["type"] == "realm":
            e["relations"].append("rule_ref:04_秘境规则.md")
        if e["type"] in ("beast", "beast_ref", "reference_species"):
            e["relations"].append("rule_ref:05_妖兽与携蛊规则.md")
    # 编号
    for i, r in enumerate(edges, 1):
        r["id"] = "REL-%05d" % i
    obj = {"schema": "hengyin/relationships/1.0", "version": VERSION, "generated_at": STAMP,
           "kinds": KINDS, "count": len(edges), "edges": edges}
    jwrite(DATA / "relationships.json", obj)
    # 回写实体 relations 简表
    for e in ents:
        rs = [r["id"] for r in edges if r["from"] == e["id"] or r["to"] == e["id"]]
        e["relations"] = list(dict.fromkeys([x for x in e["relations"] if x.startswith("rule_ref:")] + rs))
    return obj


# ----------------------------------------------------------------------------
# 三、HTML → Markdown（地方志，保留原文）
# ----------------------------------------------------------------------------
class View2MD(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip = 0
        self.in_table = False
        self.row = []
        self.cell = []
        self.rows = []
        self.header_done = False
        self.buf_block = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "") or ""
        if tag in ("svg", "script", "style", "colgroup", "col"):
            self.skip += 1
            return
        if self.skip:
            return
        if tag == "table":
            self.in_table = True; self.rows = []; self.row = []; self.cell = []; self.header_done = False
            self.out.append("\n\n")
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell = []
        elif tag in ("h1", "h2", "h3", "h4"):
            lvl = int(tag[1])
            self.out.append("\n\n" + "#" * min(lvl + 1, 4) + " ")
        elif tag == "p":
            self.out.append("\n> " if "note" in cls else "\n\n")
        elif tag == "li":
            self.out.append("\n- ")
        elif tag == "br":
            (self.cell if self.in_table else self.out).append(" " if self.in_table else "\n")
        elif tag == "dt":
            self.out.append("\n- **")
        elif tag == "dd":
            self.out.append("**：")
        elif tag == "i" and not self.in_table:
            self.out.append(" ")
        elif tag in ("div", "section"):
            if "kicker" in cls or "rid" in cls or "yr" in cls or "no" in cls or "facts" in cls or "crumb" in cls:
                self.out.append("\n")
        elif tag == "caption":
            self.out.append("\n\n*")
        elif tag == "a" and a.get("href", "").startswith("#/entity/"):
            pass

    def handle_endtag(self, tag):
        if tag in ("svg", "script", "style", "colgroup"):
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag in ("td", "th"):
            self.row.append("".join(self.cell).strip())
            self.cell = []
        elif tag == "tr":
            if self.row:
                self.rows.append(self.row)
            self.row = []
        elif tag == "table":
            if self.rows:
                width = max(len(r) for r in self.rows)
                def fmt(r):
                    return "| " + " | ".join((r + [""] * width)[:width]) + " |"
                self.out.append(fmt(self.rows[0]) + "\n")
                self.out.append("| " + " | ".join(["---"] * width) + " |\n")
                for r in self.rows[1:]:
                    self.out.append(fmt(r) + "\n")
            self.out.append("\n")
            self.in_table = False
        elif tag == "caption":
            self.out.append("*\n")
        elif tag == "dd":
            self.out.append(" ｜ ")
        elif tag in ("h1", "h2", "h3", "h4", "p", "li", "div", "section"):
            self.out.append("\n" if tag in ("h1", "h2", "h3", "h4", "li") else "")

    def handle_data(self, data):
        if self.skip:
            return
        t = re.sub(r"\s+", " ", data)
        if self.in_table and (self.cell or self.row is not None):
            self.cell.append(t)
        else:
            self.out.append(t)

    def text(self):
        s = "".join(self.out)
        s = re.sub(r"[ \t]+\n", "\n", s)
        s = re.sub(r"\n{3,}", "\n\n", s)
        return s.strip() + "\n"


VIEWS = {
    "home": "00_首页.md", "world": "01_世界.md", "linjiang": "CITY-101.md",
    "beicheng": "DIST-101-03.md", "yunqi": "LOC-101-0301.md", "garden": "LOC-101-0312.md",
    "gu": "GU_蛊道索引.md", "realms": "REALM-012.md", "status": "BUILD_建设状态.md",
}


def extract_views():
    s = read(HTML_FILE)
    for key, fn in VIEWS.items():
        m = re.search(r'<section class="view" id="v-' + key + r'"[^>]*>', s)
        if not m:
            continue
        start = m.end()
        # 用 section 深度找到视图结束（视图内部还有 block section）
        depth, pos = 1, start
        for t in re.finditer(r'</?section\b[^>]*>', s[start:]):
            if t.group(0).startswith("</"):
                depth -= 1
            else:
                depth += 1
            if depth == 0:
                pos = start + t.start()
                break
        frag = s[start:pos]
        p = View2MD()
        p.feed(frag)
        body = p.text()
        title = {"home": "首页", "world": "世界层级", "linjiang": "临江市地方志", "beicheng": "北城区地方志",
                 "yunqi": "云栖街道地方志", "garden": "云栖花园地方志", "gu": "蛊道索引页",
                 "realms": "临江秘境档案", "status": "建设状态页"}[key]
        head = (f"# {title}\n\n> 来源：第一版《衡垠世界图集》 `#/{"home" if key == "home" else key}` 页面正文，"
                "由 tools/build_kb.py 自动转为 Markdown，文字未改写。\n"
                "> 状态：existing（第一版已有正文）；其中标「本轮新增拟定」的内容为 proposed，见 sources/01_版本与状态.md。\n\n---\n\n")
        write(DATA / "gazetteers" / fn, head + body)


# ----------------------------------------------------------------------------
# 四、文档（仅首次创建；之后 data/ 内的文档为权威，可手工修订）
# ----------------------------------------------------------------------------
def ensure_docs():
    D = DATA
    write_if_missing(D / "AI_START_HERE.md", TPL_AI_START.replace("__STAMP__", STAMP))
    write_if_missing(D / "AI_INTEGRATION_GUIDE.md", TPL_AI_INTEG.replace("__STAMP__", STAMP))
    write_if_missing(D / "DATA_SCHEMA.md", TPL_SCHEMA.replace("__STAMP__", STAMP))
    for fn, txt in RULES.items():
        write_if_missing(D / "rules" / fn, txt.replace("__STAMP__", STAMP))
    for fn, txt in SOURCES.items():
        write_if_missing(D / "sources" / fn, txt.replace("__STAMP__", STAMP))
    write_if_missing(D / "README.md", TPL_README.replace("__STAMP__", STAMP))
    # 根目录镜像：方便用户直接找到交付文件；正式文件仍是 data/ 里的那份
    for fn in ("AI_START_HERE.md", "AI_INTEGRATION_GUIDE.md", "DATA_SCHEMA.md"):
        write(ROOT / fn,
              "> 镜像副本：正式文件是 `data/" + fn + "`，本文件由 `tools/build_kb.py` 自动生成，请勿在此修改。\n"
              "> 给 AI 用的完整资料包是「衡垠AI资料包.zip」。\n\n" + read(D / fn))


# ----------------------------------------------------------------------------
# 五、审计与报告
# ----------------------------------------------------------------------------
def audit(ents, rels):
    byid = {e["id"] for e in ents}
    dup = {}
    for e in ents:
        dup.setdefault(e["id"], 0)
        dup[e["id"]] += 1
    dups = {k: v for k, v in dup.items() if v > 1}
    dangling_parent = [(e["id"], e["parent_id"]) for e in ents if e.get("parent_id") and e["parent_id"] not in byid]
    dangling_rel = [r for r in rels["edges"] if r["from"] not in byid or r["to"] not in byid]
    s = read(HTML_FILE)
    hrefs = set(re.findall(r'href="(#[^"]+)"', s))
    VIEWS_JS = {"home", "world", "linjiang", "beicheng", "yunqi", "garden", "gu", "beasts", "beast", "realms", "status",
                "entities", "entity", "export"}
    anchors = set(re.findall(r'id="([A-Za-z0-9_\-]+)"', s))
    bad_links = []
    for h in hrefs:
        if "'+" in h or '"+' in h or "${" in h:   # JS 模板字符串拼接，不是静态链接
            continue
        if h == "#/":
            continue
        if h.startswith("#/entity/"):
            eid = h.split("#/entity/", 1)[1]
            if not eid:                    # JS 字符串拼接前缀，不是实际链接
                continue
            if eid not in byid:
                bad_links.append(h)
        elif h.startswith("#/beast/"):
            if not re.fullmatch(r"#/beast/\d{3}", h):
                bad_links.append(h)
        elif h.startswith("#/"):
            v = h[2:].split("?")[0].split("/")[0]
            if v not in VIEWS_JS:
                bad_links.append(h)
        elif h.startswith("#") and len(h) > 1:
            if h[1:] not in anchors and not h.startswith("#ob-"):
                bad_links.append(h)
    return {"dups": dups, "dangling_parent": dangling_parent, "dangling_rel": dangling_rel,
            "bad_links": sorted(bad_links), "href_count": len(hrefs)}


CONFLICTS = [
    ("C-01", "07 号声明 60 座核心城市，实际登记 59 行，缺 CITY-039",
     "保留原声明；本站显示「59 / 声明 60」，不补造城市。", "36_城市空间布局质量审计报告.md C-01", "待用户裁定"),
    ("C-02", "临江「城区 864 万＋常住外来 186 万＝1,050 万」与七城区合计 1,064 万差 14 万",
     "三栏并列展示，差额记为驻军、集体户与未登记流动人口的口径差，不改原值。", "09_临江市城市档案.md §4 / 36 号审计", "已标注，未修改原值"),
    ("C-03", "08 号部分城市「其余 N 区」未命名",
     "晏京、维兰、环港、朔京已在 28 号补名，标【本轮新增拟定】。", "28_全球核心城市空间骨架总表.md", "拟定，待确认"),
    ("C-04", "09 号 §4.2 街道表（0301—0306）与 §13 地点表重复使用 0301／0302／0305",
     "街道保留 0301—0306；街道办事处／菜市场／人行桥改挂 0360／0361／0362，标 proposed，不改原档。", "09_临江市城市档案.md §4.2 与 §13", "拟定，待用户确认"),
    ("C-05", "第一版蛊道页同一段出现「已接入 4 条」「其余 1,172 条」，但页面实际列出 5 条；建设状态页写「全量 1,176 条仅接入 5 条」",
     "本阶段统一口径：总目 1,176 = C-G 684 + C-K 447 + O-G 32 + O-K 13；页面展示 5 条中 4 条属于总目，另 1 条 O-G-110 界隙蛊是《仙蛊唯一性登记表》的额外登记条目，不计入 32 只原创蛊虫。故「已接入 4/1,176 条，另 1 条登记条目」，未接入 1,172 条。", "蛊道资料库_v3.0/00_总目录.md；仙蛊唯一性登记表.md §4", "口径已说明，原页面文字保留"),
    ("C-06", "09 号 §7 把 GAB 澜东分局临江办事处记为 LOC-101-0104，而 §13 把 LOC-101-0104 记为北城公交枢纽、LOC-101-0004 记为 GAB 临江办事处",
     "本站 LOC-101-0104 沿用 §13「北城公交枢纽」。GAB 办事处的正式编号存在双记载，本站不擅自裁定，列入待确认清单；不把两个地点合并。", "09_临江市城市档案.md §7 与 §13", "待用户裁定"),
    ("C-07", "第一版地图 POI 使用 LOC-101-0360／0362／NODE-101-001，但这三个编号不在 36 条实体索引中",
     "本阶段已把三者登记进统一实体索引，状态 proposed；地图、搜索、正文引用共用同一 ID。", "衡垠世界图集.html 第一版 POIS", "已修复并登记为拟定编号"),
    ("C-08", "第一版北城区「相关设施」区把「蛊坊街 LOC-101-0340」链接指向云栖街道 #/yunqi",
     "本阶段改为实体档案 #/entity/LOC-101-0340，并在 relationships.json 中明确其父级为江堤街道 LOC-101-0304。", "09_临江市城市档案.md §13", "已修复"),
]


def write_reports(ents, rels, au):
    bytype, bystatus, bycov, bycat = {}, {}, {}, {}
    for e in ents:
        bytype[e["type_label"]] = bytype.get(e["type_label"], 0) + 1
        bystatus[e["status"]] = bystatus.get(e["status"], 0) + 1
        bycov[e["coverage"]] = bycov.get(e["coverage"], 0) + 1
        bycat[e["category"]] = bycat.get(e["category"], 0) + 1

    def tbl(d, order=None):
        keys = order or sorted(d)
        return "| 项 | 条数 |\n|---|---|\n" + "\n".join(f"| {k} | {d.get(k, 0)} |" for k in keys)

    # 编号冲突报告
    lines = ["# 编号冲突检查报告", "", f"> 生成时间：{STAMP} ｜ 检查对象：`data/entities/*.json`、`data/world-index.json`、第一版网页与原始资料", "",
             "## 一、唯一性校验", "",
             f"- 实体总数：**{len(ents)}**；唯一编号数：**{len(set(e['id'] for e in ents))}**。",
             f"- 重复编号：**{len(au['dups'])}** 处" + ("（" + ", ".join(au["dups"]) + "）" if au["dups"] else "。"),
             f"- 悬空 parent_id：**{len(au['dangling_parent'])}** 处" + ("（" + ", ".join(f"{a}→{b}" for a, b in au["dangling_parent"][:10]) + "）" if au["dangling_parent"] else "。"),
             f"- 悬空关联端点：**{len(au['dangling_rel'])}** 处。", "",
             "## 二、已登记的冲突与处理", "",
             "| 编号 | 问题 | 当前处理 | 依据 | 状态 |", "|---|---|---|---|---|"]
    for c in CONFLICTS:
        lines.append("| " + " | ".join(c) + " |")
    lines += ["", "## 三、编号分配现状（重大类别）", "",
              "| 前缀 | 含义 | 已导入 | 说明 |", "|---|---|---|---|",
              "| CONT / OCEAN | 大陆 / 海洋 | 6 / 6 | 02 号 |",
              "| NAT | 国家与政治实体 | 39 | 03／04 号 |",
              "| CITY | 核心城市 | 59 | 07 号；声明 60，缺 CITY-039（C-01） |",
              "| DIST / LOC / STREET | 城区 / 地点 / 街道 | 7 / 23＋ / 6 | 09 号；含 C-04 拟定 0360—0362 |",
              "| REALM | 有名秘境 | 64 | 10 号；全球登记 4,180 处，其余为编号段批量登记 |",
              "| C-G / C-K | 原著蛊虫 / 杀招 | 684 / 447 | v3.0；多数为索引级记录 |",
              "| O-G / O-K | 原创蛊虫 / 杀招 | 32＋1 / 13 | O-G-110 为额外登记条目，不计入 32 |",
              "| O-B / C-B / R-B | 原创妖兽 / 原著兽类 / 参考物种 | 12 / 37 / 40 | O-B 二十节档案全量；C-B／R-B 仅索引 |",
              "| PLANET-000 / NODE-101-001 | 占位编号 | 1 / 1 | 非正式编号，仅用于建立层级与地图引用，见待确认清单 |", "",
              "## 四、结论", "",
              "- 统一数据层内**没有重复编号**；网页搜索、地图 POI、正文引用现在共用同一套 ID。",
              "- 原始资料本身存在 4 组编号双记载（C-01／C-04／C-06 及 0104 双用），**本站没有擅自改写原档**，只按并列保留＋状态标注处理。",
              "- CITY-039 仍缺失；未补造。", ""]
    write(DATA / "reports" / "编号冲突检查报告.md", "\n".join(lines))

    # 完整度报告
    full = [e for e in ents if e["coverage"] == "full"]
    missing_note = [
        ("C-K 原著杀招", 447, "仅导入快速索引行；36 份 A 级十节档案、409 条 B 级简档未导入知识库。"),
        ("C-G 原著蛊虫", 684, "已导入编号＋原文摘录（coverage=summary）；网页仅展示 C-G-001／004 两条。"),
        ("C-B 原著兽类", 37, "仅导入编号、名称、分类、可信度；完整档案未导入。"),
        ("R-B 参考物种", 40, "仅导入索引；R-B 不是本世界物种。"),
        ("O-G 原创蛊虫", 32, "仅导入基本资料字段；七节完整档案未导入知识库。"),
        ("O-K 原创杀招", 13, "仅导入基本资料字段；十节完整档案未导入知识库。"),
        ("CITY 全球城市", 59, "仅索引级；除临江市外均无地方志页面。"),
        ("REALM 有名秘境", 64, "仅索引级；临江 5 处有概要，仅 REALM-012 有专页正文。"),
        ("组织与经济", 11, "09 号 §11 列出 11 个势力，其中仅 2 个有编号并进入索引；其余未编号实体列入 sources/04_未编号实体清单.md。"),
        ("历史事件 / 人物 / 社会关系", None, "尚未建立实体表；20 号年表、17 号制度等仍是原始资料，未迁移。"),
        ("其余五城区 / 五街道", None, "只有概要，无地方志页面。"),
        ("跑团规则", None, "只在 rules/ 中给出导航式说明，ll.txt 等主持人提示词未导入知识库。"),
    ]
    lines = ["# 资料缺失与完整度报告", "", f"> 生成时间：{STAMP} ｜ 统计口径：本知识库（data/），不是网页展示条数", "",
             "## 一、总览", "", f"- 实体总数：**{len(ents)}**；关联关系：**{rels['count']}** 条。",
             f"- 有完整正文（coverage=full）：**{len(full)}** 条 —— " + "、".join(e["id"] for e in full[:20]) + ("…" if len(full) > 20 else ""), "",
             "### 按资料深度", "", tbl(bycov, ["full", "summary", "index", "missing"]), "",
             "### 按状态", "", tbl(bystatus, ["existing", "proposed", "uncertain", "revised"]), "",
             "### 按大类", "", tbl(bycat), "",
             "## 二、已导入 / 未导入清单（逐项如实列出）", "",
             "| 资料块 | 数量 | 当前状态 |", "|---|---|---|"]
    for name, n, note in missing_note:
        lines.append(f"| {name} | {n if n is not None else '—'} | {note} |")
    lines += ["", "## 三、明确没有做的事", "",
              "- 没有因为索引里出现 12 个 O-B 名称就说「12 种完整档案」之外的东西：O-B 十二种确实各有二十节完整档案，已全量导入；C-B 37 条与 R-B 40 条**只有索引**。",
              "- 没有把尚未导入的编号显示为「空档案」；没有补造 CITY-039、没有补造缺失的妖兽档案、没有编造统计数字。",
              "- 原著蛊虫（C-G）／原创蛊虫（O-G）／原著杀招（C-K）／原创杀招（O-K）／原著兽类（C-B）／参考物种（R-B）／原创妖兽（O-B）**分区独立保存**，没有互相混编。", "",
              "## 四、下一步建议（不自动执行）", "",
              "1. 按编号分批导入 C-K 完整档案与 O-G／O-K 七节／十节正文。",
              "2. 为 09 号 §11 未编号的 9 个势力分配正式 ORG 编号后再建关系。",
              "3. 补其余六城区、五街道地方志，再按 LOC-101-08xx 段分配地点编号。", ""]
    write(DATA / "reports" / "资料缺失与完整度报告.md", "\n".join(lines))

    # 路由校验
    lines = ["# 链接与路由校验报告", "", f"> 生成时间：{STAMP}", "",
             f"- 检查到 `href` 内部链接 **{au['href_count']}** 个（去重后）。",
             f"- 无效路由：**{len(au['bad_links'])}** 个" + ("（" + ", ".join(au["bad_links"]) + "）" if au["bad_links"] else "。"),
             "- 校验范围：`#/<view>`、`#/beast/<3位数字>`、`#/entity/<实体编号>`、页内锚点 `#ob-*` / `#bs*`。",
             "- `#/garden?map` 为「打开生活圈地图」专用路由，视图为 garden，滚动到 `#sec-life-map`。", "",
             "## 已修复的链接", "",
             "| 原问题 | 修复 |", "|---|---|",
             "| 首页「打开生活圈地图」按钮 | `data-goto-map` 委托 + `scrollToLifeMap()`；已在 hash 已是 `#/garden?map` 时重复点击也能滚动 |",
             "| 蛊坊街链接指向云栖街道 | 改为 `#/entity/LOC-101-0340`，父级明确为江堤街道 LOC-101-0304 |",
             "| 地图 POI 编号不在搜索索引 | 7 个 POI 全部登记进 world-index.json，POI 面板可直达实体档案 |",
             "| 搜索结果硬编码 36 条 | 改为读取统一实体索引（" + str(len(ents)) + " 条） |", ""]
    write(DATA / "reports" / "链接与路由校验报告.md", "\n".join(lines))

    # 待确认清单
    lines = ["# 待确认清单", "", f"> 生成时间：{STAMP} ｜ 以下事项本站**没有擅自决定**，请用户裁定后再改 data/", "",
             "| # | 事项 | 现状 | 需要用户确认什么 |", "|---|---|---|---|",
             "| Q-01 | C-04 三处拟定编号 | 街道办事处 0360、菜市场 0361、人行桥 0362，status=proposed | 是否接受这组新编号，或改用原 §13 编号并调整街道表 |",
             "| Q-02 | NODE-101-001 | 公交站沿用第一版 POI 占位编号，status=proposed | 是否分配正式 LOC 编号；NODE 前缀不在原编号体系 |",
             "| Q-03 | PLANET-000 | 行星根节点占位编号，status=proposed | 原编号体系未为行星分配前缀，是否需要正式前缀 |",
             "| Q-04 | C-06 GAB 办事处编号 | §7 记 LOC-101-0104，§13 记 LOC-101-0004，本站 LOC-101-0104 沿用公交枢纽 | 该机构以哪个编号为准；是否把 0004 与 §7 视为同一机构 |",
             "| Q-05 | C-01 缺失的 CITY-039 | 未补造 | 是补一座城市，还是把声明改为 59 |",
             "| Q-06 | 八个社区空间标签 | 云栖新村、花园里、育才坊、河西湾、桥北口、老街口、屏岭脚、河口，第一版标【本轮新增拟定】 | 是否作为正式社区实体分配编号 |",
             "| Q-07 | 云栖街道 08xx 段 | 第一版页面写「新增具体地点将沿用 LOC-101-08xx 段」，但实际把三处地点挂到了 0360—0362 | 以哪一段为准 |",
             "| Q-08 | 蛊道展示条数口径 | 已按 C-05 说明 4/1,176＋1 条登记条目 | 是否把 O-G-110 计入总目 |",
             "| Q-09 | 组织编号 | 09 号 §11 有 9 个势力无编号，未建实体 | 是否分配 ORG 编号 |", ""]
    write(DATA / "reports" / "待确认清单.md", "\n".join(lines))
    return {"bytype": bytype, "bystatus": bystatus, "bycov": bycov, "bycat": bycat,
            "full": len(full), "conflicts": len(CONFLICTS)}


# ----------------------------------------------------------------------------
# 六、生成 world-index / manifest / ZIP / 网页数据岛
# ----------------------------------------------------------------------------
def build_index_and_manifest(ents, rels, stats, au):
    idx = []
    for e in ents:
        idx.append({
            "id": e["id"], "name": e["name"], "type": e["type"], "type_label": e["type_label"],
            "category": e["category"], "parent_id": e["parent_id"], "status": e["status"],
            "coverage": e["coverage"], "route": e["route"], "entity_route": e["entity_route"],
            "content_file": e["content_file"], "record_file": "entities/" + {
                "geography": "geography", "gu": "gu", "beast": "beasts", "realm": "realms",
                "organization": "organizations"}.get(e["category"], e["category"]) + ".json",
            "tags": e["tags"], "summary": e["summary"][:120],
        })
    idx.sort(key=lambda x: x["id"])
    w = {"schema": "hengyin/world-index/1.0", "version": VERSION, "generated_at": STAMP,
         "counts": {"total": len(idx), "by_status": stats["bystatus"], "by_coverage": stats["bycov"],
                    "by_category": stats["bycat"], "full_records": stats["full"], "relations": rels["count"]},
         "status_definitions": {
             "existing": "原设定已有，来自 01_最终版/ 原始资料，不得改写",
             "proposed": "新增拟定（含【原创设定】与网站补拟编号），不是既定事实",
             "uncertain": "尚未确认，资料不足或存在互斥记载",
             "revised": "经过正式修订并留有版本记录"},
         "coverage_definitions": {
             "full": "本知识库内有完整档案正文",
             "summary": "有原文摘录或结构化概要",
             "index": "只有编号、名称与索引字段，无正文",
             "missing": "仅在总目录提及，尚未建档"},
         "id_prefixes": {
             "CONT": "大陆", "OCEAN": "海洋/内海", "NAT": "国家/政治实体", "ADM": "一级行政区",
             "CITY": "城市", "DIST": "城区", "LOC": "重要地点/建筑", "REALM": "秘境",
             "C-G": "原著蛊虫", "C-K": "原著杀招", "O-G": "原创蛊虫", "O-K": "原创杀招",
             "C-B": "原著兽类", "R-B": "跨作品参考物种（非本世界）", "O-B": "本世界原创妖兽",
             "ORG": "组织", "NODE": "交通节点（第一版拟定占位）", "PLANET": "行星（占位）"},
         "entities": idx}
    jwrite(DATA / "world-index.json", w)

    files = []
    for p in sorted(DATA.rglob("*")):
        rel = p.relative_to(DATA).as_posix()
        # beasts_render.json 是第一版网页的渲染结构，只用于重建数据岛，不进入 AI 资料包
        if p.is_file() and p.name != "manifest.json" and rel != "entities/beasts_render.json":
            files.append({"path": rel, "bytes": p.stat().st_size})
    manifest = {"schema": "hengyin/manifest/1.0", "version": VERSION, "generated_at": STAMP,
                "pack_name": "衡垠AI资料包.zip",
                "source_of_truth": "data/entities/*.json（网页数据岛与 ZIP 都由它生成，不存在第二份手工数据）",
                "counts": {"entities": len(idx), "files": len(files), "pack_files": len(files) + 2,
                           "relations": rels["count"], "full_records": stats["full"],
                           "conflicts": stats["conflicts"], "invalid_routes": len(au["bad_links"]),
                           "duplicate_ids": len(au["dups"])},
                "pack_extra_files": ["manifest.json", "README_怎么用.txt"],
                "checks": {"duplicate_ids": au["dups"], "invalid_routes": au["bad_links"],
                           "dangling_parent": au["dangling_parent"], "dangling_relations": len(au["dangling_rel"])},
                "files": files}
    jwrite(DATA / "manifest.json", manifest)
    return w, manifest, files


def build_pack(files):
    if PACK.exists():
        PACK.unlink()
    with zipfile.ZipFile(PACK, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in files:
            p = DATA / f["path"]
            z.write(p, "衡垠AI资料包/" + f["path"])
        z.writestr("衡垠AI资料包/README_怎么用.txt",
                   "把本文件夹（或整个 ZIP）上传给 AI 即可。\n"
                   "AI 请先读 AI_START_HERE.md，再按 world-index.json 查编号，按 relationships.json 查关联。\n"
                   "不要把 status=proposed 的内容当作既定事实；不要把 coverage=index 的记录当作完整档案。\n")
    return PACK.stat().st_size


def jsafe(s):
    return s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def inject(html_text, ents, rels, w, manifest, pack_bytes, raw):
    # 网页投影：省略二十节大段正文，保留指针；完整正文在 ZIP 里
    slim = []
    for e in ents:
        c = dict(e)
        c.pop("content_md", None)
        slim.append(c)
    kb = {"schema": "hengyin/site-projection/1.0", "version": VERSION, "generated_at": STAMP,
          "manifest": manifest, "entities": slim,
          "relationships": {"count": rels["count"], "kinds": rels["kinds"], "edges": rels["edges"]},
          "pois": POIS,
          "reports": {
              "conflicts": read(DATA / "reports" / "编号冲突检查报告.md"),
              "completeness": read(DATA / "reports" / "资料缺失与完整度报告.md"),
              "pending": read(DATA / "reports" / "待确认清单.md")},
          "gazetteers": {fn: read(DATA / "gazetteers" / fn) for fn in VIEWS.values()},
          }
    kb_json = jsafe(json.dumps(kb, ensure_ascii=False, separators=(",", ":")))
    beasts_json = jsafe(json.dumps(raw, ensure_ascii=False, separators=(",", ":")))
    b64 = base64.b64encode(pack_bytes).decode("ascii")

    def repl(mark_start, mark_end, body):
        nonlocal html_text
        a = html_text.find(mark_start)
        b = html_text.find(mark_end)
        if a < 0 or b < 0 or b <= a:
            raise RuntimeError("找不到数据岛标记：" + mark_start)
        html_text = html_text[:a + len(mark_start)] + "\n" + body + "\n" + html_text[b:]

    repl("<!-- KB:BEASTS:START -->", "<!-- KB:BEASTS:END -->",
         '<script type="application/json" id="beasts-json">' + beasts_json + '</script>')
    repl("<!-- KB:DATA:START -->", "<!-- KB:DATA:END -->",
         '<script type="application/json" id="kb-data">' + kb_json + '</script>')
    repl("<!-- KB:PACK:START -->", "<!-- KB:PACK:END -->",
         '<script type="text/plain" id="ai-pack-b64">' + b64 + '</script>')
    write(HTML_FILE, html_text)


POIS = {
    "garden": {"name": "云栖花园", "id": "LOC-101-0312", "desc": "7 栋六层砖混住宅，312 户，2003 年建成。3 号楼位于小区最北侧，602 在六层顶楼，阳台朝南可见云栖河。"},
    "school": {"name": "第二小学", "id": "LOC-101-0318", "desc": "育才路 26 号，1987 年建校，42 个班、1,980 名学生。距云栖花园约 1.0 km，步行约 13 分钟。"},
    "market": {"name": "云栖菜市场", "id": "LOC-101-0361", "idNote": "编号本轮拟定", "desc": "早市 5:30—11:00，晚市 16:00—19:30。小区居民买菜的主要去处，摊位沿云栖路内侧排开。"},
    "clinic": {"name": "北城社区医院", "id": "LOC-101-0330", "desc": "8:00—20:00，处理常见病、儿童保健与开窍初检；重症转西陵区中心医院。"},
    "office": {"name": "云栖街道办事处", "id": "LOC-101-0360", "idNote": "编号本轮拟定", "desc": "云栖路与育才路交叉口北侧，工作日办公；户籍、社保、租房备案都在这里办。"},
    "bridge": {"name": "云栖河人行桥", "id": "LOC-101-0362", "idNote": "编号本轮拟定", "desc": "跨云栖河的单跨人行桥，全天开放。过桥向南是江堤街道的旧码头与夜市。"},
    "bus": {"name": "“云栖花园”公交站", "id": "NODE-101-001", "idNote": "占位编号", "desc": "云栖路西侧，3 条线路停靠；早高峰 6:50—7:40 每 6—9 分钟一班。"},
}


# ----------------------------------------------------------------------------
# 七、文档模板
# ----------------------------------------------------------------------------
TPL_AI_START = """# AI_START_HERE · 衡垠世界知识库阅读入口

> 生成时间：__STAMP__ ｜ 版本：2.0.0 ｜ 本文件是给 AI 看的第一份文件，请先完整读完再回答任何问题。

## 0. 一句话说明

这是一个**静态资料包**：它由本地网站项目导出，供你（AI）在对话中读取。**你不具备联网访问用户电脑的能力**，用户把本包上传给你之后，你才能读到这些内容。任何"网站已经能被 AI 自动读取"的说法都是错误的。

## 1. 目录与读取顺序

| 顺序 | 文件 | 作用 |
|---|---|---|
| 1 | `AI_START_HERE.md` | 本文件：规则、口径、禁区 |
| 2 | `DATA_SCHEMA.md` | 字段含义、状态枚举、关系类型 |
| 3 | `manifest.json` | 版本、文件清单、统计与校验结果 |
| 4 | `world-index.json` | **所有实体的总索引**：先按名称／编号定位 |
| 5 | `entities/*.json` | 按类型保存的完整结构化记录 |
| 6 | `relationships.json` | 带关系类型的关联边 |
| 7 | `gazetteers/*.md` | 城市、城区、街道、小区、秘境的地方志正文（第一版网页原文转写） |
| 8 | `entities/beasts/O-B-*.md` | 十二种原创妖兽的二十节完整档案 |
| 9 | `rules/*.md` | 世界规则、蛊道规则、秘境与妖兽机制（导航式说明） |
| 10 | `sources/*.md` | 资料来源、版本、统计口径、未编号实体清单 |
| 11 | `reports/*.md` | 编号冲突、资料缺失、待确认、路由校验报告 |
| 12 | `AI_INTEGRATION_GUIDE.md` | 未来如何做实时接口（本阶段未实现） |

## 2. 回答问题时必须遵守的口径

1. **状态优先**：`status=existing` 才是原设定既有事实；`proposed` 是新增拟定／原创设定，**不得当作既定事实**；`uncertain` 必须说明未确认；`revised` 要看版本记录。回答时应带上状态，例如"临江市（existing）"或"界隙蛊（proposed，原创设定）"。
2. **完整度优先**：`coverage=full` 才有完整档案；`summary` 只有摘录／概要；`index` 只有编号与名称；`missing` 尚未建档。**禁止把只有索引的记录扩写成完整设定**。典型例子：C-B 37 条、R-B 40 条、C-K 447 条、CITY 59 座中除临江外的城市，都只有索引级资料。
3. **分区不可混**：C-G／C-K 是《蛊真人》原著；O-G／O-K／O-B 是本世界原创；C-B 是原著兽类；R-B 是**跨作品参考物种，不是本世界存在的物种**。绝不能把 R-B 写成衡垠世界的生物，也不能把原创写成原著。
4. **编号是主键**：所有引用用 `id`，不要用名称当主键；同一页面位置不同不产生新实体。父级关系用 `parent_id`，其他关系一律查 `relationships.json` 的带类型边。
5. **携带 ≠ 可控**：妖兽"携带蛊虫"只表示体表／体内存在，不等于能控制、能催动、能组杀招。O-G-110 界隙蛊是阈鹿体表的被动寄生野生仙蛊，阈鹿不可催动。
6. **数值不换算**：秘境 S／D／R／ST／DS 是五个独立维度，不能把 D 等级换算成蛊师转数；威胁等级同理。
7. **冲突并列保留**：`reports/编号冲突检查报告.md` 列出 C-01—C-08。遇到冲突，把两种记载并列说明，**不要自行选一个、不要调和、不要编造第三个值**。
8. **不补造**：CITY-039 缺失；未导入的杀招档案、未编号的组织、未建的城区页面，一律回答"资料包未载／尚未导入"，并指出应查哪个原始文件。
9. **来源可回溯**：每条实体记录的 `source` 字段给出文件名、版本、章节。回答重要结论时尽量给出编号＋来源文件名。

## 3. 快速判定表

| 用户问 | 先读 | 再读 |
|---|---|---|
| 某实体是什么 / 编号多少 / 属于哪类 | `world-index.json` | `entities/<category>.json` |
| 它在哪里 | 索引的 `parent_id` | `relationships.json` 的 `part_of`／`located_in` |
| 它和谁有关 | `relationships.json`（按 from/to 过滤） | 对应实体记录 |
| 它是不是已经确定的设定 | `status` 字段 | `reports/待确认清单.md` |
| 有没有完整档案 | `coverage` 字段 | `content_file` 指向的 md |
| 蛊虫／杀招规则 | `rules/03_蛊道规则.md` | 原始《蛊道资料库 v3.0》（不在包内，需另行提供） |
| 临江城市细节 | `gazetteers/CITY-101.md` | `gazetteers/DIST-101-03.md` → `LOC-101-0301.md` → `LOC-101-0312.md` |
| 妖兽生态 | `entities/beasts.json` | `entities/beasts/O-B-*.md` + `relationships.json` |
| 秘境 | `entities/realms.json` | `gazetteers/REALM-012.md` + `rules/04_秘境规则.md` |
| 哪些资料还缺 | `reports/资料缺失与完整度报告.md` | `reports/待确认清单.md` |

## 4. 三种能力不是一回事（务必区分）

| 能力 | 本阶段状态 |
|---|---|
| 本地网站浏览（人用浏览器打开 HTML） | ✅ 已实现，双击即可，不需要服务器 |
| 资料包导出后给 AI 读取 | ✅ 已实现（本 ZIP 就是导出结果） |
| 云端 AI 自动实时查询本地网站 / HTTP 接口 | ❌ **未实现**，见 `AI_INTEGRATION_GUIDE.md` |

**不要声称 ChatGPT、DeepSeek 等能自动访问用户本地网站。** 本地 `file://` 或 `localhost` 页面对云端 AI 不可见。

## 5. 跑团场景使用建议

先读 `rules/06_跑团参考.md` 与 `sources/02_统计口径.md`，把 `status=proposed` 的内容明确标成"拟定"，把 `coverage=index` 的内容只当名录使用；涉及数值时以原始资料编号为准，不自行推算。主持人提示词（`ll.txt` 等）**不在本资料包内**，需要时由用户另行提供。

---
本资料包由 `tools/build_kb.py` 从 `data/` 自动生成；网页与 ZIP 共用同一份数据源。
"""

TPL_AI_INTEG = """# AI_INTEGRATION_GUIDE · 未来 AI 接入指南（本阶段只做兼容设计）

> 生成时间：__STAMP__ ｜ 版本：2.0.0

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
"""

TPL_SCHEMA = """# DATA_SCHEMA · 衡垠世界知识库数据结构说明

> 生成时间：__STAMP__ ｜ 版本：2.0.0 ｜ 权威文件：`data/entities/*.json`

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
"""

TPL_README = """# 衡垠世界 AI 资料包 · README

> 生成时间：__STAMP__ ｜ 版本：2.0.0

这是给 AI 读取的静态资料包，**不是网站程序**。

- 人类看的网站：项目根目录的 `衡垠世界图集.html`（双击即可）或 `启动网站.bat`。
- AI 看的第一份文件：`AI_START_HERE.md`。
- 导入入口：`world-index.json`；关联：`relationships.json`；规则：`rules/`；地方志：`gazetteers/`；来源：`sources/`；缺口与冲突：`reports/`。

**纪律**：`status=proposed` 不是既定事实；`coverage=index` 不是完整档案；R-B 不是本世界物种；冲突并列保留、不调和、不编造。

本包与网页共用 `data/entities/*.json` 这一份数据源，由 `tools/build_kb.py` 生成。
"""

RULES = {
    "01_编号体系.md": """# 规则 · 编号体系

> __STAMP__ ｜ 依据：`01_最终版/现代蛊道世界_v1.0/00_世界观总目录.md` 第三节；`蛊道资料库_v3.0/00_总目录.md` 第二节；`00_工作区总导航.md` 第三节

| 前缀 | 含义 | 范围 |
|---|---|---|
| CONT | 大陆 | 001—006 |
| OCEAN | 海洋／内海 | 001—006 |
| NAT | 国家／政治实体 | 001—039 |
| ADM | 一级行政区 | 按国家段，如 ADM-101—109 |
| CITY | 城市 | 001—048 全球重点；101—108 曜川；201—299 赫兰；… |
| DIST | 城区 | `CITY 编号-两位序号`，如 DIST-101-03 |
| LOC | 重要地点／建筑 | 见 09、23 |
| REALM | 秘境 | 001—064 有名秘境；1XX-YYY 普通秘境 |
| C-G / C-K | 原著蛊虫 / 杀招 | 001—684 / 001—447 |
| O-G / O-K | 原创蛊虫 / 杀招 | 见原创两卷；O-G-110 为额外登记条目 |
| C-B / R-B / O-B | 原著兽类 / 参考物种 / 原创妖兽 | 001 起 |

**编号一经分配不得修改、重排、复用、回收；新增只能顺延追加。**
`PLANET-000`、`NODE-101-001` 为占位编号，非正式编号，见 `reports/待确认清单.md`。

本站不新增第十转，不改真元体系；完整规则以原始资料文件为准。
""",
    "02_状态与可信度.md": """# 规则 · 资料状态与可信度

> __STAMP__

## 知识库状态（本阶段统一）

| 状态 | 含义 | AI 使用方式 |
|---|---|---|
| `existing` | 原设定已有 | 可作既定事实 |
| `proposed` | 新增拟定／原创设定 | **不得当作既定事实**，须标注 |
| `uncertain` | 尚未确认 | 明确说明未确认 |
| `revised` | 经正式修订 | 看版本记录 |

## 完整度

`full` 完整档案｜`summary` 摘录／概要｜`index` 仅编号与名称｜`missing` 未建档。

## 原始资料可信度标记（沿用 v3.0）

【原著明确】【可靠资料佐证】【原著未明确】【存在争议】【合理推测】【待考证】【原创设定】。
两处设定互斥时**并列保留、标【存在争议】，不调和**；信息不足一律留空，不推测补全。

## 特别纪律

- 原著与原创严格分离；R-B 参考物种**不是本世界存在的物种**。
- 携带蛊虫 ≠ 能控制 ≠ 能催动 ≠ 能组杀招。
- 新增空间细节标【本轮新增拟定】，不能倒当成原始设定。
""",
    "03_蛊道规则.md": """# 规则 · 蛊道（导航式说明，非全文）

> __STAMP__ ｜ 权威全文：`01_最终版/蛊道资料库_v3.0/`（不在本资料包内，需另行提供）

- 浏览顺序：**转数优先、流派其次**。一转至九转为硬分层，同一转内按流派归类；十转存疑，本站不新增第十转。
- 蛊虫与杀招是两种对象：蛊虫有炼化、喂养、能力与缺点；杀招是蛊虫组合产生的整体效果，**不能把组成蛊虫的属性直接当成杀招描述**。
- 原著条目不得被原创覆盖；C-G 684 条、C-K 447 条、O-G 32 只＋O-G-110 登记条目、O-K 13 式，分区独立。
- O-G-110 界隙蛊：六转·宇道·野生仙蛊，被动寄生于 O-B-012 阈鹿体表，未被炼化、未被封印、妖兽不可催动；同名仙蛊天下唯一，以《仙蛊唯一性登记表》第四节为准。
- 临江把蛊师当「有证的技术工种」：全市登记蛊师 28.4 万、密度 2.4%，每年开窍约 1.4 万人、成功率 61%；GAB 办事处负责登记，交易市场负责交易，蛊坊街负责零售与小修（数据来自 09 号）。
- 缺失项显示「未知／待考证」，不擅自补全。

**查具体蛊虫／杀招**：`world-index.json` → `entities/gu.json`；完整档案请查 `蛊真人蛊虫合集_v3.0.md`、`原著杀招百科.md` 等原始文件。
""",
    "04_秘境规则.md": """# 规则 · 秘境（导航式说明）

> __STAMP__ ｜ 依据：`10_全球秘境总目录.md`、`11_秘境分级与评估体系.md`、本站秘境页

- 全球登记秘境 **4,180** 处；其中 **64 座有名秘境**逐条列名，其余为编号段批量登记（10 号）。临江市辖区 5 处：REALM-012、061—064。
- 规模 **S**／危险 **D**／资源 **R**／稳定性 **ST**／开发状态 **DS** 是独立维度：**不能把 D 等级直接换算成蛊师转数**；福地、洞天不是普通秘境的泛称。
- 秘境可以是城市基础设施的一部分：REALM-012 入口在中城区江堤路 9 号旧渠闸（LOC-101-0012），24 小时值守，市政把它记为「风险点」而不是「资源点」；由市政与 FRA 临江分局共管，科研与特许探索需预约、安检、登记装备，禁止携带未申报蛊虫。
- 溢流按黄／橙／红三级响应，红级全城警报；这套流程每年演练一次。
- 临江秘境服务企业 210 家、合计 6.4 万人就业；秘境服务养活 18% 就业（09 号）。

查具体秘境：`world-index.json` → `entities/realms.json` → `gazetteers/REALM-012.md`。
""",
    "05_妖兽与携蛊规则.md": """# 规则 · 妖兽与携蛊

> __STAMP__ ｜ 依据：`01_最终版/妖兽图鉴/` 十五份文件

- **三区隔离**：`C-B` 原著兽类｜`R-B` 跨作品参考物种（**不是本世界存在的物种**）｜`O-B` 本世界原创妖兽。
- O-B 001—012 十二种各有二十节完整档案，已全量导入本知识库；C-B 37 条、R-B 40 条**只有索引级记录**。
- **携带蛊虫 ≠ 能控制 ≠ 能催动 ≠ 能组杀招**。原著「兽王身上都会有一两只蛊虫寄生」等是个例描述，不得扩大成所有妖兽的固定规律。
- O-B-001 檐鸮对 REALM-012 只有**偶入记录**，不判定为该秘境或云栖花园的现存物种。
- 威胁等级按原文显示，**不换算成蛊师转数**；分布只写区域，不虚构坐标。
- 生态关系（捕食／共生／竞争等 36 条）见 `relationships.json`，来源于《妖兽分类与生态体系》§7.1。

查具体妖兽：`entities/beasts.json` → `entities/beasts/O-B-*.md`。
""",
    "06_跑团参考.md": """# 规则 · 跑团使用参考

> __STAMP__

1. **主持人提示词不在本资料包内**：`ll.txt` 等跑团主持人文件属另一套交付物，需要时由用户另行提供。本包只提供世界观资料。
2. 使用前先读 `AI_START_HERE.md` 与 `sources/02_统计口径.md`。
3. 描述场景时：只把 `status=existing` 当既定事实；`proposed` 明确标注为拟定；`coverage=index` 的实体只可作名录，不要扩写设定。
4. 数值冲突（C-01—C-08）并列保留，不自行选值；"59 / 声明 60"、「1,050 万 vs 1,064 万」照原样呈现。
5. 从地图进地点、从地点进组织／妖兽／秘境：用 `parent_id` 与 `relationships.json` 的边，不要靠名称猜。
6. 未导入资料（C-K 完整档案、组织档案、历史事件、人物关系）一律回答「资料包未载」，不要编造。
7. 本站不新增历史事件、人物、案件或蛊师活动；小说式文字只是对既有事实的呈现。
""",
}

SOURCES = {
    "00_来源总表.md": """# 资料来源总表

> __STAMP__ ｜ 版本：2.0.0

## 一、正式资料源（只读，位于工作区 `01_最终版/`）

| 目录 | 文件 | 提供的内容 | 本站用法 |
|---|---|---|---|
| `现代蛊道世界_v1.0/` | 00 总目录、01 基础设定、02 地理、03 坐标、04 国家、07 城市、09 临江、10 秘境、11 分级、27/28/36 空间与审计 | 行星、大陆、海洋、国家、城市、城区、街道、地点、秘境与统计数字 | 抽取索引与属性；编号原样沿用 |
| `蛊道资料库_v3.0/` | 蛊真人蛊虫合集 v3.0、原著杀招百科、原创两卷、关联索引、总目录 | C-G 684、C-K 447、O-G 32、O-K 13 | 抽取编号＋名称／摘录；**完整档案未导入** |
| `妖兽图鉴/` | 原创妖兽图鉴 v1.1、原著兽类图鉴、跨作品妖兽参考库、分类与生态体系、仙蛊唯一性登记表等 | O-B 12 种二十节、C-B 37、R-B 40、生态关系 36 条、O-G-110 | O-B 全量；C-B／R-B 仅索引 |
| 第一版网页 | `衡垠世界图集.html` | 九个静态页面正文、7 个地图 POI、36 条实体索引、生灵图鉴数据岛 | 地方志转写为 Markdown；POI 与实体 ID 统一 |

## 二、第一版已有页面（正文保留）

`#/` 首页、`#/world` 世界、`#/linjiang` 临江市、`#/beicheng` 北城区、`#/yunqi` 云栖街道、`#/garden` 云栖花园、`#/gu` 蛊道、`#/beasts`＋`#/beast/<num>` 生灵、`#/realms` 秘境、`#/status` 建设状态。

## 三、本阶段新增页面

`#/entities` 实体总索引、`#/entity/<id>` 统一实体档案、`#/export` 资料导出与数据报告。

## 四、版本

| 项 | 版本 |
|---|---|
| 世界观资料 | v1.0（2026-11-13） |
| 蛊道资料库 | v3.0 |
| 妖兽图鉴 | v1.1（十二种齐备） |
| 第一版网站 | v1.0 ＋ 生灵图鉴接入 |
| 本知识库 | 2.0.0 |

## 五、不在本资料包内的原始文件

`蛊真人蛊虫合集_v3.0.md` 正文、`原著杀招百科.md` 全文、A 级 36 份完整十节档案、B 级 409 条简档、C-B 完整档案、`ll.txt` 主持人提示词、20 号历史年表全文、17 号制度全文等，均**未复制进包**。需要时由用户另行提供。
""",
    "01_版本与状态.md": """# 资料版本与状态说明

> __STAMP__

## 状态定义

`existing` 原设定已有｜`proposed` 新增拟定（含原创设定）｜`uncertain` 尚未确认｜`revised` 经正式修订。

## 本阶段做了什么 / 没做什么

- 做了：把第一版网页与 `01_最终版/` 的**编号、名称、表格字段、页面正文**抽取进统一数据层；给每个实体补状态、完整度、来源；建立带类型的关联；生成可导出的 AI 资料包。
- 没做：没有改写任何原始资料文件；没有重排编号；没有补造 CITY-039；没有把索引级资料冒充完整档案；没有导入未提供的完整杀招／组织／历史档案；没有接入任何付费服务。

## 第一版网页原有标识对照

| 第一版标识 | 本知识库 |
|---|---|
| 「原设定已有／原设定锁定」 | `status=existing` |
| 「本轮新增拟定」 | `status=proposed` |
| 「待核对」 | `status=uncertain` |
| 「框架＋样例／未接入」 | `coverage=index` 或 `missing`，并在完整度报告中列出 |

## 修订记录

见项目根目录 `本次修改记录.md`。
""",
    "02_统计口径.md": """# 统计口径与数字来源

> __STAMP__ ｜ **所有数字来自原始资料，本站不自行编造或调和一个值**

| 数字 | 含义 | 来源 | 备注 |
|---|---|---|---|
| 6 | 大陆 | 02 号 | 另有 6 片海洋／内海 |
| 39 | 政治实体 | 04 号 | S 4／A 6／B 14／C 10／D 5 |
| 81.2 亿 | 全球人口 | 01 号（垠历 742 年统计）／00 号 | 六大陆 76.0 亿＋岛屿 5.2 亿 |
| 59 / 声明 60 | 已登记核心城市 / 07 号声明 | 07 号、36 号 C-01 | **缺 CITY-039，不补造**（C-01） |
| 4,180 | 全球登记秘境 | 10 号（以此为准） | 已勘探 1,240、已开发 610 |
| 64 | 有名秘境逐条列名 | 10 号 | 临江 5 处：012、061—064 |
| 1,180 万 | 临江市域人口 | 09 号 | 七城区 1,064 万＋辖县 116 万 |
| 1,064 万 / 1,050 万 | 七城区合计 / 864＋186 | 09 号 | **差 14 万，口径差，不调和**（C-02） |
| 8,240 / 1,186 km² | 行政区面积 / 建成区 | 09 号 | 密度比较只能用城区面积作分母 |
| 28.4 万 / 2.4% | 登记蛊师 / 密度 | 09 号 | 每年开窍约 1.4 万人、成功率 61% |
| 684 / 447 / 32 / 13 | C-G / C-K / O-G / O-K | 蛊道资料库 v3.0 总目录 | 合计 **1,176** |
| 1,176 / 5 / 4 / 1,172 | 蛊道总目 / 网页展示条数 / 属于总目的展示条数 / 未接入 | v3.0 总目录＋仙蛊唯一性登记表 | 第 5 条 O-G-110 是额外登记条目，**不计入 32**（C-05） |
| 12 / 37 / 40 | O-B / C-B / R-B | 妖兽图鉴总目录 | O-B 十二种二十节档案齐备；C-B／R-B 仅索引 |
| 36 | 生态关系条数 | 妖兽分类与生态体系 §7.1 | 另有 8 类线型 |

## 冲突清单

见 `reports/编号冲突检查报告.md`（C-01—C-08）与 `reports/待确认清单.md`。

## 口径纪律

1. 冲突并列保留、标注，不改原值、不造第三个值。
2. 网站统计与资料包统计都从 `manifest.json`／`world-index.json` 计算，不在多个页面手写同一数字。
3. 第一版页面里「已接入 4 条」与「列出 5 条」的表述差异，按 C-05 说明，页面原文保留但补口径说明。
""",
    "03_资料状态说明.md": """# 资料状态说明（给 AI 的口径）

> __STAMP__

- `status=proposed` 的实体包括：**全部 O-G／O-K／O-B 原创内容**、C-04 改挂的 0360—0362、NODE-101-001、PLANET-000、C-03 补名的城区等。它们不是原设定既有事实。
- `status=existing` 的实体也可能只有 `coverage=index`：**状态与完整度是两个独立维度**，不要因为「原设定已有」就认为资料包里有完整档案。
- `coverage=full` 目前只有：四页地方志、REALM-012、O-B 十二种、以及网页展示的 5 条蛊虫条目。
- 原始资料互相冲突时，本站按「并列保留＋标注」处理，见 C-01—C-08；AI 回答同样应并列，不要替用户裁定。
""",
    "04_未编号实体清单.md": """# 未编号实体清单（尚未建实体记录）

> __STAMP__ ｜ 以下对象在原始资料或网页中出现，但**没有正式编号**；本站没有为它们自造专名或编号，故未进入 `world-index.json`。

## 一、09 号 §11 主要势力（11 个，仅 2 个有编号）

| 名称 | 类型 | 说明 | 处理 |
|---|---|---|---|
| 临江市政府 | 政府 | 市长直选；城建、教育、治安 | 未编号 |
| 澜东州第二行政督察区 | 州派出 | 监督市级财政与秘境许可 | 未编号 |
| GAB 临江办事处 | 联邦派出 | 蛊师登记、禁制蛊稽查 | **编号存在双记载**（0004 / 0104），见 C-06 |
| FRA 临江分局 | 联邦派出 | 秘境监测与应急；REALM-012 共管 | 未编号 |
| 临江炼蛊集团 | 国企 | 4.2 万人；凡蛊量产、蛊具 | 已登记 ORG-016 |
| 澜东电子 | 民营上市 | 2.8 万人；蛊道监测仪器 | 未编号 |
| 临江港务集团 | 国企 | 1.6 万人；港口与保税 | 已登记 ORG-017 |
| 云栖物业 | 本地小企业 | 管理云栖花园等 11 个老小区 | 未编号 |
| 秘境服务企业 210 家 | 民营 | 向导、装备、培训、保险代理 | 群体，未编号 |
| 「三号码头」 | 非官方 | 元石与禁制蛊走私网络（规模未证实） | 未编号 |
| 北城蛊坊街商户联合会 | 行业组织 | 小作坊、维修、零售 | 未编号 |

## 二、云栖街道八个社区（第一版标【本轮新增拟定】）

云栖新村、花园里、育才坊、河西湾、桥北口、老街口、屏岭脚、河口。合计 42 万人口，属制图所需空间标签，**不替代 LOC 编号**；待用户确认后再分配编号（Q-06）。

## 三、其他未编号空间与设施

云栖路、育才路、云栖河、江堤夜市、北城老面馆、江东新区、旧排水渠、地铁 1 号线等，均为正文中的描述性名称；本阶段未建实体。

## 四、尚未迁移的资料块

20 号历史大事年表（事件）、17 号蛊师社会与制度（制度链）、18 号全球经济、19 号交通通信、人物与社会关系、跑团主持人提示词。以上**只有原始文件，未导入知识库**。
""",
}


# ----------------------------------------------------------------------------
# 八、主流程
# ----------------------------------------------------------------------------
def main():
    sync_only = "--sync" in sys.argv
    if not sync_only:
        print("[1/7] 抽取原始资料 → data/entities/")
        ents, raw = build_entities()
        print("      实体数：", len(ents))
        extract_views()
        ensure_docs()
    else:
        print("[1/7] --sync：直接读取现有 data/entities/")
        ents, raw = [], json.loads(read(ENT / "beasts_render.json"))
        for p in sorted(ENT.glob("*.json")):
            if p.name in ("beasts_render.json", "beasts_relations.json"):
                continue
            o = json.loads(read(p))
            if isinstance(o, dict) and "entities" in o:
                ents += o["entities"]
        ensure_docs()
    print("[2/7] 生成 relationships.json")
    rels = build_relations(ents, raw)
    print("      关系数：", rels["count"])
    print("[3/7] 校验并生成 reports/")
    au = audit(ents, rels)
    stats = write_reports(ents, rels, au)
    print("      重复编号/无效路由/悬空关联：", len(au["dups"]), len(au["bad_links"]), len(au["dangling_rel"]))
    print("[4/7] 回写实体分卷并生成 world-index.json / manifest.json")
    groups = {}
    for e in ents:
        groups.setdefault(e["category"], []).append(e)
    names = {"geography": "geography", "gu": "gu", "beast": "beasts", "realm": "realms", "organization": "organizations"}
    for cat, arr in groups.items():
        arr.sort(key=lambda x: x["id"])
        jwrite(ENT / (names.get(cat, cat) + ".json"), {"schema": "hengyin/entities/1.0", "category": cat, "count": len(arr), "entities": arr})
    w, manifest, files = build_index_and_manifest(ents, rels, stats, au)
    print("      索引条目：", len(w["entities"]), " 文件数：", len(files))
    print("[5/7] 生成 衡垠AI资料包.zip")
    size = build_pack(files + [{"path": "manifest.json"}])
    print("      ZIP 大小：", size, "bytes")
    print("[6/7] 注入网页数据岛")
    s = read(HTML_FILE)
    inject(s, ents, rels, w, manifest, PACK.read_bytes(), raw)
    print("[7/7] 完成：", STAMP)
    print("  → data/world-index.json / data/relationships.json / data/reports/*.md")
    print("  → 衡垠AI资料包.zip / 衡垠世界图集.html（数据岛已同步）")


if __name__ == "__main__":
    main()
