"""PerfMonitor 설정 + 메트릭 매핑.

SB2 CSV Profiler 출력 컬럼명은 빌드마다 다를 수 있어, 메트릭 1개당 후보 컬럼을
여러 개 두고 헤더에서 처음 매칭되는 것을 채택한다 (csv_source.resolve_columns).
하드코딩 대신 환경변수로 경로/포트를 override 할 수 있다.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field, replace


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default).strip() or default


@dataclass(frozen=True)
class Metric:
    """대시보드에 표시할 한 수치의 정의."""

    key: str                      # 내부 식별자 (SSE payload 키)
    label: str                    # 화면 표시명
    unit: str                     # ms / MB / fps
    candidates: tuple[str, ...]   # CSV 헤더에서 찾을 후보 컬럼명 (앞이 우선)
    warn: float | None = None     # 이 값 이상이면 주황
    crit: float | None = None     # 이 값 이상이면 빨강
    group: str = "general"        # 카드 그룹 (frame/anim/physics/memory)

    def status(self, value: float | None) -> str:
        if value is None:
            return "na"
        if self.crit is not None and value >= self.crit:
            return "crit"
        if self.warn is not None and value >= self.warn:
            return "warn"
        return "ok"


# ✅ 실측 2026-06-17 (SB2 5.7.4, Profile(...).csv 289컬럼 헤더 기준).
# 60fps = 16.6ms, 30fps = 33.3ms. anim/physics ms 임계는 보수적 가설값(⚠ 미검증).
DEFAULT_METRICS: tuple[Metric, ...] = (
    # ── 프레임 / GPU ────────────────────────────────────────────────
    Metric("frame_ms", "Frame", "ms", ("FrameTime",), 16.6, 33.3, "frame"),
    Metric("game_ms", "Game Thread", "ms", ("GameThreadTime",), 16.6, 33.3, "frame"),
    Metric("render_ms", "Render Thread", "ms", ("RenderThreadTime",), 16.6, 33.3, "frame"),
    Metric("gpu_ms", "GPU", "ms", ("GPUTime",), 16.6, 33.3, "frame"),
    Metric("draws", "Draw Calls", "", ("RHI/DrawCalls",), None, None, "frame"),
    # ── 애니메이션 평가 (GameThread 틱 비용) ─────────────────────────
    Metric(
        "anim_ms", "Animation (GT)", "ms",
        ("Exclusive/GameThread/Animation", "Animation/Total", "Animation"),
        3.0, 6.0, "anim",
    ),
    Metric(
        "skelmesh_tk", "SkelMesh 틱", "개",
        ("Ticks/SBCharacterSkeletalMeshComponent", "Ticks/SkeletalMeshComponent"),
        None, None, "anim",
    ),
    # ── 물리 / 시뮬 ─────────────────────────────────────────────────
    Metric(
        "physics_ms", "Physics (GT)", "ms",
        ("Exclusive/GameThread/Physics", "Physics/Total", "Physics"),
        4.0, 8.0, "physics",
    ),
    Metric(
        "physics_par_ms", "Physics (Workers)", "ms",
        ("Exclusive/AllWorkers/Physics",), 4.0, 8.0, "physics",
    ),
    Metric(
        "cloth_tk", "Cloth 틱", "개",
        ("Ticks/SBChaosClothComponent",), None, None, "physics",
    ),
    Metric(
        "groom_tk", "Groom 틱", "개",
        ("Ticks/SBGroomComponent",), None, None, "physics",
    ),
    # ── 메모리 ──────────────────────────────────────────────────────
    Metric(
        "mem_mb", "Physical Mem", "MB",
        ("PhysicalUsedMB", "PhysicalMemoryUsedMB", "MemoryUsedMB"),
        None, None, "memory",
    ),
    Metric(
        "gpu_mem_mb", "GPU Mem", "MB",
        ("GPUMem/LocalUsedMB",), None, None, "memory",
    ),
)


@dataclass(frozen=True)
class Config:
    sb2_project_root: str = field(
        default_factory=lambda: _env(
            "SB2_PROJECT_ROOT", r"E:\Perforce\SB2\Workspace\Internal\SB2"
        )
    )
    monolith_endpoint: str = field(
        default_factory=lambda: _env("MONOLITH_ENDPOINT", "http://localhost:9316/mcp")
    )
    host: str = field(default_factory=lambda: _env("PERF_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(_env("PERF_PORT", "8077")))
    poll_interval: float = field(
        default_factory=lambda: float(_env("PERF_POLL_INTERVAL", "1.0"))
    )
    history_len: int = field(default_factory=lambda: int(_env("PERF_HISTORY", "120")))
    # 회전 캡처: UE 가 캡처 중 .csv 를 배타 잠금하므로 tail 불가 → start→짧게→stop→읽기 반복.
    capture_window: float = field(
        default_factory=lambda: float(_env("PERF_CAPTURE_WINDOW", "1.0"))
    )
    lock_timeout: float = field(
        default_factory=lambda: float(_env("PERF_LOCK_TIMEOUT", "6.0"))
    )
    delete_csv_after: bool = field(
        default_factory=lambda: _env("PERF_DELETE_CSV", "1") not in ("0", "false", "")
    )
    autostart: bool = field(
        default_factory=lambda: _env("PERF_AUTOSTART", "0") not in ("0", "false", "")
    )
    metrics: tuple[Metric, ...] = DEFAULT_METRICS

    @property
    def display_path(self) -> str:
        """EUW(네이티브 UMG)가 Tick 마다 읽는 포맷된 표시 텍스트 파일."""
        custom = os.environ.get("PERF_DISPLAY_PATH", "").strip()
        if custom:
            return custom
        here = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(here, ".live", "display.txt")

    @property
    def csv_dir(self) -> str:
        """CSV Profiler 기본 출력 폴더. override 필요 시 PERF_CSV_DIR."""
        custom = os.environ.get("PERF_CSV_DIR", "").strip()
        if custom:
            return custom
        return os.path.join(self.sb2_project_root, "Saved", "Profiling", "CSV")

    def with_overrides(self, **kw: object) -> "Config":
        return replace(self, **kw)  # type: ignore[arg-type]
