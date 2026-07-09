# 식품 트렌드 → 브랜드커넥트 키워드 자동화 파이프라인

크롬 확장 프로그램 '네이버 브랜드 커넥터 쇼핑 검색'은 사람이 키워드를 한 개씩
입력해야 상품을 검색할 수 있습니다. 이 폴더의 스크립트들은 **"어떤 키워드를
검색할지 정하는 과정"** 자체를 자동화해서, 확장프로그램(혹은
`brandconnect_link_tool`)에 넣을 키워드 목록을 매번 스스로 만들어냅니다.

## 전체 흐름

```
daily_food_data (날짜별 랭킹 CSV)
        │
        ▼
1) analyze_daily_food_data.py   → 실제 순위 변동 기반 '상승 후보' 추출
        │
        ▼
2) validate_with_datalab.py     → 네이버 데이터랩 API로 진짜 상승인지 재검증
        │
        ▼
   trend_analysis/keywords_for_brandconnect.txt  (최종 확정 키워드 목록)
        │
        ▼
3) brandconnect_link_tool/brandconnect_link_generator.py --keywords-file ...
        │
        ▼
   제휴 상품 링크 CSV
```

## 중요: 실제로 발견한 데이터 문제

`daily_food_data`를 분석하는 과정에서 아래 사실을 확인했습니다.

- **2026-06-01 ~ 2026-06-15**: 매일 최대 500개 키워드가 들어있고, 실제로 순위가
  날마다 변합니다. → 신뢰 가능한 데이터로 판단해 이 구간만 순위 분석에 사용했습니다.
- **2026-06-16 ~ 2026-07-08 (23일치)**: 모든 날짜에 정확히 동일한 10개 키워드
  (닭가슴살, 프로틴, 제로음료, 밀키트, 오메가3, 비건, 저당, 곤약, 샐러드, 요거트)가
  순서까지 완전히 똑같이 반복되고 있습니다. 실제 일별 변동 데이터로 보기 어렵습니다.
  (이 구간을 만든 수집 스크립트/프로세스를 한번 점검해보시는 걸 권장합니다.)

그래서 이 10개 키워드를 네이버 데이터랩 API로 실제 교차검증했더니:

| 키워드 | 실제 velocity (최근/이전 구간 비율) | 판정 |
|---|---|---|
| 제로음료 | 1.53 | 실제로 상승 |
| 곤약 | 1.21 | 실제로 상승 |
| 프로틴 | 1.17 | 실제로 상승 |
| 닭가슴살 | 1.09 | 실제로 상승 |
| 샐러드 | 1.07 | 실제로 상승 |
| 요거트 | 0.94 | 보합/하락 |
| 저당 | 0.85 | 하락 |
| 밀키트 | 0.91 | 하락 |
| **비건** | **0.14** | **급하락 (정적 목록과 반대)** |

즉 정적으로 반복된 10개 목록 중 5개(제로음료·곤약·프로틴·닭가슴살·샐러드)는
실제로도 상승 신호가 있었지만, **비건은 실제 데이터랩 지표상 오히려 검색 비율이
크게 줄고 있어** 그대로 믿고 쓰기엔 위험했습니다. 이번 파이프라인은 이런 검증을
자동으로 하도록 만들었습니다.

## 사용법

```bash
cd /Users/mom/food_recommend/trend_pipeline
python3 -m pip install -r ../requirements.txt --break-system-packages

# 1) 로컬 랭킹 데이터 분석
python3 analyze_daily_food_data.py

# 2) 데이터랩 API로 검증 (프로젝트 루트 .env의 키 사용)
python3 validate_with_datalab.py

# 또는 위 두 단계를 한 번에:
python3 run_pipeline.py
```

결과는 `trend_analysis/` 폴더에 생성됩니다.

- `rising_keywords.csv` : 1단계 결과 (로컬 순위 기반 상승 점수 전체)
- `final_validated_keywords.csv` : 2단계 결과 (데이터랩 velocity까지 반영한 최종 판정)
- `keywords_for_brandconnect.txt` : '상승'으로 확정된 키워드만 모은 목록

## 브랜드커넥트 링크 생성으로 이어가기

```bash
cd /Users/mom/food_recommend/brandconnect_link_tool
python3 brandconnect_link_generator.py \
    --creator-id 971564859961248 \
    --keywords-file ../trend_pipeline/trend_analysis/keywords_for_brandconnect.txt
```

## 주기적으로 돌리려면

`daily_food_data`에 새 날짜 CSV가 계속 쌓인다는 전제 하에, 이 파이프라인을
스케줄(예: 매일 아침)로 돌리면 매번 새로운 상승 키워드를 자동으로 뽑아낼 수
있습니다. 원하시면 스케줄 등록도 도와드릴 수 있습니다.
