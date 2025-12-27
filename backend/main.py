import sys
import asyncio
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import json
from pathlib import Path
from contextlib import asynccontextmanager

# Fix for Windows asyncio loop with Playwright/Subprocesses
# if sys.platform == 'win32':
#     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse  # Added for export
from pydantic import BaseModel
from logging import getLogger

logger = getLogger("uvicorn")

# Add crawler directory to path
sys.path.append(str(Path(__file__).parent.parent / 'crawler'))

from database.db_sqlite import Database

# Add backend directory to path for service imports
sys.path.append(str(Path(__file__).parent))
from services.llm import DeepSeekService

# Import Core modules
from core.response import APIResponse
from core.exceptions import (
    APIException, 
    ValidationError, 
    NotFoundError,
    DatabaseError,
    BusinessError
)

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

# 全局异常处理器
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """处理API自定义异常"""
    return JSONResponse(
        status_code=exc.code,
        content=APIResponse.error(
            message=exc.message,
            code=exc.code,
            error_type=exc.error_type,
            details=getattr(exc, 'details', None)
        )
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """处理未捕获的异常"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=APIResponse.error(
            message="服务器内部错误",
            code=500,
            error_type="InternalServerError",
            details=str(exc) if logger.level <= 10 else None  # DEBUG模式才显示详情
        )
    )


# 初始化数据库
db = Database()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    try:
        db.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

@app.get("/api/stats")
async def get_stats():
    """Get scraping statistics"""
    try:
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT source_site, COUNT(*) as count FROM news GROUP BY source_site")
        rows = cursor.fetchall()
        stats = [{"source": row[0], "count": row[1]} for row in rows]
        conn.close()
        return APIResponse.success(data={'stats': stats})
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return APIResponse.error(message="Failed to get stats")

class SystemTimezoneConfig(BaseModel):
    timezone: str

@app.get("/api/system/timezone")
async def get_system_timezone():
    """Get system timezone config"""
    tz = db.get_config("system_timezone") or "Asia/Shanghai"
    return {"timezone": tz}

@app.post("/api/system/timezone")
async def set_system_timezone(config: SystemTimezoneConfig):
    """Set system timezone config"""
    import zoneinfo
    try:
        zoneinfo.ZoneInfo(config.timezone)
        db.set_config("system_timezone", config.timezone)
        return {"status": "success", "message": f"Timezone set to {config.timezone}"}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timezone")

class DailyPushTimeConfig(BaseModel):
    time: str # "20:00"

@app.get("/api/system/push_time")
async def get_push_time():
    """Get daily push time config"""
    t = db.get_config("daily_push_time") or "20:00"
    return {"time": t}

@app.post("/api/system/push_time")
async def set_push_time(config: DailyPushTimeConfig):
    """Set daily push time config (HH:MM)"""
    try:
        # Validate format
        datetime.strptime(config.time, "%H:%M")
        db.set_config("daily_push_time", config.time)
        return {"status": "success", "message": f"Push time set to {config.time}"}
    except ValueError:
         raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

@app.get("/api/news")
async def get_news(page: int = 1, limit: int = 50, source: Optional[str] = None, stage: Optional[str] = None, keyword: Optional[str] = None):
    """Get news list with pagination"""
    try:
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
        
        if keyword:
            query += " AND (title LIKE ? OR content LIKE ?)"
            term = f"%{keyword}%"
            params.append(term)
            params.append(term)
        
        # Count total
        count_query = "SELECT count(*) FROM (" + query + ")"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # Get data
        query += " ORDER BY published_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        news_items = []
        for row in rows:
            news_items.append(dict(zip(columns, row)))
            
        conn.close()
        
        return APIResponse.paginated(
            data=news_items,
            total=total_count,
            page=page,
            limit=limit
        )
            
    except Exception as e:
        logger.error(f"Error getting news: {e}")
        return APIResponse.error(message=f"Failed to get news: {str(e)}")


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
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === 开始手动去重 ===")
        print(f"时间窗口: {req.time_window_hours} 小时")
        
        news_list = db.get_news_by_time_range(req.time_window_hours)
        print(f"扫描新闻数量: {len(news_list) if news_list else 0}")
        
        if not news_list:
            print("未找到符合条件的新闻，结束。")
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
        print("正在调用 LocalDeduplicator (本地去重算法)...")
        dedup = LocalDeduplicator(similarity_threshold=0.50, time_window_hours=req.time_window_hours)
        
        # 记录开始前的内存状态或简单日志
        news_list = dedup.mark_duplicates(news_list)
        
        # 3. 统计和处理重复项
        duplicates = [n for n in news_list if n.get('is_local_duplicate', False)]
        print(f"发现重复项: {len(duplicates)} 条")
        
        duplicate_groups = {}
        
        for dup in duplicates:
            master_idx = dup.get('duplicate_of')
            if master_idx is not None and master_idx < len(news_list):
                master = news_list[master_idx]
                master_id = master['id']
                
                # print(f"  ❌ 重复: [ID:{dup['id']}] {dup['title'][:30]}...")
                # print(f"     → 归并到: [ID:{master_id}] {master['title'][:30]}...")
                
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
        archived_count = 0  # 初始化为 0
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

# ==================== 辅助函数 ====================

def is_working_hours():
    """
    检查当前是否为工作时间 (系统配置时区 08:00 - 24:00)
    媒体通常在 01:00 - 08:00 停止更新
    """
    # 使用系统配置的时间 (含时区转换)
    now_hour = db.get_system_time().hour
    # 允许 08:00 到 23:59 (即 [8, 24))
    return 8 <= now_hour < 24

# ==================== 调度器循环 ====================

async def scheduler_loop():
    logger.info("Starting Scheduler Loop")
    while True:
        try:
            # 检查是否在工作时间
            if not is_working_hours():
                logger.info("💤 [Scheduler] Night time (00:00-08:00), sleeping...")
                # 休眠30分钟再检查
                await asyncio.sleep(1800)
                continue

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
                    
                    # 添加随机时间波动（±20%）避免固定模式
                    import random
                    jitter_percent = 0.2
                    jitter = interval * random.uniform(-jitter_percent, jitter_percent)
                    adjusted_interval = interval + jitter
                    
                    if diff >= adjusted_interval:
                        should_run = True
                        logger.info(f"[Scheduler] {name}: interval={interval}m, jitter={jitter:.1f}m, actual={adjusted_interval:.1f}m")
                
                if should_run:
                    limit = config.get("limit", 5)
                    logger.info(f"[Scheduler] Triggering {name} (Interval: {interval}m, Limit: {limit})")
                    asyncio.create_task(run_scraper_task(name, limit))
            
            # Check for daily push (20:00 Beijing Time)
            await auto_daily_best_push()

            await asyncio.sleep(60) # Check every minute
        except Exception as e:
            logger.error(f"Scheduler Error: {e}")
            await asyncio.sleep(60)

async def auto_daily_best_push(force=False):
    """
    Daily scheduled task to push best news (Score >= 6) to Telegram at 20:00
    """
    try:
        from datetime import datetime, timedelta
        # 使用系统配置时区
        db = Database()
        now = db.get_system_time()
        
        # 1. check time window (Target Time - Target Time + 5min) unless forced
        if not force:
            target_time_str = db.get_config('daily_push_time') or "20:00"
            try:
                target_hour, target_minute = map(int, target_time_str.split(':'))
            except:
                target_hour, target_minute = 20, 0

            # 检查时间窗口 (Target ~ Target+5min)
            # 例如: 20:00 ~ 20:05
            is_time = (now.hour == target_hour and 
                       target_minute <= now.minute <= target_minute + 5)
            
            if not is_time:
                return {
                    "status": "skipped",
                    "message": f"Not push time (Current: {now.strftime('%H:%M')}, Target: {target_time_str})"
                }

            # 2. Check if already pushed today
            today_str = now.strftime('%Y-%m-%d')
            last_push_date = db.get_config('last_daily_push_date')
            if last_push_date == today_str:
                return

            logger.info(f"⏰ [Daily Push] Starting daily best news push for {today_str}")
        else:
            logger.info(f"⏰ [Daily Push] FORCED execution")
            db = Database()

        # 3. Fetch news: Published in last 24h, Score >= 6
        # Calculate time range
        end_time = now
        start_time = end_time - timedelta(hours=24)
        
        # Get news from DB
        # NOTE: 'score' column does not exist, we must parse it from 'ai_explanation'
        query = """
            SELECT title, source_url, ai_explanation
            FROM curated_news 
            WHERE published_at >= ? 
            AND ai_status IN ('approved', 'rejected')
            AND ai_explanation IS NOT NULL
        """
        rows = db.execute_query(query, (start_time.strftime('%Y-%m-%d %H:%M:%S'),))
        
        # Process and filter in Python
        news_list = []
        for row in rows:
            explanation = row['ai_explanation'] or ""
            score = 0
            # Extract score "X分 - Reason"
            if explanation and '分' in explanation:
                try:
                    score = int(explanation.split('分')[0])
                except:
                    score = 0
            
            if score >= 6:
                news_list.append({
                    'title': row['title'],
                    'source_url': row['source_url'],
                    'score': score
                })
        
        # Sort by score descending
        news_list.sort(key=lambda x: x['score'], reverse=True)
        
        if not news_list:
            logger.info("⏰ [Daily Push] No news found with score >= 6 in last 24h")
            if not force:
                today_str = now.strftime('%Y-%m-%d')
                db.set_config('last_daily_push_date', today_str)
            return {
                "status": "skipped",
                "message": "No news found with score >= 6 in last 24h"
            }

        logger.info(f"⏰ [Daily Push] Found {len(news_list)} high-quality news items")

        # 4. Format and Split Message (Telegram limit: 4096, Safe limit: 3500)
        import html
        
        # Prepare all lines first
        formatted_items = []
        for news in news_list:
            score = news.get('score', 0)
            title = news.get('title', "No Title")
            url = news.get('source_url', "")
            
            # Escape HTML characters for title
            safe_title = html.escape(title)
            
            # Format: <a href="...">Title</a>
            line = f"<a href=\"{url}\">{safe_title}</a>"
            formatted_items.append(line)

        # Split into chunks
        MAX_LENGTH = 3500
        message_parts = []
        current_part = []
        current_length = 0
        
        base_header = f"📅 <b>{now.strftime('%Y-%m-%d')} 精选日报 (Score>=6)</b>\n\n"
        
        # Initial header length
        current_length = len(base_header)
        
        # If we have many items, we might need multiple parts
        for item in formatted_items:
            # +2 for double newline
            item_len = len(item) + 2
            
            if current_length + item_len > MAX_LENGTH:
                # Current part full, finalize it
                message_parts.append(current_part)
                # Start new part
                current_part = [item]
                current_length = item_len
            else:
                current_part.append(item)
                current_length += item_len
        
        # Add last part
        if current_part:
            message_parts.append(current_part)
            
        # 5. Send to Telegram (Mulitpart)
        from services.telegram_bot import TelegramBot
        token = db.get_config("telegram_bot_token")
        chat_id = db.get_config("telegram_chat_id")

        if not token or not chat_id:
            logger.error("❌ [Daily Push] Telegram config missing")
            return {
                "status": "error",
                "message": "Telegram config missing"
            }
            
        bot = TelegramBot(token, chat_id)
        
        total_parts = len(message_parts)
        for i, part_items in enumerate(message_parts, 1):
            if total_parts > 1:
                header = f"📅 <b>{now.strftime('%Y-%m-%d')} 精选日报 ({i}/{total_parts})</b>\n\n"
            else:
                header = base_header
                
            full_message = header + "\n\n".join(part_items)
            
            # Add footer to the last part only
            if i == total_parts:
                 full_message += '\n\n🤖 由 <a href="https://t.me/CheshireBTC">AINEWS</a> 自动生成'
            
            success = await bot.send_message(full_message, parse_mode='HTML')
            if not success:
                logger.error(f"❌ [Daily Push] Failed to send part {i}/{total_parts}")
            else:
                logger.info(f"✅ [Daily Push] Sent part {i}/{total_parts}")
            
            # Small delay between parts to avoid rate limits
            if i < total_parts:
                await asyncio.sleep(1)

        if not force:
            today_str = now.strftime('%Y-%m-%d')
            db.set_config('last_daily_push_date', today_str)

        return {
            "status": "success",
            "count": len(news_list),
            "parts": total_parts,
            "message": f"Pushed {len(news_list)} items in {total_parts} parts"
        }

    except Exception as e:
        logger.error(f"❌ [Daily Push] Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/telegram/daily_push")
async def trigger_daily_push():
    """手动触发日报推送 (Force Run)"""
    return await auto_daily_best_push(force=True)

# ==================== 自动化Pipeline函数 ====================

async def auto_pipeline_loop():
    """
    自动化处理Pipeline
    每15分钟执行一次：去重 → 过滤 → AI打分 → 逐条推送
    """
    logger.info("=" * 60)
    logger.info("🤖 [Auto-Pipeline] Automated Pipeline System Started")
    logger.info("=" * 60)
    logger.info("🤖 [Auto-Pipeline] Configuration:")
    logger.info("   - Scraper interval: 15 minutes")
    logger.info("   - Working hours: 08:00 - 24:00 (Beijing Time)")
    logger.info("   - Deduplication range: 2 hours")
    logger.info("   - Min push score: ≥5")
    logger.info("   - Push interval: 30-60 seconds")
    logger.info("=" * 60)
    logger.info("🤖 [Auto-Pipeline] Waiting 10 seconds for system startup...")
    logger.info("=" * 60)
    
    # 等待10秒让系统完全启动
    await asyncio.sleep(10)
    
    while True:
        try:
            # 检查是否在工作时间
            if not is_working_hours():
                logger.info("💤 [Auto-Pipeline] Night time (00:00-08:00), sleeping...")
                # 休眠30分钟再检查
                await asyncio.sleep(1800)
                continue
                
            logger.info("=" * 60)
            logger.info("🤖 [Auto-Pipeline] Starting new cycle")
            logger.info("=" * 60)
            
            # 等待所有爬虫完成（检查状态）
            await wait_for_scrapers()
            
            # 步骤1：自动去重（最近2小时）
            await auto_deduplication()
            
            # 步骤2：自动关键词过滤
            await auto_keyword_filter()
            
            # 步骤3：自动AI打分
            await auto_ai_scoring()
            
            # 步骤4：逐条推送到Telegram
            await auto_telegram_push()
            
            logger.info("=" * 60)
            logger.info("🤖 [Auto-Pipeline] Cycle completed, waiting for next cycle...")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"🤖 [Auto-Pipeline] Error in pipeline: {e}", exc_info=True)
        
        # 15分钟后执行下一轮
        await asyncio.sleep(900)


async def wait_for_scrapers():
    """
    智能等待爬虫完成
    - 如果有爬虫正在运行，必须等待（防止数据竞争）
    - 如果所有爬虫都空闲，直接继续
    """
    logger.info("🕐 [Auto-Pipeline] Checking scraper status...")
    
    # 只需要等待那些正在运行的
    while True:
        running_scrapers = []
        for name, status in SCRAPER_STATUS.items():
            if status.get("status") == "running":
                running_scrapers.append(name)
        
        if not running_scrapers:
            logger.info("✅ [Auto-Pipeline] No active scrapers, proceeding immediately")
            return
            
        logger.info(f"⏳ [Auto-Pipeline] Waiting for {len(running_scrapers)} active scrapers: {', '.join(running_scrapers)}")
        await asyncio.sleep(10)


async def auto_deduplication():
    """自动去重：处理最近2小时的原始数据"""
    logger.info("🔄 [Auto-Dedup] Starting auto deduplication...")
    
    db = Database()
    conn = db.connect()
    cursor = conn.cursor()
    
    # 获取最近2小时stage='raw'的新闻
    from datetime import datetime, timedelta
    cutoff_time = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("""
        SELECT id, title, content, source_url, source_site, published_at, scraped_at
        FROM news 
        WHERE stage = 'raw' AND published_at >= ?
        ORDER BY published_at DESC
    """, (cutoff_time,))
    
    rows = cursor.fetchall()
    
    logger.info(f"🔄 [Auto-Dedup] Found {len(rows)} raw news items")
    
    if len(rows) == 0:
        conn.close()
        logger.info("🔄 [Auto-Dedup] No raw data to process")
        return
    
    # 转换为列表格式
    news_list = []
    for row in rows:
        news_list.append({
            'id': row['id'],
            'title': row['title'],
            'content': row['content'],
            'source_url': row['source_url'],
            'source_site': row['source_site'],
            'published_at': row['published_at'],
            'scraped_at': row['scraped_at']
        })
    
    # 使用LocalDeduplicator标记重复
    from filters.local_deduplicator import LocalDeduplicator
    deduplicator = LocalDeduplicator()
    marked_news = deduplicator.mark_duplicates(news_list)
    
    # 将非重复的新闻移到deduplicated_news表
    dedup_count = 0
    for news in marked_news:
        if not news.get('is_local_duplicate', False):
            # 插入到deduplicated_news
            cursor.execute("""
                INSERT OR IGNORE INTO deduplicated_news 
                (title, content, source_site, source_url, published_at, scraped_at, deduplicated_at, stage, type, original_news_id)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'deduplicated', 'news', ?)
            """, (
                news['title'],
                news['content'],
                news['source_site'],
                news['source_url'],
                news['published_at'],
                news['scraped_at'],
                news['id']
            ))
            
            # 更新原新闻stage为deduplicated
            cursor.execute("UPDATE news SET stage = 'deduplicated' WHERE id = ?", (news['id'],))
            dedup_count += 1
        else:
            # 标记为重复
            cursor.execute("UPDATE news SET stage = 'duplicate' WHERE id = ?", (news['id'],))
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ [Auto-Dedup] Completed: {dedup_count} items deduplicated, {len(rows)-dedup_count} duplicates filtered")


async def auto_keyword_filter():
    """
    自动关键词过滤
    使用数据库中配置的黑名单过滤去重后的新闻
    """
    logger.info("🔍 [Auto-Filter] Starting auto keyword filtering...")
    
    db = Database()
    
    try:
        # 调用数据库内置的过滤方法
        # 这个方法会:
        # 1. 自动从 keyword_blacklist 表加载规则
        # 2. 扫描 deduplicated_news 表中 deduplicated 状态的新闻
        # 3. 将通过的新闻移入 curated_news，被过滤的标记为 filtered
        # 4. 默认扫描过去24小时的数据（足够覆盖15分钟的周期）
        
        result = db.filter_news_by_blacklist(time_range_hours=24)
        
        scanned = result.get('scanned', 0)
        filtered = result.get('filtered', 0)
        curated = result.get('curated', 0)
        
        if scanned > 0:
            logger.info(f"✅ [Auto-Filter] Completed: Scanned {scanned}, Passed {curated}, Filtered {filtered}")
        else:
            logger.info("🔍 [Auto-Filter] No deduplicated data to process")
            
    except Exception as e:
        logger.error(f"❌ [Auto-Filter] Error during filtering: {e}", exc_info=True)


async def auto_ai_scoring():
    """自动AI打分：只处理未打分的精选数据"""
    logger.info("🤖 [Auto-AI] Starting auto AI scoring...")
    
    db = Database()
    
    # 获取配置
    api_key = db.get_config("llm_api_key")
    base_url = db.get_config("llm_base_url") or "https://api.deepseek.com"
    model = db.get_config("llm_model") or "deepseek-chat"
    filter_prompt = db.get_config("ai_filter_prompt") or "评估新闻价值"
    
    if not api_key:
        logger.warning("⚠️ [Auto-AI] No API key configured, skipping AI scoring")
        return
    
    # 获取未打分数据
    conn = db.connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) FROM curated_news 
        WHERE ai_status IS NULL OR ai_status = '' OR ai_status = 'pending'
    """)
    unscored_count = cursor.fetchone()[0]
    
    logger.info(f"🤖 [Auto-AI] Found {unscored_count} items to score")
    
    if unscored_count == 0:
        conn.close()
        logger.info("🤖 [Auto-AI] No items to score")
        return
    
    # 分批处理（每批10条）
    batch_size = 10
    processed = 0
    
    for offset in range(0, unscored_count, batch_size):
        cursor.execute("""
            SELECT id, title FROM curated_news 
            WHERE ai_status IS NULL OR ai_status = '' OR ai_status = 'pending'
            LIMIT ? OFFSET ?
        """, (batch_size, offset))
        
        rows = cursor.fetchall()
        if not rows:
            break
        
        news_items = [{"id": row["id"], "title": row["title"]} for row in rows]
        
        # 调用AI
        service = DeepSeekService(api_key, base_url, model)
        try:
            results = await service.filter_titles(news_items, filter_prompt)
            
            # 更新数据库
            for item in results:
                try:
                    item_id = int(item['id'])
                    score = item.get('score', 0)
                    reason = item.get('reason', '')
                    tag = item.get('tag', '')
                    
                    status = 'approved' if score >= 5 else 'rejected'
                    summary = f"{score}分 {reason} #{tag}"
                    
                    cursor.execute("""
                        UPDATE curated_news 
                        SET ai_status = ?, ai_summary = ?
                        WHERE id = ?
                    """, (status, summary, item_id))
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"⚠️ [Auto-AI] Error updating item {item}: {e}")
            
            conn.commit()
            logger.info(f"🤖 [Auto-AI] Batch processed: {len(results)} items")
            
        except Exception as e:
            logger.error(f"⚠️ [Auto-AI] Error in batch: {e}")
        
        # 批次间延迟
        await asyncio.sleep(2)
    
    conn.close()
    logger.info(f"✅ [Auto-AI] Completed: {processed} items scored")


async def auto_telegram_push():
    """自动推送：逐条推送≥5分且未推送的新闻"""
    logger.info("📤 [Auto-Push] Starting auto Telegram push...")
    
    db = Database()
    
    # 获取Telegram配置
    token = db.get_config("telegram_bot_token")
    chat_id = db.get_config("telegram_chat_id")
    
    if not token or not chat_id:
        logger.warning("⚠️ [Auto-Push] Telegram not configured, skipping push")
        return
    
    # 获取待推送新闻：ai_status='approved' AND (push_status IS NULL OR push_status='pending')
    conn = db.connect()
    cursor = conn.cursor()
    
    # 从ai_summary中提取分数并筛选≦5分
    cursor.execute("""
        SELECT id, title, source_url, content, ai_summary
        FROM curated_news
        WHERE ai_status = 'approved'
        AND (push_status IS NULL OR push_status = 'pending')
        ORDER BY curated_at DESC
    """)
    
    all_news = cursor.fetchall()
    
    # 手动筛选≥5分的
    to_push = []
    for news in all_news:
        ai_summary = news[4] or ""
        # 尝试从summary中提取分数（格式：8分 xxx）
        try:
            score_str = ai_summary.split('分')[0].strip()
            score = int(score_str)
            if score >= 5:
                to_push.append(news)
        except:
            pass
    
    logger.info(f"📤 [Auto-Push] Found {len(to_push)} items to push (≥5分)")
    
    if len(to_push) == 0:
        conn.close()
        logger.info("📤 [Auto-Push] No items to push")
        return
    
    # 逐条推送
    from services.telegram_bot import TelegramBot
    import html as html_lib
    import random
    
    TELEGRAM_FOOTER = """
<a href="https://0xcheshire.gitbook.io/web3/">币圈新人手册</a>
注册交易所 <a href="https://binance.com/join?ref=SRXT5KUM">币安</a> <a href="https://okx.com/join/A999998">欧易</a>
Web3钱包 <a href="https://web3.binance.com/referral?ref=RP3AEJ2M">币安</a> <a href="https://web3.okx.com/ul/joindex?ref=1234567">OKX</a> <a href="https://link.metamask.io/rewards?referral=36P4HH">小狐狸（刷分）</a>"""

    bot = TelegramBot(token, chat_id)
    success_count = 0
    
    for news in to_push:
        news_id, title, url, content, ai_summary = news
        
        try:
            # 构建消息
            escaped_title = html_lib.escape(title)
            escaped_content = html_lib.escape(content or '')
            
            # 限制内容长度
            if len(escaped_content) > 500:
                escaped_content = escaped_content[:500] + '...'
            
            message = f'<b><a href="{url}">{escaped_title}</a></b>\n\n{escaped_content}\n{TELEGRAM_FOOTER}'
            
            # 发送
            success = await bot.send_message(message, parse_mode='HTML')
            
            if success:
                # 标记为已推送
                cursor.execute("""
                    UPDATE curated_news 
                    SET push_status = 'sent', pushed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (news_id,))
                conn.commit()
                
                success_count += 1
                logger.info(f"✅ [Auto-Push] Sent ({success_count}/{len(to_push)}): {title[:40]}...")
            else:
                logger.error(f"❌ [Auto-Push] Failed to send: {title[:40]}...")
            
            # 随机延迟30-60秒
            delay = random.randint(30, 60)
            logger.info(f"⏳ [Auto-Push] Waiting {delay}s before next push...")
            await asyncio.sleep(delay)
            
        except Exception as e:
            logger.error(f"❌ [Auto-Push] Error pushing {title[:40]}: {e}")
            await asyncio.sleep(30)
    
    conn.close()
    logger.info(f"✅ [Auto-Push] Completed: {success_count}/{len(to_push)} items pushed")

# ==================== End of Auto-Pipeline ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Scheduler Loop")
    scraper_task = asyncio.create_task(scheduler_loop())
    
    # 启动自动化Pipeline
    pipeline_task = asyncio.create_task(auto_pipeline_loop())
    logger.info("🤖 [Auto-Pipeline] Automated pipeline task started")
    
    yield
    
    # Shutdown
    scraper_task.cancel()
    pipeline_task.cancel()
    try:
        await scraper_task
        await pipeline_task
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
    try:
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT source_site, count(*) as count FROM news GROUP BY source_site")
        rows = cursor.fetchall()
        conn.close()
        
        stats = [{"source": row['source_site'], "count": row['count']} for row in rows]
        return APIResponse.success(data={"stats": stats}, message="统计查询成功")
    except Exception as e:
        raise DatabaseError(f"查询统计失败: {str(e)}")

@app.get("/api/news")
@app.get("/api/news")
def get_news(page: int = 1, limit: int = 50, source: Optional[str] = None, stage: Optional[str] = None, keyword: Optional[str] = None):
    """Get news list with pagination"""
    try:
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
        
        if keyword:
            query += " AND (title LIKE ? OR content LIKE ?)"
            term = f"%{keyword}%"
            params.append(term)
            params.append(term)
        
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
        if keyword:
            count_query += " AND (title LIKE ? OR content LIKE ?)"
            term = f"%{keyword}%"
            count_params.append(term)
            count_params.append(term)
            
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return APIResponse.paginated(
            data=[dict(row) for row in rows],
            total=total,
            page=page,
            limit=limit
        )
    except Exception as e:
        raise DatabaseError(f"查询新闻失败: {str(e)}")

@app.delete("/api/news/{news_id}")
def delete_news(news_id: int):
    """Delete a news item"""
    success = db.delete_news(news_id)
    if success:
        return APIResponse.success(message="删除成功")
    raise NotFoundError("新闻不存在或删除失败")

@app.get("/api/deduplicated/news")
def get_deduplicated_news_api(page: int = 1, limit: int = 50, source: Optional[str] = None, keyword: Optional[str] = None):
    """获取已去重的数据"""
    result = db.get_deduplicated_news(page, limit, source, keyword)
    return APIResponse.paginated(
        data=result['data'],
        total=result['total'],
        page=result['page'],
        limit=result['limit']
    )

@app.get("/api/deduplicated/stats")
def get_deduplicated_stats():
    """获取已去重数据的统计"""
    stats = db.get_deduplicated_stats()
    return APIResponse.success(data=stats, message="统计查询成功")

@app.delete("/api/deduplicated/news/{news_id}")
def delete_deduplicated_news(news_id: int):
    """删除已去重数据"""
    success = db.delete_deduplicated_news(news_id)
    if success:
        return APIResponse.success(message="删除成功")
    raise NotFoundError("数据不存在或删除失败")

@app.post("/api/deduplicated/batch_restore_all")
async def batch_restore_all_deduplicated():
    """批量还原所有去重数据到 raw 状态"""
    db_instance = Database()
    try:
        conn = db_instance.connect()
        cursor = conn.cursor()
        
        # 查询所有 deduplicated_news 记录（不限 stage）
        cursor.execute("""
            SELECT id, original_news_id 
            FROM deduplicated_news
        """)
        rows = cursor.fetchall()
        processed_count = len(rows)
        
        if processed_count > 0:
            # 收集所有 original_news_id
            news_ids = [row[1] for row in rows if row[1] is not None]
            
            # 将对应的 news 记录的 stage 改回 'raw'
            if news_ids:
                placeholders = ','.join('?' * len(news_ids))
                cursor.execute(f"""
                    UPDATE news 
                    SET stage = 'raw'
                    WHERE id IN ({placeholders})
                """, news_ids)
            
            # 删除所有 deduplicated_news 记录
            cursor.execute("DELETE FROM deduplicated_news")
            
            # 同时删除 curated_news 中对应的记录（如果存在）
            if news_ids:
                cursor.execute(f"""
                    DELETE FROM curated_news 
                    WHERE original_news_id IN ({placeholders})
                """, news_ids)
            
            conn.commit()
        
        conn.close()
        
        return APIResponse.success(
            data={"restored_count": processed_count},
            message=f"成功还原 {processed_count} 条数据到原始状态，可重新去重"
        )
    except Exception as e:
        logger.error(f"批量还原去重数据失败: {e}")
        raise DatabaseError(f"批量还原失败: {str(e)}")

@app.post("/api/filtered/batch_restore_all")
async def batch_restore_all_filtered():
    """批量还原已过滤和已精选的数据，重新执行本地过滤"""
    db_instance = Database()
    try:
        conn = db_instance.connect()
        cursor = conn.cursor()
        
        # 查询需要还原的数据数量（filtered + curated）
        cursor.execute("SELECT COUNT(*) FROM deduplicated_news WHERE stage IN ('filtered', 'curated')")
        restore_count = cursor.fetchone()[0]
        
        if restore_count > 0:
            # 将 filtered 和 curated 都改回 deduplicated
            cursor.execute("""
                UPDATE deduplicated_news 
                SET stage = 'deduplicated'
                WHERE stage IN ('filtered', 'curated')
            """)
            
            # 清空 curated_news 表
            cursor.execute("DELETE FROM curated_news")
            
            conn.commit()
        
        conn.close()
        
        return APIResponse.success(
            data={"restored_count": restore_count},
            message=f"成功还原 {restore_count} 条数据，可重新执行本地过滤"
        )
    except Exception as e:
        logger.error(f"批量还原已过滤数据失败: {e}")
        raise DatabaseError(f"批量还原失败: {str(e)}")

@app.get("/api/curated/news")
def get_curated_news_api(page: int = 1, limit: int = 50, source: Optional[str] = None, keyword: Optional[str] = None):
    """获取精选数据"""
    result = db.get_curated_news(page, limit, source, keyword)
    return APIResponse.paginated(
        data=result['data'],
        total=result['total'],
        page=result['page'],
        limit=result['limit']
    )

@app.get("/api/curated/stats")
def get_curated_stats_api():
    """获取精选数据统计"""
    stats = db.get_curated_stats()
    return APIResponse.success(data=stats, message="统计查询成功")

@app.delete("/api/curated/news/{news_id}")
def delete_curated_news(news_id: int):
    """删除精选数据"""
    success = db.delete_curated_news(news_id)
    if success:
        return APIResponse.success(message="删除成功")
    raise NotFoundError("数据不存在或删除失败")

class RestoreRequest(BaseModel):
    source_table: str = 'deduplicated_news'

@app.post("/api/news/restore/{news_id}")
def restore_news_api(news_id: int, req: RestoreRequest):
    """还原被过滤的新闻"""
    success = db.restore_news(news_id, req.source_table)
    if success:
        return APIResponse.success(message="还原成功")
    raise BusinessError("还原失败")

# AI Filtering Endpoints

class AIFilterRequest(BaseModel):
    hours: int = 8
    filter_prompt: str

class AIConfig(BaseModel):
    prompt: Optional[str] = None
    hours: Optional[int] = 8

@app.get("/api/ai/config")
def get_ai_config():
    """获取AI配置"""
    prompt = db.get_config("ai_filter_prompt") or ""
    hours = db.get_config("ai_filter_hours")
    return APIResponse.success(
        data={"prompt": prompt, "hours": int(hours) if hours else 8}
    )

@app.post("/api/ai/config")
def set_ai_config(config: AIConfig):
    """设置AI配置"""
    if config.prompt is not None:
        db.set_config("ai_filter_prompt", config.prompt)
    if config.hours is not None:
        db.set_config("ai_filter_hours", str(config.hours))
    return APIResponse.success(message="配置已保存")


@app.post("/api/curated/ai_filter")
async def ai_filter_curated(req: AIFilterRequest):
    """执行AI筛选:筛选精选数据中的新闻标题"""
    db = Database()
    
    # 加载AI配置 (这里简化处理,实际应该从配置表读取)
    # 暂时硬编码,后续可以改进
    api_key = db.get_config("llm_api_key")
    base_url = db.get_config("llm_base_url") or "https://api.deepseek.com"
    model = db.get_config("llm_model") or "deepseek-chat"
    
    if not api_key:
        raise ValidationError("请先配置 DeepSeek API Key")
    
    # 获取指定时间范围内未处理或通过的精选数据
    # 支持分页处理以优化速度
    from datetime import datetime, timedelta
    if req.hours <= 0:
        cutoff_time = '1970-01-01 00:00:00'
    else:
        cutoff_time = (datetime.now() - timedelta(hours=req.hours)).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[DEBUG] AI Filter: Hours={req.hours}, Cutoff={cutoff_time}")
    
    conn = db.connect()
    cursor = conn.cursor()
    
    # 首先获取总数 - 只处理未筛选的数据(pending或NULL)
    cursor.execute(
        "SELECT COUNT(*) FROM curated_news WHERE published_at >= ? AND (ai_status IS NULL OR ai_status = '' OR ai_status = 'pending')",
        (cutoff_time,)
    )
    total_count = cursor.fetchone()[0]
    print(f"[DEBUG] AI Filter: Found {total_count} items to process")
    
    if total_count == 0:
        conn.close()
        return APIResponse.success(
            data={"processed": 0, "filtered": 0, "total": 0},
            message="没有待筛选的数据"
        )
    
    # 获取当前批次的数据（默认每批 10 条，避免 JSON 过长被截断）
    batch_size = getattr(req, 'batch_size', 10)
    offset = getattr(req, 'offset', 0)
    
    cursor.execute(
        "SELECT id, title FROM curated_news WHERE published_at >= ? AND (ai_status IS NULL OR ai_status = '' OR ai_status = 'pending') LIMIT ? OFFSET ?",
        (cutoff_time, batch_size, offset)
    )
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return APIResponse.success(
            data={"processed": 0, "total": total_count, "offset": offset},
            message="当前批次没有数据"
        )
    
    news_items = [{"id": row["id"], "title": row["title"]} for row in rows]
    
    # 调用AI筛选
    service = DeepSeekService(api_key, base_url, model)
    try:
        results = await service.filter_titles(news_items, req.filter_prompt)
        # results example: [{"id": 1, "score": 8, "reason": "Good", "tag": "AI"}, ...]
        
        # Build map - 将 id 转换为整数以匹配数据库类型
        result_map = {}
        for item in results:
            try:
                item_id = int(item['id'])  # 转换字符串 ID 为整数
                result_map[item_id] = item
            except (ValueError, KeyError) as e:
                print(f"[WARNING] Skipping invalid result item: {item}, error: {e}")
        
        print(f"[DEBUG] Built result_map with {len(result_map)} items")
        
        # 更新数据库
        conn = db.connect()
        cursor = conn.cursor()
        
        updated_count = 0
        filtered_count = 0
        
        for news_item in news_items:
            news_id = news_item['id']
            # Default to rejected if AI didn't return it (safety fallback), or use AI result
            resolution = result_map.get(news_id)
            
            new_status = 'rejected'
            reason = "AI未返回结果"
            
            if resolution:
                # 评分制：获取分数、理由和标签
                score = resolution.get('score', 0)
                raw_reason = resolution.get('reason', '')
                tag = resolution.get('tag', '')
                
                # 阈值判断：>=6分为approved，<6分为rejected
                if score >= 6:
                    new_status = 'approved'
                else:
                    new_status = 'rejected'
                
                # 组合显示格式：分数-理由 #标签
                if tag:
                    reason = f"{score}分-{raw_reason} #{tag}"
                elif raw_reason:
                    reason = f"{score}分-{raw_reason}"
                else:
                    reason = f"{score}分"
            
            cursor.execute(
                "UPDATE curated_news SET ai_status = ?, ai_explanation = ? WHERE id = ?",
                (new_status, reason, news_id)
            )
            if cursor.rowcount > 0:
                updated_count += 1
                if new_status == 'rejected':
                    filtered_count += 1
            
        conn.commit()
        conn.close()
        
        
        return APIResponse.success(
            data={
                "processed": updated_count,
                "filtered": filtered_count,
                "total": total_count,
                "results": results,  # 返回详细处理结果
                "offset": offset,
                "has_more": (offset + batch_size) < total_count
            },
            message=f"筛选完成: 处理 {updated_count} 条, 拒绝 {filtered_count} 条"
        )

        
    except Exception as e:
        logger.error(f"AI筛选失败: {e}")
        raise DatabaseError(f"AI筛选失败: {str(e)}")


@app.post("/api/curated/batch_restore")
async def batch_restore_rejected():
    """批量还原所有被拒绝的数据"""
    db = Database()
    try:
        conn = db.connect()
        cursor = conn.cursor()
        
        # 查询被拒绝的数据数量
        cursor.execute("SELECT COUNT(*) FROM curated_news WHERE ai_status = 'rejected'")
        rejected_count = cursor.fetchone()[0]
        
        if rejected_count > 0:
            # 将所有 rejected 状态改为 pending，并清空 ai_explanation
            cursor.execute("""
                UPDATE curated_news 
                SET ai_status = 'pending', ai_explanation = NULL 
                WHERE ai_status = 'rejected'
            """)
            conn.commit()
        
        conn.close()
        
        return APIResponse.success(
            data={"restored_count": rejected_count},
            message=f"成功还原 {rejected_count} 条数据"
        )
    except Exception as e:
        logger.error(f"批量还原失败: {e}")
        raise DatabaseError(f"批量还原失败: {str(e)}")


@app.post("/api/curated/clear_all_ai_status")
async def clear_all_ai_status():
    """清空所有 AI 筛选状态"""
    db = Database()
    try:
        conn = db.connect()
        cursor = conn.cursor()
        
        # 查询所有有 AI 状态的数据
        cursor.execute("SELECT COUNT(*) FROM curated_news WHERE ai_status IS NOT NULL AND ai_status != ''")
        total_count = cursor.fetchone()[0]
        
        if total_count > 0:
            # 清空所有 AI 相关字段
            cursor.execute("""
                UPDATE curated_news 
                SET ai_status = NULL, ai_explanation = NULL 
                WHERE ai_status IS NOT NULL AND ai_status != ''
            """)
            conn.commit()
        
        conn.close()
        
        
        return APIResponse.success(
            data={"cleared_count": total_count},
            message=f"成功清空 {total_count} 条数据的 AI 筛选状态"
        )
    except Exception as e:
        logger.error(f"清空失败: {e}")
        raise DatabaseError(f"清空失败: {str(e)}")


@app.get("/api/curated/export")
async def get_export_news(hours: int = 24, min_score: int = 6):
    """获取可导出的新闻列表（所有被AI评分的数据）"""
    db = Database()
    try:
        conn = db.connect()
        cursor = conn.cursor()
        
        # 查询所有被AI评分的数据（approved + rejected）
        if hours ==0:
            # "全部时间" - 不限制时间范围
            logger.info("查询时间范围: 全部时间 (无限制)")
            cursor.execute("""
                SELECT id, title, content, source_url, source_site, ai_status, ai_explanation, curated_at, published_at
                FROM curated_news 
                WHERE ai_status IN ('approved', 'rejected')
                AND ai_explanation IS NOT NULL
            """)
        else:
            # 计算时间范围 - 使用系统配置时间
            cutoff_time = db.get_system_time() - timedelta(hours=hours)
            cutoff_time_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"查询时间范围: >= {cutoff_time_str} (Published)")
            
            cursor.execute("""
                SELECT id, title, content, source_url, source_site, ai_status, ai_explanation, curated_at, published_at
                FROM curated_news 
                WHERE published_at >= ? 
                AND ai_status IN ('approved', 'rejected')
                AND ai_explanation IS NOT NULL
            """, (cutoff_time_str,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 解析评分并过滤
        filtered_news = []
        for row in rows:
            news_item = {
                'id': row['id'],
                'title': row['title'],
                'content': row['content'],
                'source_url': row['source_url'],
                'source_site': row['source_site'],
                'ai_status': row['ai_status'],
                'ai_explanation': row['ai_explanation'],
                'curated_at': row['curated_at']
            }
            
            # 提取评分
            explanation = row['ai_explanation'] or ""
            score = 0
            if explanation and '分' in explanation:
                try:
                    score = int(explanation.split('分')[0])
                except:
                    score = 0
            
            news_item['score'] = score
            
            # 过滤：评分>=min_score
            if score >= min_score:
                filtered_news.append(news_item)
        
        # 按评分从高到低排序
        filtered_news.sort(key=lambda x: x['score'], reverse=True)
        
        return APIResponse.success(
            data={"news": filtered_news, "total": len(filtered_news)}
        )
        
    except Exception as e:
        logger.error(f"获取导出新闻失败: {e}")
        raise DatabaseError(f"获取导出新闻失败: {str(e)}")


@app.post("/api/curated/restore/{news_id}")
def restore_curated_news_api(news_id: int):
    """还原被AI拒绝的新闻"""
    db = Database()
    conn = db.connect()
    cursor = conn.cursor()
    # 将状态设置为 'restored' (或者 'approved' ? 用户想要不被再筛选，所以 'restored' 更安全)
    # 但前端 'AI 精选' 列表可能只查 'approved'。我们需要修改 get_filtered_curated_news
    # 或者我们设为 'approved' 并加个额外字段？
    # 简单点：设为 'restored'，然后修改查询逻辑让它出现在精选列表里。
    cursor.execute("UPDATE curated_news SET ai_status = 'restored' WHERE id = ?", (news_id,))
    conn.commit()
    conn.close()
    return APIResponse.success(message="已还原")


@app.get("/api/curated/filtered")
def get_filtered_curated(status: str, page: int = 1, limit: int = 50, source: Optional[str] = None, keyword: Optional[str] = None):
    """获取筛选后的精选数据 (approved 或 rejected)"""
    db = Database()
    if status not in ['approved', 'rejected']:
        raise ValidationError("status 必须是 'approved' 或 'rejected'")
    result = db.get_filtered_curated_news(status, page, limit, source, keyword)
    return APIResponse.paginated(
        data=result['data'],
        total=result['total'],
        page=result['page'],
        limit=result['limit']
    )

@app.get("/api/filtered/dedup/news")
def get_filtered_dedup_news_api(page: int = 1, limit: int = 50, keyword: Optional[str] = None):
    result = db.get_filtered_dedup_news(page, limit, keyword)
    return APIResponse.paginated(
        data=result['data'],
        total=result['total'],
        page=result['page'],
        limit=result['limit']
    )

# --- Blacklist APIs ---

@app.get("/api/blacklist")
def get_blacklist():
    return APIResponse.success(data={"keywords": db.get_blacklist_keywords()})

class AddBlacklistRequest(BaseModel):
    keyword: str
    match_type: str = 'contains'

@app.post("/api/blacklist")
def add_blacklist(req: AddBlacklistRequest):
    """添加黑名单关键词"""
    db = Database()
    success = db.add_blacklist_keyword(req.keyword, req.match_type)
    if success:
        return APIResponse.success(message="添加成功")
    raise BusinessError("添加失败，可能关键词已存在")

@app.delete("/api/blacklist/{id}")
def delete_blacklist(id: int):
    """删除黑名单关键词"""
    success = db.remove_blacklist_keyword(id)
    if success:
        return APIResponse.success(message="删除成功")
    raise NotFoundError("删除失败")

class FilterRequest(BaseModel):
    time_range_hours: int = 24

@app.post("/api/news/filter")
def filter_news(req: FilterRequest):
    """根据黑名单执行过滤"""
    result = db.filter_news_by_blacklist(req.time_range_hours)
    return APIResponse.success(data={"stats": result})

class LoginRequest(BaseModel):
    password: str

@app.post("/api/login")
def login(req: LoginRequest):
    # Simple password check
    if req.password == "admin123": # Default password
        return APIResponse.success(data={"token": "valid-session"}, message="Login successful")
    raise AuthenticationError("Invalid password")

# --- Telegram Endpoints ---
class TelegramConfig(BaseModel):
    bot_token: str
    chat_id: str
    enabled: bool

class TelegramSendRequest(BaseModel):
    news_ids: List[int]

@app.get("/api/telegram/config")
def get_telegram_config_api():
    """获取Telegram配置"""
    return APIResponse.success(data={
        "bot_token": db.get_config("telegram_bot_token") or "",
        "chat_id": db.get_config("telegram_chat_id") or "",
        "enabled": db.get_config("telegram_enabled") == "true"
    })

@app.post("/api/telegram/config")
def set_telegram_config_api(config: TelegramConfig):
    """设置Telegram配置"""
    db.set_config("telegram_bot_token", config.bot_token)
    db.set_config("telegram_chat_id", config.chat_id)
    db.set_config("telegram_enabled", "true" if config.enabled else "false")
    return APIResponse.success(message="配置已保存")

@app.post("/api/telegram/test")
async def test_telegram_push():
    """Test Telegram Push"""
    db = Database()
    token = db.get_config("telegram_bot_token")
    chat_id = db.get_config("telegram_chat_id")
    
    if not token or not chat_id:
        raise ValidationError("请先配置 Telegram Bot Token 和 Chat ID")
        
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "🔔 <b>AINews Filter</b>\n这是一条测试消息\nThis is a test message.",
                    "parse_mode": "HTML"
                },
                timeout=10.0
            )
            data = resp.json()
            if not data.get("ok"):
                raise Exception(data.get("description", "Unknown error"))
    except Exception as e:
        raise BusinessError(f"发送失败: {str(e)}")
            
    return APIResponse.success(message="测试消息发送成功")

@app.post("/api/telegram/send_news")
async def send_news_to_telegram(request: TelegramSendRequest):
    """发送选中的新闻到Telegram"""
    db = Database()
    
    # 1. 获取Telegram配置
    token = db.get_config("telegram_bot_token")
    chat_id = db.get_config("telegram_chat_id")
    
    if not token or not chat_id:
        raise ValidationError("请先在API配置中设置Telegram Bot Token和Chat ID")
    
    if not request.news_ids:
        raise ValidationError("请选择要发送的新闻")
    
    # 2. 查询新闻详情（从curated_news表）
    conn = db.connect()
    cursor = conn.cursor()
    
    placeholders = ','.join(['?' for _ in request.news_ids])
    query = f'''
        SELECT id, title, source_url, content
        FROM curated_news
        WHERE id IN ({placeholders})
    '''
    cursor.execute(query, request.news_ids)
    news_items = cursor.fetchall()
    conn.close()
    
    if not news_items:
        raise ValidationError("未找到要发送的新闻")
    
    # 3. 构建HTML格式消息
    import html as html_lib
    messages = []
    for news in news_items:
        news_id, title, url, content = news
        # HTML转义标题和内容中的特殊字符
        escaped_title = html_lib.escape(title)
        escaped_content = html_lib.escape(content or '')
        
        # 构建HTML消息：标题（超链接）+ 空行 + 内容
        # 格式：<b>标题链接</b>\n\n内容
        message = f'<b><a href="{url}">{escaped_title}</a></b>\n\n{escaped_content}'
        messages.append(message)
    
    # 用两个换行分隔每条新闻
    full_message = '\n\n'.join(messages)
    
    # 4. 检查消息长度（Telegram限制4096字符）
    # 如果超长，逐个截断新闻内容
    if len(full_message) > 4096:
        messages = []
        for news in news_items:
            news_id, title, url, content = news
            escaped_title = html_lib.escape(title)
            escaped_content = html_lib.escape(content or '')
            
            # 构建基础消息（标题部分）
            base_message = f'<b><a href="{url}">{escaped_title}</a></b>\n\n'
            
            # 如果当前已有消息，预留分隔符长度
            current_length = len('\n\n'.join(messages))
            if messages:
                current_length += 2  # \n\n 分隔符
            
            # 计算当前新闻可用的空间
            available_space = 4096 - current_length - len(base_message)
            
            if available_space > 100:  # 至少保留100字符用于内容
                truncated_content = escaped_content[:available_space] + '...' if len(escaped_content) > available_space else escaped_content
                message = base_message + truncated_content
            else:
                # 空间不足，只发送标题
                message = base_message.rstrip('\n\n')
            
            messages.append(message)
            
            # 检查总长度，如果已经接近限制就停止
            if len('\n\n'.join(messages)) > 4000:  # 留一些余量
                break
        
        full_message = '\n\n'.join(messages)
    
    # 5. 发送到Telegram
    from services.telegram_bot import TelegramBot
    bot = TelegramBot(token, chat_id)
    success = await bot.send_message(full_message, parse_mode='HTML')
    
    if not success:
        raise Exception("发送到Telegram失败，请检查Bot配置和网络连接")
    
    return APIResponse.success(
        message=f"成功发送 {len(news_items)} 条新闻到Telegram",
        data={"sent_count": len(news_items)}
    )



# --- Analyst API (External Access) ---
class ApiKeyCreate(BaseModel):
    key_name: str
    notes: Optional[str] = None

def verify_analyst_api_key(api_key: str) -> bool:
    """验证分析师API密钥（支持多密钥）"""
    db = Database()
    conn = db.connect()
    cursor = conn.cursor()
    
    # 查询api_keys表
    cursor.execute(
        'SELECT id, last_used_at FROM api_keys WHERE api_key = ? AND enabled = 1',
        (api_key,)
    )
    result = cursor.fetchone()
    
    # 如果找到，更新最后使用时间
    if result:
        from datetime import datetime
        cursor.execute(
            'UPDATE api_keys SET last_used_at = ? WHERE id = ?',
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), result[0])
        )
        conn.commit()
    
    conn.close()
    return result is not None

@app.post("/api/analyst/keys")
async def create_api_key(request: ApiKeyCreate):
    """创建新的API密钥"""
    db = Database()
    
    # 生成随机密钥
    import secrets
    api_key = f"analyst_{secrets.token_urlsafe(24)}"
    
    # 插入数据库
    conn = db.connect()
    cursor = conn.cursor()
    
    try:
        from datetime import datetime
        cursor.execute(
            'INSERT INTO api_keys (key_name, api_key, notes, created_at) VALUES (?, ?, ?, ?)',
            (request.key_name, api_key, request.notes, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        key_id = cursor.lastrowid
        conn.close()
        
        return APIResponse.success(
            message=f"已为 '{request.key_name}' 创建密钥",
            data={
                "id": key_id,
                "key_name": request.key_name,
                "api_key": api_key,
                "notes": request.notes
            }
        )
    except Exception as e:
        conn.close()
        raise BusinessError(f"创建密钥失败: {str(e)}")

@app.get("/api/analyst/keys")
async def get_api_keys():
    """获取所有API密钥列表"""
    db = Database()
    conn = db.connect()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, key_name, api_key, created_at, enabled, last_used_at, notes
        FROM api_keys
        ORDER BY created_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    keys = []
    for row in rows:
        keys.append({
            "id": row[0],
            "key_name": row[1],
            "api_key": row[2],
            "created_at": row[3],
            "enabled": bool(row[4]),
            "last_used_at": row[5],
            "notes": row[6]
        })
    
    return APIResponse.success(data=keys)

@app.delete("/api/analyst/keys/{key_id}")
async def delete_api_key(key_id: int):
    """删除API密钥"""
    db = Database()
    conn = db.connect()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM api_keys WHERE id = ?', (key_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    if affected > 0:
        return APIResponse.success(message="密钥已删除")
    else:
        raise ValidationError("密钥不存在")

@app.get("/api/analyst/news")
async def get_analyst_news(
    api_key: str = Query(..., description="API密钥"),
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    min_score: int = Query(6, ge=1, le=10, description="最低AI评分"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制")
):
    """
    获取AI筛选的新闻数据（供外部分析师使用）
    
    该API允许授权用户获取经过AI筛选的高质量新闻数据。
    
    - **api_key**: API密钥（在系统配置中设置）
    - **hours**: 时间范围，1-168小时（默认24小时）
    - **min_score**: 最低AI评分，1-10分（默认6分）
    - **limit**: 返回数量，1-100条（默认50条）
    
    **响应示例**:
    ```json
    {
      "success": true,
      "data": {
        "news": [...],
        "metadata": {
          "count": 10,
          "time_range_hours": 24,
          "min_score": 6
        }
      }
    }
    ```
    """
    # 1. 验证API密钥
    if not verify_analyst_api_key(api_key):
        raise HTTPException(
            status_code=401,
            detail="无效的API密钥。请检查api_key参数或联系管理员获取有效密钥。"
        )
    
    # 2. 计算时间范围
    from datetime import datetime, timedelta
    db = Database()
    time_threshold = datetime.now() - timedelta(hours=hours)
    
    # 3. 查询符合条件的新闻
    conn = db.connect()
    cursor = conn.cursor()
    
    query = '''
        SELECT 
            id, title, content, source_url, source_site, 
            published_at, ai_status, ai_summary
        FROM curated_news
        WHERE published_at >= ?
          AND ai_status = 'approved'
        ORDER BY published_at DESC
        LIMIT ?
    '''
    
    cursor.execute(query, (
        time_threshold.strftime('%Y-%m-%d %H:%M:%S'),
        limit
    ))
    
    rows = cursor.fetchall()
    conn.close()
    
    # 4. 格式化响应数据
    news_list = []
    for row in rows:
        news_item = {
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "source_url": row[3],
            "source_site": row[4],
            "published_at": row[5],
            "ai_status": row[6],
            "ai_summary": row[7]
        }
        news_list.append(news_item)
    
    # 5. 返回结果
    return APIResponse.success(
        message=f"成功获取 {len(news_list)} 条新闻",
        data={
            "news": news_list,
            "metadata": {
                "count": len(news_list),
                "time_range_hours": hours,
                "query_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    )


# --- DeepSeek Endpoints ---
class DeepSeekConfig(BaseModel):
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"

@app.get("/api/deepseek/config")
def get_deepseek_config_api():
    """获取DeepSeek配置"""
    return APIResponse.success(data={
        "api_key": db.get_config("llm_api_key") or "",
        "base_url": db.get_config("llm_base_url") or "https://api.deepseek.com",
        "model": db.get_config("llm_model") or "deepseek-chat"
    })

@app.post("/api/deepseek/config")
def set_deepseek_config_api(config: DeepSeekConfig):
    """设置DeepSeek配置"""
    db.set_config("llm_api_key", config.api_key)
    db.set_config("llm_base_url", config.base_url)
    db.set_config("llm_model", config.model)
    return APIResponse.success(message="配置已保存")

@app.post("/api/deepseek/test")
async def test_deepseek_connection_api():
    """Test DeepSeek/LLM Connection"""
    db = Database()
    api_key = db.get_config("llm_api_key")
    base_url = db.get_config("llm_base_url") or "https://api.deepseek.com"
    model = db.get_config("llm_model") or "deepseek-chat"
    
    if not api_key:
        raise ValidationError("请先配置 API Key")
        
    try:
        service = DeepSeekService(api_key, base_url, model)
        result = await service.test_connection()
        if not result["ok"]:
            raise BusinessError(f"连接失败: {result.get('error')}")
        return APIResponse.success(data=result)
    except APIException:
        raise
    except Exception as e:
        raise DatabaseError(str(e))

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

