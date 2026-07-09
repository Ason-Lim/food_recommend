# 🍏 애플소다 식품 트렌드 & 브랜드커넥트 블로그 초안 생성기 웹앱

이 웹 애플리케이션은 네이버 데이터랩 API와 브랜드커넥트 가이드라인을 하나로 융합하여, 인기 키워드 검색부터 어필리에이트 상품 링크 매핑, 법적 준수 사항을 반영한 AI 블로그 초안 작성까지의 모든 워크플로우를 원스톱으로 처리합니다.

---

## 🏗 주요 기능 및 화면 구성

1. **📊 트렌드 분석기 (Trend Analyzer)**
   - `daily_food_data/` 폴더에 수집된 날짜별 식품 키워드 랭킹을 실시간 분석합니다.
   - 분석 결과 도출된 키워드 후보군을 네이버 데이터랩 쇼핑인사이트 API와 교차 검증하여 상승 속도(velocity)를 산출합니다.
   - 키워드 클릭 비율 변화를 **인터랙티브 SVG 트렌드 차트**로 가시화합니다.
   - 사용자가 임의의 키워드를 직접 입력하여 데이터랩 트렌드를 즉시 조회할 수도 있습니다.
2. **🔗 브랜드커넥트 링크 (Brand Connect Links Mapper)**
   - 이미 브라우저에 설치되어 있는 **'네이버 브랜드 커넥트 검색'** 크롬 확장 프로그램과 함께 사용하도록 유기적으로 구성되어 있습니다.
   - 분석된 급상승 키워드를 1클릭 복사하고, 브랜드커넥트 상품 목록 검색 링크로 즉시 연결됩니다.
   - 복사한 키워드로 크롬 확장 프로그램에서 검색해 발급받은 제휴 상품 링크를 각 키워드 옆에 그대로 붙여넣어 매핑합니다.
3. **✍️ 블로그 에디터 (AI Blog Composer)**
   - Claude 3.5 Sonnet API를 연동하여 트렌드 데이터(velocity 수치)와 실제 매핑된 제휴 상품 링크들을 정확히 포함하는 블로그 원고 초안을 생성합니다.
   - **브랜드커넥트 가이드라인 및 표시광고법**을 엄격하게 반영하도록 AI 프롬프트를 보강했습니다.
   - 작성된 글은 마크다운 또는 텍스트 형태로 손쉽게 복사해 네이버 스마트에디터에 바로 적용할 수 있습니다.
4. **🛡️ 준수 사항 & 가이드 (Compliance Guard)**
   - 대가성 문구 노출 및 표시광고법 준수, 글 유지 기간 등의 네이버 규정을 모니터링하고 실시간으로 체크리스트를 검증합니다.

---

## 💻 로컬 실행 방법

### 1. 사전 준비 (환경 변수 등록)
프로젝트 루트 디렉토리의 `.env` 파일에 네이버 데이터랩 API 키와 Anthropic API 키가 설정되어 있어야 합니다.
```env
NAVER_CLIENT_ID=여러분의_네이버_클라이언트_ID
NAVER_CLIENT_SECRET=여러분의_네이버_클라이언트_시크릿
ANTHROPIC_API_KEY=여러분의_클로드_API_키
```

### 2. 패키지 설치
`trend_web_app` 폴더 내의 `requirements.txt` 패키지 목록을 설치합니다.
```bash
pip install -r requirements.txt --break-system-packages
```

### 3. 서버 구동
FastAPI 웹 앱을 기동합니다.
```bash
python main.py
```
서버가 시작되면 브라우저를 열고 `http://localhost:8000` 주소로 접속합니다.

---

## 🚀 GitHub 저장소 업로드 및 관리 방법

로컬에서 개발이 완료되면 아래 명령어로 GitHub 원격 저장소에 올릴 수 있습니다.

```bash
# 1. 깃 레포지토리 상태 확인 및 브랜치 설정
git status
git branch -M main

# 2. 변경사항 스테이징 및 커밋
git add .
git commit -m "feat: 네이버 데이터랩 및 브랜드커넥트 생성기 웹앱 구축 완료"

# 3. 깃허브 원격 저장소 연결 (GitHub에서 생성한 새 빈 레포지토리 주소 입력)
git remote add origin https://github.com/사용자이름/저장소이름.git

# 4. 저장소로 푸시
git push -u origin main
```

---

## 🌐 서버 배포 방법

이 웹앱은 경량화되어 있어 Heroku, Render, Railway, AWS 등의 다양한 클라우드 환경에 자유롭게 배포할 수 있습니다.

### 방법 1. Render / Railway 등 PaaS 배포 (가장 단순함)
1. 코드가 올려진 GitHub 저장소를 Render나 Railway에 연동합니다.
2. Web Service를 생성하고 빌드 및 실행 명령을 아래와 같이 세팅합니다:
   - **Build Command:** `pip install -r trend_web_app/requirements.txt`
   - **Start Command:** `python trend_web_app/main.py`
3. 플랫폼 관리 패널의 **Environment Variables (환경 변수)** 설정창에 아래 3개 변수를 등록하세요:
   - `NAVER_CLIENT_ID`
   - `NAVER_CLIENT_SECRET`
   - `ANTHROPIC_API_KEY`

### 방법 2. Docker를 이용한 컨테이너 배포
1. 제공된 `Dockerfile`을 사용해 빌드합니다. (컨텍스트 유지를 위해 반드시 **프로젝트 루트**에서 빌드 명령을 실행해야 합니다.)
```bash
docker build -t food-trend-web -f trend_web_app/Dockerfile .
```
2. 컨테이너를 로컬 또는 클라우드 서버에서 실행합니다:
```bash
docker run -d -p 8000:8000 \
  -e NAVER_CLIENT_ID="실제값" \
  -e NAVER_CLIENT_SECRET="실제값" \
  -e ANTHROPIC_API_KEY="실제값" \
  food-trend-web
```
