"""
네이버 오픈 API - 데이터랩(검색어 트렌드 / 쇼핑인사이트) 클라이언트
=====================================================================

.env 파일에서 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 값을 읽어와
아래 세 가지 공식 API를 호출하는 함수를 제공합니다.

1. search_trend()                 : 검색어 트렌드 (통합 검색어)
2. shopping_category_trend()      : 쇼핑인사이트 - 분야별 트렌드
3. shopping_category_keyword_trend(): 쇼핑인사이트 - 분야 내 키워드별 트렌드

사전 준비:
    1) https://developers.naver.com/apps 에서 애플리케이션 등록
       (사용 API: '검색' > 데이터랩(검색어트렌드), 데이터랩(쇼핑인사이트) 체크)
    2) 발급받은 Client ID / Client Secret을 이 폴더의 .env 파일에 입력
        NAVER_CLIENT_ID=...
        NAVER_CLIENT_SECRET=...
    3) pip install python-dotenv requests --break-system-packages

참고 문서: https://developers.naver.com/docs/serviceapi/datalab/
"""

import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

# 이 파일이 있는 폴더의 .env를 명시적으로 로드 (실행 위치와 무관하게 동작)
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

SEARCH_TREND_URL = "https://openapi.naver.com/v1/datalab/search"
SHOPPING_CATEGORY_URL = "https://openapi.naver.com/v1/datalab/shopping/categories"
SHOPPING_KEYWORD_URL = "https://openapi.naver.com/v1/datalab/shopping/category/keywords"


class NaverDataLabError(Exception):
    pass


def _check_credentials():
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        raise NaverDataLabError(
            "NAVER_CLIENT_ID / NAVER_CLIENT_SECRET이 설정되지 않았습니다. "
            f".env 파일({_ENV_PATH})에 값을 입력했는지 확인하세요."
        )


def _headers():
    return {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        "Content-Type": "application/json",
    }


def _post(url, body):
    _check_credentials()
    response = requests.post(url, headers=_headers(), data=json.dumps(body, ensure_ascii=False).encode("utf-8"))
    if response.status_code != 200:
        raise NaverDataLabError(f"API 호출 실패 ({response.status_code}): {response.text}")
    return response.json()


def search_trend(keyword_groups, start_date, end_date, time_unit="date", device=None, gender=None, ages=None):
    """
    통합 검색어 트렌드 조회.

    keyword_groups: [{"groupName": "그룹명", "keywords": ["키워드1", "키워드2"]}, ...]  (최대 5그룹, 그룹당 최대 20개 키워드)
    start_date / end_date: "YYYY-MM-DD" (2016-01-01 이후)
    time_unit: "date" | "week" | "month"
    device: None | "pc" | "mo"
    gender: None | "m" | "f"
    ages: None 또는 ["1".."11"] 리스트 (1: 0~12세 ... 11: 60세 이상)
    """
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": keyword_groups,
    }
    if device:
        body["device"] = device
    if gender:
        body["gender"] = gender
    if ages:
        body["ages"] = ages
    return _post(SEARCH_TREND_URL, body)


def shopping_category_trend(category_name, category_code, start_date, end_date,
                             time_unit="date", device=None, gender=None, ages=None):
    """
    쇼핑인사이트 - 분야별 트렌드 조회 (클릭량 상대 비율).

    category_name: 결과에 표시될 이름 (예: "식품")
    category_code: 네이버 쇼핑 카테고리 코드 (예: "50000006")
    """
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "category": [{"name": category_name, "param": [category_code]}],
    }
    if device:
        body["device"] = device
    if gender:
        body["gender"] = gender
    if ages:
        body["ages"] = ages
    return _post(SHOPPING_CATEGORY_URL, body)


def shopping_category_keyword_trend(category_code, keyword_groups, start_date, end_date,
                                     time_unit="date", device=None, gender=None, ages=None):
    """
    쇼핑인사이트 - 분야 내 키워드별 트렌드 조회.
    (동일 분야 안에서 후보 키워드들의 상대적 클릭 비율 변화를 비교할 때 사용)

    category_code: 네이버 쇼핑 카테고리 코드 (예: "50000006", 문자열 하나)
    keyword_groups: [{"name": "키워드명", "param": ["키워드1", "키워드2"]}, ...] (최대 5개)
    """
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "category": category_code,
        "keyword": keyword_groups,
    }
    if device:
        body["device"] = device
    if gender:
        body["gender"] = gender
    if ages:
        body["ages"] = ages
    return _post(SHOPPING_KEYWORD_URL, body)


if __name__ == "__main__":
    # 간단한 동작 확인용 예시 (실행 전 .env에 키를 넣어두세요)
    from datetime import date, timedelta

    end = date.today()
    start = end - timedelta(days=30)

    result = search_trend(
        keyword_groups=[{"groupName": "프로틴", "keywords": ["프로틴", "단백질보충제"]}],
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        time_unit="date",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
