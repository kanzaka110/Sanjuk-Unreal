# TA 액션 아이템 & 로드맵

> 2026-04-06 브리핑 | [목차로 돌아가기](00_INDEX.md)

---

## 즉시 실행 (이번 주)

- [ ] **Cascadeur 2026.1** UE Live Link 플러그인 테스트 (4/9 출시)
- [ ] Epic "Rigging in UE 5.6 Workshop" 학습 시작 (무료, 5일 과정)
- [ ] GASP 5.7 프로젝트 다운로드 및 400개 신규 애니메이션 분석

---

## 이번 분기 (Q2 2026)

### 학습 & 실험
- [ ] UAF 5.7 플러그인 활성화 → GASP 캐릭터로 실험
- [ ] Mover 2.0 + UAF + Motion Matching 조합 셋업 테스트
- [ ] Motorica Motion Factory로 커스텀 로코모션 데이터셋 생성
- [ ] ML Deformer 근육 시뮬레이션 퀄리티 vs 성능 벤치마크
- [ ] Control Rig Physics (Experimental) 테스트

### 파이프라인
- [ ] 웹캠 기반 MetaHuman Animator 워크플로 검증
- [ ] DeepMotion AI 모캡 → MetaHuman 파이프라인 구축
- [ ] mGear/UEGear 1.0으로 Maya ↔ UE 리깅 파이프라인 테스트
- [ ] ChiR24 MCP로 Chaos Cloth 자동화 테스트

### MCP 환경
- [ ] Monolith + runreal 조합 최신 버전 추적 유지
- [ ] 애니메이션 자동화 스크립트 확장 (UAF 대비)

---

## 모니터링 (하반기)

- [ ] **UAF 5.8 프리뷰** — GASP 캐릭터 UAF 완전 구성 분석
- [ ] **멀티캐릭터 Motion Matching** 로드맵 추적
- [ ] **Epic 공식 MCP** 발표 여부 모니터링
- [ ] Cascadeur, Motorica 업데이트 추적

---

## 우선순위 매트릭스

```
              높은 영향
                 │
    UAF 실험     │    Cascadeur Live Link
    MM 데이터셋   │    리깅 워크숍
                 │
낮은 긴급 ───────┼─────── 높은 긴급
                 │
    멀티캐릭 MM  │    GASP 5.7 분석
    Epic MCP    │    MetaHuman 웹캠
                 │
              낮은 영향
```

---

## 관련 튜토리얼/가이드 (이 레포 내)

| 폴더 | 연관 주제 |
|------|-----------|
| `Tutorial/AnimNext-Migration-Guide/` | UAF/AnimNext 전환 |
| `Tutorial/Monolith-MCP-Tutorial/` | MCP 애니메이션 제어 |
| `Tutorial/runreal-MCP-Tutorial/` | Python 기반 UE 자동화 |
| `Tutorial/UAF-Setup-Guide/` | UAF 셋업 |
