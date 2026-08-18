"""언리얼 브리핑 Slack 전송.

briefing_telegram을 대체한다. 반환 계약은 그대로:
{"success", "reason_code", "attempts"} → record_delivery(**delivery)

전송 자체는 Slack_bot.slack_notify가 담당한다 (세 브리핑 봇이 공유).
그 모듈은 Sanjuk-Notion-Telegram-Bot 저장소에 있으므로 실행 래퍼가
PYTHONPATH로 잡아준다 — run_ue_briefing.sh 참고.
"""

from __future__ import annotations

from datetime import date

from slack_notify_bridge import send_slack


def format_briefing(results: list[dict], *, notion_db_id: str) -> str:
    """브리핑 결과를 Slack 본문으로. 링크는 <url|라벨> 형식이다."""
    lines: list[str] = []

    for r in results:
        cat = r.get("category", "")
        title = r.get("title", "")
        difficulty = r.get("difficulty", "")
        version = r.get("version", "")
        summary = (r.get("summary") or "")[:120]
        url = r.get("url", "")

        meta = " | ".join(x for x in (f"UE {version}" if version else "",
                                      difficulty) if x)
        lines.append(f"📂 *{cat}*" + (f"  {meta}" if meta else ""))
        lines.append(f"▸ <{url}|{title}>" if url else f"▸ {title}")
        if summary:
            lines.append(f"   {summary}")
        lines.append("")

    if not results:
        lines.append("오늘 새로운 업데이트가 없습니다.")
        lines.append("")

    notion_url = f"https://notion.so/{notion_db_id.replace('-', '')}"
    lines.append(f"📋 <{notion_url}|Notion에서 보기>")
    return "\n".join(lines)


def send_briefing(
    results: list[dict],
    *,
    channel: str,
    notion_db_id: str,
    token: str = "",
) -> dict[str, object]:
    today = date.today().strftime("%Y.%m.%d")
    header = f"🎮 *언리얼 튜토리얼 가이드 비서*\n{today} 업데이트"
    body = format_briefing(results, notion_db_id=notion_db_id)

    delivery = send_slack(body, channel=channel, header=header, token=token)
    print("  ✅ Slack 전송 완료" if delivery["success"]
          else f"  ⚠️ Slack 전송 실패: {delivery['reason_code']}")
    return delivery
