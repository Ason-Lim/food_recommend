# 애플소다 블로그 원고 생성기

`trend_pipeline`이 검증한 상승 키워드로 애플소다 블로그 원고를 자동 작성하는
별도 앱입니다. 기존 `BrandConnectLinkGenerator` 앱은 그대로 두고 새로 만들었습니다.

## 처음 실행할 때

1. 프로젝트 루트 `.env`에 `ANTHROPIC_API_KEY` 입력 (https://console.anthropic.com 에서 발급)
2. `BlogDraftGenerator.app`을 **우클릭 → 열기** (macOS 보안 경고 최초 1회 우회)

## 사용 순서

1. 먼저 `trend_pipeline`(또는 `BrandConnectLinkGenerator` 앱의 1번 버튼)으로
   `final_validated_keywords.csv`를 최신 상태로 만들어두세요.
2. `BlogDraftGenerator.app`을 엽니다.
3. 필요하면 "상위 키워드 개수"와 "제목"을 입력하고(비워두면 자동),
   **"블로그 원고 생성 시작"** 클릭
4. 완료되면 `blog_drafts/` 폴더에 새 원고(.md)가 생성됩니다.
   **"생성된 폴더 열기"** 버튼으로 바로 확인할 수 있습니다.

## 자동으로 항상 포함되는 것 (AI 응답과 무관하게 고정)

- 대가성 고지 문구 (공정거래위원회 지침, 본문 최상단)
- 발행 전 체크리스트
- 제휴 링크 삽입 안내

이 부분은 AI가 빠뜨릴 수 없도록 스크립트가 항상 고정으로 붙입니다.

## 문제가 생기면

- `blog_generator_app/last_run.log`에서 오류 확인
- "ANTHROPIC_API_KEY가 없습니다" 오류가 뜨면 `.env` 확인
- 인터넷 연결이 필요합니다 (Claude API 호출)
