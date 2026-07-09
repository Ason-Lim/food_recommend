# 브랜드커넥트 제휴 상품 링크 자동 생성기 사용법

키워드를 넣으면 네이버 브랜드커넥트(쇼핑 커넥트) 제휴 상품 페이지에서
검색 → 상품 클릭 → 링크 생성 → 결과 저장까지 자동으로 처리하는 스크립트입니다.

네이버가 브랜드커넥트 공식 API를 제공하지 않기 때문에, 실제 웹 화면을
그대로 자동 조작하는 방식입니다. 그래서 최초 1회는 아래 "선택자 확인" 과정이 필요합니다.

## 1. 설치

```bash
pip install playwright --break-system-packages
python -m playwright install chromium
```

## 2. 실행

```bash
python3 brandconnect_link_generator.py --creator-id 971564859961248 --keywords "텀블러,캠핑의자,공기청정기"
```

키워드가 많으면 파일로 관리하는 걸 추천합니다.

`keywords.txt` (한 줄에 하나씩):
```
텀블러
캠핑의자
공기청정기
```

```bash
python brandconnect_link_generator.py --creator-id 971564859961248 --keywords-file keywords.txt --output product_links.csv
```

- `--creator-id` : 브랜드커넥트 주소의 숫자 부분 (예: `https://brandconnect.naver.com/971564859961248/...` → `971564859961248`)
- `--output` : 결과가 저장될 CSV 파일 (기본값 `product_links.csv`)
- 처음 실행하면 브라우저 창이 뜹니다. 로그인이 안 되어 있으면 터미널에 안내 메시지가 뜨고, 로그인 창에서 직접 로그인한 뒤 터미널에서 Enter를 누르면 됩니다.
- 로그인 세션은 `./naver_browser_profile` 폴더에 저장되므로, **다음번 실행부터는 다시 로그인할 필요가 없습니다.**

## 3. 화면 구조가 다를 때 (선택자 조정)

브랜드커넥트 페이지의 실제 HTML 구조를 미리 확인할 수 없었기 때문에,
`brandconnect_link_generator.py` 상단의 `SELECTORS` 값은 일반적인 패턴으로
채워둔 추정값입니다. 실행 중 아래처럼 안내 메시지가 뜨면:

```
[알림] '링크 생성 버튼' 요소를 자동으로 찾지 못했습니다.
브라우저 창에서 해당 버튼/항목을 직접 클릭해 주세요.
```

그 단계만 직접 클릭하고 Enter를 누르면 스크립트가 계속 진행됩니다.
(자동화가 100%는 아니지만 멈추지 않고 끝까지 실행됩니다.)

같은 안내가 매번 반복돼서 번거롭다면, 아래 방법으로 선택자를 한 번만 고쳐두면
완전 자동화됩니다.

### 선택자 찾는 법 (크롬 개발자도구)

1. 브랜드커넥트 상품 페이지를 크롬에서 엽니다.
2. 자동으로 못 찾았던 요소(예: '링크 생성' 버튼) 위에서 **마우스 우클릭 → 검사(Inspect)**.
3. 개발자도구에서 해당 요소가 파란색으로 강조되어 표시됩니다.
4. 강조된 HTML 태그를 우클릭 → **Copy → Copy selector**.
5. 복사한 값을 `brandconnect_link_generator.py`의 `SELECTORS` 딕셔너리에서
   해당 항목에 붙여넣습니다.

| SELECTORS 키 | 의미 |
|---|---|
| `search_input` | 상품 검색창 |
| `product_item` | 검색 결과 상품 목록의 각 항목 |
| `generate_link_button` | '링크 생성'/'링크 복사' 버튼 |
| `link_result_field` | 생성된 링크가 표시되는 입력창 |

## 4. 결과 확인

실행이 끝나면 지정한 CSV 파일에 아래 컬럼으로 저장됩니다.

| timestamp | keyword | product_name | link |
|---|---|---|---|

## 참고 / 한계

- 브랜드커넥트는 크리에이터 계정에 연동된 개인화 제휴 링크를 발급하므로, 로그인한
  계정 기준으로 링크가 생성됩니다.
- 네이버가 페이지 디자인을 바꾸면 `SELECTORS`를 다시 맞춰야 할 수 있습니다.
- 검색 결과에서 항상 "첫 번째 상품"을 대상으로 링크를 생성합니다. 원하는 상품이
  다르면 실행 중 브라우저 창에서 직접 다른 상품을 선택해 주세요.
