import os
import sys
import json
import statistics
from datetime import date, timedelta, datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Resolve paths
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
DATA_DIR = CURRENT_DIR / "daily_food_data"

# Load environment variables
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"PostgreSQL connection error: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if not conn:
        print("No DATABASE_URL configured or failed to connect. Running in session-only mode.")
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS blog_history (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    title VARCHAR(255),
                    keywords_json TEXT,
                    links_json TEXT,
                    content TEXT
                );
                CREATE TABLE IF NOT EXISTS daily_keyword_rankings (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    rank INT NOT NULL,
                    keyword VARCHAR(255) NOT NULL,
                    UNIQUE(date, rank)
                );
            """)
            conn.commit()
            print("PostgreSQL database tables initialized successfully.")
    except Exception as e:
        print(f"Error initializing database tables: {e}")
    finally:
        conn.close()

# Import Naver DataLab Client
try:
    from naver_datalab_client import shopping_category_keyword_trend, NaverDataLabError
except ImportError as e:
    # Fallback/Mock wrapper if not importable
    print(f"Warning: Could not import naver_datalab_client: {e}")
    shopping_category_keyword_trend = None
    NaverDataLabError = Exception

app = FastAPI(title="Naver DataLab & Brand Connect Helper")

@app.on_event("startup")
def startup_event():
    init_db()

# CORS middleware for local testing and server configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FOOD_CATEGORY_CODE = "50000006"  # 쇼핑인사이트 '식품'
LOOKBACK_DAYS = 30

# Pydantic models for API request/response validation
class CustomKeywordsRequest(BaseModel):
    keywords: List[str]

class KeywordLinkMap(BaseModel):
    keyword: str
    link: str

class GenerateBlogRequest(BaseModel):
    title_hint: Optional[str] = None
    keywords_with_links: List[KeywordLinkMap]
    model: Optional[str] = "claude-sonnet-5"
    custom_prompt: Optional[str] = None

class SaveDraftRequest(BaseModel):
    title: str
    content: str
    keywords: List[str] = []
    links: Dict[str, str] = {}

# Helper functions for calculations
def load_daily_rankings() -> Dict[str, Dict[str, int]]:
    """Loads rankings from PostgreSQL database first, falls back to CSV files."""
    daily = {}
    
    # Try loading from database
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT date, rank, keyword 
                    FROM daily_keyword_rankings 
                    ORDER BY date, rank
                """)
                rows = cur.fetchall()
                for r_date, r_rank, r_kw in rows:
                    # Handle both datetime.date object and string
                    date_str = r_date.isoformat() if hasattr(r_date, "isoformat") else str(r_date)
                    if date_str not in daily:
                        daily[date_str] = {}
                    daily[date_str][r_kw] = r_rank
                if daily:
                    print(f"Loaded daily rankings for {len(daily)} dates from database.")
                    return daily
        except Exception as e:
            print(f"Error loading rankings from database: {e}")
        finally:
            conn.close()

    # Fallback to local files
    print("Falling back to local CSV files for daily rankings...")
    if not DATA_DIR.exists():
        return daily
    
    for path in sorted(DATA_DIR.glob("food_*.csv")):
        date_str = path.stem.replace("food_", "")
        rankings = {}
        try:
            with open(path, encoding="utf-8-sig") as f:
                import csv
                reader = csv.DictReader(f)
                for row in reader:
                    if "keyword" in row and "rank" in row:
                        rankings[row["keyword"]] = int(row["rank"])
        except Exception as e:
            print(f"Error loading {path}: {e}")
            continue
        daily[date_str] = rankings
    return daily

def detect_variable_window(daily: Dict[str, Dict[str, int]]):
    """Identifies dates that have dynamic keyword list (> 10 keywords)."""
    dates = sorted(daily.keys())
    variable_dates = [d for d in dates if len(daily[d]) > 10]
    static_dates = [d for d in dates if d not in variable_dates]
    return variable_dates, static_dates

def compute_rising_scores(daily: Dict[str, Dict[str, int]], variable_dates: List[str]) -> List[Dict[str, Any]]:
    """Runs the ranking trend analysis algorithm from analyze_daily_food_data.py."""
    if not variable_dates:
        return []
    
    half = len(variable_dates) // 2
    early_dates = variable_dates[:half]
    late_dates = variable_dates[half:]
    top_n_per_day = 500

    from collections import defaultdict
    keyword_ranks = defaultdict(list)
    for d in variable_dates:
        for kw, rank in daily[d].items():
            keyword_ranks[kw].append((d, rank))

    rows = []
    for kw, entries in keyword_ranks.items():
        early_ranks = [r for d, r in entries if d in early_dates]
        late_ranks = [r for d, r in entries if d in late_dates]
        appearances = len(entries)

        early_avg = statistics.mean(early_ranks) if early_ranks else None
        late_avg = statistics.mean(late_ranks) if late_ranks else None
        new_entry = (early_avg is None) and (late_avg is not None)

        if early_avg is not None and late_avg is not None:
            rank_gain = early_avg - late_avg
        elif new_entry:
            rank_gain = max(0, top_n_per_day - late_avg) / top_n_per_day * 50
        else:
            rank_gain = 0

        score = rank_gain + appearances * 0.5 + (30 if new_entry else 0)

        rows.append({
            "keyword": kw,
            "appearances": appearances,
            "early_avg_rank": round(early_avg, 1) if early_avg else None,
            "late_avg_rank": round(late_avg, 1) if late_avg else None,
            "new_entry": new_entry,
            "rising_score": round(score, 2),
        })

    rows.sort(key=lambda r: r["rising_score"], reverse=True)
    return rows

def compute_velocity(data_points: List[Dict[str, Any]]):
    """Calculates search click ratio velocity (velocity = second_half_avg / first_half_avg)."""
    if len(data_points) < 4:
        return 1.0, 0.0, 0.0
    half = len(data_points) // 2
    early = data_points[:half]
    late = data_points[half:]
    early_avg = sum(p["ratio"] for p in early) / len(early)
    late_avg = sum(p["ratio"] for p in late) / len(late)
    velocity = (late_avg / early_avg) if early_avg > 0 else 1.0
    return velocity, early_avg, late_avg

def query_naver_datalab(keywords: List[str]) -> Dict[str, Dict[str, Any]]:
    """Helper to retrieve DataLab search volumes and calculate trends."""
    if not shopping_category_keyword_trend:
        # If API client is missing, return fallback/empty dictionary
        return {}

    end_date = date.today()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    
    results = {}
    # Call in batches of 5 (Naver API constraint)
    batch_size = 5
    for i in range(0, len(keywords), batch_size):
        batch = keywords[i:i+batch_size]
        keyword_groups = [{"name": kw, "param": [kw]} for kw in batch]
        try:
            response = shopping_category_keyword_trend(
                category_code=FOOD_CATEGORY_CODE,
                keyword_groups=keyword_groups,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                time_unit="date",
            )
            for r in response.get("results", []):
                title = r["title"]
                data_points = r.get("data", [])
                velocity, early_avg, late_avg = compute_velocity(data_points)
                results[title] = {
                    "velocity": round(velocity, 2),
                    "early_avg": round(early_avg, 2),
                    "late_avg": round(late_avg, 2),
                    "series": data_points
                }
        except Exception as e:
            print(f"Naver DataLab API error for batch {batch}: {e}")
            for kw in batch:
                results[kw] = {
                    "velocity": 1.0,
                    "early_avg": 0.0,
                    "late_avg": 0.0,
                    "series": []
                }
    return results


# API Endpoints
@app.get("/api/status")
def get_status():
    """Checks credentials existence and returns status configuration."""
    naver_id = os.getenv("NAVER_CLIENT_ID")
    naver_secret = os.getenv("NAVER_CLIENT_SECRET")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    return {
        "naver_configured": bool(naver_id and naver_secret),
        "anthropic_configured": bool(anthropic_key),
        "naver_client_id_hint": naver_id[:4] + "***" if naver_id else None,
        "env_path": str(PROJECT_ROOT / ".env")
    }

@app.get("/api/trends")
def get_trends(limit: int = 15):
    """Processes daily ranking files and validates top candidates using Naver DataLab API."""
    try:
        daily_ranks = load_daily_rankings()
        if not daily_ranks:
            raise HTTPException(status_code=404, detail="No ranking data files found in daily_food_data.")
            
        var_dates, _ = detect_variable_window(daily_ranks)
        if not var_dates:
            raise HTTPException(status_code=400, detail="Could not identify variable date windows in data files.")
            
        ranking_scores = compute_rising_scores(daily_ranks, var_dates)
        top_candidates = [r["keyword"] for r in ranking_scores[:limit]]
        
        # Cross validate with Naver DataLab API
        datalab_results = query_naver_datalab(top_candidates)
        
        # Merge results
        final_trends = []
        for r in ranking_scores[:limit]:
            kw = r["keyword"]
            dl = datalab_results.get(kw, {
                "velocity": 1.0,
                "early_avg": 0.0,
                "late_avg": 0.0,
                "series": []
            })
            
            final_trends.append({
                "keyword": kw,
                "rising_score": r["rising_score"],
                "appearances": r["appearances"],
                "new_entry": r["new_entry"],
                "datalab_velocity": dl.get("velocity", 1.0),
                "early_avg": dl.get("early_avg", 0.0),
                "late_avg": dl.get("late_avg", 0.0),
                "trend_series": dl.get("series", [])
            })
            
        # Sort by velocity descending
        final_trends.sort(key=lambda x: x["datalab_velocity"], reverse=True)
        return final_trends
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trends/custom")
def validate_custom_trends(request: CustomKeywordsRequest):
    """Directly queries Naver DataLab API for user-inputted keywords."""
    if not request.keywords:
        raise HTTPException(status_code=400, detail="Keywords list cannot be empty.")
        
    try:
        datalab_results = query_naver_datalab(request.keywords)
        response_data = []
        
        for kw in request.keywords:
            dl = datalab_results.get(kw, {
                "velocity": 1.0,
                "early_avg": 0.0,
                "late_avg": 0.0,
                "series": []
            })
            response_data.append({
                "keyword": kw,
                "datalab_velocity": dl.get("velocity", 1.0),
                "early_avg": dl.get("early_avg", 0.0),
                "late_avg": dl.get("late_avg", 0.0),
                "trend_series": dl.get("series", [])
            })
            
        # Sort by velocity descending
        response_data.sort(key=lambda x: x["datalab_velocity"], reverse=True)
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-blog")
def generate_blog_draft(request: GenerateBlogRequest):
    """Generates compliance-aligned blog post draft using Claude."""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        raise HTTPException(status_code=500, detail="Anthropic API key is not configured in .env")
        
    if not request.keywords_with_links:
        raise HTTPException(status_code=400, detail="No keywords and links provided.")
        
    try:
        import anthropic
    except ImportError:
        raise HTTPException(status_code=500, detail="Anthropic SDK is not installed on the server.")

    # Format the keyword-link lines for prompting
    kw_details = []
    for item in request.keywords_with_links:
        link_str = item.link if item.link.strip() else "(제휴 링크 미등록 - 수동 삽입 필요)"
        kw_details.append(f"- 키워드: {item.keyword}\n  삽입될 제휴 상품 링크: {link_str}")
        
    kw_block = "\n".join(kw_details)
    title_hint = request.title_hint or f"{date.today().strftime('%Y년 %-m월')} 추천 건강식품 및 식품 트렌드 리포트"

    disclosure_text = "이 포스팅은 네이버 쇼핑 커넥트 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."

    prompt = f"""당신은 네이버 블로그 '애플소다'의 전문 푸드 트렌드 & 라이프스타일 작가입니다. 
아래 가이드라인에 따라 주어진 식품/가공식품 트렌드 키워드들을 자연스럽게 융합한 블로그 초안 원고를 작성해 주세요.

# 필수 반영해야 할 브랜드 커넥트 블로그 작성 및 운영 규정 (표시광고법 준수)
1. [대가성 문구 필수 표기]: 본문 맨 위(목차보다도 앞)에 다음 대가성 고지 문구를 반드시 볼드(굵게) 처리하여 눈에 띄게 삽입하세요:
   "**{disclosure_text}**"
2. [표시광고법 및 가이드라인 준수]: 의학적으로 검증되지 않은 허위·과장 광고성 효능이나 성분 묘사를 절대로 금지합니다. (예: "암을 예방한다", "당뇨를 완치한다" 같은 과장 표현 대신 "식단 관리에 도움을 줄 수 있는 것으로 알려져 있다" 등으로 완곡히 작성). 추천·보증 지침을 준수하세요.
3. [콘텐츠 공개 유지]: 원고 마지막에 "제휴 콘텐츠는 정해진 캠페인 기간 동안 전체 공개로 유지해야 합니다."라는 브랜드 커넥트 가이드 문구를 참고용 안내 박스로 삽입하세요.
4. [캠페인 수락/거절 신중]: 취소 불가에 대한 내용을 유념하여 신뢰도 있는 블로거의 톤앤매너로 작성하세요.

# 블로그 본문 스타일 가이드
- 어투: 반말이 아닌, 친근하고 공감을 유도하는 존댓말 (~하시죠?, ~랍니다)과 적당한 이모지(🙋‍♀️, 🍏, 💡 등)를 사용합니다.
- 데이터 기반 신뢰도 강화: 각 키워드를 소개할 때 "검색 통계 분석에 따르면 최근 이전 대비 상승세를 보이고 있다" 등 트렌드 상승의 근거를 자연스러운 문맥으로 묘사하세요.
- 각 키워드 섹션 필수 내용:
  - 해당 키워드가 주목받는 배경 및 추천 섭취 방법
  - 제휴 상품 추천 및 실제 구매 링크 삽입
    제공된 상품 링크는 글의 문맥에 맞추어 `[상품 상세 알아보기 >](실제링크)` 또는 `👉 **[제휴 상품 바로가기 →](실제링크)**` 형태로 정확하게 해당 키워드 소개 영역에 삽입하세요.
- 전체 레이아웃 구조:
  1. 대가성 고지 문구 (맨 위 배치)
  2. 도입부 (독자의 흥미 유발 및 인사말)
  3. 목차
  4. 각 키워드별 상세 소개 섹션 (비교표, 추천 제품 및 제휴 링크 포함)
  5. 구매 시 체크리스트
  6. 마무리 맺음말 및 공감/댓글 유도
  7. 다음 추천 포스팅 주제 2~3개 제안

# 이번 포스팅에서 다룰 키워드 및 링크 목록
제목 제안: {title_hint}

{kw_block}

위 가이드라인에 맞춰 마크다운 형식으로 한글 1,200자 ~ 1,800자 사이 분량의 본문 내용만 작성해 주세요. 대가성 문구는 최상단에 자연스럽게 노출되도록 해주세요.
"""

    if request.custom_prompt and request.custom_prompt.strip():
        prompt += f"\n\n# 사용자 추가 요청 사항 (최우선 반영할 것):\n{request.custom_prompt}\n"

    try:
        client = anthropic.Anthropic(api_key=anthropic_key)
        # We target a stable modern Claude 3.5 model
        model_name = request.model if request.model else "claude-sonnet-5"
        
        response = client.messages.create(
            model=model_name,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        content_text = "".join(block.text for block in response.content if hasattr(block, "text"))
        
        # Verify if disclosure is in the content
        has_disclosure = disclosure_text in content_text
        
        # Save to DB if connection is active
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO blog_history (title, keywords_json, links_json, content)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            title_hint,
                            json.dumps([item.keyword for item in request.keywords_with_links], ensure_ascii=False),
                            json.dumps({item.keyword: item.link for item in request.keywords_with_links}, ensure_ascii=False),
                            content_text
                        )
                    )
                    conn.commit()
                    print("Blog post saved to PostgreSQL history database.")
            except Exception as db_err:
                print(f"Failed to save blog post to DB: {db_err}")
            finally:
                conn.close()

        # Build checklist validation metadata
        compliance_check = {
            "has_disclosure": has_disclosure,
            "disclosure_text": disclosure_text,
            "advertising_policy_warning": True,
            "post_duration_warning": True,
            "penalty_system_warning": True
        }
        
        return {
            "title": title_hint,
            "blog_post_markdown": content_text,
            "compliance": compliance_check
        }
    except Exception as e:
        print(f"Claude API Error: {e}")
        raise HTTPException(status_code=500, detail=f"Claude API failed: {str(e)}")

@app.get("/api/history")
def get_blog_history():
    """Fetches past generated blog posts from the PostgreSQL database."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, created_at, title, keywords_json, links_json, content
                FROM blog_history
                ORDER BY created_at DESC
                LIMIT 50
                """
            )
            rows = cur.fetchall()
            results = []
            for r in rows:
                results.append({
                    "id": r["id"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "title": r["title"],
                    "keywords": json.loads(r["keywords_json"]) if r["keywords_json"] else [],
                    "links": json.loads(r["links_json"]) if r["links_json"] else {},
                    "content": r["content"]
                })
            return results
    except Exception as e:
        print(f"Failed to fetch blog history: {e}")
        return []
    finally:
        conn.close()

@app.post("/api/history/save")
def save_blog_draft(request: SaveDraftRequest):
    """Manually saves the current blog draft to the PostgreSQL database."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection is not configured or offline.")
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO blog_history (title, keywords_json, links_json, content)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    request.title,
                    json.dumps(request.keywords, ensure_ascii=False),
                    json.dumps(request.links, ensure_ascii=False),
                    request.content
                )
            )
            conn.commit()
            return {"status": "success", "message": "Draft saved successfully."}
    except Exception as e:
        print(f"Failed to manually save blog draft: {e}")
        raise HTTPException(status_code=500, detail=f"Database save error: {str(e)}")
    finally:
        conn.close()

@app.get("/api/debug-paths")
def debug_paths():
    import os
    from pathlib import Path
    
    current_dir = Path(__file__).resolve().parent
    cwd = os.getcwd()
    
    app_files = os.listdir("/app") if os.path.exists("/app") else []
    root_files = os.listdir("/") if os.path.exists("/") else []
    
    daily_food_data_in_app = os.listdir("/app/daily_food_data") if os.path.exists("/app/daily_food_data") else None
    daily_food_data_in_root = os.listdir("/daily_food_data") if os.path.exists("/daily_food_data") else None
    
    return {
        "__file__": __file__,
        "CURRENT_DIR": str(current_dir),
        "cwd": cwd,
        "PROJECT_ROOT": str(PROJECT_ROOT),
        "DATA_DIR": str(DATA_DIR),
        "DATA_DIR_exists": DATA_DIR.exists(),
        "app_files": app_files,
        "root_files": root_files,
        "daily_food_data_in_app": daily_food_data_in_app,
        "daily_food_data_in_root": daily_food_data_in_root,
    }


# Serve Static files (index.html, app.js, style.css)
# Serve index.html on root '/'
@app.get("/")
def read_root():
    static_file_path = CURRENT_DIR / "static" / "index.html"
    if not static_file_path.exists():
        raise HTTPException(status_code=404, detail="Static files not generated yet. Verify frontend creation.")
    with open(static_file_path, "r", encoding="utf-8") as f:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=f.read(), status_code=200)

app.mount("/static", StaticFiles(directory=CURRENT_DIR / "static"), name="static")

if __name__ == "__main__":
    import uvicorn
    # Local run uses port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
