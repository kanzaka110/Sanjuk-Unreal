"""PerfMonitor 웹 서버 — stdlib only (FastAPI/uvicorn 불필요).

데이터 경로 = 회전 캡처(rotating capture):
  UE 는 CSV Profiler 캡처 중 .csv 를 배타 잠금하므로 tail 이 불가능하다(Windows
  ERROR_SHARING_VIOLATION). 그래서 [start → 짧게 캡처 → stop → 잠금 풀린 파일의
  마지막 행 읽기 → 파일 삭제] 사이클을 반복한다. 갱신 주기 ≈ capture_window + ~2.2s
  (파이널라이즈 지연). 진짜 프레임 단위가 필요하면 Phase 3(엔진 subsystem push).

구조:
  [Collector 스레드]  회전 캡처 → snapshot/history 갱신 (모니터링 on 일 때만)
  [HTTP 핸들러]       /  대시보드 / /meta / /snapshot / /stream(SSE)
                      /api/start 모니터링 시작  /api/stop 정지

실행:
    py perf_monitor/server.py           # 서버 기동 (대시보드 ▶ 버튼으로 모니터링 시작)
    py perf_monitor/server.py --start   # 기동 즉시 모니터링 시작
    py perf_monitor/server.py --probe   # csvprofile 가용성만 점검 후 종료
"""
from __future__ import annotations

import argparse
import json
import os
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from config import Config
from csv_source import list_csvs, newest_csv, read_last_row, wait_readable
from display import write_display
from monolith_control import ProfilerControl

_HERE = os.path.dirname(os.path.abspath(__file__))


class Collector:
    """회전 캡처로 최신 snapshot + 히스토리를 보관. 모니터링 on/off 토글 가능."""

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.profiler = ProfilerControl(cfg.monolith_endpoint)
        self._lock = threading.Lock()
        self._tick = 0
        self._snapshot: dict[str, Any] = self._base_snapshot()
        self._history: dict[str, deque[float | None]] = {
            m.key: deque(maxlen=cfg.history_len) for m in cfg.metrics
        }
        self._resolved: dict[str, str] = {}
        self._running = threading.Event()
        self._stop = threading.Event()
        self._cats_set = False

    def _base_snapshot(self) -> dict[str, Any]:
        return {
            "t": 0, "monitoring": False, "last_file": None, "error": None,
            "values": {m.key: None for m in self.cfg.metrics},
            "status": {m.key: "na" for m in self.cfg.metrics},
        }

    # ── 모니터링 토글 ────────────────────────────────────────────────
    def set_running(self, on: bool) -> None:
        if on:
            self._running.set()
        else:
            self._running.clear()
            self.profiler.stop()  # 진행 중 캡처 확실히 종료
        self._write_display()  # 상태 변화를 EUW 표시 파일에 즉시 반영

    def is_running(self) -> bool:
        return self._running.is_set()

    # ── 수집 루프 ────────────────────────────────────────────────────
    def run(self) -> None:
        while not self._stop.is_set():
            if not self._running.is_set():
                self._running.wait(timeout=0.5)
                continue
            try:
                self._capture_cycle()
            except Exception as e:  # 루프는 죽지 않는다
                self._set_error(f"{type(e).__name__}: {e}")
                self._stop.wait(2.0)

    def _capture_cycle(self) -> None:
        if not self._cats_set:
            try:
                self.profiler.set_categories()
                self._cats_set = True
            except Exception:
                pass  # 카테고리 실패해도 기본값으로 진행

        before = list_csvs(self.cfg.csv_dir)
        self.profiler.start()
        self._stop.wait(self.cfg.capture_window)
        self.profiler.stop()

        path = self._wait_for_new_file(before)
        if path is None:
            self._set_error("새 CSV 파일 미발견 (csvprofile 동작 확인 필요)")
            return
        if not wait_readable(path, self.cfg.lock_timeout):
            self._set_error("CSV 잠금 해제 타임아웃")
            return

        row = read_last_row(path, self.cfg.metrics)
        self._publish(row, os.path.basename(path))
        self._cleanup(path)

    def _wait_for_new_file(self, before: set[str]) -> str | None:
        """stop 후 새로 생긴 .csv 가 나타날 때까지 잠깐 폴링."""
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            new = list_csvs(self.cfg.csv_dir) - before
            if new:
                return max(new, key=os.path.getmtime)
            time.sleep(0.1)
        return newest_csv(self.cfg.csv_dir)  # 폴백: 가장 최근 파일

    def _cleanup(self, path: str) -> None:
        if not self.cfg.delete_csv_after:
            return
        try:
            os.remove(path)
        except OSError:
            pass  # 잠겨있거나 이미 없음 — 무시

    # ── snapshot 발행 ────────────────────────────────────────────────
    def _publish(self, row: dict[str, float] | None, fname: str) -> None:
        self._tick += 1
        values: dict[str, float | None] = {}
        status: dict[str, str] = {}
        for m in self.cfg.metrics:
            v = row.get(m.key) if row else None
            values[m.key] = v
            status[m.key] = m.status(v)
        with self._lock:
            self._snapshot = {
                "t": self._tick, "monitoring": self._running.is_set(),
                "last_file": fname, "error": None,
                "values": values, "status": status,
            }
            for key, v in values.items():
                self._history[key].append(v)
        self._write_display()

    def _set_error(self, msg: str) -> None:
        with self._lock:
            self._snapshot = {**self._snapshot, "error": msg,
                              "monitoring": self._running.is_set()}
        self._write_display()

    def _write_display(self) -> None:
        try:
            write_display(self.cfg, self.snapshot())
        except Exception:
            pass  # 표시 파일 기록 실패가 수집을 막지 않게

    def stop(self) -> None:
        self._stop.set()
        self.profiler.stop()

    # ── 조회 ─────────────────────────────────────────────────────────
    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._snapshot))

    def history(self) -> dict[str, list[float | None]]:
        with self._lock:
            return {k: list(v) for k, v in self._history.items()}


def _meta_payload(cfg: Config) -> dict[str, Any]:
    # 컬럼 resolve 는 캡처가 한 번 돌아야 채워지므로, 여기선 정의만 노출.
    return {
        "poll_interval": cfg.capture_window + 2.5,  # 대략적 갱신 주기(표시용)
        "history_len": cfg.history_len,
        "metrics": [
            {"key": m.key, "label": m.label, "unit": m.unit, "group": m.group,
             "warn": m.warn, "crit": m.crit, "column": m.candidates[0]}
            for m in cfg.metrics
        ],
    }


def make_handler(cfg: Config, collector: Collector):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *_: Any) -> None:
            pass

        def _json(self, obj: Any, code: int = 200) -> None:
            body = json.dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _file(self, path: str, ctype: str) -> None:
            try:
                with open(path, "rb") as f:
                    body = f.read()
            except OSError:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            route = self.path.split("?", 1)[0]
            if route == "/":
                self._file(os.path.join(_HERE, "dashboard.html"), "text/html; charset=utf-8")
            elif route == "/meta":
                self._json(_meta_payload(cfg))
            elif route == "/snapshot":
                self._json({"snapshot": collector.snapshot(), "history": collector.history()})
            elif route == "/stream":
                self._stream()
            else:
                self.send_error(404)

        def do_POST(self) -> None:  # noqa: N802
            route = self.path.split("?", 1)[0]
            if route == "/api/start":
                collector.set_running(True)
                self._json({"ok": True, "monitoring": True})
            elif route == "/api/stop":
                collector.set_running(False)
                self._json({"ok": True, "monitoring": False})
            else:
                self.send_error(404)

        def _stream(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            try:
                while True:
                    payload = json.dumps(collector.snapshot())
                    self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    time.sleep(1.0)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                return

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser(description="SB2 실시간 성능 대시보드")
    ap.add_argument("--start", action="store_true", help="기동 즉시 모니터링 시작")
    ap.add_argument("--probe", action="store_true", help="csvprofile 가용성만 점검 후 종료")
    args = ap.parse_args()

    cfg = Config()

    if args.probe:
        ok, msg = ProfilerControl(cfg.monolith_endpoint).probe()
        print(("OK   " if ok else "FAIL ") + msg)
        print(f"csv_dir = {cfg.csv_dir}")
        return

    collector = Collector(cfg)
    threading.Thread(target=collector.run, daemon=True).start()
    if args.start or cfg.autostart:
        collector.set_running(True)

    httpd = ThreadingHTTPServer((cfg.host, cfg.port), make_handler(cfg, collector))
    shown = "localhost" if cfg.host in ("0.0.0.0", "") else cfg.host
    print(f"PerfMonitor → http://{shown}:{cfg.port}  (csv_dir={cfg.csv_dir})")
    print(f"모니터링: {'ON' if collector.is_running() else 'OFF (대시보드 ▶ 로 시작)'}  |  Ctrl+C 종료")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n종료 중…")
    finally:
        collector.stop()
        httpd.shutdown()


if __name__ == "__main__":
    main()
