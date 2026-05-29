"""Maya commandPort 실행기 — MayaMCP(maya_mcp_server.py)의 송신 규칙을 그대로 미러.

maya_send.py 는 백슬래시 이스케이프 + trailing ';\\n' 때문에 commandPort 실행이 깨졌다.
MayaMCP 는 (1) '"' 와 '\\n' 만 이스케이프, (2) trailing 문자 없음, (3) 결과를
전역 _mcp_maya_results 에 저장 후 2차 조회로 회수한다. 그 규칙을 복제한다.

사용:
    py scripts/maya/maya_run.py <python_file>      # 파일 내용 실행
    py scripts/maya/maya_run.py --code "<inline>"  # 인라인 코드 실행

주의: 보내는 파이썬 코드에 백슬래시(\\) 금지 (MayaMCP 규칙과 동일). 경로는 forward slash.
"""
from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path

HOST = "127.0.0.1"
PORT = 50007


def _encode(python_code: str) -> str:
    mel = python_code.replace('"', '\\"')
    mel = mel.replace("\n", "\\n")
    return 'python("{}")'.format(mel)


def _send_once(payload: str, timeout: float) -> str | None:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(timeout)
    try:
        client.connect((HOST, PORT))
        client.send(payload.encode("utf-8"))
        result = data = client.recv(1024)
        while len(data) == 1024:
            data = client.recv(1024)
            result += data
    finally:
        client.close()
    if result:
        return result.decode("utf-8", errors="replace")
    return None


def run_python(python_script: str, timeout: float = 60.0) -> str | None:
    """MayaMCP 규칙: 결과를 _mcp_maya_results 에 담고, 비면 2차 조회."""
    wrapped = "_mcp_maya_results = None\n" + python_script
    result = _send_once(_encode(wrapped), timeout)
    if result:
        result = result.replace(chr(0), "").replace(chr(10), "")
    if not result or result == "\n":
        result = _send_once(_encode("_mcp_maya_results"), timeout)
        if result:
            result = result.replace(chr(0), "").replace(chr(10), "")
    return result


def _main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Maya commandPort runner (MayaMCP-compatible)")
    p.add_argument("target", nargs="?", help="python file path")
    p.add_argument("--code", help="inline python code")
    p.add_argument("--timeout", type=float, default=60.0)
    args = p.parse_args(argv)

    if args.code:
        code = args.code
    elif args.target:
        code = Path(args.target).read_text(encoding="utf-8")
    else:
        print("ERROR: provide a file path or --code", file=sys.stderr)
        return 1

    if "\\" in code:
        print(
            "ERROR: code contains backslash — MayaMCP wrap can't escape it. "
            "Use forward slashes only.",
            file=sys.stderr,
        )
        return 1

    try:
        out = run_python(code, timeout=args.timeout)
    except ConnectionRefusedError:
        print("ERROR: commandPort {}:{} refused. Maya 실행 확인.".format(HOST, PORT), file=sys.stderr)
        return 2
    except socket.timeout:
        print("ERROR: timeout", file=sys.stderr)
        return 3

    print(out if out is not None else "<no result>")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
