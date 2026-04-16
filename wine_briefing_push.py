#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
葡萄酒行业简报 · 飞书推送脚本
每日自动将 wine-briefing.html 的简报内容以卡片消息推送到飞书
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# ─── 配置 ───────────────────────────────────────────────
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/bdac50b2-eec3-48f3-a58e-870373388c9e"
BRIEFING_FILE = Path(__file__).parent / "wine-briefing.html"
# ────────────────────────────────────────────────────────


def extract_briefing_content(html_path: Path) -> dict:
    """从 HTML 简报中提取各模块核心内容"""
    if not html_path.exists():
        return {"error": "简报文件不存在"}

    content = html_path.read_text(encoding="utf-8")

    # 先把 <style> 和 <script> 块整体剔除，避免 CSS/JS 代码被当文字抓取
    content_clean = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content_clean = re.sub(r'<script[^>]*>.*?</script>', '', content_clean, flags=re.DOTALL | re.IGNORECASE)

    # 提取期数和日期（从 header date 行）
    issue_match = re.search(r'第(\S+?)期[^<·]*·\s*([\d年月日\w（）·\s]+)', content_clean)
    issue_info = issue_match.group(0).strip() if issue_match else datetime.now().strftime("%Y年%m月%d日")
    # 截断太长的 issue_info
    if len(issue_info) > 30:
        issue_info = issue_info[:30]

    def strip_tags(text):
        """去除所有 HTML 标签，合并空白"""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'&[a-zA-Z]+;', '', text)   # 去除 HTML 实体
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # 提取所有卡片标题和摘要
    cards = []
    card_blocks = re.findall(
        r'<div class="card-name">(.*?)</div>.*?<div class="card-body">(.*?)</div>',
        content_clean, re.DOTALL
    )
    for name, body in card_blocks:
        name_clean = strip_tags(name)
        body_clean = strip_tags(body)
        if len(body_clean) > 85:
            body_clean = body_clean[:85] + "…"
        if name_clean:
            cards.append({"name": name_clean, "summary": body_clean})

    return {"issue_info": issue_info, "cards": cards}


def build_feishu_card(data: dict) -> dict:
    """构建飞书消息卡片 JSON"""
    today = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    cards = data.get("cards", [])
    issue_info = data.get("issue_info", today)

    # 把卡片内容分成三组（App / 教育 / 行业）
    # 按顺序：前4条=App，接下来3条=教育，最后4条=行业
    app_cards    = cards[0:4]   if len(cards) > 3 else cards
    edu_cards    = cards[4:7]   if len(cards) > 6 else []
    news_cards   = cards[7:11]  if len(cards) > 10 else (cards[7:] if len(cards) > 7 else [])

    def fmt_section(items):
        if not items:
            return "暂无动态"
        lines = []
        for item in items:
            lines.append(f"**· {item['name']}**\n  {item['summary']}")
        return "\n\n".join(lines)

    elements = [
        # 副标题
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"📅 {issue_info}　|　App动态 · 教育资讯 · 行业要闻"
            }
        },
        {"tag": "hr"},

        # Module 1: App
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**📱 核心 App 更新动态**\n\n{fmt_section(app_cards)}"
            }
        },
        {"tag": "hr"},

        # Module 2: 教育
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**🎓 学习 & 教育工具资讯**\n\n{fmt_section(edu_cards) if edu_cards else '暂无动态'}"
            }
        },
        {"tag": "hr"},

        # Module 3: 行业新闻
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**📰 葡萄酒行业重要新闻**\n\n{fmt_section(news_cards) if news_cards else '暂无动态'}"
            }
        },
        {"tag": "hr"},

        # 底部按钮
        {
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "📄 查看完整简报"},
                    "type": "primary",
                    "url": "https://andiloswang.github.io/wine-briefing/"
                }
            ]
        },
        {
            "tag": "note",
            "elements": [
                {"tag": "plain_text", "content": f"🤖 WorkBuddy 自动推送 · {today} · 信息时效 ≤72h"}
            ]
        }
    ]

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "🍷 葡萄酒行业简报"
            },
            "template": "red"
        },
        "elements": elements
    }

    return {"msg_type": "interactive", "card": card}


def push_to_feishu(payload: dict) -> bool:
    """发送消息到飞书"""
    try:
        resp = requests.post(
            WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=15
        )
        result = resp.json()
        if result.get("code") == 0:
            print(f"✅ 飞书推送成功：{datetime.now().strftime('%H:%M:%S')}")
            return True
        else:
            print(f"❌ 飞书推送失败：{result}")
            return False
    except Exception as e:
        print(f"❌ 推送异常：{e}")
        return False


def sync_to_github():
    """将最新 HTML 同步到 GitHub Pages"""
    import subprocess
    repo_dir = Path(__file__).parent
    try:
        # 复制为 index.html（GitHub Pages 默认入口）
        import shutil
        shutil.copy(repo_dir / "wine-briefing.html", repo_dir / "index.html")

        subprocess.run(["git", "-C", str(repo_dir), "add", "index.html", "wine-briefing.html"],
                       check=True, capture_output=True)
        result = subprocess.run(["git", "-C", str(repo_dir), "diff", "--cached", "--stat"],
                                capture_output=True, text=True)
        if not result.stdout.strip():
            print("📋 GitHub Pages：无变更，跳过推送")
            return
        date_str = datetime.now().strftime("%Y-%m-%d")
        subprocess.run(["git", "-C", str(repo_dir), "commit", "-m", f"update: 简报更新 {date_str}"],
                       check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo_dir), "push", "origin", "main"],
                       check=True, capture_output=True)
        print("✅ GitHub Pages 同步成功")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  GitHub Pages 同步失败（不影响飞书推送）：{e}")


def main():
    print(f"📤 开始推送葡萄酒简报到飞书 [{datetime.now().strftime('%Y-%m-%d %H:%M')}]")

    # 同步最新 HTML 到 GitHub Pages
    sync_to_github()

    # 提取简报内容
    data = extract_briefing_content(BRIEFING_FILE)
    if "error" in data:
        print(f"⚠️  {data['error']}，将推送占位消息")
        data = {"issue_info": datetime.now().strftime("%Y年%m月%d日"), "cards": []}

    # 构建并发送卡片
    payload = build_feishu_card(data)
    push_to_feishu(payload)


if __name__ == "__main__":
    main()
