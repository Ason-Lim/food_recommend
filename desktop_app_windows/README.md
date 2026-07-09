# BrandConnect 링크 생성기 - Windows 버전

팀원 PC(Windows)에서 실행하는 버전입니다. 기능은 맥 버전과 동일합니다.

## 팀원에게 전달할 때 필요한 것

`food_recommend_windows_package.zip` 안에 필요한 것이 전부 들어 있습니다
(API 키가 든 `.env`, 로그인 세션이 든 `naver_browser_profile` 포함). IT를
잘 모르는 동료라는 점을 고려해서, 이번엔 요청하신 대로 **바로 실행되도록**
API 키와 로그인 세션을 함께 넣었습니다. 압축을 풀고 `desktop_app_windows/run.bat`만
더블클릭하면 됩니다.

```
food_recommend/
  trend_pipeline/                (트렌드 분석)
  brandconnect_link_tool/        (링크 생성 스크립트 + naver_browser_profile 포함)
  daily_food_data/                (원본 데이터)
  naver_datalab_client.py
  requirements.txt
  .env                            ← 실제 API 키 포함됨
  desktop_app_windows/            ← 지금 이 폴더
```

**중요 - 로그인 세션이 그대로 안 통할 수 있습니다.** Chrome/Chromium은 쿠키를
macOS 키체인으로 암호화해서 저장하는데, 이 암호화 키는 Windows에서 복호화가
안 됩니다. 즉 `naver_browser_profile`을 그대로 옮겨도 팀원 PC에서는 로그인이
풀려 있을 가능성이 높습니다. 이 경우 2번 버튼("로그인 창 열기")으로 새로
로그인 한 번만 하면 되고, 그다음부터는 Windows 쪽에 새로 저장된 세션이
계속 유지됩니다. (즉, 최초 1회 로그인 수고는 어차피 필요할 수 있습니다.)

**API 키는 이 zip에 포함된 실제 값이 팀원과 공유됩니다.** 같은 키를 같이 쓰면
호출 한도를 공유하고 누가 얼마나 썼는지 구분이 안 되니, 나중에 문제가 되면
`.env`를 팀원 본인 명의 키로 바꿔주세요. (`NAVER_DATALAB_설정법.md`에 발급 방법 있음)

## 팀원 PC에 설치할 것

1. Python 설치: https://python.org/downloads (Microsoft Store 버전 말고 공식 설치본)
   - 설치 화면에서 **"Add python.exe to PATH"** 체크박스 필수
   - tcl/tk (tkinter)는 공식 설치본에 기본 포함됨
2. `desktop_app_windows/run.bat` 더블클릭

## 실행 시 보안 경고가 뜨면

Windows Defender SmartScreen이 "인식할 수 없는 앱입니다" 같은 경고를 띄우면
**"추가 정보"** 클릭 → **"실행"** 클릭하면 됩니다. (직접 만든 배치파일이라
서명이 없어서 뜨는 경고이며, 파일 자체는 이 프로젝트 스크립트만 실행합니다.)

## 화면 구성 (맥 버전과 동일)

| 버튼 | 하는 일 |
|---|---|
| 1) 트렌드 분석 + 검증 실행 | daily_food_data 분석 + 데이터랩 API 검증 |
| 2) 브랜드커넥트 로그인 창 열기 | 실제 네이버 로그인 페이지를 브라우저로 엽니다. 로그인은 팀원 본인 계정으로 직접 |
| 3) 키워드로 링크 자동 생성 | 새 명령 프롬프트 창에서 링크 생성 실행 (캡차 등은 그 창에서 직접 처리) |

## 문제가 생기면

- `run.bat` 창에 에러 메시지가 그대로 남아있으니 그 내용을 캡처해서 공유해주세요.
- Chromium 설치가 안 되면 명령 프롬프트에서 직접: `python -m playwright install chromium`
