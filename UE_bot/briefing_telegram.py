"""텔레그램 알림 전송."""

from __future__ import annotations

import requests
from datetime import date

from briefing_config import CATEGORIES


NOTION_DATABASE_ID = ""  # run_briefing에서 주입


def send_telegram(
    results: list[dict],
    *,
    bot_token: str,
    chat_id: str,
    notion_db_id: str,
) -> dict[str, object]:
    """브리핑 결과를 텔레그램으로 전송."""
    if not bot_token or not chat_id:
        return {"success": False, "reason_code": "telegram_config_missing", "attempts": 0}

    today = date.today().strftime("%Y.%m.%d")
    msg = f"🎮 언리얼 튜토리얼 가이드 비서\n{today} 업데이트\n\n"

    for r in results:
        cat = r.get("category", "")
        title = r.get("title", "")
        difficulty = r.get("difficulty", "")
        version = r.get("version", "")
        summary = r.get("summary", "")[:120]
        url = r.get("url", "")

        msg += f"📂 {cat}"
        if version:
            msg += f" | UE {version}"
        if difficulty:
            msg += f" | {difficulty}"
        msg += f"\n▸ {title}\n"
        if summary:
            msg += f"  {summary}\n"
        if url:
            msg += f"  🔗 {url}\n"
        msg += "\n"

    if not results:
        msg += "오늘 새로운 업데이트가 없습니다.\n"

    msg += f"📋 Notion: https://notion.so/{notion_db_id.replace('-', '')}"

    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "disable_web_page_preview": True,
    }
    try:
        res = requests.post(api_url, json=payload, timeout=30)
        api_ok = True
        try:
            body = res.json()
            api_ok = not isinstance(body, dict) or body.get("ok") is not False
        except Exception:
            api_ok = True
        if res.status_code == 200 and api_ok:
            print("  ✅ 텔레그램 전송 완료")
            return {"success": True, "reason_code": "", "attempts": 1}
        else:
            print(f"  ⚠️ 텔레그램 전송 실패: {res.status_code}")
            return {"success": False, "reason_code": "telegram_http_failed", "attempts": 1}
    except Exception as exc:
        print(f"  ⚠️ 텔레그램 전송 오류: {type(exc).__name__}")
        return {"success": False, "reason_code": "telegram_transport_failed", "attempts": 1}
