"""
브랜드커넥트 로그인 창 열기
==============================

brandconnect_link_tool과 동일한 영구 브라우저 프로필을 사용해서
실제 네이버 로그인 페이지를 엽니다. 캡차/2단계 인증은 사용자가
직접 창에서 처리해야 합니다. 로그인 세션은 프로필 폴더에 저장되므로
이후에는 brandconnect_link_generator.py 실행 시 다시 로그인할 필요가 없습니다.

사용법: python3 open_brandconnect_login.py <creator_id>
"""

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

DEFAULT_CREATOR_ID = "971564859961248"
PROFILE_DIR = Path(__file__).resolve().parent.parent / "brandconnect_link_tool" / "naver_browser_profile"


def main():
    creator_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CREATOR_ID
    url = f"https://brandconnect.naver.com/{creator_id}/affiliate/products"

    print(f"프로필 폴더: {PROFILE_DIR}")
    print(f"접속 주소: {url}")

    anti_detection_args = ["--disable-blink-features=AutomationControlled"]

    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                str(PROFILE_DIR), headless=False, channel="chrome",
                viewport={"width": 1400, "height": 900}, args=anti_detection_args,
            )
        except Exception as e:
            print(f"[안내] 설치된 Chrome을 찾지 못해 기본 Chromium을 사용합니다. ({e})")
            context = p.chromium.launch_persistent_context(
                str(PROFILE_DIR), headless=False,
                viewport={"width": 1400, "height": 900}, args=anti_detection_args,
            )
        page = context.new_page()
        page.goto(url)
        print("브라우저 창이 열렸습니다. 로그인이 필요하면 창에서 직접 로그인해주세요.")
        print("로그인을 마쳤으면 이 브라우저 창을 닫으시면 됩니다 (세션은 자동 저장됨).")

        # 사용자가 창을 닫을 때까지 대기 (입력 콘솔이 없어도 동작하도록 폴링 방식 사용)
        try:
            while True:
                time.sleep(1)
                _ = page.title()  # 창이 닫히면 여기서 예외 발생
        except Exception:
            pass

        print("브라우저 창이 닫혔습니다. 세션이 저장되었는지 확인하려면 다시 열어보세요.")
        try:
            context.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
