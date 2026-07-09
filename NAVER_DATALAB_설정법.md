# 네이버 데이터랩 API 설정법

## 1. 애플리케이션 등록 (Client ID / Secret 발급)

이미 키를 받으셨다면 이 단계는 건너뛰어도 됩니다. 나중에 키를 재발급하거나
다른 API를 추가할 때 참고하세요.

1. https://developers.naver.com/apps 접속 (네이버 계정 로그인)
2. "Application 등록" 클릭
3. 사용 API에서 아래 항목 체크
   - 검색 (검색어트렌드용)
   - 데이터랩(쇼핑인사이트)
4. 서비스 URL은 로컬에서만 쓸 경우 `http://localhost` 등으로 입력해도 됩니다.
5. 등록 완료 후 "내 애플리케이션"에서 **Client ID**, **Client Secret** 확인

## 2. 이 프로젝트에 키 넣기

프로젝트 루트의 `.env` 파일을 열어 아래처럼 값을 채우면 됩니다.

```
NAVER_CLIENT_ID=발급받은_client_id
NAVER_CLIENT_SECRET=발급받은_client_secret
```

`.env`는 `.gitignore`에 등록되어 있어 커밋되지 않습니다.

## 3. 설치 및 테스트

```bash
python3 -m pip install -r requirements.txt --break-system-packages
python3 naver_datalab_client.py
```

정상이면 최근 30일간 "프로틴" 관련 검색어 트렌드 JSON이 출력됩니다.

## 4. 코드에서 사용하기

```python
from naver_datalab_client import search_trend, shopping_category_trend, shopping_category_keyword_trend

# 1) 통합 검색어 트렌드
search_trend(
    keyword_groups=[{"groupName": "닭가슴살", "keywords": ["닭가슴살", "닭가슴살요리"]}],
    start_date="2026-06-01",
    end_date="2026-07-08",
)

# 2) 쇼핑인사이트 - 분야별 트렌드 (예: 식품 카테고리 코드)
shopping_category_trend(
    category_name="식품",
    category_code="50000006",
    start_date="2026-06-01",
    end_date="2026-07-08",
)

# 3) 쇼핑인사이트 - 분야 내 키워드별 트렌드 비교
shopping_category_keyword_trend(
    category_code="50000006",
    keyword_groups=[
        {"name": "프로틴", "param": ["프로틴"]},
        {"name": "제로음료", "param": ["제로음료"]},
    ],
    start_date="2026-06-01",
    end_date="2026-07-08",
)
```

카테고리 코드는 네이버쇼핑 URL의 `cat_id` 값으로 확인할 수 있습니다.

## 참고

- `daily_food_data/` 폴더의 CSV(날짜별 급상승 식품 키워드 랭킹)는 이 API로 얻은 데이터를
  누적한 것으로 보입니다. 새 후보 키워드를 검증할 때 `shopping_category_keyword_trend`로
  최근 구간 대비 상승폭을 비교해볼 수 있습니다.
- 공식 문서: https://developers.naver.com/docs/serviceapi/datalab/
