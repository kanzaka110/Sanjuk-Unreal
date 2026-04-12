"""Notion 업로드 — DB 쿼리, 중복 체크, 페이지 생성, 마크다운→블록 변환."""

from __future__ import annotations

import re
import requests
from datetime import date

from notion_client import Client
from notion_client.errors import APIResponseError

from briefing_config import (
    CATEGORIES, VALID_TAGS, DIFFICULTY_LEVELS, UE_VERSIONS,
)


# ─── Notion DB 쿼리 ──────────────────────────────────────────────────────────

def notion_db_query(database_id: str, payload: dict, *, api_key: str) -> dict:
    """Notion API databases/query를 requests로 직접 호출."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    res = requests.post(
        f"https://api.notion.com/v1/databases/{database_id}/query",
        headers=headers, json=payload, timeout=30,
    )
    res.raise_for_status()
    return res.json()


def already_briefed_today(
    database_id: str, category: str, *, api_key: str,
) -> bool:
    """오늘 날짜 + 해당 카테고리로 이미 Notion 엔트리가 있는지 확인."""
    today = date.today().isoformat()
    try:
        result = notion_db_query(database_id, {
            "filter": {
                "and": [
                    {"property": "날짜", "date": {"equals": today}},
                    {"property": "카테고리", "select": {"equals": category}},
                ]
            },
            "page_size": 1,
        }, api_key=api_key)
        if result.get("results"):
            title = (
                result["results"][0]
                .get("properties", {})
                .get("제목", {})
                .get("title", [{}])[0]
                .get("plain_text", "알 수 없음")
            )
            print(f"  ⏭  이미 오늘 브리핑 존재: [{category}] — {title}")
            return True
        return False
    except Exception as e:
        print(f"  ⚠️  중복 체크 오류 ({category}): {e}")
        return False


def get_existing_summaries(
    database_id: str, *, api_key: str, limit: int = 30,
) -> list[dict]:
    """최근 Notion 페이지들의 요약/카테고리/날짜/태그를 가져옴."""
    try:
        result = notion_db_query(database_id, {
            "sorts": [{"property": "날짜", "direction": "descending"}],
            "page_size": limit,
        }, api_key=api_key)
        summaries = []
        for page in result.get("results", []):
            props = page.get("properties", {})
            summary_rt = props.get("요약", {}).get("rich_text", [])
            summary = summary_rt[0].get("plain_text", "") if summary_rt else ""
            title_arr = props.get("제목", {}).get("title", [])
            title = title_arr[0].get("plain_text", "") if title_arr else ""
            category = props.get("카테고리", {}).get("select", {})
            cat_name = category.get("name", "") if category else ""
            date_prop = props.get("날짜", {}).get("date", {})
            date_str = date_prop.get("start", "") if date_prop else ""
            tags = [t.get("name", "") for t in props.get("태그", {}).get("multi_select", [])]
            summaries.append({
                "title": title,
                "summary": summary,
                "category": cat_name,
                "date": date_str,
                "tags": tags,
                "text": f"{title}|{summary}",
            })
        return summaries
    except Exception as e:
        print(f"  ⚠️  기존 요약 조회 오류: {e}")
        return []


def is_content_duplicate(
    new_summary: str,
    existing_summaries: list[dict],
    threshold: float = 0.5,
) -> bool:
    """새 요약이 기존 요약과 내용이 유사한지 단어 겹침으로 판별."""
    if not new_summary or not existing_summaries:
        return False
    new_words = set(new_summary.lower().split())
    if len(new_words) < 3:
        return False
    for existing in existing_summaries:
        existing_text = existing.get("text", "") if isinstance(existing, dict) else str(existing)
        existing_words = set(existing_text.lower().split())
        if len(existing_words) < 3:
            continue
        overlap = new_words & existing_words
        similarity = len(overlap) / min(len(new_words), len(existing_words))
        if similarity >= threshold:
            print(f"  ⏭  내용 중복 감지 (유사도 {similarity:.0%})")
            return True
    return False


def remove_new_badges(
    notion: Client, database_id: str, *, api_key: str,
) -> int:
    """어제 이전 페이지의 🆕 표기를 제거."""
    today = date.today().isoformat()
    removed = 0
    try:
        result = notion_db_query(database_id, {
            "filter": {
                "and": [
                    {"property": "날짜", "date": {"before": today}},
                    {"property": "🆕 신규", "checkbox": {"equals": True}},
                ]
            },
            "page_size": 50,
        }, api_key=api_key)
        for page in result.get("results", []):
            page_id = page["id"]
            title_arr = page.get("properties", {}).get("제목", {}).get("title", [])
            old_title = title_arr[0].get("plain_text", "") if title_arr else ""
            new_title = old_title.replace("🆕 ", "").replace("🆕", "").strip()

            update_props: dict = {"🆕 신규": {"checkbox": False}}
            if new_title != old_title:
                update_props["제목"] = {"title": [{"text": {"content": new_title}}]}

            notion.pages.update(page_id=page_id, properties=update_props)
            print(f"  🔄 🆕 해제: {old_title[:60]}")
            removed += 1
    except Exception as e:
        print(f"  ⚠️  🆕 제거 오류: {e}")
    return removed


# ─── Notion 업로드 ────────────────────────────────────────────────────────────

def upload_to_notion(notion: Client, database_id: str, data: dict) -> bool:
    """Notion 데이터베이스에 브리핑 페이지를 생성."""
    difficulty = data.get("난이도", "중급")
    if difficulty not in DIFFICULTY_LEVELS:
        difficulty = "중급"

    ue_version = data.get("UE_버전", "5.7")
    if ue_version not in UE_VERSIONS:
        ue_version = "5.7"

    tags = [t for t in data.get("태그", []) if t in VALID_TAGS]

    category = data.get("카테고리", "Animation Blueprint")
    if category not in CATEGORIES:
        category = "Animation Blueprint"

    title = str(data.get("제목", f"{category} 브리핑"))[:2000]
    summary = str(data.get("요약", ""))[:2000]
    source_link = data.get("소스_링크") or "https://dev.epicgames.com/documentation/ko-kr/unreal-engine"
    body_md = data.get("본문_마크다운", "")
    page_blocks = markdown_to_notion_blocks(body_md) if body_md else build_page_content(data)

    properties: dict = {
        "제목":       {"title":     [{"text": {"content": title}}]},
        "날짜":       {"date":      {"start": date.today().isoformat()}},
        "카테고리":   {"select":    {"name": category}},
        "UE 버전":    {"select":    {"name": ue_version}},
        "난이도":     {"select":    {"name": difficulty}},
        "요약":       {"rich_text": [{"text": {"content": summary}}]},
        "소스 링크":  {"url":       source_link},
        "브리핑 완료": {"checkbox":  True},
        "🆕 신규":    {"checkbox":  True},
    }
    if tags:
        properties["태그"] = {"multi_select": [{"name": t} for t in tags]}

    try:
        page = notion.pages.create(
            parent={"database_id": database_id},
            properties=properties,
            children=page_blocks,
        )
        print(f"  ✅ Notion 페이지 생성: {title}")
        print(f"     🔗 {page['url']}")
        return True
    except APIResponseError as e:
        print(f"  ❌ Notion API 오류: {e.status} — {e.body}")
        return False
    except Exception as e:
        print(f"  ❌ Notion 업로드 실패: {e}")
        return False


# ─── 마크다운 → Notion 블록 변환 ──────────────────────────────────────────────

NOTION_LANGUAGES = {
    "abap","abc","agda","arduino","ascii art","assembly","bash","basic","bnf",
    "c","c#","c++","clojure","coffeescript","coq","css","dart","dhall","diff",
    "docker","ebnf","elixir","elm","erlang","f#","flow","fortran","gherkin",
    "glsl","go","graphql","groovy","haskell","hcl","html","idris","java",
    "javascript","json","julia","kotlin","latex","less","lisp","livescript",
    "llvm ir","lua","makefile","markdown","markup","matlab","mathematica",
    "mermaid","nix","notion formula","objective-c","ocaml","pascal","perl",
    "php","plain text","powershell","prolog","protobuf","purescript","python",
    "r","racket","reason","ruby","rust","sass","scala","scheme","scss","shell",
    "smalltalk","solidity","sql","swift","toml","typescript","vb.net","verilog",
    "vhdl","visual basic","webassembly","xml","yaml","java/c/c++/c#",
}


def markdown_to_notion_blocks(markdown: str) -> list[dict]:
    """마크다운을 Notion API 블록으로 변환. 테이블, 코드블록, 콜아웃 지원."""
    blocks: list[dict] = []
    lines = markdown.split("\n")
    i = 0

    def _rt(text: str) -> list[dict]:
        return [{"type": "text", "text": {"content": text[:2000]}}]

    while i < len(lines):
        line = lines[i]

        # 코드블록
        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip().lower()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if lang not in NOTION_LANGUAGES:
                lang = "plain text"
            blocks.append({
                "object": "block", "type": "code",
                "code": {
                    "rich_text": _rt("\n".join(code_lines)),
                    "language": lang if lang else "plain text",
                },
            })
            i += 1
            continue

        # 테이블
        if line.strip().startswith("|") and i + 1 < len(lines) and "---" in lines[i + 1]:
            table_lines: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                if "---" not in lines[i]:
                    cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                    table_lines.append(cells)
                i += 1
            if table_lines:
                col_count = max(len(row) for row in table_lines)
                table = {
                    "object": "block", "type": "table",
                    "table": {
                        "table_width": col_count,
                        "has_column_header": True,
                        "has_row_header": False,
                        "children": [],
                    },
                }
                for row in table_lines[:50]:
                    while len(row) < col_count:
                        row.append("")
                    table["table"]["children"].append({
                        "object": "block", "type": "table_row",
                        "table_row": {
                            "cells": [[{"type": "text", "text": {"content": cell[:2000]}}] for cell in row[:col_count]],
                        },
                    })
                blocks.append(table)
            continue

        # 단독 테이블 행
        if line.strip().startswith("|") and "---" not in line:
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": _rt(line)}})
            i += 1
            continue

        # 구분선
        if line.strip() == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            i += 1
            continue

        # 헤딩
        if line.startswith("# "):
            blocks.append({"object": "block", "type": "heading_1",
                "heading_1": {"rich_text": _rt(line[2:]), "color": "blue_background"}})
            i += 1
            continue
        if line.startswith("## "):
            blocks.append({"object": "block", "type": "heading_2",
                "heading_2": {"rich_text": _rt(line[3:])}})
            i += 1
            continue
        if line.startswith("### "):
            blocks.append({"object": "block", "type": "heading_3",
                "heading_3": {"rich_text": _rt(line[4:])}})
            i += 1
            continue

        # 인용구 / 콜아웃
        if line.startswith("> "):
            text = line[2:]
            emoji = "💡"
            color = "blue_background"
            if "Tip" in text or "팁" in text:
                emoji, color = "💡", "yellow_background"
            elif "핵심" in text:
                emoji, color = "🎯", "yellow_background"
            elif "⚠" in text or "주의" in text:
                emoji, color = "⚠️", "orange_background"
            blocks.append({"object": "block", "type": "callout",
                "callout": {"rich_text": _rt(text), "icon": {"type": "emoji", "emoji": emoji}, "color": color}})
            i += 1
            continue

        # 불릿 리스트
        if line.startswith("- "):
            blocks.append({"object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": _rt(line[2:])}})
            i += 1
            continue

        # 번호 리스트
        if re.match(r"^\d+\.\s", line):
            text = re.sub(r"^\d+\.\s", "", line)
            blocks.append({"object": "block", "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": _rt(text)}})
            i += 1
            continue

        # 일반 텍스트
        if line.strip():
            blocks.append({"object": "block", "type": "paragraph",
                "paragraph": {"rich_text": _rt(line)}})

        i += 1

    return blocks[:100]


# ─── 구조화 블록 빌더 (JSON 데이터 → Notion 블록) ─────────────────────────────

def build_page_content(data: dict) -> list[dict]:
    """구조화된 data dict → Notion API 블록 리스트."""
    tut = data.get("튜토리얼", {})
    blocks: list[dict] = []

    def _divider():
        blocks.append({"object": "block", "type": "divider", "divider": {}})

    def _heading1(text):
        blocks.append({"object": "block", "type": "heading_1",
            "heading_1": {"rich_text": [{"type": "text", "text": {"content": text}}], "color": "blue_background"}})

    def _heading2(text):
        blocks.append({"object": "block", "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]}})

    def _heading3(text):
        blocks.append({"object": "block", "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": text}}]}})

    def _paragraph(text, bold=False, color="default"):
        if not text.strip():
            return
        rt = [{"type": "text", "text": {"content": text[:2000]}, "annotations": {"bold": bold, "color": color}}]
        blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": rt, "color": "default"}})

    def _callout(text, emoji="💡", color="blue_background"):
        blocks.append({"object": "block", "type": "callout",
            "callout": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
                        "icon": {"type": "emoji", "emoji": emoji}, "color": color}})

    def _bullet(text):
        blocks.append({"object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}})

    def _numbered(text):
        blocks.append({"object": "block", "type": "numbered_list_item",
            "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}})

    def _toggle(title, children_texts):
        children = []
        for ct in children_texts:
            children.append({"object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": ct[:2000]}}]}})
        blocks.append({"object": "block", "type": "toggle",
            "toggle": {"rich_text": [{"type": "text", "text": {"content": title[:2000]}}],
                       "children": children[:10]}})

    def _bookmark(url, caption=""):
        b: dict = {"object": "block", "type": "bookmark", "bookmark": {"url": url}}
        if caption:
            b["bookmark"]["caption"] = [{"type": "text", "text": {"content": caption[:2000]}}]
        blocks.append(b)

    # 한줄 요약
    one_liner = tut.get("한줄_요약", "")
    if one_liner:
        _callout(f"📌  {one_liner}", "🎯", "yellow_background")
    _divider()

    # 배경 설명
    bg = tut.get("배경_설명", "") or tut.get("개요", "")
    if bg:
        _heading1("📖 배경 및 개요")
        _paragraph(bg)
    _divider()

    # 사전 준비
    prereqs = tut.get("사전_준비", [])
    if prereqs:
        _heading1("🔧 사전 준비")
        _callout("아래 항목을 먼저 확인해주세요.", "⚡", "red_background")
        for p in prereqs:
            _numbered(p)
    _divider()

    # 핵심 개념
    concepts = tut.get("핵심_개념", [])
    if concepts:
        _heading1("🔑 핵심 개념")
        for c in concepts:
            importance = c.get("중요도", "권장")
            emoji = "🔴" if importance == "필수" else ("🟡" if importance == "권장" else "🔵")
            _heading3(f"{emoji} {c.get('제목', '')}  [{importance}]")
            _paragraph(c.get("설명", ""))
    _divider()

    # 비교표
    comparisons = tut.get("비교표", [])
    if comparisons and any(c.get("항목") for c in comparisons):
        _heading1("⚖️ 기존 방식 vs 새 방식 비교")
        for c in comparisons:
            item = c.get("항목", "")
            if item:
                _heading3(f"📊 {item}")
                _callout(f"❌ 기존: {c.get('기존_방식', '')}", "❌", "gray_background")
                _callout(f"✅ 개선: {c.get('새_방식', '')}", "✅", "green_background")
                effect = c.get("개선_효과", "")
                if effect:
                    _paragraph(f"→ 개선 효과: {effect}", bold=True)
    _divider()

    # 단계별 가이드
    steps = tut.get("단계별_가이드", [])
    if steps:
        _heading1("🛠️ 단계별 튜토리얼 가이드")
        _callout(f"총 {len(steps)}단계로 구성되어 있습니다.", "📋", "blue_background")
        for s in steps:
            _heading2(f"Step {s.get('단계', '?')}.  {s.get('제목', '')}")
            _paragraph(s.get("내용", ""))
            why = s.get("왜", "")
            if why:
                _callout(f"왜 이 단계가 필요한가요? → {why}", "🤔", "purple_background")
            tip = s.get("팁", "")
            if tip:
                _callout(f"💡 Tip: {tip}", "💡", "yellow_background")
    _divider()

    # 자주 하는 실수
    mistakes = tut.get("자주_하는_실수", [])
    if mistakes:
        _heading1("🚫 초보자가 자주 하는 실수")
        for m in mistakes:
            _callout(f"❌ 실수: {m.get('실수', '')}", "❌", "red_background")
            _callout(f"✅ 해결: {m.get('해결법', '')}", "✅", "green_background")
    _divider()

    # FAQ
    faqs = tut.get("FAQ", [])
    if faqs:
        _heading1("❓ 자주 묻는 질문 (FAQ)")
        for faq in faqs:
            q, a = faq.get("질문", ""), faq.get("답변", "")
            if q and a:
                _toggle(f"Q. {q}", [f"A. {a}"])
    _divider()

    # 주의사항
    cautions = tut.get("주의사항", [])
    if cautions:
        _heading1("⚠️ 주의사항")
        for c in cautions:
            _callout(c, "⚠️", "orange_background")
    _divider()

    # 추천 영상
    videos = tut.get("추천_영상", [])
    if videos:
        _heading1("🎬 추천 튜토리얼 영상")
        for v in videos:
            title = v.get("제목", "영상")
            url = v.get("url", "")
            channel = v.get("채널", "")
            length = v.get("길이", "")
            desc = v.get("설명", "")
            info = f"📺 {channel}" + (f"  |  ⏱️ {length}" if length else "")
            _heading3(title)
            _paragraph(info)
            if desc:
                _paragraph(desc)
            if url:
                _bookmark(url, f"{title} — {channel}")
    _divider()

    # 관련 문서
    docs = tut.get("관련_문서", []) or tut.get("관련_링크", [])
    if docs:
        _heading1("🔗 관련 공식 문서 및 자료")
        for d in docs:
            title = d.get("제목", "문서")
            url = d.get("url", "")
            desc = d.get("설명", "")
            if url:
                _bookmark(url, f"{title}: {desc}" if desc else title)
    _divider()

    # 다음 학습
    next_learn = tut.get("다음_학습", "")
    if next_learn:
        _heading1("🚀 다음 학습 로드맵")
        _callout(next_learn, "🗺️", "blue_background")

    return blocks[:100]
