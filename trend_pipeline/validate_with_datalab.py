"""
후보 키워드를 네이버 데이터랩 쇼핑인사이트 API로 검증
========================================================

analyze_daily_food_data.py가 만든 rising_keywords.csv 상위 후보들을
실제 데이터랩 '식품' 카테고리(50000006) 키워드별 트렌드 API로 조회해서
최근 구간 대비 이전 구간의 상대 검색 비율(velocity)을 계산합니다.

velocity = 최근 구간 평균 ratio / 이전 구간 평균 ratio
  - 1.0보다 크면 상승, 작으면 하락

같은 폴더의 naver_datalab_client.py(.env의 NAVER_CLIENT_ID/SECRET 사용)를 통해
공식 API(https://openapi.naver.com/v1/datalab/shopping/category/keywords)를 호출합니다.
"""

import csv
import sys
from pathlib import Path
from datetime import date, timedelta

# 이 스크립트는 food_recommend/trend_pipeline/ 안에 위치합니다.
# naver_datalab_client.py는 프로젝트 루트(food_recommend)에 있습니다.
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
from naver_datalab_client import shopping_category_keyword_trend, NaverDataLabError

FOOD_CATEGORY_CODE = "50000006"  # 네이버 쇼핑 '식품' 카테고리
TREND_ANALYSIS_DIR = BASE_DIR / "trend_analysis"
INPUT_CSV = TREND_ANALYSIS_DIR / "rising_keywords.csv"
STATIC_KEYWORDS_TXT = TREND_ANALYSIS_DIR / "static_period_keywords.txt"
OUTPUT_CSV = TREND_ANALYSIS_DIR / "final_validated_keywords.csv"
OUTPUT_KEYWORDS_TXT = TREND_ANALYSIS_DIR / "keywords_for_brandconnect.txt"

BATCH_SIZE = 5           # API 한 번 호출 시 넣을 수 있는 최대 키워드 수
TOP_LOCAL_CANDIDATES = 20  # rising_keywords.csv에서 검증할 상위 후보 개수
LOOKBACK_DAYS = 28       # 최근 구간 계산에 사용할 일 수
VELOCITY_THRESHOLD = 1.0  # 이 값 이상만 '검증된 상승 키워드'로 채택


def load_local_candidates(limit=TOP_LOCAL_CANDIDATES):
    """
    검증 대상 후보 = (1) 로컬 순위 분석 상위 N개 + (2) '고정 반복' 구간에 등장한
    키워드(static_period_keywords.txt, 있는 경우). static 목록은 실제 변동 데이터가
    아니라 의심스럽지만, 그렇다고 무시하면 놓칠 수 있으므로 반드시 함께 검증합니다.
    """
    if not INPUT_CSV.exists():
        print(f"[오류] {INPUT_CSV} 가 없습니다. 먼저 analyze_daily_food_data.py를 실행하세요.")
        sys.exit(1)
    with open(INPUT_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    local_rows = {r["keyword"]: r for r in rows}
    candidates = [r["keyword"] for r in rows[:limit]]

    if STATIC_KEYWORDS_TXT.exists():
        static_keywords = [k.strip() for k in STATIC_KEYWORDS_TXT.read_text(encoding="utf-8").splitlines() if k.strip()]
        for kw in static_keywords:
            if kw not in candidates:
                candidates.append(kw)
            local_rows.setdefault(kw, {"keyword": kw, "rising_score": "(정적목록)"})

    return candidates, local_rows


def batched(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def compute_velocity(keyword_result):
    """API 응답의 data 배열(기간별 ratio)로 최근/이전 구간 평균 velocity 계산."""
    data_points = keyword_result.get("data", [])
    if len(data_points) < 4:
        return None, None, None
    half = len(data_points) // 2
    early = data_points[:half]
    late = data_points[half:]
    early_avg = sum(p["ratio"] for p in early) / len(early)
    late_avg = sum(p["ratio"] for p in late) / len(late)
    velocity = (late_avg / early_avg) if early_avg > 0 else None
    return velocity, early_avg, late_avg


def validate_keywords(keywords):
    end = date.today()
    start = end - timedelta(days=LOOKBACK_DAYS)
    results = {}

    for batch in batched(keywords, BATCH_SIZE):
        keyword_groups = [{"name": kw, "param": [kw]} for kw in batch]
        try:
            response = shopping_category_keyword_trend(
                category_code=FOOD_CATEGORY_CODE,
                keyword_groups=keyword_groups,
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                time_unit="date",
            )
        except NaverDataLabError as e:
            print(f"[경고] 배치 {batch} 조회 실패: {e}")
            continue

        for r in response.get("results", []):
            velocity, early_avg, late_avg = compute_velocity(r)
            results[r["title"]] = {
                "velocity": round(velocity, 2) if velocity is not None else None,
                "early_avg_ratio": round(early_avg, 2) if early_avg is not None else None,
                "late_avg_ratio": round(late_avg, 2) if late_avg is not None else None,
            }
    return results


def main():
    candidates, local_rows = load_local_candidates()
    print(f"검증할 후보 키워드 {len(candidates)}개: {candidates}")

    datalab_results = validate_keywords(candidates)

    final_rows = []
    for kw in candidates:
        local = local_rows.get(kw, {})
        dl = datalab_results.get(kw, {})
        velocity = dl.get("velocity")
        verdict = "데이터부족"
        if velocity is not None:
            verdict = "상승" if velocity >= VELOCITY_THRESHOLD else "하락/보합"
        final_rows.append({
            "keyword": kw,
            "local_rising_score": local.get("rising_score", ""),
            "datalab_velocity": velocity if velocity is not None else "",
            "early_avg_ratio": dl.get("early_avg_ratio", ""),
            "late_avg_ratio": dl.get("late_avg_ratio", ""),
            "verdict": verdict,
        })

    final_rows.sort(key=lambda r: (r["datalab_velocity"] if isinstance(r["datalab_velocity"], (int, float)) else -1), reverse=True)

    TREND_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["keyword", "local_rising_score", "datalab_velocity", "early_avg_ratio", "late_avg_ratio", "verdict"])
        writer.writeheader()
        writer.writerows(final_rows)

    confirmed = [r["keyword"] for r in final_rows if r["verdict"] == "상승"]
    OUTPUT_KEYWORDS_TXT.write_text("\n".join(confirmed), encoding="utf-8")

    print(f"\n결과 저장: {OUTPUT_CSV}")
    print(f"'상승'으로 검증된 키워드 {len(confirmed)}개를 {OUTPUT_KEYWORDS_TXT}에 저장했습니다.")
    print("이 파일을 brandconnect_link_tool의 --keywords-file 인자로 바로 사용할 수 있습니다.")


if __name__ == "__main__":
    main()
