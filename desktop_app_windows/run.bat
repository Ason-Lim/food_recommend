@echo off
setlocal
cd /d "%~dp0"

echo === BrandConnect 링크 생성기 (Windows) ===

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo [오류] python이 설치되어 있지 않거나 PATH에 등록되어 있지 않습니다.
    echo https://www.python.org/downloads/ 에서 설치해주세요.
    echo 설치 화면에서 "Add python.exe to PATH" 체크박스를 꼭 선택하세요.
    echo.
    pause
    exit /b 1
)

python -c "import tkinter" >nul 2>nul
if errorlevel 1 (
    echo.
    echo [오류] 이 파이썬에는 tkinter가 없습니다. python.org 공식 설치 파일을 사용해주세요.
    echo (Microsoft Store 버전 파이썬은 tkinter가 빠져있는 경우가 있습니다.)
    echo.
    pause
    exit /b 1
)

echo 필요한 패키지 설치 확인 중 (playwright, python-dotenv, requests)...
python -m pip install -q playwright python-dotenv requests

if not exist ".chromium_installed" (
    echo.
    echo Playwright용 Chromium 최초 설치 중입니다. 몇 분 걸릴 수 있어요...
    python -m playwright install chromium
    if not errorlevel 1 (
        echo done > .chromium_installed
    )
)

echo.
echo GUI 앱을 실행합니다...
python gui_app.py

echo.
echo (앱 창을 닫으면 이 창도 닫아도 됩니다)
pause
