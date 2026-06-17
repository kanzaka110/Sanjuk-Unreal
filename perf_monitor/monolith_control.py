"""Monolith 콘솔 명령으로 CSV Profiler 제어.

scripts/monolith_helpers.MonolithClient 를 재활용한다. 에디터(PIE) 에서 CSV Profiler 를
켜고/끄는 콘솔 명령을 editor.run_console_command 로 송신한다.

엔진 C++ 수정 없음. SB2 licensee 빌드에 csvprofile 명령이 살아있어야 한다
(없으면 start() 가 MonolithError 또는 무반응 → ping_csv_dir 로 산출물 확인).
"""
from __future__ import annotations

import os
import sys

# scripts/monolith_helpers 재사용
_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from monolith_helpers import MonolithClient, MonolithError  # noqa: E402


# CSV Profiler 의 stat 카테고리. 필요한 도메인만 켜 토큰/오버헤드 절감.
DEFAULT_CATEGORIES: tuple[str, ...] = (
    "Basic", "FrameTime", "Animation", "Physics", "Cloth", "Memory",
)


class ProfilerControl:
    """CSV Profiler start/stop wrapper. asset 불필요 → 더미 경로로 클라이언트 생성."""

    def __init__(self, endpoint: str) -> None:
        # editor_query 는 asset_path 를 안 쓰지만 MonolithClient 는 asset 필수.
        self._cli = MonolithClient(asset="/Engine/Transient", endpoint=endpoint)

    def _cmd(self, command: str) -> object:
        return self._cli.editor("run_console_command", command=command)

    def set_categories(self, categories: tuple[str, ...] = DEFAULT_CATEGORIES) -> None:
        """캡처 stat 카테고리 설정 (세션당 1회면 충분)."""
        self._cmd(f"csv.Categories {','.join(categories)}")

    def start(self) -> str:
        """CSV Profiler 캡처 시작. (회전 캡처에서 매 사이클 호출)

        ContinuousWrites 는 쓰지 않는다 — UE 가 캡처 중 파일을 배타 잠금해 tail 이
        불가하고, stop 시 버퍼 전체가 flush 되므로 짧은 캡처도 모든 프레임을 담는다.
        """
        self._cmd("CsvProfile start")
        return "CsvProfile start"

    def stop(self) -> str:
        self._cmd("CsvProfile stop")
        return "CsvProfile stop"

    def probe(self) -> tuple[bool, str]:
        """csvprofile 명령이 먹는지 가볍게 확인. (성공여부, 메시지)."""
        try:
            self._cmd("CsvProfile stop")  # 안 돌고 있으면 no-op, 크래시 X
            return True, "run_console_command 응답 OK (csvprofile 송신됨)"
        except MonolithError as e:
            return False, f"Monolith 오류: {e}"
        except Exception as e:  # 연결 실패 등
            return False, f"연결 실패: {type(e).__name__}: {e}"
