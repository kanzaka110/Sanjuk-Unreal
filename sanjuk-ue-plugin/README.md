# sanjuk-ue

SB2(UE5 커스텀 5.7.4) 애니메이션 TA 워크플로 자산을 하나의 Claude Code 플러그인으로 묶은 것.
목적은 **다중 PC 동기화** — `.claude/agents`, `.claude/commands`에 흩어져 있던 자산을
리포에 넣어 `git pull` 한 번으로 어느 머신에서든 동일하게 쓰기 위함이다.

## 구성

### 에이전트 (6)

| 이름 | 역할 |
|------|------|
| `animbp-inspector` | AnimBP 분석·진단 (read-only). Tuner 호출 전 필수 선행 |
| `animbp-tuner` | Inspector 처방을 Monolith HTTP API로 실제 적용 |
| `sim-inspector` | Groom / Chaos Cloth / PhysAsset / KawaiiPhysics 진단 (read-only) |
| `sim-tuner` | Sim Inspector 처방 적용 |
| `ta-tool-builder` | SB2 에디터용 TA 툴(tkinter + EU_TA_Action) 제작 |
| `ue-root-cause-reviewer` | 원인 분석 반박·검수 전용 (수동 호출만) |

### 커맨드 (17)

- **진단/튜닝** — `/inspect-abp` `/inspect-sim` `/tune-abp` `/tune-sim`
- **UE 워크플로** — `/ue-anim` `/ue-debug` `/ue-setup` `/ue-status` `/footclamp-plan`
- **환경** — `/doctor` `/recover` `/start`
- **동기화/기록** — `/push` `/pull` `/hermes` `/evidence`
- **리서치** — `/브리핑`

## 설치

리포 루트가 곧 마켓플레이스다 (`.claude-plugin/marketplace.json`).

```bash
claude plugin marketplace add "H:/내 드라이브/Claude/Sanjuk-Unreal"
claude plugin install sanjuk-ue@sanjuk-unreal
```

다른 PC에서는 리포를 clone/pull 한 뒤 그 경로로 같은 두 줄을 실행한다.

## 중복 등록 주의

설치 후에도 `.claude/agents/`, `.claude/commands/` 원본이 남아 있으면
**같은 에이전트·커맨드가 두 번 등록**된다. 설치 검증이 끝나면 원본을 지울 것:

```bash
rm -rf .claude/agents .claude/commands
```

되돌리려면 `claude plugin uninstall sanjuk-ue` 후 git에서 복원.

## 범위 밖 (의도적 제외)

- **훅** — `objective-guard`, `hermes_auto_share`, `transcript-vault`, `orca`는
  머신별 절대경로(venv, `~/.claude/...`)에 묶여 있어 이식 대상이 아니다.
  `~/.claude/settings.json`에 그대로 둔다.
- **`/objective-*` 커맨드 5종** — `~/.claude/commands/`의 user 스코프 자산이며
  objective-guard 설치본과 짝이라 함께 두었다.
