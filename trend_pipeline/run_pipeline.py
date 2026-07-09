"""
식품 트렌드 -> 브랜드커넥트 키워드 자동 생성 파이프라인
==========================================================

Chrome 확장 프로그램 '네이버 브랜드 커넥터 쇼핑 검색'은 키워드를 사람이 한 개씩
입력해야 합니다. 이 파이프라인은 그 앞단(어떤 키워드를 검색할지 정하는 과정)을
자동화합니다.

실행 순서:
    1) analyze_daily_food_data.py : daily_food_data의 날짜별 랭킹으로 상승 키워드 후보 추출
    2) validate_with_datalab.py   : 후보를 실제 데이터랩 API로 검증(진짜 상승인지 확인)
    3) 결과로 나온 keywords_for_brandconnect.txt를
       brandconnect_link_tool/brandconnect_link_generator.py --keywords-file 인자로 사용

사용법:
    python3 run_pipeline.py
"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def run_step(script_name):
    print(f"\n{'=' * 60}\n[실행] {script_name}\n{'=' * 60}")
    result = subprocess.run([sys.executable, str(BASE_DIR / script_name)])
    if result.returncode != 0:
        print(f"[중단] {script_name} 실행 중 오류가 발생했습니다.")
        sys.exit(result.returncode)


def main():
    run_step("analyze_daily_food_data.py")
    run_step("validate_with_datalab.py")

    keywords_file = BASE_DIR / "trend_analysis" / "keywords_for_brandconnect.txt"
    print(f"\n{'=' * 60}")
    print("완료. 다음 명령으로 브랜드커넥트 링크를 생성하세요:\n")
    print(f'  cd "{BASE_DIR / "brandconnect_link_tool"}"')
    print(f'  python3 brandconnect_link_generator.py --creator-id <크리에이터ID> '
          f'--keywords-file "{keywords_file}"')
    print("=" * 60)


if __name__ == "__main__":
    main()
