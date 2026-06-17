"""CSV Profiler 출력 파일 tail + 최신 행 파싱.

UE CSV Profiler 는 csv.ContinuousWrites 1 일 때 캡처 중 파일에 주기적으로 flush 한다.
이 모듈은 csv_dir 의 가장 최근 .csv 를 골라 헤더를 읽고, 메트릭별 실제 컬럼을
resolve 한 뒤, tail() 호출마다 마지막 '완성된' 행을 dict 로 돌려준다.

파일 회전(새 프로파일 시작 → 새 csv) 도 mtime 으로 자동 추종한다.
"""
from __future__ import annotations

import csv
import glob
import os
import time
from dataclasses import dataclass

from config import Metric


def list_csvs(csv_dir: str) -> set[str]:
    """csv_dir 하위 모든 .csv 경로 집합."""
    if not os.path.isdir(csv_dir):
        return set()
    return set(glob.glob(os.path.join(csv_dir, "**", "*.csv"), recursive=True))


def wait_readable(path: str, timeout: float, poll: float = 0.1) -> bool:
    """파일이 읽기 가능(배타 잠금 해제)해질 때까지 대기. 성공 시 True."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with open(path, "rb"):
                return True
        except OSError:
            time.sleep(poll)
    return False


def read_last_row(path: str, metrics: tuple[Metric, ...]) -> dict[str, float] | None:
    """파일을 열어 헤더 resolve + 마지막 유효 데이터 행을 메트릭 dict 로."""
    reader = CsvReader.open(path, metrics)
    if reader is None:
        return None
    return reader.read_latest()


def newest_csv(csv_dir: str) -> str | None:
    """csv_dir 에서 가장 최근 수정된 .csv 경로. 없으면 None."""
    if not os.path.isdir(csv_dir):
        return None
    files = glob.glob(os.path.join(csv_dir, "**", "*.csv"), recursive=True)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def resolve_columns(
    header: list[str], metrics: tuple[Metric, ...]
) -> dict[str, str]:
    """metric.key -> 실제 CSV 컬럼명. 후보 중 헤더에 있는 첫 항목.

    대소문자/공백 무시 매칭. 못 찾은 metric 은 결과에서 빠진다.
    """
    norm = {h.strip().lower(): h for h in header}
    resolved: dict[str, str] = {}
    for m in metrics:
        for cand in m.candidates:
            actual = norm.get(cand.strip().lower())
            if actual is not None:
                resolved[m.key] = actual
                break
    return resolved


@dataclass
class CsvReader:
    """단일 CSV 파일에 대한 tail 상태."""

    path: str
    header: list[str]
    column_map: dict[str, str]  # metric.key -> CSV 컬럼명
    _last_row: dict[str, float] | None = None

    @classmethod
    def open(cls, path: str, metrics: tuple[Metric, ...]) -> "CsvReader | None":
        """파일을 열어 헤더 파싱 + 컬럼 resolve. 헤더가 없으면 None."""
        try:
            with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
                first = f.readline()
        except OSError:
            return None
        if not first.strip():
            return None
        header = next(csv.reader([first]))
        header = [h.strip() for h in header]
        return cls(path=path, header=header, column_map=resolve_columns(header, metrics))

    def read_latest(self) -> dict[str, float] | None:
        """파일 끝에서 가장 최근의 '유효 데이터 행'을 메트릭 dict 로 반환.

        CSV Profiler 는 캡처 종료 시 파일 끝에 메타데이터 푸터(`[HasHeaderRowAtEnd]` 등)
        와 중복 헤더 행을 붙인다. 그래서 단순 마지막 줄이 아니라, 뒤에서부터 스캔하며
        컬럼 수가 헤더와 일치하고 메타/헤더가 아닌 첫 행을 채택한다.
        """
        line = self._tail_data_line()
        if line is None:
            return self._last_row
        values = next(csv.reader([line]))
        row_by_col = dict(zip(self.header, values))
        out: dict[str, float] = {}
        for key, col in self.column_map.items():
            raw = row_by_col.get(col, "").strip()
            try:
                out[key] = float(raw)
            except (TypeError, ValueError):
                continue
        if out:
            self._last_row = out
        return self._last_row

    def _tail_data_line(self) -> str | None:
        """파일 끝 64KB 안에서 뒤→앞으로 첫 유효 데이터 행을 찾아 반환."""
        try:
            size = os.path.getsize(self.path)
        except OSError:
            return None
        if size == 0:
            return None
        read_back = min(size, 64 * 1024)
        try:
            with open(self.path, "rb") as f:
                f.seek(size - read_back)
                chunk = f.read(read_back)
        except OSError:
            return None
        text = chunk.decode("utf-8", errors="replace")
        lines = [ln for ln in text.splitlines() if ln.strip()]
        ncols = len(self.header)
        first_col = self.header[0]
        for ln in reversed(lines):
            if ln.lstrip().startswith("["):
                continue  # 메타데이터 푸터
            first = ln.split(",", 1)[0].strip()
            if first == first_col:
                continue  # (중복) 헤더 행
            try:
                values = next(csv.reader([ln]))
            except StopIteration:
                continue
            # 데이터 행은 헤더보다 1 많을 수 있음(끝 트레일링 콤마). zip 이 흡수.
            if len(values) >= ncols:
                return ln  # 완성된 데이터 행
        return None


@dataclass
class CsvSource:
    """csv_dir 를 감시하며 항상 '가장 최근 파일'을 따라가는 상위 래퍼."""

    csv_dir: str
    metrics: tuple[Metric, ...]
    _reader: CsvReader | None = None
    _active_path: str | None = None

    def poll(self) -> tuple[dict[str, float] | None, "SourceState"]:
        """(최신 메트릭 dict | None, 상태) 반환. 파일 회전 자동 추종."""
        path = newest_csv(self.csv_dir)
        if path is None:
            self._reader = None
            self._active_path = None
            return None, SourceState(active_file=None, columns={}, found=False)
        if path != self._active_path or self._reader is None:
            reader = CsvReader.open(path, self.metrics)
            if reader is None:
                return None, SourceState(active_file=path, columns={}, found=True)
            self._reader = reader
            self._active_path = path
        row = self._reader.read_latest()
        state = SourceState(
            active_file=self._active_path,
            columns=dict(self._reader.column_map),
            found=True,
        )
        return row, state


@dataclass(frozen=True)
class SourceState:
    active_file: str | None
    columns: dict[str, str]
    found: bool
