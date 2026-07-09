"""
검증된 상승 키워드로 애플소다 블로그 원고 자동 생성
========================================================

기존 analyze_daily_food_data.py / validate_with_datalab.py / run_pipeline.py는
건드리지 않는 새 스크립트입니다. 이 스크립트만 별도로 실행하면 됩니다.

trend_analysis/final_validated_keywords.csv에서 verdict == '상승'인 키워드만
골라 Anthropic API(Claude)로 애플소다 블로그 톤에 맞는 원고를 자동 작성하고,
blog_drafts/ 폴더에 저장합니다.

법적 필수 문구(대가성 고지)와 발행 체크리스트는 AI 응답에 맡기지 않고
이 스크립트가 항상 고정으로 삽입합니다 (누락 방지).

사전 준비:
    1) pip install anthropic --break-system-packages
    2) .env 에 ANTHROPIC_API_KEY=발급받은키 추가
       (https://console.anthropic.com 에서 발급)

사용법:
    cd food_recommend/trend_pipeline
    python3 generate_blog_draft.py
    python3 generate_blog_draft.py --top 5          # 상위 5개 키워드만 사용
    python3 generate_blog_draft.py --model claude-sonnet-5
"""

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent            # .../trend_pipeline
PROJECT_ROOT = BASE_DIR.parent                          # .../food_recommend
TREND_ANALYSIS_DIR = BASE_DIR / "trend_analysis"
FINAL_CSV = TREND_ANALYSIS_DIR / "final_validated_keywords.csv"
BLOG_DRAFTS_DIR = PROJECT_ROOT / "blog_drafts"

sys.path.insert(0, str(PROJECT_ROOT))

DISCLOSURE_TEXT = (
    "이 포스팅은 네이버 쇼핑 커넥트 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
)

DEFAULT_MODEL = "claude-sonnet-5"


def load_env():
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("[오류] python-dotenv가 설치되어 있지 않습니다: pip install python-dotenv --break-system-packages")
        sys.exit(1)
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


def load_rising_keywords(top_n=None):
    if not FINAL_CSV.exists():
        print(f"[오류] {FINAL_CSV} 가 없습니다. 먼저 validate_with_datalab.py를 실행하세요.")
        sys.exit(1)

    with open(FINAL_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r.get("verdict") == "상승"]

    def velocity(r):
        try:
            return float(r["datalab_velocity"])
        except (ValueError, TypeError):
            return 0.0

    rows.sort(key=velocity, reverse=True)
    if top_n:
        rows = rows[:top_n]
    return rows


def build_prompt(rows):
    keyword_lines = []
    for r in rows:
        keyword_lines.append(
            f"- {r['keyword']}: 데이터랩 velocity {r['datalab_velocity']} "
            f"(최근 구간 평균 {r.get('late_avg_ratio', '?')} / 이전 구간 평균 {r.get('early_avg_ratio', '?')})"
        )
    keyword_block = "\n".join(keyword_lines)

    return f"""당신은 네이버 블로그 '애플소다'의 포스팅 작가입니다. 아래 스타일 가이드를
그대로 따라서, 주어진 식품 키워드들로 블로그 본문을 작성해주세요.

# 스타일 가이드 (반드시 준수)
- 반말 아닌 친근한 존댓말, 공감형 도입부로 시작 (예: "~하시죠? 🙋‍♀️")
- 이모지를 적당히 사용 (과하지 않게)
- 데이터 기반 신뢰도 강조: 각 키워드마다 "데이터랩 실제 검색 데이터로 확인한
  상승세" 같은 문구와 함께 velocity 수치를 자연스럽게 풀어서 설명 (예: "검색
  비율이 약 OO% 상승")
- 키워드마다: 왜 뜨는지 설명 + 필요하면 비교 표(형태별/종류별 비교) + "✅ 구매
  포인트" 콜아웃 + "👉 **[상품명 확인하기 →](#)** *(제휴 링크 삽입)*" 링크 자리
- 전체 구성: 도입부 -> 목차 -> 키워드별 섹션 -> 구매 전 체크리스트 -> 결론
  표(고민별 추천) -> 마무리 인사말(댓글/공감 유도)
- 마지막에 "다음 포스팅 추천 주제" 3~4개 (velocity 데이터 기반 근거 포함)
- 전체 1,200~1,800자 분량의 한국어 마크다운

# 절대 포함하지 말 것
- 법적 대가성 고지 문구는 이 스크립트가 별도로 삽입하므로 본문에 넣지 마세요.
- 제목(H1)과 SEO 메타 정보 표도 이 스크립트가 별도로 붙이므로 넣지 마세요.
  "### 도입부" 부터 시작해주세요.

# 이번에 다룰 키워드 (데이터랩으로 검증된 상승 키워드, velocity 높은 순)
{keyword_block}

위 키워드로 본문만 마크다운으로 작성해주세요.
"""


def call_claude(prompt, model):
    try:
        import anthropic
    except ImportError:
        print("[오류] anthropic 패키지가 없습니다: pip install anthropic --break-system-packages")
        sys.exit(1)

    import os
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print(f"[오류] ANTHROPIC_API_KEY가 없습니다. {PROJECT_ROOT / '.env'} 에 추가해주세요.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in message.content if hasattr(block, "text"))


def assemble_markdown(rows, body_md, title_hint):
    keyword_list_str = "·".join(r["keyword"] for r in rows[:5])
    header = f"""# [블로그 포스팅] {title_hint}

> 발행용 제목 (SEO):
> **"{title_hint} | {keyword_list_str} 총정리"**

---

## ⚠️ 필수 삽입 문구 (대가성 고지, 공정거래위원회 지침)

> {DISCLOSURE_TEXT}

**본문 맨 위, 목차보다 앞에 반드시 노출되도록 배치하세요.**

---

## ✍️ 포스팅 본문

---

> {DISCLOSURE_TEXT}

"""

    footer = f"""

---

## ⚠️ 참고: 링크 삽입 안내

이 원고의 `(제휴 링크 삽입)` 표시된 부분에는 brandconnect_link_tool로 생성한
실제 제휴 링크를, 또는 수동으로 브랜드커넥트에서 만든 링크를 넣으시면 됩니다.
대상 키워드: {', '.join(r['keyword'] for r in rows)}

## ✅ 발행 전 브랜드커넥트 운영정책 체크리스트

- [ ] 대가성 문구가 본문 맨 위(목차보다 앞)에 노출되어 있는지 확인
- [ ] 과장·허위 효능 표현이 없는지 확인 (표시광고법 준수)
- [ ] 캠페인사와 협의한 게재 기간 동안 **전체공개** 상태 유지
- [ ] `(제휴 링크 삽입)` 자리에 실제 링크가 모두 채워졌는지 확인 후 발행

## 📎 데이터 출처

daily_food_data 랭킹 분석 + 네이버 데이터랩 쇼핑인사이트 식품 카테고리(50000006)
실측 데이터 기반 (trend_pipeline 자동 생성, {date.today().isoformat()})
"""

    return header + body_md.strip() + footer


def main():
    parser = argparse.ArgumentParser(description="검증된 상승 키워드로 블로그 원고 자동 생성")
    parser.add_argument("--top", type=int, default=None, help="상위 몇 개 키워드로 작성할지 (기본: 전체 상승 키워드)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="사용할 Claude 모델")
    parser.add_argument("--title", default=None, help="포스팅 제목 (생략 시 자동 생성)")
    args = parser.parse_args()

    load_env()
    rows = load_rising_keywords(top_n=args.top)
    if not rows:
        print("검증된 '상승' 키워드가 없습니다. validate_with_datalab.py 결과를 확인하세요.")
        return

    print(f"블로그에 사용할 키워드 {len(rows)}개: {[r['keyword'] for r in rows]}")

    title_hint = args.title or f"{date.today().strftime('%Y년 %-m월')} 요즘 뜨는 식품 트렌드 TOP {len(rows)}"

    prompt = build_prompt(rows)
    print("Claude API 호출 중...")
    body_md = call_claude(prompt, args.model)

    final_md = assemble_markdown(rows, body_md, title_hint)

    BLOG_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BLOG_DRAFTS_DIR / f"blog_post_{date.today().isoformat()}.md"
    out_path.write_text(final_md, encoding="utf-8")

    print(f"\n블로그 원고 저장 완료: {out_path}")


if __name__ == "__main__":
    main()
