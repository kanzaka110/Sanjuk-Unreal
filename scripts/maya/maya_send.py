"""Maya commandPort 50007 직접 호출 — MayaMCP 미가용 시 fallback.

사용:
    py scripts/maya/maya_send.py mel 'pluginInfo -q -l;'
    py scripts/maya/maya_send.py py  'import maya.cmds as cmds; print(cmds.ls(type="xgmSplineDescription"))'
    py scripts/maya/maya_send.py file scripts/maya/snippets/groom_inspect.mel

Maya 의 commandPort 가 50007 에 떠 있어야 한다. shiftup.MOD + userSetup.py 셋업이
정상이면 Maya 시작 시 자동으로 열림. 안 열렸으면 Script Editor 에서:

    commandPort -name ":50007" -sourceType "mel" -echoOutput false;
"""
from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path


HOST = "127.0.0.1"
PORT = 50007
RECV_BUFSIZE = 65536
TIMEOUT_SEC = 30.0


def send(cmd: str, *, timeout: float = TIMEOUT_SEC) -> str:
    """단일 MEL 명령 전송 + 응답 수신."""
    with socket.create_connection((HOST, PORT), timeout=timeout) as s:
        if not cmd.endswith("\n"):
            cmd = cmd + "\n"
        s.sendall(cmd.encode("utf-8"))
        chunks: list[bytes] = []
        try:
            while True:
                data = s.recv(RECV_BUFSIZE)
                if not data:
                    break
                chunks.append(data)
        except socket.timeout:
            pass
    return b"".join(chunks).decode("utf-8", errors="replace")


def send_python(python_code: str, *, timeout: float = TIMEOUT_SEC) -> str:
    """Python 코드 라인을 MEL 의 python() 으로 wrap 해서 전송."""
    escaped = python_code.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return send('python("{}");'.format(escaped), timeout=timeout)


def send_file(path: str, *, mode: str = "mel", timeout: float = TIMEOUT_SEC) -> str:
    """.mel 또는 .py 파일 내용을 그대로 전송."""
    src = Path(path).read_text(encoding="utf-8")
    if mode == "mel":
        return send(src, timeout=timeout)
    return send_python(src, timeout=timeout)


def _main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Maya commandPort sender")
    p.add_argument("mode", choices=("mel", "py", "file_mel", "file_py"))
    p.add_argument("payload", help="명령 문자열 또는 파일 경로")
    p.add_argument("--timeout", type=float, default=TIMEOUT_SEC)
    args = p.parse_args(argv)

    try:
        if args.mode == "mel":
            out = send(args.payload, timeout=args.timeout)
        elif args.mode == "py":
            out = send_python(args.payload, timeout=args.timeout)
        elif args.mode == "file_mel":
            out = send_file(args.payload, mode="mel", timeout=args.timeout)
        else:
            out = send_file(args.payload, mode="py", timeout=args.timeout)
    except ConnectionRefusedError:
        print(
            "ERROR: Maya commandPort {}:{} 응답 없음. Maya 실행 + commandPort 50007 확인.".format(
                HOST, PORT
            ),
            file=sys.stderr,
        )
        return 2
    except socket.timeout:
        print("ERROR: timeout {}s".format(args.timeout), file=sys.stderr)
        return 3

    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
