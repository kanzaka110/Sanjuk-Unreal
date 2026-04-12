{
  "permissions": {
    "allow": [
      "Bash(gcloud compute:*)",
      "Bash(git pull:*)",
      "Bash(git fetch:*)",
      "Bash(cd /tmp)",
      "Bash(gh repo:*)",
      "Bash(rm -rf claw-code)",
      "Bash(xargs ls:*)",
      "Bash(ls /tmp/claw-code/rust/crates/*/tests/)",
      "Bash(wc -l /tmp/claw-code/rust/crates/*/src/*.rs)",
      "Read({{USER_HOME_UNC}}/OneDrive/문서/Unreal Projects/MonolithTest/Plugins/Monolith/**)",
      "Read({{USER_HOME_UNC}}/OneDrive/문서/Unreal Projects/MonolithTest/Plugins/UnrealClaude/**)",
      "Bash(ls {{USER_HOME}}/.claude/projects/C--dev-Sanjuk-Unreal/memory/*.md)",
      "Bash(npx --version)",
      "Bash(tasklist)",
      "Bash(bash {{REPO_ROOT}}/.claude/hooks/pre-monolith-check.sh)",
      "Bash(echo \"EXIT_CODE: $?\")",
      "Bash(curl -s -o /dev/null -w \"%{http_code}\" --connect-timeout 3 http://localhost:9316/mcp)",
      "Bash(curl -s -o /dev/null -w \"%{http_code}\" --connect-timeout 3 http://localhost:3000)",
      "Bash(curl -s http://localhost:9316/mcp)",
      "Bash(echo \"EXIT: $?\")",
      "Bash(curl -s -X POST http://localhost:9316/mcp -H \"Content-Type: application/json\" -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}')",
      "Bash(python -c ':*)",
      "Bash(curl:*)",
      "Bash(python -c \"import json,sys; d=json.load\\(sys.stdin\\); print\\(d['result']['content'][0]['text'][:500]\\)\")",
      "Bash(python -c \"import json,sys; d=json.load\\(sys.stdin\\); print\\(d['result']['content'][0]['text'][:2000]\\)\")",
      "Bash(xargs grep:*)",
      "Bash(python -c \"import json,sys; d=json.load\\(sys.stdin\\); print\\(d['result']['content'][0]['text']\\)\")",
      "Bash(python -c \"import json,sys; d=json.load\\(sys.stdin\\); print\\(json.dumps\\(json.loads\\(d['result']['content'][0]['text']\\), indent=2\\)\\)\")",
      "Bash(python -c \"import json,sys; d=json.load\\(sys.stdin\\); print\\(json.dumps\\(json.loads\\(d['result']['content'][0]['text']\\), indent=2\\)[:2000]\\)\")",
      "Bash(python -c \"import json,sys; d=json.load\\(sys.stdin\\); print\\(d['result']['content'][0]['text'][:200]\\)\")",
      "Bash(python {{REPO_ROOT}}/.claude/hooks/parse_cr.py)",
      "Bash(mkdir -p /c/tmp)",
      "Bash(git add:*)",
      "Bash(git commit -m ':*)",
      "Bash(git push:*)",
      "Bash(pip list:*)",
      "Bash(pip install:*)",
      "Bash(python briefing.py --count 1 --force)",
      "Bash(PYTHONIOENCODING=utf-8 python briefing.py --count 1 --force)",
      "Bash(where claude:*)",
      "Bash(bash migration/backup.sh)"
    ]
  },
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": [
    "monolith"
  ],
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__monolith",
        "hooks": [
          {
            "type": "command",
            "command": "bash {{REPO_ROOT}}/.claude/hooks/pre-monolith-check.sh"
          }
        ]
      },
      {
        "matcher": "mcp__unrealclaude",
        "hooks": [
          {
            "type": "command",
            "command": "bash {{REPO_ROOT}}/.claude/hooks/pre-unrealclaude-check.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__monolith",
        "hooks": [
          {
            "type": "command",
            "command": "bash {{REPO_ROOT}}/.claude/hooks/post-monolith-verify.sh"
          }
        ]
      }
    ]
  }
}
