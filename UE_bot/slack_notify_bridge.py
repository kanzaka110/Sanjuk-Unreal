"""Slack 전송 모듈을 다른 저장소에서 끌어온다.

세 브리핑 봇(언리얼/게임뉴스/운세)이 같은 전송 계층을 쓴다. 그 원본은
Sanjuk-Notion-Telegram-Bot 저장소의 Slack_bot/slack_notify.py 하나뿐이다.
전송 로직을 저장소마다 복사하면 Slack API가 바뀔 때 세 군데를 고쳐야 한다.

경로는 SANJUK_BOT_REPO로 덮어쓸 수 있다. 저장소를 옮기면 그 환경변수만
바꾸면 된다.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(os.getenv(
    "SANJUK_BOT_REPO",
    str(Path.home() / "Sanjuk-Notion-Telegram-Bot"),
))

if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

try:
    from Slack_bot.slack_notify import send_slack, telegram_html_to_mrkdwn
except ImportError as exc:      # 경로가 틀리면 조용히 실패하지 말고 이유를 말한다
    raise ImportError(
        f"Slack 전송 모듈을 찾지 못했다: {_REPO}/Slack_bot/slack_notify.py\n"
        f"저장소가 다른 곳에 있으면 SANJUK_BOT_REPO 환경변수로 지정해라."
    ) from exc

__all__ = ["send_slack", "telegram_html_to_mrkdwn"]
