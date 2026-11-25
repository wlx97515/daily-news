#!/usr/bin/env python3
"""每天抓取中新网滚动新闻，筛出与日常生活相关的条目，写入 data.json。"""
import json
import re
import sys
import datetime
import urllib.request

BASE = "https://www.chinanews.com.cn/scroll-news/news{n}.html"

# 只保留民生类频道，避开时政、国际、军事、体育、娱乐
CAT_OK = {"健康", "社会", "财经", "生活", "教育", "科技", "地方", "图片"}

KEYWORDS = [
    "价格", "物价", "油价", "电价", "气价", "菜价", "肉价", "粮价", "药价",
    "医保", "社保", "养老", "退休", "工资", "薪酬", "就业", "招聘", "失业",
    "补贴", "低保", "公积金", "住房", "租房", "房贷", "学位", "幼儿园", "托育",
    "高考", "开学", "医院", "看病", "药品", "疫苗", "食品安全", "外卖", "快递",
    "消费", "退货", "退款", "地铁", "公交", "铁路", "火车", "航班", "机票",
    "天气", "气温", "寒潮", "暴雨", "台风", "干旱", "水质", "空气", "充电",
    "停车", "燃气", "供热", "供暖", "水费", "电费", "残疾", "救助", "生育",
    "育儿", "假期", "加班", "欠薪", "消费者", "抽检", "召回",
]

ITEM_RE = re.compile(
    r'<li><div class="dd_lm">\[<a href=[^>]*>(?P<cat>.*?)</a>\]</div>'
    r' <div class="dd_bt"><a href="(?P<href>.*?)">(?P<title>.*?)</a></div>'
    r'<div class="dd_time">(?P<time>.*?)</div></li>'
)

TAG_RE = re.compile(r"<[^>]+>")


def clean(s: str) -> str:
    return TAG_RE.sub("", s).replace("&amp;", "&").strip()


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read()
    return raw.decode("utf-8", "ignore")


def main() -> int:
    items, seen = [], set()
    for page in (1, 2):
        try:
            html_text = fetch(BASE.format(n=page))
        except Exception as e:  # 网络波动时跳过该页
            print(f"page {page} failed: {e}", file=sys.stderr)
            continue

        for m in ITEM_RE.finditer(html_text):
            cat = clean(m.group("cat"))
            title = clean(m.group("title"))
            href = m.group("href").strip()
            t = clean(m.group("time"))
            if cat not in CAT_OK or not title or title in seen:
                continue
            if not any(k in title for k in KEYWORDS):
                continue
            if href.startswith("/"):
                href = "https://www.chinanews.com.cn" + href
            seen.add(title)
            items.append({"title": title, "url": href, "source": "中新网·" + cat, "time": t})

    if len(items) < 4:
        # 关键词命中太少时，退一步只按频道筛选，保证栏目不空
        for page in (1, 2):
            try:
                html_text = fetch(BASE.format(n=page))
            except Exception:
                continue
            for m in ITEM_RE.finditer(html_text):
                cat = clean(m.group("cat"))
                title = clean(m.group("title"))
                href = m.group("href").strip()
                t = clean(m.group("time"))
                if cat not in {"健康", "社会", "生活", "教育"} or not title or title in seen:
                    continue
                if href.startswith("/"):
                    href = "https://www.chinanews.com.cn" + href
                seen.add(title)
                items.append({"title": title, "url": href, "source": "中新网·" + cat, "time": t})

    items = items[:12]
    if not items:
        print("no items fetched, keep previous data.json", file=sys.stderr)
        return 0

    payload = {
        "updated": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
        .replace(microsecond=0).isoformat(),
        "source": "中国新闻网 滚动新闻",
        "items": items,
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(items)} items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
