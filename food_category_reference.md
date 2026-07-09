# 식품 크롤링 카테고리 & DB 참조 가이드

**작성일**: 2026-06-06  
**대상 플랫폼**: 네이버 쇼핑 (DataLab + 스마트스토어), 쿠팡  
**용도**: `food-trend-automation` 수집 범위 확장 참조

---

## 1. 네이버 쇼핑 DataLab (Shopping Insight)

### 1-1. DataLab API 핵심 파라미터

| 파라미터 | 값 | 설명 |
|---|---|---|
| `cid` | `50000006` | 식품 전체 (현재 시스템 사용 중) |
| `endpoint` | `https://datalab.naver.com/shoppingInsight/getShopping CategoryKeywords.naver` | 키워드 순위 |
| `timeUnit` | `date` / `week` / `month` | 집계 단위 |
| `device` | `""` (전체) / `pc` / `mo` | 기기 필터 |
| `gender` | `""` (전체) / `m` / `f` | 성별 필터 |

### 1-2. 식품 세부 카테고리 cid 목록

> **공식 전체 목록 다운로드**: 네이버 광고센터 로그인 후  
> `상품관리 > 상품정보 수신 현황 > 네이버쇼핑 카테고리ID 다운로드`  
> URL: https://adcenter.shopping.naver.com/product/manage/massmatreq/download_matchable_categories.nhn

아래는 DataLab Shopping Insight에서 확인된 식품 관련 주요 cid입니다.

| cid | 카테고리명 | 비고 |
|---|---|---|
| `50000006` | 식품 (전체) | 현재 시스템 사용 |
| `50000009` | 과일/채소 | 신선식품 |
| `50000010` | 정육/계란/유제품 | |
| `50000011` | 수산물/건어물 | |
| `50000012` | 가공식품 | 통조림, 냉동, 레토르트 |
| `50000013` | 건강식품 | 영양제, 홍삼 등 |
| `50000014` | 간식/과자/빵 | |
| `50000015` | 생수/음료/주류 | |
| `50000016` | 커피/차 | |
| `50000017` | 양념/오일/조미료 | |
| `50000018` | 유기농/친환경 | |

> ⚠️ 위 cid는 공개 DataLab에서 추출한 값이며, 세부 서브카테고리 cid는 공식 다운로드 파일로 확인 필요.

---

## 2. 네이버 스마트스토어 / 쇼핑 검색 API

### 2-1. 검색 API (shopping search)
```
GET https://openapi.naver.com/v1/search/shop.json
  ?query=닭가슴살&display=100&sort=sim&filter=naverpay
```
- `query`: 검색어
- `category1` ~ `category4`: 카테고리 필터 (아래 코드 사용)
- `exclude`: 중고=used, 성인=adult, 전문자료=rental

### 2-2. 스마트스토어 카테고리 계층 (식품)

```
식품 (50000006)
├── 과일/채소
│   ├── 과일 (50000193)
│   │   ├── 사과/배 (50000195)
│   │   ├── 복숭아/자두/살구 (50000196)
│   │   ├── 포도/체리 (50000197)
│   │   ├── 감귤/오렌지/레몬 (50000198)
│   │   ├── 딸기/블루베리 (50000199)
│   │   ├── 수박/참외/멜론 (50000200)
│   │   ├── 바나나/망고/파인애플 (50000201)  ← 이색과일
│   │   ├── 아보카도/두리안/용과 등 (이색과일)
│   │   └── 건과일/말린과일 (50000202)
│   ├── 채소 (50000203)
│   │   ├── 잎채소/쌈채소 (50000204)
│   │   ├── 뿌리채소 (50000205)
│   │   ├── 열매채소/고추 (50000206)
│   │   ├── 브로콜리/양배추/콜리플라워 (50000207)
│   │   ├── 마늘/양파/파 (50000208)
│   │   ├── 호박/오이/가지 (50000209)
│   │   └── 유기농/친환경 채소
│   ├── 나물/버섯
│   │   ├── 버섯 (50000210)
│   │   └── 나물/산나물
│   └── 허브/새싹
│       ├── 허브 (바질, 로즈마리, 민트 등)
│       └── 새싹/마이크로그린
│
├── 정육/계란/유제품
│   ├── 소고기 (50000211)
│   ├── 돼지고기 (50000212)
│   ├── 닭고기/오리고기 (50000213)
│   ├── 계란/오리알 (50000214)
│   └── 유제품 (치즈, 버터, 우유)
│
├── 수산물/건어물
│   ├── 생선류 (50000215)
│   ├── 조개/갑각류/연체류 (50000216)
│   ├── 건어물/젓갈/어묵 (50000217)
│   └── 해조류/미역/김
│
├── 가공식품
│   ├── 통조림/캔 (50000218)
│   ├── 냉동식품 (50000219)
│   ├── 면류 (라면, 파스타, 국수)
│   ├── 즉석밥/죽/레토르트 (50000220)
│   ├── 햄/소시지/베이컨 (50000221)
│   ├── 두부/콩나물/묵
│   └── 김치/장류 (50000222)
│
├── 건강식품
│   ├── 건강기능식품 (50000223)
│   ├── 비타민/미네랄 (50000224)
│   ├── 홍삼/인삼 (50000225)
│   ├── 오메가3/EPA/DHA (50000226)
│   ├── 프로바이오틱스/유산균 (50000227)
│   ├── 콜라겐/히알루론산 (50000228)
│   ├── 다이어트/체중조절 (50000229)
│   ├── 단백질/헬스보충제 (50000230)
│   └── 건강즙/발효액 (50000231)
│
├── 간식/과자/빵
│   ├── 과자/스낵 (50000232)
│   ├── 초콜릿/캔디/젤리 (50000233)
│   ├── 빵/케이크/떡 (50000234)
│   └── 시리얼/그래놀라
│
├── 생수/음료/주류
│   ├── 생수/탄산수 (50000235)
│   ├── 탄산음료/주스 (50000236)
│   ├── 건강음료/이온음료 (50000237)
│   ├── 맥주/와인/막걸리 (50000238)
│   └── 전통주
│
├── 커피/차
│   ├── 원두커피 (50000239)
│   ├── 인스턴트커피/믹스 (50000240)
│   ├── 녹차/홍차/허브차 (50000241)
│   └── 기능성 차/발효차
│
├── 양념/오일/조미료
│   ├── 간장/된장/고추장 (50000242)
│   ├── 식용유/참기름/들기름 (50000243)
│   ├── 소금/설탕/식초 (50000244)
│   ├── 소스/케첩/마요네즈 (50000245)
│   ├── 향신료/스파이스 (50000246)
│   └── 국/찌개 베이스/육수
│
└── 유기농/친환경
    ├── 유기농 인증 식품
    └── 무농약/친환경 식품
```

---

## 3. 쿠팡 카테고리 ID

### 3-1. 쿠팡 카테고리 URL 구조
```
https://www.coupang.com/np/categories/{categoryId}
https://www.coupang.com/np/search?q={keyword}&channel=user&listSize=36&page=1
```

### 3-2. 쿠팡 식품 주요 카테고리 ID

| categoryId | URL | 카테고리명 |
|---|---|---|
| `519489` | /np/categories/519489 | **신선식품** (베이커리, 과일, 정육/계란, 냉장/냉동) |
| `519619` | /np/categories/519619 | **식품** (과일, 견과/건과, 채소, 축산/계란) |
| `194276` | /np/categories/194276 | **식품** (프리미엄, 수입식품, 선물세트, 건강식품) |
| `420186` | /np/categories/420186 | 과일 (토마토, 참외, 오렌지, 사과/배) |
| `196076` | /np/categories/196076 | **건강식품** (건강기능식품, 홍삼, 건강즙, 비타민) |
| `194190` | /np/categories/194190 | 귤/감귤 (leaf category 예시) |

### 3-3. 쿠팡 세부 카테고리 발굴 방법

**방법 1 (권장): WING 셀러 포털 전체 다운로드**
```
WING 로그인 → 상품관리 → 상품등록 → 상품대량등록(엑셀)
→ 엑셀업로드 → [전체 카테고리 정보 다운로드]
```
`displayCategoryCode` 컬럼이 크롤링에 쓰는 categoryId와 동일.

**방법 2: URL 파싱으로 카테고리 트리 탐색**
```python
import requests
from bs4 import BeautifulSoup

# 쿠팡 카테고리 페이지에서 서브카테고리 링크 추출
def get_sub_categories(category_id):
    url = f"https://www.coupang.com/np/categories/{category_id}"
    headers = {"User-Agent": "Mozilla/5.0 ..."}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    # 서브카테고리 링크 파싱
    links = soup.select("a[href*='/np/categories/']")
    return [(a.text.strip(), a['href']) for a in links]
```

**방법 3: 쿠팡 Open API (판매자 전용)**
```
GET https://api-gateway.coupang.com/v2/providers/seller_api/apis/api/v1/categories
```
- 판매자 Access Key / Secret Key 필요
- 전체 카테고리 트리를 JSON으로 반환

> ⚠️ **2024년 이후 주의**: Akamai Bot Manager 도입으로 Selenium/Playwright 등 자동화 도구가 차단됨. 공식 API 우선 사용 권장.

---

## 4. 식품 전체 분류 체계 (크롤링 대상 taxonomy)

### 4-1. 신선식품 (Fresh)

```yaml
fresh_produce:
  fruits:                          # 과일
    domestic:
      - 사과, 배, 복숭아, 포도, 자두
      - 감귤, 한라봉, 천혜향, 레드향
      - 딸기, 블루베리, 참외, 수박
      - 토마토, 방울토마토, 체리, 무화과
    imported_exotic:               # 이색/수입 과일
      - 망고, 아보카도, 두리안, 용과(드래곤프루트)
      - 파인애플, 바나나, 파파야, 구아바
      - 리치, 람부탄, 마라쿠자, 스타프루트
      - 석류, 코코넛, 패션프루트
    dried_fruits:                  # 건과일
      - 건포도, 건자두, 건살구, 건망고
      - 대추, 곶감, 건블루베리, 크랜베리

  vegetables:                      # 채소/야채
    leafy:                         # 잎채소
      - 상추, 깻잎, 시금치, 쑥갓, 청경채
      - 케일, 루꼴라, 로메인, 어린잎채소
    root:                          # 뿌리채소
      - 당근, 무, 연근, 우엉, 감자, 고구마
      - 비트, 토란, 야콘
    allium:                        # 마늘/파류
      - 마늘, 양파, 대파, 쪽파, 부추
    brassica:                      # 배추/브로콜리
      - 배추, 양배추, 브로콜리, 콜리플라워
      - 방울양배추(브뤼셀스프라우트), 청경채
    fruiting:                      # 열매채소
      - 오이, 호박, 가지, 피망, 파프리카
      - 고추, 옥수수, 콩, 완두
    herbs:                         # 허브
      - 바질, 로즈마리, 타임, 민트
      - 고수(실란트로), 파슬리, 딜, 차이브
      - 레몬그라스, 카피르라임잎
    mushrooms:                     # 버섯
      - 느타리, 새송이, 팽이, 표고, 양송이
      - 송이, 트러플, 목이, 석이버섯
    sprouts:                       # 새싹/마이크로그린
      - 새싹채소, 마이크로그린, 콩나물, 숙주

  meat_eggs:                       # 정육/계란
    - 소고기(한우/수입), 돼지고기, 닭고기
    - 오리고기, 양고기, 염소고기
    - 계란, 메추리알, 오리알

  seafood:                         # 수산물
    - 생선(연어, 참치, 고등어, 갈치, 광어)
    - 조개(바지락, 홍합, 굴, 전복)
    - 갑각류(새우, 게, 랍스터)
    - 해조류(미역, 다시마, 김, 톳)
    - 건어물(북어, 명태, 오징어채)
```

### 4-2. 가공식품 (Processed)

```yaml
processed_foods:
  instant_convenience:
    - 즉석밥, 컵밥, 햇반
    - 라면, 컵라면, 우동
    - 레토르트 (카레, 짜장, 국/찌개)
    - 간편조리식 (밀키트)

  preserved:
    - 통조림(참치, 꽁치, 골뱅이)
    - 냉동식품(만두, 피자, 돈가스)
    - 햄/소시지/베이컨
    - 김치(배추김치, 깍두기, 총각김치)

  grains_carbs:
    - 쌀(현미, 찹쌀, 잡곡)
    - 밀가루/전분류
    - 파스타/국수/당면
    - 시리얼/오트밀/그래놀라

  soy_fermented:                   # 두부/발효
    - 두부, 순두부, 연두부
    - 청국장, 낫토
    - 된장, 간장(공장/전통)
```

### 4-3. 건강식품 (Health & Supplements)

```yaml
health_foods:
  functional_supplements:          # 건강기능식품 (식약처 인증)
    vitamins:
      - 비타민C, 비타민D, 비타민B군, 멀티비타민
    omega:
      - 오메가3(EPA/DHA), 크릴오일
    probiotics:
      - 유산균, 프로바이오틱스, 프리바이오틱스
    collagen_beauty:
      - 콜라겐, 히알루론산, 비오틴
    mineral:
      - 마그네슘, 칼슘, 아연, 철분, 셀레늄
    immunity:
      - 홍삼, 인삼, 흑마늘
      - 밀크씨슬, 루테인, 아스타잔틴

  diet_fitness:
    - 단백질보충제(프로틴), BCAA
    - 다이어트 보조제, CLA, L-카르니틴
    - 방탄커피, MCT오일, 곤약

  traditional_health:
    - 건강즙(흑마늘즙, 석류즙, 홍삼즙)
    - 발효효소, 식초(홍초, 흑초)
    - 한방건강식품(녹용, 꿀, 로열제리)

  superfoods:
    - 퀴노아, 치아씨드, 아마씨
    - 마카, 스피루리나, 클로렐라
    - 아사이베리, 고지베리, 아로니아
```

### 4-4. 양념/조미료 (Seasonings)

```yaml
seasonings:
  korean_basics:
    - 고추장, 된장, 쌈장, 청국장
    - 간장(양조/왜간장/국간장)
    - 고춧가루, 참기름, 들기름
    - 소금(천일염/죽염/히말라야핑크솔트)

  oils_vinegars:
    - 식용유(콩기름, 카놀라, 해바라기)
    - 올리브오일(엑스트라버진 포함)
    - 코코넛오일, 아보카도오일
    - 식초(사과식초, 현미식초, 발사믹)

  sauces_condiments:
    - 케첩, 마요네즈, 머스타드
    - 굴소스, 피시소스, 스리라차
    - 불고기소스, 바비큐소스, 데리야키
    - 드레싱(샐러드, 참깨)

  spices_herbs_dried:
    - 후추, 커민, 파프리카파우더
    - 강황, 카레파우더, 오레가노
    - 계피, 넛맥, 올스파이스
    - 건조허브(바질, 로즈마리, 타임)

  fermented_paste:
    - 새우젓, 멸치액젓, 까나리액젓
    - 미소(일본된장), 두반장
```

### 4-5. 음료/차/커피 (Beverages)

```yaml
beverages:
  water:
    - 생수(삼다수, 에비앙), 탄산수(페리에, 산펠레그리노)
    - 수소수, 알칼리수, 이온음료(포카리, 게토레이)

  hot_beverages:
    - 원두커피(싱글오리진, 블렌드)
    - 인스턴트커피/믹스
    - 녹차, 홍차, 보이차
    - 허브차(캐모마일, 히비스커스, 루이보스)
    - 기능성차(당귀차, 둥굴레, 도라지)

  cold_beverages:
    - 과채주스(착즙, 냉압착)
    - 탄산음료, 에너지드링크
    - 식혜, 수정과, 전통음료

  alcohol:
    - 맥주(국산/수입/크래프트)
    - 와인(레드/화이트/스파클링)
    - 막걸리, 청주, 전통주
    - 위스키, 진, 보드카
```

---

## 5. Google Trends 카테고리 매핑 (현재 시스템 22개)

기존 `config/default.yaml`에 추가 권장 카테고리:

```yaml
# 현재 22개 → 아래 추가 고려
additional_google_categories:
  - id: 1240
    name: "이색과일_수입과일"
    anchor: "이색과일"
  - id: 1241
    name: "허브_요리재료"
    anchor: "허브"
  - id: 1242
    name: "비건_채식"
    anchor: "비건"
  - id: 1243
    name: "간편식_밀키트"
    anchor: "밀키트"
  - id: 1244
    name: "발효식품_장류"
    anchor: "김치"
  - id: 1245
    name: "프로틴_헬스식품"
    anchor: "프로틴"
  - id: 1246
    name: "제로음료_다이어트"
    anchor: "제로칼로리"
  - id: 1247
    name: "수입식품_글로벌"
    anchor: "수입식품"
```

---

## 6. 크롤링 전략 요약

### 플랫폼별 접근법

| 플랫폼 | 권장 방법 | 주의사항 |
|---|---|---|
| **네이버 DataLab** | 공식 역방향 API (현재 사용 중) | Rate limit: 초당 1회 이하 |
| **네이버 쇼핑 검색** | 공식 Search API (OAuth) | 하루 25,000회 제한 |
| **네이버 스마트스토어** | Shopping Insight cid별 순위 수집 | 25페이지 × 20개 = 500개/cid |
| **쿠팡 상품** | Open API (판매자 키) or 웹 파싱 | Akamai 차단: User-Agent 필수, 딜레이 2-5초 |
| **쿠팡 키워드 트렌드** | 별도 API 없음 → 검색 결과 수/순위 수집 | robots.txt 준수 |

### Python 크롤링 기본 패턴

```python
# collectors/coupang.py 예시 골격
import time
import requests
from bs4 import BeautifulSoup
from datetime import date
import pandas as pd
from .base import Collector

COUPANG_FOOD_CATEGORIES = {
    "신선식품": 519489,
    "식품_전체": 519619,
    "과일": 420186,
    "건강식품": 196076,
    "식품_프리미엄": 194276,
}

class CoupangCollector(Collector):
    BASE_URL = "https://www.coupang.com/np/categories/{}"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9",
    }

    def collect(self, target_date: date, category_id: int, pages: int = 5) -> pd.DataFrame:
        rows = []
        for page in range(1, pages + 1):
            url = self.BASE_URL.format(category_id)
            params = {"page": page, "listSize": 72, "sortType": "BEST_SELLER"}
            resp = requests.get(url, params=params, headers=self.HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select("li.baby-product")
            for rank, item in enumerate(items, start=(page - 1) * 72 + 1):
                name_tag = item.select_one(".name")
                price_tag = item.select_one(".price-value")
                rating_tag = item.select_one(".rating")
                if name_tag:
                    rows.append({
                        "date": target_date,
                        "rank": rank,
                        "keyword": name_tag.text.strip(),
                        "price": price_tag.text.strip() if price_tag else None,
                        "rating": rating_tag.text.strip() if rating_tag else None,
                        "category_id": category_id,
                        "source": "coupang",
                    })
            time.sleep(2.5)  # Akamai 차단 방지
        return pd.DataFrame(rows)
```

### 권장 수집 스케줄 (config/default.yaml 추가)

```yaml
schedule:
  naver_hour: 6        # 네이버 DataLab (현재)
  google_hour: 8       # Google Trends (현재)
  integration_hour: 7  # 통합 (현재)
  coupang_hour: 7      # 쿠팡 추가 시 (네이버 이후)
```

---

## 7. 식품안전처 공공 DB (오픈 데이터)

크롤링 외 보완 데이터로 활용 가능:

| DB명 | URL | 활용처 |
|---|---|---|
| 식품영양성분 DB | https://various.foodsafetykorea.go.kr/nutrient/ | 성분명 → 트렌드 매핑 |
| 건강기능식품 공시 DB | https://www.foodsafetykorea.go.kr/ | 인증 성분 목록 확인 |
| 농산물 표준코드 | https://www.naqs.go.kr | 농산물 표준명 정규화 |
| 수산물 이력제 | https://www.fishtrace.go.kr | 수산물 품목 분류 |
| 공공데이터포털 식품 | https://www.data.go.kr (식품 검색) | 다양한 식품 API |

---

## 8. 노이즈 필터 확장 (config/default.yaml)

현재 시스템 노이즈 리스트에 추가 권장:

```yaml
filters:
  # 기존 노이즈에 추가
  noise_keywords_additional:
    - "중고", "대여", "렌탈"
    - "택배", "배송", "무료배송"
    - "할인", "쿠폰", "이벤트"
    - "블로그", "후기", "리뷰"
    - "칼로리", "영양성분표"  # 정보 쿼리, 구매 의도 낮음

  # 카테고리별 valuable_words 확장
  valuable_words_by_category:
    fresh: ["국내산", "유기농", "무농약", "친환경", "당일수확", "산지직송"]
    health: ["효능", "복용법", "추천", "영양제", "건강기능식품인증"]
    processed: ["레시피", "요리법", "밀키트", "간편식"]
    seasoning: ["만드는법", "활용법", "대용량", "업소용"]
```

---

*참고: 네이버 카테고리 cid 전체 목록은 공식 다운로드 파일 기준으로 주기적 업데이트 필요.*  
*쿠팡 categoryId는 WING 포털 전체 카테고리 다운로드 또는 URL 탐색으로 확인.*
