import sys
import asyncio
from typing import List, Optional, Dict
from datetime import datetime
import json
from pathlib import Path
from contextlib import asynccontextmanager

# Fix for Windows asyncio loop with Playwright/Subprocesses
# if sys.platform == 'win32':
#     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse # Added for export
from pydantic import BaseModel
from logging import getLogger

logger = getLogger("uvicorn")

# Add crawler directory to path
sys.path.append(str(Path(__file__).parent.parent / 'crawler'))

from database.db_sqlite import Database
# Import Scrapers
from scrapers.techflow import TechFlowScraper
from scrapers.odaily import OdailyScraper
from scrapers.blockbeats import BlockBeatsScraper
from scrapers.foresight import ForesightScraper
from scrapers.chaincatcher import ChainCatcherScraper
from scrapers.panews import PANewsScraper
from scrapers.marsbit import MarsBitScraper

SCRAPER_MAP = {
    "techflow": TechFlowScraper,
    "odaily": OdailyScraper,
    "blockbeats": BlockBeatsScraper,
    "foresight": ForesightScraper,
    "chaincatcher": ChainCatcherScraper,
    "panews": PANewsScraper,
    "marsbit": MarsBitScraper,
}

app = FastAPI(title="AINews Admin API")

# ... (CORS and DB init remain same)

# ... (Stats and News endpoints remain same)

# ... imports

SCRAPER_STATUS: Dict[str, Dict] = {} 
RUNNING_TASKS: Dict[str, asyncio.Task] = {} # { "techflow": task_obj }

class RunScraperRequest(BaseModel):
    items: int = 10

class DeduplicateRequest(BaseModel):
    time_window_hours: int = 24
    action: str = 'mark'  # 'mark' or 'delete'

@app.post("/api/spiders/stop/{name}")
async def stop_scraper(name: str):
    """Stop a running scraper task"""
    if name in RUNNING_TASKS:
        task = RUNNING_TASKS[name]
        task.cancel()
        logger.info(f"Requested cancellation for {name}")
        return {"status": "success", "message": f"Stop signal sent to {name}"}
    return {"status": "error", "message": "Scraper not running"}

async def run_scraper_task(name: str, max_items: int):
    """Refactored scraper runner for background task"""
    logger.info(f"Starting background scrape task for {name}")
    import datetime
    
    SCRAPER_STATUS[name] = {
        "status": "running", 
        "start_time": datetime.datetime.now().isoformat(),
        "items_scraped": 0,
        "logs": []
    }
    
    import sys
    def log_scraper(msg: str):
        full_msg = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}"
        print(f"[{name}] {msg}")
        sys.stdout.flush()
        
        logger.info(f"[{name}] {msg}")
        if "logs" not in SCRAPER_STATUS[name]:
             SCRAPER_STATUS[name]["logs"] = []
        SCRAPER_STATUS[name]["logs"].append(full_msg)
        # Keep limit
        if len(SCRAPER_STATUS[name]["logs"]) > 100:
            SCRAPER_STATUS[name]["logs"].pop(0)

    scraper = None
    try:
        # Register Task
        RUNNING_TASKS[name] = asyncio.current_task()
        
        scraper_cls = SCRAPER_MAP.get(name)
        if not scraper_cls:
            log_scraper("Error: Scraper not found")
            SCRAPER_STATUS[name]["status"] = "error"
            SCRAPER_STATUS[name]["error"] = "Scraper not found"
            return
            SCRAPER_STATUS[name]["error"] = "Scraper not found"
            return
            
        scraper = scraper_cls()
        scraper.max_items = max_items
        log_scraper(f"Initialized scraper with limit {max_items}")
            
        # Prepare Incremental Mode (More Robust)
        db_conn = Database()
        recent_urls = db_conn.get_recent_news_urls(name, limit=20)
        
        if recent_urls:
            scraper.existing_urls = set(recent_urls)
            scraper.last_news_url = recent_urls[0] # For backward compatibility logs
            scraper.incremental_mode = True
            log_scraper(f"Incremental mode enabled. History size: {len(recent_urls)}. Latest: {recent_urls[0][:30]}...")
        else:
            # Fallback to single latest check if recent list empty (though list includes latest)
            latest_url = db_conn.get_latest_news_url(name)
            if latest_url:
                scraper.last_news_url = latest_url
                scraper.incremental_mode = True
                log_scraper(f"Incremental mode enabled (Legacy). Stopping at: {latest_url[:30]}...")
            else:
                 log_scraper("No previous history found. Scraping limit items.")

        # Run
        log_scraper("Starting scrape...")
        news_list = await scraper.run()
        count_scraped = len(news_list)
        log_scraper(f"Scraped {count_scraped} items")
        
        # Save to DB (re-use conn or new one? using existing)
        count_saved = 0
        log_scraper("Saving to database...")
        for news in news_list:
            if 'source_site' not in news:
                news['source_site'] = scraper.site_name
            if db_conn.insert_news(news):
                count_saved += 1
                log_scraper(f"Saved: {news.get('title', 'Unknown')[:30]}...")
            else:
                log_scraper(f"Skipped (Duplicate URL): {news.get('title', 'Unknown')[:30]}...")

        log_scraper(f"Completed. Saved {count_saved} new items.")
        
        SCRAPER_STATUS[name].update({
            "status": "idle",
            "last_run": datetime.datetime.now().isoformat(),
            "last_result": f"Scraped {count_scraped}, Saved {count_saved}",
            "last_error": None
        })
        
    except asyncio.CancelledError:
        log_scraper("⚠️ Task Cancelled by User")
        SCRAPER_STATUS[name]["status"] = "idle"
        SCRAPER_STATUS[name]["last_result"] = "Cancelled by User"
        logger.info(f"Task {name} cancelled")
    except Exception as e:
        import traceback
        err_msg = str(e)
        logger.error(f"Error running scraper {name}: {e}")
        logger.error(traceback.format_exc())
        if 'log_scraper' in locals():
            log_scraper(f"Error: {str(e)}")
        SCRAPER_STATUS[name].update({
            "status": "error",
            "last_run": datetime.now().isoformat(),
            "last_result": "Failed",
            "last_error": str(e)
        })
    finally:
        # Cleanup
        if name in RUNNING_TASKS:
            del RUNNING_TASKS[name]
        try:
             if scraper:
                 await scraper.close_browser()
        except:
            pass

@app.get("/api/spiders/status")
def get_spider_status():
    """Get status of all spiders"""
    # Merge config into status
    for name, status in SCRAPER_STATUS.items():
        if name in SCRAPER_CONFIG:
            config = SCRAPER_CONFIG[name]
            if isinstance(config, dict):
                status.update(config)
            # else: legacy format ignored
    return SCRAPER_STATUS

# Scraper Config Persistence
CONFIG_FILE = Path("scraper_config.json")

def load_config():
    if CONFIG_FILE.exists():
        import json
        try:
            return json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
        except:
            return {}
    return {}

def save_config(config):
    import json
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding='utf-8')

SCRAPER_CONFIG = load_config()

class ConfigRequest(BaseModel):
    interval: Optional[str] = None # "30", "60", "manual"
    limit: Optional[int] = None

@app.post("/api/spiders/config/{name}")
async def config_scraper(name: str, req: ConfigRequest):
    if name not in SCRAPER_CONFIG:
        SCRAPER_CONFIG[name] = {}
    
    # Update Interval
    if req.interval:
        if req.interval == "manual":
             SCRAPER_CONFIG[name].pop("interval", None)
        else:
            SCRAPER_CONFIG[name]["interval"] = int(req.interval)
            
    # Update Limit
    if req.limit:
        SCRAPER_CONFIG[name]["limit"] = req.limit
    
    save_config(SCRAPER_CONFIG)
    return {"status": "success", "config": SCRAPER_CONFIG}

@app.post("/api/news/deduplicate")
async def deduplicate_news(req: DeduplicateRequest):
    """手动触发跨平台去重"""
    try:
        import sys
        sys.path.insert(0, 'crawler')
        from filters.local_deduplicator import LocalDeduplicator
        
        db = Database()
        
        # 1. 获取时间范围内的新闻
        news_list = db.get_news_by_time_range(req.time_window_hours)
        
        if not news_list:
            return {
                "status": "success",
                "message": "未找到符合条件的新闻",
                "stats": {
                    "total_scanned": 0,
                    "duplicates_found": 0,
                    "duplicates_processed": 0
                }
            }
        
        # 2. 使用LocalDeduplicator找出重复
        dedup = LocalDeduplicator(similarity_threshold=0.65, time_window_hours=req.time_window_hours)
        news_list = dedup.mark_duplicates(news_list)
        
        # 3. 统计和处理重复项
        duplicates = [n for n in news_list if n.get('is_local_duplicate', False)]
        duplicate_groups = {}
        
        for dup in duplicates:
            master_idx = dup.get('duplicate_of')
            if master_idx is not None and master_idx < len(news_list):
                master = news_list[master_idx]
                master_id = master['id']
                
                if master_id not in duplicate_groups:
                    duplicate_groups[master_id] = {
                        'master': {
                            'id': master['id'],
                            'title': master['title'],
                            'source': master['source_site']
                        },
                        'duplicates': []
                    }
                
                duplicate_groups[master_id]['duplicates'].append({
                    'id': dup['id'],
                    'title': dup['title'],
                    'source': dup['source_site']
                })
                
                # 执行操作
                if req.action == 'mark':
                    db.mark_as_duplicate(dup['id'], master_id)
                elif req.action == 'delete':
                    db.delete_news(dup['id'])
        
        # 归档非重复的新闻到deduplicated_news
        archived_count = 0
        if news_list:
            unique_ids = [n['id'] for n in news_list if not n.get('is_local_duplicate', False)]
            if unique_ids:
                archived_count = db.archive_to_deduplicated(unique_ids)
        
        return {
            "status": "success",
            "message": f"去重完成",
            "stats": {
                "total_scanned": len(news_list),
                "duplicates_found": len(duplicates),
                "duplicates_processed": len(duplicates),
                "duplicate_groups": len(duplicate_groups),
                "archived_count": archived_count
            },
            "duplicate_groups": list(duplicate_groups.values())
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Deduplication error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

async def scheduler_loop():
    logger.info("Starting Scheduler Loop")
    while True:
        try:
            now = datetime.now()
            for name, config in SCRAPER_CONFIG.items():
                if not isinstance(config, dict): 
                    continue # Skip old config format if any
                    
                interval = config.get("interval")
                if not interval:
                    continue

                # Check status
                status = SCRAPER_STATUS.get(name, {})
                if status.get("status") == "running":
                    continue
                
                last_run_str = status.get("last_run")
                should_run = False
                
                if not last_run_str:
                    should_run = True
                else:
                    last_run = datetime.fromisoformat(last_run_str)
                    diff = (now - last_run).total_seconds() / 60
                    if diff >= interval:
                        should_run = True
                
                if should_run:
                    limit = config.get("limit", 5)
                    logger.info(f"[Scheduler] Triggering {name} (Interval: {interval}m, Limit: {limit})")
                    asyncio.create_task(run_scraper_task(name, limit))
            
            await asyncio.sleep(60) # Check every minute
        except Exception as e:
            logger.error(f"Scheduler Error: {e}")
            await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Scheduler Loop")
    task = asyncio.create_task(scheduler_loop())
    yield
    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

# Fix: Do not re-initialize app, as it wipes out previously registered endpoints.
# Instead, attach lifespan to the existing app instance.
app.router.lifespan_context = lifespan

@app.post("/api/spiders/run/{name}")
async def run_spider(name: str, background_tasks: BackgroundTasks, req: RunScraperRequest):
    if name not in SCRAPER_MAP:
        raise HTTPException(status_code=404, detail="Scraper not found")
    
    background_tasks.add_task(run_scraper_task, name, req.items)
    return {"status": "accepted", "message": f"Scraper {name} started in background"}

@app.get("/api/spiders")
def get_spiders():
    """List all available spiders"""
    return {
        "spiders": list(SCRAPER_MAP.keys())
    }


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB
db = Database()

@app.get("/")
def read_root():
    return {"message": "Welcome to AINews Admin API"}

@app.get("/api/stats")
def get_stats():
    """Get crawling stats for today"""
    conn = db.connect()
    cursor = conn.cursor()
    # Count news per source for today (scraped_at like 'YYYY-MM-DD%')
    # Using 'now' logic from db_sqlite is complex, simpler validation:
    # Just group by source_site overall for now
    cursor.execute("SELECT source_site, count(*) as count FROM news GROUP BY source_site")
    rows = cursor.fetchall()
    conn.close()
    
    return {
        "stats": [{"source": row['source_site'], "count": row['count']} for row in rows]
    }

@app.get("/api/news")
def get_news(page: int = 1, limit: int = 50, source: Optional[str] = None, stage: Optional[str] = None):
    """Get news list with pagination"""
    conn = db.connect()
    cursor = conn.cursor()
    offset = (page - 1) * limit
    
    query = "SELECT * FROM news WHERE 1=1"
    params = []
    
    if source:
        query += " AND source_site = ?"
        params.append(source)
    
    if stage:
        query += " AND stage = ?"
        params.append(stage)
    
    query += " ORDER BY published_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Get total count
    count_query = "SELECT count(*) FROM news WHERE 1=1"
    count_params = []
    if source:
        count_query += " AND source_site = ?"
        count_params.append(source)
    if stage:
        count_query += " AND stage = ?"
        count_params.append(stage)
        
    cursor.execute(count_query, count_params)
    total = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "data": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "limit": limit
    }

@app.delete("/api/news/{news_id}")
def delete_news(news_id: int):
    """Delete a news item"""
    conn = db.connect() # Or better, use db.delete_news but db instance here is 'Database' class not instance? 
    # Wait, 'db' in main.py is initialized as 'db = Database()'.
    # db_sqlite methods like 'connect' are instance methods.
    # So we can use db.delete_news(news_id).
    # But wait, db instance logic in main.py:
    # `db = Database()` at line 155.
    success = db.delete_news(news_id)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="删除失败")

@app.get("/api/deduplicated/news")
def get_deduplicated_news_api(page: int = 1, limit: int = 50, source: Optional[str] = None):
    """获取已去重的数据"""
    return db.get_deduplicated_news(page, limit, source)

@app.get("/api/deduplicated/stats")
def get_deduplicated_stats():
    """获取已去重数据的统计"""
    db = Database()
    return db.get_deduplicated_stats()

@app.delete("/api/deduplicated/news/{news_id}")
def delete_deduplicated_news(news_id: int):
    """删除已去重数据"""
    db = Database()
    success = db.delete_deduplicated_news(news_id)
    if success:
        return {"status": "success", "message": "删除成功"}
    else:
        raise HTTPException(status_code=404, detail="数据不存在或删除失败")

@app.get("/api/curated/news")
def get_curated_news_api(page: int = 1, limit: int = 50, source: Optional[str] = None):
    """获取精选数据"""
    return db.get_curated_news(page, limit, source)

@app.get("/api/curated/stats")
def get_curated_stats_api():
    """获取精选数据统计"""
    db = Database()
    return db.get_curated_stats()

@app.delete("/api/curated/news/{news_id}")
def delete_curated_news(news_id: int):
    """删除精选数据"""
    db = Database()
    success = db.delete_curated_news(news_id)
    if success:
        return {"status": "success", "message": "删除成功"}
    else:
        raise HTTPException(status_code=404, detail="数据不存在或删除失败")

class RestoreRequest(BaseModel):
    source_table: str = 'deduplicated_news'

@app.post("/api/news/restore/{news_id}")
def restore_news_api(news_id: int, req: RestoreRequest):
    """还原被过滤的新闻"""
    db = Database()
    success = db.restore_news(news_id, req.source_table)
    if success:
        return {"status": "success", "message": "还原成功"}
    else:
        raise HTTPException(status_code=400, detail="还原失败")

@app.get("/api/filtered/dedup/news")
def get_filtered_dedup_news_api(page: int = 1, limit: int = 50):
    """获取去重库中的已过滤数据"""
    return db.get_filtered_dedup_news(page, limit)

# --- Blacklist APIs ---

@app.get("/api/blacklist")
def get_blacklist():
    """获取所有黑名单关键词"""
    db = Database()
    return {"keywords": db.get_blacklist_keywords()}

class AddBlacklistRequest(BaseModel):
    keyword: str
    match_type: str = 'contains'

@app.post("/api/blacklist")
def add_blacklist(req: AddBlacklistRequest):
    """添加黑名单关键词"""
    db = Database()
    success = db.add_blacklist_keyword(req.keyword, req.match_type)
    if success:
        return {"status": "success", "message": "添加成功"}
    else:
        raise HTTPException(status_code=400, detail="添加失败，可能关键词已存在")

@app.delete("/api/blacklist/{id}")
def delete_blacklist(id: int):
    """删除黑名单关键词"""
    db = Database()
    success = db.remove_blacklist_keyword(id)
    if success:
        return {"status": "success", "message": "删除成功"}
    else:
        raise HTTPException(status_code=404, detail="删除失败")

class FilterRequest(BaseModel):
    time_range_hours: int = 24

@app.post("/api/news/filter")
def filter_news(req: FilterRequest):
    """根据黑名单执行过滤"""
    db = Database()
    result = db.filter_news_by_blacklist(req.time_range_hours)
    return {"status": "success", "stats": result}

class LoginRequest(BaseModel):
    password: str

@app.post("/api/login")
def login(req: LoginRequest):
    # Simple password check
    if req.password == "admin123": # Default password
        return {"token": "valid-session", "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid password")

@app.get("/api/export")
def export_news(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    source: Optional[str] = None,
    stage: Optional[str] = None,
    fields: Optional[str] = None
):
    """Export news data to JSON file"""
    db = Database()
    news_list = db.get_news_for_export(start_date, end_date, keyword, source, stage)
    
    def iter_json():
        field_list = [f.strip() for f in fields.split(',')] if fields else []
        yield "["
        for i, news in enumerate(news_list):
            if i > 0: yield ","
            
            if field_list:
                # Filter keys if fields provided
                # Only keep keys that exist in news item
                item = {k: news[k] for k in field_list if k in news}
            else:
                item = news
                
            yield json.dumps(item, default=str, ensure_ascii=False)
        yield "]"

    filename = f"ainews_export_{datetime.now().strftime('%Y%m%d%H%M')}.json"
    
    return StreamingResponse(
        iter_json(),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    import os
    import sys
    from pathlib import Path

    # Add project root to sys.path and PYTHONPATH for reloader subprocess
    root_dir = str(Path(__file__).parent.parent)
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    
    # Update PYTHONPATH so uvicorn subprocess can find 'backend' module
    current_pythonpath = os.environ.get("PYTHONPATH", "")
    if root_dir not in current_pythonpath:
        os.environ["PYTHONPATH"] = f"{root_dir}{os.pathsep}{current_pythonpath}"

    print(f"🚀 Starting AINews Backend on http://0.0.0.0:8000 (Root: {root_dir})")
    try:
        # NOTE: 'reload=True' on Windows causes conflict with Playwright (SelectorEventLoop vs ProactorEventLoop).
        # We must disable reload to ensure crawlers work correctly.
        use_reload = False if sys.platform == 'win32' else True
        
        if use_reload:
             uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
        else:
             uvicorn.run(app, host="0.0.0.0", port=8000)
             
    except Exception as e:
        print(f"Fallback to standard run: {e}")
        uvicorn.run(app, host="0.0.0.0", port=8000)

