"""
daily_food_data 급상승/신규 키워드 분석
==========================================

daily_food_data/ 폴더의 날짜별 랭킹 CSV(date,rank,keyword)를 읽어
키워드별로 아래 지표를 계산하고 '상승 점수(rising_score)' 기준으로 정렬합니다.

주의: 이 폴더의 데이터는 2026-06-01 ~ 2026-06-15는 매일 최대 500개 키워드가
들어있어 실제로 순위가 변하지만, 2026-06-16 이후 파일은 10개 키워드가
모든 날짜에 완전히 동일하게 반복되고 있어(닭가슴살, 프로틴, 제로음료, 밀키트,
오메가3, 비건, 저당, 곤약, 샐러드, 요거트) 실제 일별 변동 데이터로 보기 어렵습니다.
(수집 스크립트가 고정값을 반복 저장했을 가능성이 있습니다 - 확인 필요)

그래서 이 스크립트는:
  1) 06-01~06-15 구간(실제 변동 있는 데이터)으로 순위 기반 상승 점수를 계산하고
  2) 06-16 이후의 '고정 top10' 목록은 참고용 카테고리로 별도 표시합니다.
"""

import csv
import statistics
from pathlib import Path
from collections import defaultdict

# 이 스크립트는 food_recommend/trend_pipeline/ 안에 위치합니다.
# daily_food_data는 프로젝트 루트(food_recommend) 바로 아래에 있습니다.
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "daily_food_data"
OUTPUT_DIR = BASE_DIR / "trend_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TOP_N_PER_DAY = 500  # 랭킹 파일당 최대 순위 수 (분석 대상 상한)


def load_daily_rankings():
    """{date: {keyword: rank}} 형태로 전체 로드."""
    daily = {}
    for path in sorted(DATA_DIR.glob("food_*.csv")):
        date = path.stem.replace("food_", "")
        rankings = {}
        with open(path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rankings[row["keyword"]] = int(row["rank"])
        daily[date] = rankings
    return daily


def detect_variable_window(daily):
    """날짜별로 서로 다른 랭킹 셋을 갖는(=실제 변동이 있는) 날짜만 추려냄."""
    dates = sorted(daily.keys())
    variable_dates = [d for d in dates if len(daily[d]) > 10]
    static_dates = [d for d in dates if d not in variable_dates]
    return variable_dates, static_dates


def compute_rising_scores(daily, variable_dates):
    """
    변동 구간(variable_dates)에서 키워드별 상승 점수 계산.

    - early_avg_rank: 앞쪽 절반 구간 평균 순위 (없으면 결측)
    - late_avg_rank : 뒤쪽 절반 구간 평균 순위
    - rank_gain     : early_avg_rank - late_avg_rank (양수면 순위가 좋아짐 = 상승)
    - new_entry     : 앞쪽 구간엔 없다가 뒤쪽 구간에만 등장 (신규 진입)
    - appearances   : 전체 변동 구간 중 등장한 날짜 수
    """
    half = len(variable_dates) // 2
    early_dates = variable_dates[:half]
    late_dates = variable_dates[half:]

    keyword_ranks = defaultdict(list)  # keyword -> [(date, rank), ...]
    for d in variable_dates:
        for kw, rank in daily[d].items():
            keyword_ranks[kw].append((d, rank))

    rows = []
    for kw, entries in keyword_ranks.items():
        early_ranks = [r for d, r in entries if d in early_dates]
        late_ranks = [r for d, r in entries if d in late_dates]
        appearances = len(entries)

        early_avg = statistics.mean(early_ranks) if early_ranks else None
        late_avg = statistics.mean(late_ranks) if late_ranks else None

        new_entry = (early_avg is None) and (late_avg is not None)

        if early_avg is not None and late_avg is not None:
            rank_gain = early_avg - late_avg  # 양수 = 순위 상승(좋아짐)
        elif new_entry:
            # 새로 등장한 키워드는 상승 신호로 간주하되, 최근 평균 순위가 좋을수록 점수↑
            rank_gain = max(0, TOP_N_PER_DAY - late_avg) / TOP_N_PER_DAY * 50
        else:
            rank_gain = 0

        # 최종 점수: 순위 개선폭 + 등장 빈도 보너스 + 신규 진입 보너스
        score = rank_gain + appearances * 0.5 + (30 if new_entry else 0)

        rows.append({
            "keyword": kw,
            "appearances": appearances,
            "early_avg_rank": round(early_avg, 1) if early_avg else "",
            "late_avg_rank": round(late_avg, 1) if late_avg else "",
            "new_entry": new_entry,
            "rising_score": round(score, 2),
        })

    rows.sort(key=lambda r: r["rising_score"], reverse=True)
    return rows


def main():
    daily = load_daily_rankings()
    variable_dates, static_dates = detect_variable_window(daily)

    print(f"전체 날짜 수: {len(daily)}")
    print(f"실제 변동 있는 날짜: {len(variable_dates)}개 ({variable_dates[0]} ~ {variable_dates[-1]})")
    print(f"고정(변동 없음) 날짜: {len(static_dates)}개 ({static_dates[0] if static_dates else '-'} ~ {static_dates[-1] if static_dates else '-'})")

    rows = compute_rising_scores(daily, variable_dates)

    # CSV 저장
    out_path = OUTPUT_DIR / "rising_keywords.csv"
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["keyword", "appearances", "early_avg_rank", "late_avg_rank", "new_entry", "rising_score"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n상승 점수 상위 30개 (총 {len(rows)}개 키워드 중):")
    for r in rows[:30]:
        tag = "[신규]" if r["new_entry"] else ""
        print(f"  {r['keyword']:<15} 점수={r['rising_score']:<8} 등장={r['appearances']:<3} "
              f"초반평균={r['early_avg_rank']:<6} 후반평균={r['late_avg_rank']:<6} {tag}")

    # 고정 구간(06-16 이후) 목록도 참고용으로 별도 저장
    if static_dates:
        static_keywords = list(daily[static_dates[-1]].keys())
        static_path = OUTPUT_DIR / "static_period_keywords.txt"
        static_path.write_text("\n".join(static_keywords), encoding="utf-8")
        print(f"\n[참고] {static_dates[0]} 이후 고정 반복된 키워드 {len(static_keywords)}개를 "
              f"static_period_keywords.txt에 저장했습니다 (실제 변동 데이터 아님 - 확인 필요).")

    print(f"\n결과 저장: {out_path}")


if __name__ == "__main__":
    main()
