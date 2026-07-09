"""
네이버 브랜드커넥트(쇼핑 커넥트) 제휴 상품 링크 자동 생성기
================================================================

키워드를 입력하면 브랜드커넥트 제휴 상품 페이지에서 검색 -> 상품 선택 ->
'링크 생성' 클릭 -> 생성된 링크 추출 을 자동으로 반복하고 결과를 CSV로 저장합니다.

주의:
- 네이버 브랜드커넥트는 공식 오픈 API를 제공하지 않으므로, 이 스크립트는
  실제 웹페이지를 브라우저 자동화(Playwright)로 조작합니다.
- 페이지의 정확한 HTML 구조를 미리 알 수 없기 때문에, 아래 SELECTORS 값이
  실제 화면과 다를 수 있습니다. 다를 경우 이 파일의 SELECTORS 부분만 수정하면
  됩니다. (찾는 방법은 README_사용법.md 참고)
- 자동 선택자를 못 찾으면 스크립트가 멈추고, 사용자가 브라우저 창에서 직접
  그 단계만 클릭한 뒤 터미널에서 Enter를 누르면 이어서 진행됩니다.
  (선택자를 못 찾을 때마다 매번 손으로 하지 않도록, 실패한 선택자는
   로그로 출력되니 이후 SELECTORS를 업데이트해서 완전 자동화하세요.)

설치:
    pip install playwright --break-system-packages
    python -m playwright install chromium

실행 예:
    python brandconnect_link_generator.py --creator-id 971564859961248 \
        --keywords "텀블러,캠핑의자,공기청정기"

    python brandconnect_link_generator.py --creator-id 971564859961248 \
        --keywords-file keywords.txt --output product_links.csv
"""

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("playwright가 설치되어 있지 않습니다. 아래 명령으로 설치하세요:")
    print("  pip install playwright --break-system-packages")
    print("  python -m playwright install chromium")
    sys.exit(1)


# ----------------------------------------------------------------------------
# 선택자(SELECTORS) 설정 - 실제 화면과 다르면 여기만 수정하면 됩니다.
# 각 값은 CSS 선택자(예: 'input.search_box') 또는
# Playwright 텍스트 선택자(예: 'text=링크 생성')를 사용할 수 있습니다.
# ----------------------------------------------------------------------------
SELECTORS = {
    # 상품 검색창
    "search_input": 'input[placeholder*="검색"]',
    # 검색 결과 상품 리스트의 개별 아이템 (첫 번째 결과를 사용)
    "product_item": '[class*="product"]',
    # 상품 클릭/호버 시 나타나는 '링크 생성' 또는 '링크 복사' 버튼
    "generate_link_button": 'text=/링크\\s*(생성|복사)/',
    # 링크 생성 후 결과가 표시되는 input (readonly) 또는 텍스트 영역
    "link_result_field": 'input[readonly]',
}

BASE_URL_TEMPLATE = "https://brandconnect.naver.com/{creator_id}/affiliate/products"
DEFAULT_TIMEOUT_MS = 8000


def launch_browser_context(p, profile_dir, headless):
    """
    가능하면 실제 설치된 Chrome을 사용합니다. Playwright 내장 Chromium은
    네이버 쪽에서 자동화 브라우저로 감지해 캡차를 더 자주 띄우는 경향이 있어서,
    실제 브라우저를 쓰면 감지를 줄일 수 있습니다 (캡차 자체를 우회하는 게 아니라
    '평범한 브라우저처럼 보이게' 만드는 설정입니다. 캡차가 뜨면 여전히 직접
    풀어야 합니다). 설치된 Chrome이 없으면 내장 Chromium으로 자동 대체합니다.
    """
    anti_detection_args = ["--disable-blink-features=AutomationControlled"]
    try:
        return p.chromium.launch_persistent_context(
            profile_dir,
            headless=headless,
            channel="chrome",
            viewport={"width": 1400, "height": 900},
            args=anti_detection_args,
        )
    except Exception as e:
        print(f"[안내] 설치된 Chrome을 찾지 못해 Playwright 기본 Chromium을 사용합니다. ({e})")
        return p.chromium.launch_persistent_context(
            profile_dir,
            headless=headless,
            viewport={"width": 1400, "height": 900},
            args=anti_detection_args,
        )


def wait_for_manual_login(page):
    """로그인이 안 되어 있으면 사용자가 직접 로그인할 때까지 대기."""
    if "nid.naver.com" in page.url or "login" in page.url.lower():
        print("\n[안내] 네이버 로그인 화면이 감지되었습니다.")
        print("열려 있는 브라우저 창에서 직접 로그인해 주세요.")
        input("로그인을 완료했으면 여기서 Enter를 누르세요...")


def assisted_click(page, selector_key, description):
    """
    설정된 선택자로 클릭을 시도하고, 실패하면 사용자가 직접 클릭하도록 안내.
    선택자를 찾아 성공하면 True, 수동 개입이 필요했으면 False를 반환.
    """
    selector = SELECTORS[selector_key]
    try:
        page.locator(selector).first.click(timeout=DEFAULT_TIMEOUT_MS)
        return True
    except PlaywrightTimeoutError:
        print(f"\n[알림] '{description}' 요소를 자동으로 찾지 못했습니다.")
        print(f"       (사용한 선택자: {selector})")
        print("브라우저 창에서 해당 버튼/항목을 직접 클릭해 주세요.")
        input("클릭을 완료했으면 여기서 Enter를 누르세요...")
        return False


def extract_link(page):
    """생성된 링크 텍스트를 추출. readonly input 우선, 없으면 클립보드 확인."""
    try:
        field = page.locator(SELECTORS["link_result_field"]).first
        value = field.input_value(timeout=DEFAULT_TIMEOUT_MS)
        if value and value.startswith("http"):
            return value
    except Exception:
        pass

    # 대체 수단: 화면에서 http로 시작하는 텍스트 찾기
    try:
        link_text = page.locator("text=/https?:\\/\\/[^\\s\"']+/").first.inner_text(
            timeout=DEFAULT_TIMEOUT_MS
        )
        return link_text.strip()
    except Exception:
        pass

    print("\n[알림] 생성된 링크를 자동으로 읽지 못했습니다.")
    manual_link = input("화면에 표시된 링크를 복사해서 여기에 붙여넣어 주세요: ").strip()
    return manual_link


def search_keyword(page, keyword):
    try:
        search_box = page.locator(SELECTORS["search_input"]).first
        search_box.click(timeout=DEFAULT_TIMEOUT_MS)
        search_box.fill("")
        search_box.type(keyword, delay=30)
        search_box.press("Enter")
        page.wait_for_timeout(1500)
        return True
    except PlaywrightTimeoutError:
        print(f"\n[알림] 검색창을 자동으로 찾지 못했습니다. (선택자: {SELECTORS['search_input']})")
        print(f"브라우저에서 '{keyword}'를 직접 검색해 주세요.")
        input("검색을 완료했으면 여기서 Enter를 누르세요...")
        return False


def process_keyword(page, keyword):
    """키워드 하나에 대해 검색 -> 상품 선택 -> 링크 생성 -> 추출까지 처리."""
    print(f"\n=== 키워드: {keyword} ===")
    search_keyword(page, keyword)

    # 첫 번째 상품 결과 클릭 (상품명은 알 수 없으므로 사람이 확인 후 진행 권장)
    try:
        product = page.locator(SELECTORS["product_item"]).first
        product.scroll_into_view_if_needed(timeout=DEFAULT_TIMEOUT_MS)
        product_name = product.inner_text(timeout=DEFAULT_TIMEOUT_MS).strip().split("\n")[0]
    except Exception:
        product_name = "(확인 필요)"

    assisted_click(page, "generate_link_button", "링크 생성 버튼")
    page.wait_for_timeout(1000)
    link = extract_link(page)

    print(f"  -> 상품: {product_name}")
    print(f"  -> 링크: {link}")
    return {"keyword": keyword, "product_name": product_name, "link": link}


def load_keywords(args):
    if args.keywords_file:
        path = Path(args.keywords_file)
        return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [k.strip() for k in args.keywords.split(",") if k.strip()]


def save_results(results, output_path):
    file_exists = Path(output_path).exists()
    with open(output_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "keyword", "product_name", "link"])
        if not file_exists:
            writer.writeheader()
        for row in results:
            writer.writerow({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                **row,
            })


def main():
    parser = argparse.ArgumentParser(description="네이버 브랜드커넥트 제휴 상품 링크 자동 생성기")
    parser.add_argument("--creator-id", required=True, help="브랜드커넥트 URL의 크리에이터 ID (예: 971564859961248)")
    parser.add_argument("--keywords", help="쉼표로 구분한 키워드 목록 (예: '텀블러,캠핑의자')")
    parser.add_argument("--keywords-file", help="한 줄에 하나씩 키워드가 적힌 텍스트 파일 경로")
    parser.add_argument("--output", default="product_links.csv", help="결과 저장 CSV 경로")
    parser.add_argument("--profile-dir", default="./naver_browser_profile", help="로그인 세션을 저장할 브라우저 프로필 폴더")
    parser.add_argument("--headless", action="store_true", help="브라우저 창을 띄우지 않고 실행 (최초 로그인 이후에만 권장)")
    args = parser.parse_args()

    if not args.keywords and not args.keywords_file:
        parser.error("--keywords 또는 --keywords-file 중 하나는 반드시 입력해야 합니다.")

    keywords = load_keywords(args)
    if not keywords:
        print("처리할 키워드가 없습니다.")
        return

    base_url = BASE_URL_TEMPLATE.format(creator_id=args.creator_id)

    with sync_playwright() as p:
        context = launch_browser_context(p, args.profile_dir, args.headless)
        page = context.new_page()
        page.goto(base_url)
        page.wait_for_timeout(2000)
        wait_for_manual_login(page)

        if page.url != base_url:
            page.goto(base_url)
            page.wait_for_timeout(2000)

        results = []
        for keyword in keywords:
            try:
                result = process_keyword(page, keyword)
                results.append(result)
            except Exception as e:
                print(f"[오류] '{keyword}' 처리 중 문제 발생: {e}")
                results.append({"keyword": keyword, "product_name": "(오류)", "link": "(오류)"})
            time.sleep(1)

        save_results(results, args.output)
        print(f"\n총 {len(results)}건을 '{args.output}'에 저장했습니다.")

        context.close()


if __name__ == "__main__":
    main()
