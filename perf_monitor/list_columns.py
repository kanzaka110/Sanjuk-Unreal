"""가장 최근 CSV Profiler 파일의 실제 컬럼 헤더를 출력 + 메트릭 resolve 결과 표시.

SB2 커스텀 빌드의 CSV 컬럼명이 config.py 의 후보와 다를 때, 실제 이름을 확인해
candidates 를 보강하기 위한 진단 도구.

    py perf_monitor/list_columns.py
"""
from __future__ import annotations

from config import Config
from csv_source import CsvReader, newest_csv


def main() -> None:
    cfg = Config()
    path = newest_csv(cfg.csv_dir)
    print(f"csv_dir = {cfg.csv_dir}")
    if path is None:
        print("→ .csv 파일 없음. 먼저 CSV Profiler 를 켜세요:")
        print("    py perf_monitor/server.py --start")
        return
    print(f"최신 파일 = {path}\n")

    reader = CsvReader.open(path, cfg.metrics)
    if reader is None:
        print("→ 헤더를 읽을 수 없음 (빈 파일 / 기록 대기 중).")
        return

    print(f"--- 전체 컬럼 ({len(reader.header)}) ---")
    for h in reader.header:
        print(f"  {h}")

    print("\n--- 메트릭 resolve 결과 ---")
    for m in cfg.metrics:
        col = reader.column_map.get(m.key)
        mark = "OK " if col else "MISS"
        print(f"  [{mark}] {m.label:<16} → {col or '(후보 ' + ', '.join(m.candidates) + ' 중 없음)'}")


if __name__ == "__main__":
    main()
