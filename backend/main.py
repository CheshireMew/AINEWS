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

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse  # Added for export
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from logging import getLogger
import jwt
import secrets
from datetime import datetime, timedelta

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
from scrapers.foresight_article import (
    ForesightExclusiveScraper,
    ForesightExpressScraper,
    ForesightDepthScraper,

)
from scrapers.blockbeats_article import BlockBeatsArticleScraper
from scrapers.chaincatcher_article import ChainCatcherArticleScraper
from scrapers.marsbit_article import MarsBitArticleScraper
from scrapers.odaily_article import OdailyArticleScraper
from scrapers.panews_article import PANewsArticleScraper
from scrapers.techflow_article import TechflowArticleScraper
from scrapers.wublock_article import WuBlockArticleScraper
from scrapers.chainfeeds_article import ChainfeedsArticleScraper

# 快讯类爬虫 (News)
NEWS_SCRAPERS = {
    "techflow": TechFlowScraper,
    "odaily": OdailyScraper,
    "blockbeats": BlockBeatsScraper,
    "foresight": ForesightScraper,
    "chaincatcher": ChainCatcherScraper,
    "panews": PANewsScraper,
    "marsbit": MarsBitScraper,
}

# 深度文章类爬虫 (Articles)
ARTICLE_SCRAPERS = {
    # 拆分后的 Foresight 专栏爬虫
    "foresight_exclusive": ForesightExclusiveScraper,
    "foresight_express": ForesightExpressScraper,
    "foresight_depth": ForesightDepthScraper,

    
    "blockbeats_article": BlockBeatsArticleScraper,
    "chaincatcher_article": ChainCatcherArticleScraper,
    "marsbit_article": MarsBitArticleScraper,
    "odaily_article": OdailyArticleScraper,
    "panews_article": PANewsArticleScraper,
    "techflow_article": TechflowArticleScraper,
    "wublock_article": WuBlockArticleScraper,
    "chainfeeds_article": ChainfeedsArticleScraper,
}

# 所有爬虫的统一映射
SCRAPER_MAP = {**NEWS_SCRAPERS, **ARTICLE_SCRAPERS}

# 爬虫类型映射（用于前端过滤）
SCRAPER_TYPES = {
    **{name: 'news' for name in NEWS_SCRAPERS.keys()},
    **{name: 'article' for name in ARTICLE_SCRAPERS.keys()}
}

app = FastAPI(title="AINews Admin API")

# CORS 配置
import os
from dotenv import load_dotenv

# 加载环境变量
env_file = '.env.production' if os.getenv('ENV') == 'production' else '.env.development'
load_dotenv(env_file)

# 获取允许的来源
allowed_origins_str = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173')
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# --- JWT Auth Configuration ---
# 生产环境应该从环境变量读取 SECRET_KEY
# 也可以自动生成一个持久化的密钥，或者为了简单每次重启生成一个（会导致重启后Token失效）
# 这里我们尝试从数据库配置读取，如果没有则生成一个
SECRET_KEY = db.get_config("jwt_secret_key")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(32)
    db.set_config("jwt_secret_key", SECRET_KEY)

# 初始化默认凭证
if not db.get_config("admin_username"):
    db.set_config("admin_username", "admin")
if not db.get_config("admin_password"):
    db.set_config("admin_password", "admin123")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天过期

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception

    # Verify username and password against database config
    db_username = db.get_config("admin_username") or "admin" # Fallback if missing
    db_password = db.get_config("admin_password") or "admin123"
    
    # Note: Passwords should be hashed in production using bcrypt/argon2 (e.g. methods from passlib)
    # Since we are using system_config (plaintext), we compare directly.
    # Future improvement: Store hashed password.
    
    if token_data.username != db_username:
        raise credentials_exception
        
    return User(username=token_data.username)

class CredentialsUpdate(BaseModel):
    current_password: str
    new_username: Optional[str] = None
    new_password: Optional[str] = None

@app.post("/api/system/credentials")
async def update_credentials(req: CredentialsUpdate, user: User = Depends(get_current_user)):
    """Update admin credentials"""
    db_password = db.get_config("admin_password") or "admin123"
    
    if req.current_password != db_password:
        raise HTTPException(
            status_code=400,
            detail="当前密码错误"
        )
    
    if req.new_username:
        if len(req.new_username) < 3:
            raise HTTPException(status_code=400, detail="用户名长度至少为3个字符")
        db.set_config("admin_username", req.new_username)
        
    if req.new_password:
        if len(req.new_password) < 6:
            raise HTTPException(status_code=400, detail="密码长度至少为6个字符")
        db.set_config("admin_password", req.new_password)
        
    return APIResponse.success(message="账户信息已更新")


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

# ==================== 公开 API（无需认证）====================

@app.get("/api/public/news")
async def get_public_news(limit: int = 20, offset: int = 0):
    """获取精选快讯列表（最近3天）- 查询已推送数据"""
    try:
        conn = db.connect()
        cursor = conn.cursor()
        
        # 直接查询已推送的快讯（已经过去重检查）
        # ai_explanation 格式：7分-深度思考#AI与人文
        cursor.execute("""
            SELECT id, title, source_url, published_at, source_site, ai_category, ai_explanation
            FROM curated_news
            WHERE type = 'news'
              AND push_status = 'sent'
              AND published_at >= datetime('now', '-3 days')
            ORDER BY published_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        
        # 获取总数
        cursor.execute("""
            SELECT COUNT(*) FROM curated_news
            WHERE type = 'news'
              AND push_status = 'sent'
              AND published_at >= datetime('now', '-3 days')
        """)
        total = cursor.fetchone()[0]
        
        conn.close()
        
        news_list = []
        for row in rows:
            # 从 ai_explanation 中提取标签
            # 格式：7分-深度思考#AI与人文
            ai_tag = None
            
            if row[6]:  # ai_explanation
                try:
                    explanation = row[6]
                    # 如果包含 #，提取 # 后面的标签
                    if '#' in explanation:
                        ai_tag = explanation.split('#')[1].strip()
                    # 如果没有 #，尝试提取"分-"后面的第一个词
                    elif '分-' in explanation:
                        after_dash = explanation.split('分-', 1)[1]
                        ai_tag = after_dash.split()[0] if after_dash.strip() else None
                except Exception as e:
                    logger.debug(f"Failed to extract tag from explanation: {row[6]}, error: {e}")
            
            # 如果没有提取到，使用 ai_category
            if not ai_tag and row[5]:  # ai_category
                ai_tag = row[5]
            
            # 如果都没有，使用来源
            if not ai_tag:
                ai_tag = row[4]  # source_site
            
            news_list.append({
                'id': row[0],
                'title': row[1],
                'source_url': row[2],
                'published_at': row[3],
                'source_site': row[4],
                'ai_tag': ai_tag
            })
        
        return APIResponse.success(data={
            'items': news_list,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        logger.error(f"获取公开快讯失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/public/articles")
async def get_public_articles(limit: int = 20, offset: int = 0):
    """获取精选文章列表（最近7天）- 查询已推送数据"""
    try:
        conn = db.connect()
        cursor = conn.cursor()
        
        # 直接查询已推送的文章（已经过去重检查）
        # ai_explanation 格式：7分-深度思考#AI与人文
        cursor.execute("""
            SELECT id, title, source_url, published_at, source_site, ai_category, ai_explanation
            FROM curated_news
            WHERE type = 'article'
              AND push_status = 'sent'
              AND published_at >= datetime('now', '-7 days')
            ORDER BY published_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        
        # 获取总数
        cursor.execute("""
            SELECT COUNT(*) FROM curated_news
            WHERE type = 'article'
              AND push_status = 'sent'
              AND published_at >= datetime('now', '-7 days')
        """)
        total = cursor.fetchone()[0]
        
        conn.close()
        
        articles_list = []
        for row in rows:
            # 从 ai_explanation 中提取标签
            # 格式：7分-深度思考#AI与人文
            ai_tag = None
            
            if row[6]:  # ai_explanation
                try:
                    explanation = row[6]
                    # 如果包含 #，提取 # 后面的标签
                    if '#' in explanation:
                        ai_tag = explanation.split('#')[1].strip()
                    # 如果没有 #，尝试提取"分-"后面的第一个词
                    elif '分-' in explanation:
                        after_dash = explanation.split('分-', 1)[1]
                        ai_tag = after_dash.split()[0] if after_dash.strip() else None
                except Exception as e:
                    logger.debug(f"Failed to extract tag from explanation: {row[6]}, error: {e}")
            
            # 如果没有提取到，使用 ai_category
            if not ai_tag and row[5]:  # ai_category
                ai_tag = row[5]
            
            # 如果都没有，使用来源
            if not ai_tag:
                ai_tag = row[4]  # source_site
            
            articles_list.append({
                'id': row[0],
                'title': row[1],
                'source_url': row[2],
                'published_at': row[3],
                'source_site': row[4],
                'ai_tag': ai_tag
            })
        
        return APIResponse.success(data={
            'items': articles_list,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        logger.error(f"获取公开文章失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/public/dailies")
async def get_public_dailies(type: Optional[str] = None, limit: int = 20, offset: int = 0):
    """获取每日日报列表"""
    try:
        conn = db.connect()
        cursor = conn.cursor()
        
        # 构建查询
        # 构建查询
        rows = []
        total = 0
        
        if type:
            cursor.execute("""
                SELECT id, date, type, title, content, news_count, created_at
                FROM daily_reports
                WHERE type = ?
                ORDER BY date DESC
                LIMIT ? OFFSET ?
            """, (type, limit, offset))
            rows = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) FROM daily_reports WHERE type = ?", (type,))
            total = cursor.fetchone()[0]
        else:
            cursor.execute("""
                SELECT id, date, type, title, content, news_count, created_at
                FROM daily_reports
                ORDER BY date DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            rows = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) FROM daily_reports")
            total = cursor.fetchone()[0]
        
        conn.close()
        
        dailies_list = [{
            'id': row[0],
            'date': row[1],
            'type': row[2],
            'title': row[3],
            'content': row[4],
            'news_count': row[5],
            'created_at': row[6]
        } for row in rows]
        
        return APIResponse.success(data={
            'items': dailies_list,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        logger.error(f"获取日报失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/public/search")
async def search_public_content(q: str, type: str = 'all', limit: int = 20, offset: int = 0):
    """搜索精选内容（快讯+文章）"""
    try:
        if not q or len(q.strip()) < 2:
            raise HTTPException(status_code=400, detail="搜索关键词至少需要2个字符")
        
        conn = db.connect()
        cursor = conn.cursor()
        
        search_term = f"%{q}%"
        
        # 构建查询条件
        if type == 'all':
            type_condition = "AND (type = 'news' OR type = 'article')"
            time_condition = """
                AND (
                    (type = 'news' AND published_at >= datetime('now', '-3 days'))
                    OR
                    (type = 'article' AND published_at >= datetime('now', '-7 days'))
                )
            """
        elif type == 'news':
            type_condition = "AND type = 'news'"
            time_condition = "AND published_at >= datetime('now', '-3 days')"
        elif type == 'article':
            type_condition = "AND type = 'article'"
            time_condition = "AND published_at >= datetime('now', '-7 days')"
        else:
            raise HTTPException(status_code=400, detail="无效的类型参数")
        
        # 执行搜索
        cursor.execute(f"""
            SELECT id, title, content, source_url, published_at, source_site, type
            FROM curated_news
            WHERE ai_status = 'approved'
              {type_condition}
              {time_condition}
              AND (title LIKE ? OR content LIKE ?)
            ORDER BY published_at DESC
            LIMIT ? OFFSET ?
        """, (search_term, search_term, limit, offset))
        
        rows = cursor.fetchall()
        
        # 获取总数
        cursor.execute(f"""
            SELECT COUNT(*) FROM curated_news
            WHERE ai_status = 'approved'
              {type_condition}
              {time_condition}
              AND (title LIKE ? OR content LIKE ?)
        """, (search_term, search_term))
        total = cursor.fetchone()[0]
        
        conn.close()
        
        results = [{
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'source_url': row[3],
            'published_at': row[4],
            'source_site': row[5],
            'type': row[6]
        } for row in rows]
        
        return APIResponse.success(data={
            'items': results,
            'total': total,
            'limit': limit,
            'offset': offset,
            'query': q
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ====================

class SystemTimezoneConfig(BaseModel):
    timezone: str

@app.get("/api/system/timezone")
async def get_system_timezone():
    """Get system timezone config"""
    tz = db.get_config("system_timezone") or "Asia/Shanghai"
    return {"timezone": tz}

@app.post("/api/system/timezone")
async def set_system_timezone(config: SystemTimezoneConfig, user: User = Depends(get_current_user)):
    """Set system timezone config"""
    import zoneinfo
    try:
        zoneinfo.ZoneInfo(config.timezone)
        db.set_config("system_timezone", config.timezone)
        return {"status": "success", "message": f"Timezone set to {config.timezone}"}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timezone")

class DailyPushTimeConfig(BaseModel):
    time: Optional[str] = None  # News daily push time "20:00"
    article_time: Optional[str] = None  # Article daily push time "21:00"

@app.get("/api/system/push_time")
async def get_push_time():
    """Get daily push time config for news and articles"""
    news_time = db.get_config("daily_push_time") or "20:00"
    article_time = db.get_config("daily_article_push_time") or "21:00"
    return {"time": news_time, "article_time": article_time}

@app.post("/api/system/push_time")
async def set_push_time(config: DailyPushTimeConfig, user: User = Depends(get_current_user)):
    """Set daily push time config for news and articles (HH:MM)"""
    try:
        # Validate and save news push time
        if config.time:
            datetime.strptime(config.time, "%H:%M")
            db.set_config("daily_push_time", config.time)
        
        # Validate and save article push time
        if config.article_time:
            datetime.strptime(config.article_time, "%H:%M")
            db.set_config("daily_article_push_time", config.article_time)
        
        return {"status": "success", "message": "Push time(s) updated successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

# Auto-Pipeline Configuration
class AutoPipelineConfig(BaseModel):
    # News config
    dedup_hours: Optional[int] = None
    filter_hours: Optional[int] = None
    ai_scoring_hours: Optional[int] = None
    push_hours: Optional[int] = None
    # Article config
    article_dedup_hours: Optional[int] = None
    article_filter_hours: Optional[int] = None
    article_ai_scoring_hours: Optional[int] = None
    article_push_hours: Optional[int] = None

@app.get("/api/config/auto_pipeline")
async def get_auto_pipeline_config():
    """Get auto-pipeline configuration for news and articles"""
    return {
        # News config
        "dedup_hours": int(db.get_config("auto_dedup_hours") or 2),
        "filter_hours": int(db.get_config("auto_filter_hours") or 24),
        "ai_scoring_hours": int(db.get_config("auto_ai_scoring_hours") or 12),
        "push_hours": int(db.get_config("auto_push_hours") or 12),
        # Article config
        "article_dedup_hours": int(db.get_config("auto_article_dedup_hours") or 7*24),  # 7天
        "article_filter_hours": int(db.get_config("auto_article_filter_hours") or 7*24),  # 7天
        "article_ai_scoring_hours": int(db.get_config("auto_article_ai_scoring_hours") or 7*24),  # 7天
        "article_push_hours": int(db.get_config("auto_article_push_hours") or 3*24),  # 3天
    }

@app.post("/api/config/auto_pipeline")
async def set_auto_pipeline_config(config: AutoPipelineConfig, user: User = Depends(get_current_user)):
    """Set auto-pipeline configuration for news and articles"""
    # Save news config
    if config.dedup_hours is not None:
        db.set_config("auto_dedup_hours", str(config.dedup_hours))
    if config.filter_hours is not None:
        db.set_config("auto_filter_hours", str(config.filter_hours))
    if config.ai_scoring_hours is not None:
        db.set_config("auto_ai_scoring_hours", str(config.ai_scoring_hours))
    if config.push_hours is not None:
        db.set_config("auto_push_hours", str(config.push_hours))
    
    # Save article config
    if config.article_dedup_hours is not None:
        db.set_config("auto_article_dedup_hours", str(config.article_dedup_hours))
    if config.article_filter_hours is not None:
        db.set_config("auto_article_filter_hours", str(config.article_filter_hours))
    if config.article_ai_scoring_hours is not None:
        db.set_config("auto_article_ai_scoring_hours", str(config.article_ai_scoring_hours))
    if config.article_push_hours is not None:
        db.set_config("auto_article_push_hours", str(config.article_push_hours))
    
    return {"status": "success", "message": "Auto-pipeline configuration updated"}




SCRAPER_STATUS: Dict[str, Dict] = {} 
RUNNING_TASKS: Dict[str, asyncio.Task] = {} # { "techflow": task_obj }

class RunScraperRequest(BaseModel):
    items: int = 10

class DeduplicateRequest(BaseModel):
    time_window_hours: int = 24
    action: str = 'mark'  # 'mark' or 'delete'
    threshold: float = 0.50 # 相似度阈值
    type: str = 'news'  # 'news' or 'article'

class CheckSimilarityRequest(BaseModel):
    news_id_1: int
    news_id_2: int

@app.post("/api/spiders/stop/{name}")
async def stop_scraper(name: str, user: User = Depends(get_current_user)):
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
    
    SCRAPER_STATUS[name] = {
        "status": "running", 
        "start_time": datetime.now().isoformat(),
        "items_scraped": 0,
        "logs": []
    }
    
    import sys
    def log_scraper(msg: str):
        full_msg = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
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
        recent_urls = db_conn.get_recent_news_urls(scraper.site_name, limit=200)
        
        if recent_urls:
            scraper.existing_urls = set(recent_urls)
            scraper.last_news_url = recent_urls[0] # For backward compatibility logs
            scraper.incremental_mode = True
            log_scraper(f"Incremental mode enabled. History size: {len(recent_urls)}. Latest: {recent_urls[0][:30]}...")
        else:
            # Fallback to single latest check if recent list empty (though list includes latest)
            latest_url = db_conn.get_latest_news_url(scraper.site_name)
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
                print(f"[DEBUG] Set source_site = '{news['source_site']}' (from scraper.site_name='{scraper.site_name}')")
            if db_conn.insert_news(news):
                count_saved += 1
                log_scraper(f"Saved: {news.get('title', 'Unknown')[:30]}...")
            else:
                log_scraper(f"Skipped (Duplicate URL): {news.get('title', 'Unknown')[:30]}...")

        log_scraper(f"Completed. Saved {count_saved} new items.")
        
        SCRAPER_STATUS[name].update({
            "status": "idle",
            "last_run": datetime.now().isoformat(),
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
    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')

# 加载配置并设置文章爬虫默认值
SCRAPER_CONFIG = load_config()

# 为文章爬虫设置不同的默认值（如果未配置）
for name in ARTICLE_SCRAPERS.keys():
    if name not in SCRAPER_CONFIG:
        SCRAPER_CONFIG[name] = {
            "limit": 20,          # 默认抓取20篇
            "interval": 240       # 默认4小时（240分钟）
        }
        save_config(SCRAPER_CONFIG)
        print(f"✅ 已为 {name} 设置默认配置: limit=20, interval=240min (4小时)")

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
        print(f"时间窗口: {req.time_window_hours} 小时, 类型: {req.type}")
        
        news_list = db.get_news_by_time_range(req.time_window_hours, type_filter=req.type)
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
        print(f"正在调用 LocalDeduplicator (本地去重算法) [阈值: {req.threshold}]...")
        
        # 保存用户设置的阈值到系统配置，供自动化流程使用
        db.set_config("dedup_threshold", str(req.threshold))
        
        # 注意：前端的time_window_hours只用于限定查询范围
        # 算法内部固定使用2小时窗口进行两两对比
        dedup = LocalDeduplicator(
            similarity_threshold=req.threshold, 
            time_window_hours=2  # 固定2小时窗口
        )
        
        # 记录开始前的内存状态或简单日志
        news_list = dedup.mark_duplicates(news_list)
        
        # 3. 统计和处理重复项
        duplicates = [n for n in news_list if n.get('is_local_duplicate', False)]
        print(f"发现重复项: {len(duplicates)} 条")
        
        duplicate_groups = {}
        
        for dup in duplicates:
            # 🔧 FIX: duplicate_of现在直接是新闻ID，不再是列表索引
            master_id = dup.get('duplicate_of')
            if master_id is None:
                continue
            
            # 获取主新闻信息用于显示（可选）
            master = next((n for n in news_list if n['id'] == master_id), None)
            if not master:
                print(f"⚠️ 警告: 找不到主新闻 ID={master_id}")
                continue
                
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

@app.post("/api/news/check_similarity")
async def check_news_similarity(req: CheckSimilarityRequest):
    """检测两条新闻的相似度"""
    try:
        import sys
        sys.path.insert(0, 'crawler')
        from filters.local_deduplicator import LocalDeduplicator
        
        db = Database()
        conn = db.connect()
        cursor = conn.cursor()
        
        # 获取两条新闻
        cursor.execute("SELECT id, title FROM news WHERE id IN (?, ?)", (req.news_id_1, req.news_id_2))
        rows = cursor.fetchall()
        
        if len(rows) < 2:
            conn.close()
            raise HTTPException(status_code=404, detail="找不到指定的新闻")
        
        news_1 = {'id': rows[0][0], 'title': rows[0][1]}
        news_2 = {'id': rows[1][0], 'title': rows[1][1]}
        
        conn.close()
        
        # 计算相似度 (使用与手动去重相同的默认阈值)
        threshold = 0.50  # 与 DeduplicateRequest 的默认值保持一致
        deduplicator = LocalDeduplicator(similarity_threshold=threshold)
        
        # 提取特征
        features1 = deduplicator.extract_features(news_1['title'])
        features2 = deduplicator.extract_features(news_2['title'])
        
        # 计算相似度
        similarity = deduplicator.calculate_similarity(features1, features2)
        
        # 使用去重器的阈值，而不是硬编码
        threshold = deduplicator.similarity_threshold
        is_duplicate = similarity >= threshold
        
        return {
            "news_1": news_1,
            "news_2": news_2,
            "similarity": round(similarity, 4),
            "threshold": threshold,
            "is_duplicate": is_duplicate
        }
        
    except Exception as e:
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
            
            # Check for daily pushes (Non-blocking check)
            asyncio.create_task(auto_daily_best_push())
            asyncio.create_task(auto_daily_article_push())

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

            # 检查时间：只要当前时间晚于设定时间，且今天未推送过，就触发
            # Logic: Current Time >= Target Time
            current_minutes = now.hour * 60 + now.minute
            target_minutes = target_hour * 60 + target_minute
            
            is_time = current_minutes >= target_minutes
            
            if not is_time:
                return {
                    "status": "skipped",
                    "message": f"Not push time yet (Current: {now.strftime('%H:%M')}, Target: {target_time_str})"
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
            AND type = 'news'
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
            
            if score >= 5:
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
        seen_identifiers = set() # Check for dups by URL or Title

        for news in news_list:
            score = news.get('score', 0)
            title = news.get('title', "No Title")
            url = news.get('source_url', "")
            
            # Use URL as primary unique key, fallback to Title
            identifier = url if url else title
            if identifier in seen_identifiers:
                continue
            seen_identifiers.add(identifier)
            
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
            
            # 保存日报到 daily_reports 表
            try:
                # 构建完整的日报内容（HTML格式）
                report_content = base_header + "\n\n".join(formatted_items)
                report_content += '\n\n🤖 由 <a href="https://t.me/CheshireBTC">AINEWS</a> 自动生成'
                
                conn = db.connect()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO daily_reports 
                    (date, type, title, content, news_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (today_str, 'news', f'{today_str} 精选日报', 
                      report_content, len(news_list)))
                conn.commit()
                conn.close()
                logger.info(f"✅ [Daily Push] Saved report to database for {today_str}")
            except Exception as e:
                logger.error(f"❌ [Daily Push] Failed to save report: {e}")

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
    """手动触发日报推送 (Force Run for News)"""
    return await auto_daily_best_push(force=True)

@app.post("/api/telegram/daily_article_push")
async def trigger_daily_article_push():
    """手动触发文章日报推送 (Force Run for Articles)"""
    return await auto_daily_article_push(force=True)

async def auto_daily_article_push(force=False):
    """
    Daily scheduled task to push Articles to Telegram at 21:00 (Beijing Time)
    Query: Last 24h, Type='article'
    """
    try:
        from datetime import datetime, timedelta
        # 使用系统配置时区
        db = Database()
        now = db.get_system_time()
        
        # 1. check time window (Target Time - Target Time + 5min) unless forced
        if not force:
            target_time_str = db.get_config('daily_article_push_time') or "21:00"
            try:
                target_hour, target_minute = map(int, target_time_str.split(':'))
            except:
                target_hour, target_minute = 21, 0

            # 检查时间：只要当前时间晚于设定时间，且今天未推送过，就触发
            current_minutes = now.hour * 60 + now.minute
            target_minutes = target_hour * 60 + target_minute
            
            is_time = current_minutes >= target_minutes
            
            if not is_time:
                # logger.debug(f"Matches? {is_time} (Now: {now_time_str}, Target: {target_time_str})")
                return {
                    "status": "skipped",
                    "message": f"Not push time yet (Current: {now.strftime('%H:%M')}, Target: {target_time_str})"
                }

            # 2. Check if already pushed today
            today_str = now.strftime('%Y-%m-%d')
            last_push_date = db.get_config('last_daily_article_push_date')
            if last_push_date == today_str:
                return

            logger.info(f"⏰ [Daily Article Push] Starting daily article push for {today_str}")
        else:
            logger.info(f"⏰ [Daily Article Push] FORCED execution")
            db = Database()

        # 3. Fetch articles: Published in last 24h
        end_time = db.get_system_time()
        start_time = end_time - timedelta(hours=24)
        
        query = """
            SELECT title, source_url, ai_explanation
            FROM curated_news 
            WHERE published_at >= ? 
            AND type = 'article'
            AND ai_status IN ('approved', 'rejected') 
            ORDER BY published_at DESC
        """
        # User said "don't check score OR score > 0". 
        # We select all processed articles (approved or rejected). 
        # If we really want to filter 'garbage' (score<=0), we can filter in loop.
        
        rows = db.execute_query(query, (start_time.strftime('%Y-%m-%d %H:%M:%S'),))
        
        # Process and filter in Python
        news_list = []
        for row in rows:
            explanation = row['ai_explanation'] or ""
            score = 0
            # Extract score if possible, but for Article default we push unless it's really bad?
            # User said: "不看AI评分或者你设置分数大于0"
            # So let's check score > 0.
            if explanation and '分' in explanation:
                try:
                    score = int(explanation.split('分')[0])
                except:
                    score = 0
            
            if score > 0:
                news_list.append({
                    'title': row['title'],
                    'source_url': row['source_url'],
                    'score': score
                })
        
        if not news_list:
            logger.info("⏰ [Daily Article Push] No articles found (Score > 0) in last 24h")
            if not force:
                today_str = now.strftime('%Y-%m-%d')
                db.set_config('last_daily_article_push_date', today_str)
            return {
                "status": "skipped",
                "message": "No articles found"
            }

        logger.info(f"⏰ [Daily Article Push] Found {len(news_list)} articles")

        # 4. Format Message
        import html
        formatted_items = []
        for news in news_list:
            title = news.get('title', "No Title")
            url = news.get('source_url', "")
            safe_title = html.escape(title)
            # Format: 📰 <a href="...">Title</a>
            line = f"📰 <a href=\"{url}\">{safe_title}</a>"
            formatted_items.append(line)

        # Split into chunks
        MAX_LENGTH = 3500
        message_parts = []
        current_part = []
        current_length = 0
        
        base_header = f"📅 <b>{now.strftime('%Y-%m-%d')} 深度文章日报</b>\n\n"
        current_length = len(base_header)
        
        for item in formatted_items:
            item_len = len(item) + 2
            if current_length + item_len > MAX_LENGTH:
                message_parts.append(current_part)
                current_part = [item]
                current_length = item_len
            else:
                current_part.append(item)
                current_length += item_len
        
        if current_part:
            message_parts.append(current_part)
            
        # 5. Send
        from services.telegram_bot import TelegramBot
        token = db.get_config("telegram_bot_token")
        chat_id = db.get_config("telegram_chat_id")

        if not token or not chat_id:
            logger.error("❌ [Daily Article Push] Telegram config missing")
            return {"status": "error", "message": "Telegram config missing"}
            
        bot = TelegramBot(token, chat_id)
        
        total_parts = len(message_parts)
        for i, part_items in enumerate(message_parts, 1):
            if total_parts > 1:
                header = f"📅 <b>{now.strftime('%Y-%m-%d')} 深度文章日报 ({i}/{total_parts})</b>\n\n"
            else:
                header = base_header
                
            full_message = header + "\n\n".join(part_items)
            
            if i == total_parts:
                 full_message += '\n\n🤖 由 <a href="https://t.me/CheshireBTC">AINEWS</a> 自动生成'
            
            success = await bot.send_message(full_message, parse_mode='HTML')
            if not success:
                logger.error(f"❌ [Daily Article Push] Failed to send part {i}/{total_parts}")
            else:
                logger.info(f"✅ [Daily Article Push] Sent part {i}/{total_parts}")
            
            if i < total_parts:
                await asyncio.sleep(1)

        if not force:
            today_str = now.strftime('%Y-%m-%d')
            db.set_config('last_daily_article_push_date', today_str)
            
            # 保存文章日报到 daily_reports 表
            try:
                # 构建完整的日报内容（HTML格式）
                report_content = base_header + "\n\n".join(formatted_items)
                report_content += '\n\n🤖 由 <a href="https://t.me/CheshireBTC">AINEWS</a> 自动生成'
                
                conn = db.connect()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO daily_reports 
                    (date, type, title, content, news_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (today_str, 'article', f'{today_str} 深度文章日报', 
                      report_content, len(news_list)))
                conn.commit()
                conn.close()
                logger.info(f"✅ [Daily Article Push] Saved report to database for {today_str}")
            except Exception as e:
                logger.error(f"❌ [Daily Article Push] Failed to save report: {e}")

        return {
            "status": "success",
            "count": len(news_list),
            "parts": total_parts,
            "message": f"Pushed {len(news_list)} articles"
        }

    except Exception as e:
        logger.error(f"❌ [Daily Article Push] Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

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
            await auto_deduplication(type='news')
            await auto_deduplication(type='article')
            
            # 步骤2：自动关键词过滤
            await auto_keyword_filter()
            
            # 步骤3：自动AI打分
            await auto_ai_scoring()
            
            # 步骤4：逐条推送到Telegram
            await auto_telegram_push()

            # 步骤5 & 6 removed: Moved to scheduler_loop for precision
            
            logger.info("=" * 60)
            logger.info("🤖 [Auto-Pipeline] Cycle completed, waiting for next cycle...")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"🤖 [Auto-Pipeline] Error in pipeline: {e}", exc_info=True)
        
        # 15分钟后执行下一轮
        await asyncio.sleep(900)


async def wait_for_scrapers(timeout=300):
    """
    智能等待爬虫完成
    - 如果有爬虫正在运行，必须等待（防止数据竞争）
    - 如果所有爬虫都空闲，直接继续
    - 如果等待超过 timeout 秒，强制继续
    """
    import time
    logger.info("🕐 [Auto-Pipeline] Checking scraper status...")
    start_time = time.time()
    
    # 只需要等待那些正在运行的
    while True:
        # 检查是否超时
        elapsed = time.time() - start_time
        if elapsed > timeout:
            running_scrapers = [name for name, status in SCRAPER_STATUS.items() if status.get("status") == "running"]
            logger.warning(f"⚠️ [Auto-Pipeline] Timeout after {int(elapsed)}s, proceeding anyway. Still running: {', '.join(running_scrapers) if running_scrapers else 'none'}")
            return
        
        running_scrapers = []
        for name, status in SCRAPER_STATUS.items():
            if status.get("status") == "running":
                running_scrapers.append(name)
        
        if not running_scrapers:
            logger.info("✅ [Auto-Pipeline] No active scrapers, proceeding immediately")
            return
        logger.info(f"⏳ [Auto-Pipeline] Waiting for {len(running_scrapers)} active scrapers: {', '.join(running_scrapers)} (elapsed: {int(elapsed)}s/{timeout}s)")
        await asyncio.sleep(10)


async def auto_deduplication(type: str = 'news'):
    """自动去重：处理最近N小时的原始数据，根据类型使用不同时间窗口"""
    logger.info(f"🔄 [Auto-Dedup] Starting auto deduplication for {type}...")
    
    db = Database()
    conn = db.connect()
    cursor = conn.cursor()
    
    # 根据类型从配置读取去重时间窗口
    # 文章默认7天（168小时），快讯默认2小时
    if type == 'article':
        dedup_hours = int(db.get_config("article_dedup_hours") or 168)
        dedup_window_hours = int(db.get_config("article_dedup_window_hours") or 72)  # 3天
    else:
        dedup_hours = int(db.get_config("news_dedup_hours") or 2)
        dedup_window_hours = int(db.get_config("news_dedup_window_hours") or 2)  # 2小时
    
    logger.info(f"🔄 [Auto-Dedup] Using time range: {dedup_hours}h, window: {dedup_window_hours}h for {type}")
    
    # 获取最近N小时stage='raw'的新闻
    from datetime import datetime, timedelta
    cutoff_time = (datetime.now() - timedelta(hours=dedup_hours)).strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("""
        SELECT id, title, content, source_url, source_site, published_at, scraped_at, type
        FROM news 
        WHERE stage = 'raw' AND scraped_at >= ? AND type = ?
        ORDER BY scraped_at DESC
    """, (cutoff_time, type))
    
    rows = cursor.fetchall()
    if not rows:
        conn.close()
        logger.info(f"🔄 [Auto-Dedup] No raw {type} data to process")
        return
    
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
            'scraped_at': row['scraped_at'],
            'type': row['type'] if 'type' in row.keys() else 'news'  # 修复: sqlite3.Row 不支持 get
        })
    
    # 使用LocalDeduplicator标记重复
    from filters.local_deduplicator import LocalDeduplicator
    # 从系统配置读取阈值，默认0.50
    threshold = float(db.get_config("dedup_threshold") or 0.50)
    
    # 使用对应类型的时间窗口
    deduplicator = LocalDeduplicator(similarity_threshold=threshold, time_window_hours=dedup_window_hours)
    marked_news = deduplicator.mark_duplicates(news_list)
    
    # 将非重复的新闻移到deduplicated_news表
    dedup_count = 0
    for news in marked_news:
        if not news.get('is_local_duplicate', False):
            # 插入到deduplicated_news
            cursor.execute("""
                INSERT OR IGNORE INTO deduplicated_news 
                (title, content, source_site, source_url, published_at, scraped_at, deduplicated_at, stage, type, original_news_id)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'deduplicated', ?, ?)
            """, (
                news['title'],
                news['content'],
                news['source_site'],
                news['source_url'],
                news['published_at'],
                news['scraped_at'],
                news.get('type', 'news'),  # news 是字典，支持 get
                news['id']
            ))
            
            # 更新原新闻stage为deduplicated
            cursor.execute("UPDATE news SET stage = 'deduplicated' WHERE id = ?", (news['id'],))
            dedup_count += 1
        else:
            # 标记为重复
            # 关键修复：必须更新 duplicate_of 和 is_local_duplicate
            dup_of = news.get('duplicate_of')
            cursor.execute("""
                UPDATE news 
                SET stage = 'duplicate', 
                    duplicate_of = ?, 
                    is_local_duplicate = 1 
                WHERE id = ?
            """, (dup_of, news['id']))
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ [Auto-Dedup] Completed: {dedup_count} items deduplicated, {len(rows)-dedup_count} duplicates filtered")


async def auto_keyword_filter():
    """
    自动关键词过滤
    分别处理新闻和文章，使用各自的配置
    """
    logger.info("🔍 [Auto-Filter] Starting auto keyword filtering...")
    
    db = Database()
    
    # 读取新闻和文章的时间范围配置
    news_filter_hours = int(db.get_config("auto_filter_hours") or 24)
    article_filter_hours = int(db.get_config("auto_article_filter_hours") or 7*24)
    
    try:
        # 1. 过滤新闻
        logger.info(f"🔍 [Auto-Filter] Filtering news (time range: {news_filter_hours} hours)...")
        news_result = db.filter_news_by_blacklist(time_range_hours=news_filter_hours, type_filter='news')
        
        news_scanned = news_result.get('scanned', 0)
        news_filtered = news_result.get('filtered', 0)
        news_curated = news_result.get('curated', 0)
        
        if news_scanned > 0:
            logger.info(f"✅ [Auto-Filter] News: Scanned {news_scanned}, Passed {news_curated}, Filtered {news_filtered}")
        
        # 2. 过滤文章
        logger.info(f"🔍 [Auto-Filter] Filtering articles (time range: {article_filter_hours} hours)...")
        article_result = db.filter_news_by_blacklist(time_range_hours=article_filter_hours, type_filter='article')
        
        article_scanned = article_result.get('scanned', 0)
        article_filtered = article_result.get('filtered', 0)
        article_curated = article_result.get('curated', 0)
        
        if article_scanned > 0:
            logger.info(f"✅ [Auto-Filter] Articles: Scanned {article_scanned}, Passed {article_curated}, Filtered {article_filtered}")
        
        # 总结
        total_scanned = news_scanned + article_scanned
        total_passed = news_curated + article_curated
        total_filtered = news_filtered + article_filtered
        
        if total_scanned > 0:
            logger.info(f"✅ [Auto-Filter] Total: Scanned {total_scanned}, Passed {total_passed}, Filtered {total_filtered}")
        else:
            logger.info("🔍 [Auto-Filter] No deduplicated data to process")
            
    except Exception as e:
        logger.error(f"❌ [Auto-Filter] Error during filtering: {e}", exc_info=True)


async def auto_ai_scoring():
    """
    自动AI打分：分别处理新闻和文章
    新闻和文章使用各自的时间范围和提示词配置
    """
    logger.info("🤖 [Auto-AI] Starting auto AI scoring...")
    
    db = Database()
    
    # 获取通用配置
    api_key = db.get_config("llm_api_key")
    base_url = db.get_config("llm_base_url") or "https://api.deepseek.com"
    model = db.get_config("llm_model") or "deepseek-chat"
    
    if not api_key:
        logger.warning("⚠️ [Auto-AI] No API key configured, skipping AI scoring")
        return
    
    # 获取新闻和文章的独立配置
    news_ai_hours = int(db.get_config("auto_ai_scoring_hours") or 12)
    article_ai_hours = int(db.get_config("auto_article_ai_scoring_hours") or 7*24)
    
    news_prompt = db.get_config("ai_filter_prompt") or "评估新闻价值"
    article_prompt = db.get_config("article_ai_filter_prompt") or "评估文章质量和深度"
    
    total_processed = 0
    
    # 1. 处理新闻
    logger.info(f"🤖 [Auto-AI] Processing news (time range: {news_ai_hours} hours, prompt: {news_prompt[:20]}...)")
    news_processed = await _process_ai_scoring_by_type(
        db, api_key, base_url, model, 
        type_filter='news', 
        time_hours=news_ai_hours, 
        prompt=news_prompt
    )
    total_processed += news_processed
    
    # 2. 处理文章
    logger.info(f"🤖 [Auto-AI] Processing articles (time range: {article_ai_hours} hours, prompt: {article_prompt[:20]}...)")
    article_processed = await _process_ai_scoring_by_type(
        db, api_key, base_url, model, 
        type_filter='article', 
        time_hours=article_ai_hours, 
        prompt=article_prompt
    )
    total_processed += article_processed
    
    logger.info(f"✅ [Auto-AI] Completed: {total_processed} items scored (News: {news_processed}, Articles: {article_processed})")


async def _process_ai_scoring_by_type(db: Database, api_key: str, base_url: str, model: str, 
                                       type_filter: str, time_hours: int, prompt: str) -> int:
    """
    处理特定类型的AI打分
    返回处理的条数
    """
    from datetime import timedelta
    
    conn = db.connect()
    cursor = conn.cursor()
    
    current_time = db.get_system_time()
    time_ago = current_time - timedelta(hours=time_hours)
    time_ago_str = time_ago.strftime('%Y-%m-%d %H:%M:%S')
    
    # 查询未打分数据
    cursor.execute("""
        SELECT COUNT(*) FROM curated_news 
        WHERE (ai_status IS NULL OR ai_status = '' OR ai_status = 'pending')
        AND published_at >= ?
        AND type = ?
    """, (time_ago_str, type_filter))
    unscored_count = cursor.fetchone()[0]
    
    logger.info(f"🤖 [Auto-AI] Found {unscored_count} {type_filter} items to score")
    
    if unscored_count == 0:
        conn.close()
        return 0
    
    # 分批处理（每批10条）
    batch_size = 10
    processed = 0
    
    for offset in range(0, unscored_count, batch_size):
        cursor.execute("""
            SELECT id, title FROM curated_news 
            WHERE (ai_status IS NULL OR ai_status = '' OR ai_status = 'pending')
            AND published_at >= ?
            AND type = ?
            LIMIT ? OFFSET ?
        """, (time_ago_str, type_filter, batch_size, offset))
        
        rows = cursor.fetchall()
        if not rows:
            break
        
        news_items = [{"id": row["id"], "title": row["title"]} for row in rows]
        
        # 调用AI
        service = DeepSeekService(api_key, base_url, model)
        try:
            results = await service.filter_titles(news_items, prompt)
            
            # 更新数据库
            for item in results:
                try:
                    item_id = int(item['id'])
                    score = item.get('score', 0)
                    reason = item.get('reason', '')
                    tag = item.get('tag', '')
                    
                    status = 'approved' if score >= 5 else 'rejected'
                    # 组合显示格式：分数-理由 #标签 (与前端 AIFilterTab.jsx 解析逻辑一致)
                    if tag:
                        summary = f"{score}分-{reason} #{tag}"
                    elif reason:
                        summary = f"{score}分-{reason}"
                    else:
                        summary = f"{score}分"
                    
                    cursor.execute("""
                        UPDATE curated_news 
                        SET ai_status = ?, ai_explanation = ?
                        WHERE id = ?
                    """, (status, summary, item_id))
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"⚠️ [Auto-AI] Error updating item {item}: {e}")
            
            conn.commit()
            logger.info(f"🤖 [Auto-AI] Batch processed: {len(results)} {type_filter} items")
            
        except Exception as e:
            logger.error(f"⚠️ [Auto-AI] Error in batch: {e}")
        
        # 批次间延迟
        await asyncio.sleep(2)
    
    conn.close()
    return processed


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
    
    # 获取待推送新闻和文章，使用各自的时间范围
    conn = db.connect()
    cursor = conn.cursor()
    
    # 从配置读取新闻和文章的时间范围
    news_push_hours = int(db.get_config("auto_push_hours") or 12)
    article_push_hours = int(db.get_config("auto_article_push_hours") or 72)
    
    # 计算时间（北京时间）
    from datetime import timedelta
    current_time = db.get_system_time()
    
    news_time_ago = current_time - timedelta(hours=news_push_hours)
    news_time_ago_str = news_time_ago.strftime('%Y-%m-%d %H:%M:%S')
    
    article_time_ago = current_time - timedelta(hours=article_push_hours)
    article_time_ago_str = article_time_ago.strftime('%Y-%m-%d %H:%M:%S')
    
    logger.info(f"📤 [Auto-Push] News time range: {news_push_hours} hours (after {news_time_ago_str})")
    logger.info(f"📤 [Auto-Push] Articles time range: {article_push_hours} hours (after {article_time_ago_str})")
    
    # 1. 查询新闻 (≥5分, news_push_hours内)
    cursor.execute("""
        SELECT id, title, source_url, content, ai_explanation, type
        FROM curated_news
        WHERE (push_status IS NULL OR push_status = 'pending')
        AND published_at >= ?
        AND type = 'news'
        AND ai_status = 'approved'
        ORDER BY published_at DESC
    """, (news_time_ago_str,))
    news_items = cursor.fetchall()
    
    # 2. 查询文章 (>0分, article_push_hours内)
    cursor.execute("""
        SELECT id, title, source_url, content, ai_explanation, type
        FROM curated_news
        WHERE (push_status IS NULL OR push_status = 'pending')
        AND published_at >= ?
        AND type = 'article'
        AND ai_status IN ('approved', 'rejected')
        AND ai_explanation IS NOT NULL
        ORDER BY published_at DESC
    """, (article_time_ago_str,))
    article_items = cursor.fetchall()
    
    # 合并所有待推送内容
    all_news = list(news_items) + list(article_items)
    
    # 手动筛选分数
    # News: ≥5 分
    # Article: >0 分
    to_push = []
    for news in all_news:
        ai_summary = news[4] or ""
        type = news[5] or 'news'
        
        # 尝试从summary中提取分数（格式：8分-xxx）
        try:
            score_str = ai_summary.split('分')[0].strip()
            score = int(score_str)
            
            if type == 'news':
                if score >= 5:
                    to_push.append(news)
            elif type == 'article':
                if score > 0:
                    to_push.append(news)
        except:
            pass
    
    logger.info(f"📤 [Auto-Push] Found {len(to_push)} items to push (News: {len([n for n in to_push if (n[5] or 'news') == 'news'])}, Articles: {len([n for n in to_push if n[5] == 'article'])})")
    
    if len(to_push) == 0:
        conn.close()
        logger.info("📤 [Auto-Push] No items to push")
        return
    
    # 获取最近已推送的30条新闻用于去重
    cursor.execute("""
        SELECT title 
        FROM curated_news 
        WHERE push_status = 'sent' 
        ORDER BY pushed_at DESC 
        LIMIT 30
    """)
    recent_pushed = cursor.fetchall()
    
    # 逐条推送
    from services.telegram_bot import TelegramBot
    import html as html_lib
    import random
    import sys
    sys.path.insert(0, 'crawler')
    from filters.local_deduplicator import LocalDeduplicator
    
    # 从系统配置读取阈值，默认0.50
    threshold = float(db.get_config("dedup_threshold") or 0.50)
    
    # 创建两个deduplicator，分别用于文章和快讯
    # 使用独立的去重时间窗口配置
    article_dedup_window = int(db.get_config("article_dedup_window_hours") or 72)  # 3天
    news_dedup_window = int(db.get_config("news_dedup_window_hours") or 2)  # 2小时
    
    deduplicator_article = LocalDeduplicator(similarity_threshold=threshold, time_window_hours=article_dedup_window)
    deduplicator_news = LocalDeduplicator(similarity_threshold=threshold, time_window_hours=news_dedup_window)
    
    TELEGRAM_FOOTER = """
注册交易所 <a href="https://binance.com/join?ref=SRXT5KUM">币安</a> <a href="https://okx.com/join/A999998">欧易</a> <a href="https://0xcheshire.gitbook.io/web3/">新手教程</a>
Web3钱包 <a href="https://web3.binance.com/referral?ref=RP3AEJ2M">币安</a> <a href="https://web3.okx.com/ul/joindex?ref=1234567">OKX</a> <a href="https://link.metamask.io/rewards?referral=36P4HH">小狐狸（刷分）</a>"""
    # 获取最近已推送的记录（用于查重）
    # 分别获取新闻和文章的最近记录
    limit_news = int(db.get_config("dedup_check_count_news") or 30)
    limit_article = int(db.get_config("dedup_check_count_article") or 100)
    
    recent_pushed_news = []
    recent_pushed_articles = []
    
    try:
        # 获取最近的新闻
        cursor.execute("""
            SELECT title FROM curated_news 
            WHERE push_status = 'sent' AND (type = 'news' OR type IS NULL)
            ORDER BY pushed_at DESC LIMIT ?
        """, (limit_news,))
        recent_pushed_news = cursor.fetchall()

        # 获取最近的文章
        cursor.execute("""
            SELECT title FROM curated_news 
            WHERE push_status = 'sent' AND type = 'article'
            ORDER BY pushed_at DESC LIMIT ?
        """, (limit_article,))
        recent_pushed_articles = cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching recent push: {e}")
        recent_pushed_news = []
        recent_pushed_articles = []
    
    # 合并查重列表，但在循环中我们可以根据类型选择对比哪个列表
    # 为简单起见，且LocalDeduplicator是通用的，我们可以构建两个Deduplicator或者在循环中决定
    # 但Deduplicator本身没有状态，只是方法。
    # 我们可以把查重列表分开传给查重逻辑
    
    news_to_send = []
    
    bot = TelegramBot(token, chat_id)
    
    # 收集所有通过查重的新闻
    news_to_send = []
    
    for news in to_push:
        news_id, title, url, content, ai_summary, type = news
        type = type or 'news'
        
        # 根据类型选择对应的deduplicator和查重列表
        if type == 'article':
            deduplicator = deduplicator_article
            check_against = recent_pushed_articles
            check_limit_log = limit_article
        else:
            deduplicator = deduplicator_news
            check_against = recent_pushed_news
            check_limit_log = limit_news
            
        # 🛡️ 查重检查
        is_duplicate = False
        for pushed in check_against:
            pushed_title = pushed[0]
            title_features = deduplicator.extract_features(title)
            pushed_features = deduplicator.extract_features(pushed_title)
            if deduplicator.calculate_similarity(title_features, pushed_features) >= deduplicator.similarity_threshold:
                logger.warning(f"🛡️ [Auto-Push] Prevented duplicate push: {title[:30]}... (Similar to pushed: {pushed_title[:30]}...)")
                is_duplicate = True
                
                # 标记为重复
                try:
                    cursor.execute("SELECT id FROM news WHERE title = ? LIMIT 1", (pushed_title,))
                    parent_row = cursor.fetchone()
                    if parent_row:
                        parent_id = parent_row[0]
                        cursor.execute("""
                            UPDATE news 
                            SET duplicate_of = ?, is_local_duplicate = 1, stage = 'deduplicated'
                            WHERE id = ?
                        """, (parent_id, news_id))
                        
                        # 关键修复：同时更新 curated_news 表，防止下次循环再次被选中
                        cursor.execute("""
                            UPDATE curated_news 
                            SET push_status = 'duplicate'
                            WHERE id = ?
                        """, (news_id,))
                        
                        conn.commit()
                        logger.info(f"   ↳ Marked news {news_id} as duplicate of {parent_id} in DB (and skipped push)")
                except Exception as e:
                    logger.error(f"   ↳ Failed to update DB status for duplicate: {e}")
                break
        
        if not is_duplicate:
            news_to_send.append((news_id, title, url, content, type))
    
    # 如果没有要推送的新闻，直接返回
    if len(news_to_send) == 0:
        conn.close()
        logger.info("✅ [Auto-Push] Completed: 0/0 items pushed")
        return
    
    # 分批构建和发送消息
    # Telegram 限制：4096 字符，我们留出安全余量使用 4000
    MAX_MESSAGE_LENGTH = 4000
    FOOTER_LENGTH = len(TELEGRAM_FOOTER)
    
    # 将新闻分组，每组不超过字符限制
    message_batches = []
    current_batch = []
    current_length = FOOTER_LENGTH  # 初始长度包含页脚
    
    for news_id, title, url, content, type in news_to_send:
        escaped_title = html_lib.escape(title)
        
        if type == 'article':
             news_line = f'📰 <b><a href="{url}">{escaped_title}</a></b>'
        else:
             # 快讯：⚡ Emoji，Title Only (No Content)
             news_line = f'⚡ <b><a href="{url}">{escaped_title}</a></b>'

        news_line_length = len(news_line) + 2  # +2 for '\n\n'
        
        # 检查添加这条新闻是否会超出限制
        if current_length + news_line_length > MAX_MESSAGE_LENGTH:
            # 当前批次已满，保存并开始新批次
            if current_batch:  # 确保当前批次不为空
                message_batches.append(current_batch)
            current_batch = [(news_id, title, url, content, type)]
            current_length = news_line_length + FOOTER_LENGTH
        else:
            current_batch.append((news_id, title, url, content, type))
            current_length += news_line_length
    
    # 添加最后一批
    if current_batch:
        message_batches.append(current_batch)
    
    # 逐批发送消息
    total_sent = 0
    for batch_index, batch in enumerate(message_batches, 1):
        # 构建当前批次的消息
        news_lines = []
        for _, title, url, content, type in batch:
            # HTML转义
            escaped_title = html_lib.escape(title)
            
            if type == 'article':
                 # 文章：📰 Emoji，Title Only
                 news_lines.append(f'📰 <b><a href="{url}">{escaped_title}</a></b>')
            else:
                 # 快讯：⚡ Emoji，Title Only (No Content)
                 # Reverting to original behavior as requested
                 news_lines.append(f'⚡ <b><a href="{url}">{escaped_title}</a></b>')

        message = '\n\n'.join(news_lines) + f'\n{TELEGRAM_FOOTER}'
        
        try:
            success = await bot.send_message(message, parse_mode='HTML')
            
            if success:
                # 批量更新当前批次新闻的状态
                batch_news_ids = [news[0] for news in batch]
                placeholders = ','.join('?' * len(batch_news_ids))
                cursor.execute(f"""
                    UPDATE curated_news 
                    SET push_status = 'sent', pushed_at = CURRENT_TIMESTAMP
                    WHERE id IN ({placeholders})
                """, batch_news_ids)
                conn.commit()
                
                total_sent += len(batch)
                logger.info(f"✅ [Auto-Push] Batch {batch_index}/{len(message_batches)}: Sent {len(batch)} items")
            else:
                logger.error(f"❌ [Auto-Push] Batch {batch_index}/{len(message_batches)}: Failed to send")
        except Exception as e:
            logger.error(f"❌ [Auto-Push] Batch {batch_index}/{len(message_batches)}: Error sending message: {e}")
    
    logger.info(f"✅ [Auto-Push] Completed: {total_sent}/{len(news_to_send)} items pushed in {len(message_batches)} batch(es)")
    conn.close()

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
async def run_spider(name: str, background_tasks: BackgroundTasks, req: RunScraperRequest, user: User = Depends(get_current_user)):
    if name not in SCRAPER_MAP:
        raise HTTPException(status_code=404, detail="Scraper not found")
    
    background_tasks.add_task(run_scraper_task, name, req.items)
    return {"status": "accepted", "message": f"Scraper {name} started in background"}

@app.get("/api/spiders")
def get_spiders():
    """List all available spiders with their types and display names"""
    spiders_with_types = []
    for name, scraper_cls in SCRAPER_MAP.items():
        # 实例化爬虫获取 site_name
        try:
            scraper = scraper_cls()
            display_name = scraper.site_name
        except:
            # 如果实例化失败，使用ID作为备用
            display_name = name
        
        spiders_with_types.append({
            "name": name,
            "display_name": display_name,
            "type": SCRAPER_TYPES.get(name, 'news')
        })
    
    return {
        "spiders": spiders_with_types
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
def get_stats(type: str = 'news'):
    """Get crawling stats by content type"""
    try:
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT source_site, count(*) as count FROM news WHERE type = ? GROUP BY source_site", 
            (type,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        stats = [{"source": row['source_site'], "count": row['count']} for row in rows]
        return APIResponse.success(data={"stats": stats}, message="统计查询成功")
    except Exception as e:
        raise DatabaseError(f"查询统计失败: {str(e)}")

@app.get("/api/news")
@app.get("/api/news")
def get_news(page: int = 1, limit: int = 50, source: Optional[str] = None, stage: Optional[str] = None, keyword: Optional[str] = None, type: Optional[str] = 'news'):
    """Get news list with pagination"""
    try:
        conn = db.connect()
        cursor = conn.cursor()
        offset = (page - 1) * limit
        print(f"DEBUG: get_news called with stage={stage}")
        
        # Modified query to include master news info for duplicates
        query = """
            SELECT n.*, m.title as master_title, m.id as master_id_ref
            FROM news n
            LEFT JOIN news m ON n.duplicate_of = m.id
            WHERE 1=1
        """
        params = []
        
        
        if source:
            # 将爬虫ID转换为对应的site_name用于查询
            # 前端传递的是爬虫ID（如'blockbeats_article'），需要转换为site_name（如'BlockBeats Article'）
            if source in SCRAPER_MAP:
                try:
                    scraper = SCRAPER_MAP[source]()
                    source_site = scraper.site_name
                except:
                    source_site = source  # 转换失败，使用原值
            else:
                source_site = source  # 不在映射中，使用原值
            
            query += " AND n.source_site = ?"
            params.append(source_site)
        
        if stage:
            query += " AND n.stage = ?"
            params.append(stage)
            
        # Filter by type (default to 'news')
        # Frontend explicitly passes 'news' or 'article' or other types
        if type:
            query += " AND n.type = ?"
            params.append(type)
        
        if keyword:
            query += " AND (n.title LIKE ? OR n.content LIKE ?)"
            term = f"%{keyword}%"
            params.append(term)
            params.append(term)
        
        query += " ORDER BY n.published_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Get total count
        count_query = "SELECT count(*) FROM news n WHERE 1=1"
        count_params = []
        if source:
            count_query += " AND n.source_site = ?"
            count_params.append(source)
        if stage:
            count_query += " AND n.stage = ?"
            count_params.append(stage)
        if type:
            count_query += " AND n.type = ?"
            count_params.append(type)
        if keyword:
            count_query += " AND (n.title LIKE ? OR n.content LIKE ?)"
            term = f"%{keyword}%"
            count_params.append(term)
            count_params.append(term)
            
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]
        
        conn.close()
        
        results = []
        for row in rows:
            item = dict(row)
            # Ensure master_title is present even if null
            if 'master_title' not in item:
                # This should not happen if query works
                pass 
            results.append(item)
        
        return APIResponse.paginated(
            data=results,
            total=total,
            page=page,
            limit=limit
        )
    except Exception as e:
        raise DatabaseError(f"查询新闻失败: {str(e)}")

@app.delete("/api/news/{news_id}")
def delete_news(news_id: int, user: User = Depends(get_current_user)):
    """Delete a news item"""
    success = db.delete_news(news_id)
    if success:
        return APIResponse.success(message="删除成功")
    raise NotFoundError("新闻不存在或删除失败")

@app.get("/api/deduplicated/news")
def get_deduplicated_news_api(page: int = 1, limit: int = 50, source: Optional[str] = None, keyword: Optional[str] = None, type: Optional[str] = 'news', stage: Optional[str] = None):
    """获取已去重的数据 (支持 stage 筛选: deduplicated, filtered, verified)"""
    result = db.get_deduplicated_news(page, limit, source, keyword, type_filter=type, stage=stage)
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
def delete_deduplicated_news(news_id: int, user: User = Depends(get_current_user)):
    """删除已去重数据"""
    success = db.delete_deduplicated_news(news_id)
    if success:
        return APIResponse.success(message="删除成功")
    raise NotFoundError("数据不存在或删除失败")

@app.post("/api/deduplicated/batch_restore_all")
async def batch_restore_all_deduplicated(type: str = 'news', user: User = Depends(get_current_user)):
    """批量还原所有去重数据到 raw 状态 (支持类型筛选)"""
    db_instance = Database()
    try:
        conn = db_instance.connect()
        cursor = conn.cursor()
        
        # 1. 还原仅处于 'deduplicated' 状态的新闻 (不影响 curated/filtered)
        cursor.execute("UPDATE news SET stage = 'raw' WHERE stage = 'deduplicated' AND type = ?", (type,))
        restored_count = cursor.rowcount

        # 2. 还原处于 'duplicate' 状态的新闻 (清空重复对照)
        cursor.execute("""
            UPDATE news 
            SET stage = 'raw', is_duplicate = 0, duplicate_of = NULL 
            WHERE (stage = 'duplicate' OR is_duplicate = 1) AND type = ?
        """, (type,))
        restored_duplicates = cursor.rowcount
        
        # 3. 清理 deduplicated_news 表 (完全清空，不保留任何数据)
        # 注意：deduplicated_news 表中也应该有 type 字段才行。如果不区分 type，清空会误删。
        # 如果 deduplicated_news 没有 type 字段，我们暂时只能全部清空，或者不做这一步。
        # 检查 deduplicated_news 表结构，如果有 type 则加条件。没有则全删会有副作用。
        # 假设 deduplicated_news 仅作为归档查看，清空影响不大。但为了严谨应该加条件。
        # 暂时先不加 type 条件删除 deduplicated_news，避免报错 (如果表没type字段)
        # 但这会导致查看"已去重"列表时，清空操作会清空所有类型的归档记录。
        # 考虑到用户需求是隔离操作，建议 deduplicated_news 也需要 type。
        # 这里先只还原 news 表的状态，deduplicated_news 表暂时全清空 (或者先check一下)
        
        # 更好的策略：根据 ids 来删。
        # 既然我们已经 update 了 news 表，那 deduplicated_news 表里对应的数据就失效了。
        # 但 deduplicated_news 是 news 的副本吗？ db.archive_to_deduplicated 是 INSERT INTO ... SELECT FROM news
        # 是的一份拷贝。
        # 如果不删 deduplicated_news，前端"已去重"列表还会显示。
        # 让我们尝试按 type 删除 (假设 deduplicated_news 也有 type，因为它是从 news 表复制过去的)
        try:
            cursor.execute("DELETE FROM deduplicated_news WHERE type = ?", (type,))
        except Exception:
            # 如果没有 type 字段，回退到清空 (虽然不完美，但能工作)
            # 或者不删？
            pass
            
        conn.commit()
        conn.close()
        
        return APIResponse.success(
            data={"restored_count": restored_count + restored_duplicates},
            message=f"批量还原成功！已重置 {restored_count} 条去重数据和 {restored_duplicates} 条重复数据 (保留了已过滤/精选数据)"
        )
    except Exception as e:
        logger.error(f"批量还原失败: {e}")
        raise DatabaseError(f"批量还原失败: {str(e)}")

@app.post("/api/filtered/batch_restore_all")
async def batch_restore_all_filtered(type: str = 'news', user: User = Depends(get_current_user)):
    """批量还原已过滤和已精选的数据，重新执行本地过滤 (支持类型)"""
    db_instance = Database()
    try:
        conn = db_instance.connect()
        cursor = conn.cursor()
        
        # 查询需要还原的数据数量（filtered + verified + curated）
        cursor.execute("SELECT COUNT(*) FROM deduplicated_news WHERE stage IN ('filtered', 'verified', 'curated') AND type = ?", (type,))
        restore_count = cursor.fetchone()[0]
        
        if restore_count > 0:
            # 将 filtered, verified 和 curated 都改回 deduplicated
            cursor.execute("""
                UPDATE deduplicated_news 
                SET stage = 'deduplicated', keyword_filter_reason = NULL
                WHERE stage IN ('filtered', 'verified', 'curated') AND type = ?
            """, (type,))
            
            # 清空 curated_news 表 (如果之前的 Verified 数据被自动加精了，这里也会清空)
            # cursor.execute("DELETE FROM curated_news") 
            # 暂时注释掉清空 curated_news，防止误删用户手动加精的数据。
            # 但用户意图是重置过滤，如果 verified 变回 deduplicated，
            # 那么 curated_news 里对应的记录若不删，可能会导致数据不一致（源头变了）。
            # 不过根据最新逻辑，verified 不自动进 curated_news。
            # 为了安全，我们只重置 deduplicated_news 里的状态。
            pass
            
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
def get_curated_news_api(page: int = 1, limit: int = 50, source: Optional[str] = None, keyword: Optional[str] = None, type: Optional[str] = 'news', ai_status: Optional[str] = None):
    """获取精选数据"""
    result = db.get_curated_news(page, limit, source, keyword, type_filter=type, ai_status=ai_status)
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
def delete_curated_news(news_id: int, user: User = Depends(get_current_user)):
    """删除精选数据"""
    success = db.delete_curated_news(news_id)
    if success:
        return APIResponse.success(message="删除成功")
    raise NotFoundError("数据不存在或删除失败")

class RestoreRequest(BaseModel):
    source_table: str = 'deduplicated_news'

@app.post("/api/news/restore/{news_id}")
def restore_news_api(news_id: int, req: RestoreRequest, user: User = Depends(get_current_user)):
    """还原被过滤的新闻"""
    success = db.restore_news(news_id, req.source_table)
    if success:
        return APIResponse.success(message="还原成功")
    raise BusinessError("还原失败")

# AI Filtering Endpoints

class AIFilterRequest(BaseModel):
    hours: int = 8
    filter_prompt: str
    type: str = 'news'

class AIConfig(BaseModel):
    prompt: Optional[str] = None
    hours: Optional[int] = 8

@app.get("/api/ai/config")
def get_ai_config(type: str = 'news'):
    """获取AI配置（按类型）"""
    config_key = f"ai_filter_prompt_{type}"
    prompt = db.get_config(config_key) or ""
    hours = db.get_config("ai_filter_hours")
    return APIResponse.success(
        data={"prompt": prompt, "hours": int(hours) if hours else 8, "type": type}
    )

@app.post("/api/ai/config")
def set_ai_config(config: AIConfig, type: str = 'news', user: User = Depends(get_current_user)):
    """设置AI配置（按类型）"""
    if config.prompt is not None:
        config_key = f"ai_filter_prompt_{type}"
        db.set_config(config_key, config.prompt)
    if config.hours is not None:
        db.set_config("ai_filter_hours", str(config.hours))
    return APIResponse.success(message="配置已保存")


@app.post("/api/curated/ai_filter")
async def ai_filter_curated(req: AIFilterRequest, user: User = Depends(get_current_user)):
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
    
    # 首先获取总数 - 只处理未筛选的数据(pending或NULL) AND type match
    type_filter = getattr(req, 'type', 'news') or 'news'
    cursor.execute(
        "SELECT COUNT(*) FROM curated_news WHERE published_at >= ? AND (ai_status IS NULL OR ai_status = '' OR ai_status = 'pending') AND type = ?",
        (cutoff_time, type_filter)
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
    
    # Add type filtering
    type_filter = getattr(req, 'type', 'news') or 'news'
    
    cursor.execute(
        "SELECT id, title FROM curated_news WHERE published_at >= ? AND (ai_status IS NULL OR ai_status = '' OR ai_status = 'pending') AND type = ? LIMIT ? OFFSET ?",
        (cutoff_time, type_filter, batch_size, offset)
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
                # 阈值判断：>=5分为approved，<5分为rejected
                if score >= 5:
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
async def batch_restore_rejected(type: str = 'news', user: User = Depends(get_current_user)):
    """批量还原所有被拒绝的数据 (支持类型)"""
    db = Database()
    try:
        conn = db.connect()
        cursor = conn.cursor()
        
        # 查询被拒绝的数据数量
        cursor.execute("SELECT COUNT(*) FROM curated_news WHERE ai_status = 'rejected' AND type = ?", (type,))
        rejected_count = cursor.fetchone()[0]
        
        if rejected_count > 0:
            # 将所有 rejected 状态改为 pending，并清空 ai_explanation
            cursor.execute("""
                UPDATE curated_news 
                SET ai_status = 'pending', ai_explanation = NULL 
                WHERE ai_status = 'rejected' AND type = ?
            """, (type,))
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
async def clear_all_ai_status(type: str = 'news', user: User = Depends(get_current_user)):
    """清空所有 AI 筛选状态 (支持类型)"""
    db = Database()
    try:
        conn = db.connect()
        cursor = conn.cursor()
        
        # 查询所有有 AI 状态的数据
        cursor.execute("SELECT COUNT(*) FROM curated_news WHERE ai_status IS NOT NULL AND ai_status != '' AND type = ?", (type,))
        total_count = cursor.fetchone()[0]
        
        if total_count > 0:
            # 清空所有 AI 相关字段
            cursor.execute("""
                UPDATE curated_news 
                SET ai_status = NULL, ai_explanation = NULL 
                WHERE ai_status IS NOT NULL AND ai_status != '' AND type = ?
            """, (type,))
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
async def get_export_news(hours: int = 24, min_score: int = 5, type: str = 'news'):
    """获取可导出的新闻列表（所有被AI评分的数据）"""
    db = Database()
    try:
        conn = db.connect()
        cursor = conn.cursor()
        
        # 查询所有被AI评分的数据（approved + rejected）
        if hours ==0:
            # "全部时间" - 不限制时间范围
            logger.info(f"查询时间范围: 全部时间 (无限制), type={type}")
            cursor.execute("""
                SELECT id, title, content, source_url, source_site, ai_status, ai_explanation, curated_at, published_at
                FROM curated_news 
                WHERE ai_status IN ('approved', 'rejected')
                AND ai_explanation IS NOT NULL
                AND type = ?
            """, (type,))
        else:
            # 计算时间范围 - 使用系统配置时间
            cutoff_time = db.get_system_time() - timedelta(hours=hours)
            cutoff_time_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"查询时间范围: >= {cutoff_time_str} (Published), type={type}")
            
            cursor.execute("""
                SELECT id, title, content, source_url, source_site, ai_status, ai_explanation, curated_at, published_at
                FROM curated_news 
                WHERE published_at >= ? 
                AND ai_status IN ('approved', 'rejected')
                AND ai_explanation IS NOT NULL
                AND type = ?
            """, (cutoff_time_str, type))
        
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
def get_filtered_curated(status: str, page: int = 1, limit: int = 50, source: Optional[str] = None, keyword: Optional[str] = None, type: Optional[str] = 'news'):
    """获取筛选后的精选数据 (approved 或 rejected)"""
    db = Database()
    if status not in ['approved', 'rejected']:
        raise ValidationError("status 必须是 'approved' 或 'rejected'")
    result = db.get_filtered_curated_news(status, page, limit, source, keyword, type_filter=type)
    return APIResponse.paginated(
        data=result['data'],
        total=result['total'],
        page=result['page'],
        limit=result['limit']
    )

@app.get("/api/filtered/dedup/news")
def get_filtered_dedup_news_api(page: int = 1, limit: int = 50, keyword: Optional[str] = None, type: Optional[str] = 'news'):
    result = db.get_filtered_dedup_news(page, limit, keyword, type_filter=type)
    return APIResponse.paginated(
        data=result['data'],
        total=result['total'],
        page=result['page'],
        limit=result['limit']
    )

# --- Blacklist APIs ---

@app.get("/api/blacklist")
def get_blacklist(type: str = 'news'):
    """获取指定类型的黑名单关键词"""
    return APIResponse.success(data={"keywords": db.get_blacklist_keywords(type)})

class AddBlacklistRequest(BaseModel):
    keyword: str
    match_type: str = 'contains'
    type: str = 'news'

@app.post("/api/blacklist")
def add_blacklist(req: AddBlacklistRequest, user: User = Depends(get_current_user)):
    """添加黑名单关键词"""
    success = db.add_blacklist_keyword(req.keyword, req.match_type, req.type)
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

# --- Auto-Pipeline Config APIs ---

class AutoPipelineConfigRequest(BaseModel):
    dedup_hours: int = Field(ge=1, le=72, description="去重时间范围（小时）")
    filter_hours: int = Field(ge=1, le=72, description="过滤时间范围（小时）")
    ai_scoring_hours: int = Field(ge=1, le=72, description="AI打分时间范围（小时）")
    push_hours: int = Field(ge=1, le=72, description="推送时间范围（小时)")  
    article_dedup_hours: int = Field(default=2, ge=1, le=72, description="文章去重时间范围")
    article_filter_hours: int = Field(default=24, ge=1, le=72, description="文章过滤时间范围")
    article_ai_scoring_hours: int = Field(default=12, ge=1, le=72, description="文章AI打分时间范围")
    article_push_hours: int = Field(default=12, ge=1, le=72, description="文章推送时间范围")

@app.get("/api/config/auto_pipeline")
async def get_auto_pipeline_config():
    """获取自动化流程配置（包括快讯和文章）"""
    return APIResponse.success(data={
        # News config
        "dedup_hours": int(db.get_config("auto_dedup_hours") or 2),
        "filter_hours": int(db.get_config("auto_filter_hours") or 24),
        "ai_scoring_hours": int(db.get_config("auto_ai_scoring_hours") or 10),
        "push_hours": int(db.get_config("auto_push_hours") or 12),
        # Article config
        "article_dedup_hours": int(db.get_config("article_auto_dedup_hours") or 2),
        "article_filter_hours": int(db.get_config("article_auto_filter_hours") or 24),
        "article_ai_scoring_hours": int(db.get_config("article_auto_ai_scoring_hours") or 10),
        "article_push_hours": int(db.get_config("article_auto_push_hours") or 12),
    })

@app.post("/api/config/auto_pipeline")
async def set_auto_pipeline_config(req: AutoPipelineConfigRequest, user: User = Depends(get_current_user)):
    """设置自动化流程配置（包括快讯和文章）"""
    # News config
    db.set_config("auto_dedup_hours", str(req.dedup_hours))
    db.set_config("auto_filter_hours", str(req.filter_hours))
    db.set_config("auto_ai_scoring_hours", str(req.ai_scoring_hours))
    db.set_config("auto_push_hours", str(req.push_hours))
    
    # Article config
    db.set_config("article_auto_dedup_hours", str(req.article_dedup_hours))
    db.set_config("article_auto_filter_hours", str(req.article_filter_hours))
    db.set_config("article_auto_ai_scoring_hours", str(req.article_ai_scoring_hours))
    db.set_config("article_auto_push_hours", str(req.article_push_hours))
    
    logger.info(f"Auto-pipeline config updated - News: dedup={req.dedup_hours}h, filter={req.filter_hours}h, AI={req.ai_scoring_hours}h, push={req.push_hours}h")
    logger.info(f"Auto-pipeline config updated - Article: dedup={req.article_dedup_hours}h, filter={req.article_filter_hours}h, AI={req.article_ai_scoring_hours}h, push={req.article_push_hours}h")
    return APIResponse.success(message="配置已保存")

class FilterRequest(BaseModel):
    time_range_hours: int = 24
    type: str = 'news'

@app.post("/api/news/filter")
def filter_news(req: FilterRequest, user: User = Depends(get_current_user)):
    """根据黑名单执行过滤"""
    result = db.filter_news_by_blacklist(req.time_range_hours, type_filter=req.type)
    return APIResponse.success(data={"stats": result})

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login", response_model=Token)
async def login_for_access_token(req: LoginRequest):
    # Check credentials against database
    db_username = db.get_config("admin_username") or "admin"
    db_password = db.get_config("admin_password") or "admin123"
    
    if req.username != db_username or req.password != db_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

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
def set_telegram_config_api(config: TelegramConfig, user: User = Depends(get_current_user)):
    """设置Telegram配置"""
    db.set_config("telegram_bot_token", config.bot_token)
    db.set_config("telegram_chat_id", config.chat_id)
    db.set_config("telegram_enabled", "true" if config.enabled else "false")
    return APIResponse.success(message="配置已保存")

@app.post("/api/telegram/test")
async def test_telegram_push(user: User = Depends(get_current_user)):
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
async def send_news_to_telegram(request: TelegramSendRequest, user: User = Depends(get_current_user)):
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
        SELECT id, title, source_url, content, type
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
        news_id, title, url, content, type = news
        type = type or 'news'  # Default to news if null

        # HTML转义标题和内容中的特殊字符
        escaped_title = html_lib.escape(title)
        
        if type == 'article':
            # 文章：📰 Emoji，只显示蓝字链接，无内容
            message = f'📰 <b><a href="{url}">{escaped_title}</a></b>'
        else:
            # 快讯：⚡ Emoji，显示标题+内容
            escaped_content = html_lib.escape(content or '')
            message = f'⚡ <b><a href="{url}">{escaped_title}</a></b>\n\n{escaped_content}'
            
        messages.append(message)
    
    # 用两个换行分隔每条新闻
    full_message = '\n\n'.join(messages)
    
    # 4. 检查消息长度（Telegram限制4096字符）
    # 如果超长，逐个截断新闻内容
    if len(full_message) > 4096:
        messages = []
        for news in news_items:
            news_id, title, url, content, type = news
            type = type or 'news'

            escaped_title = html_lib.escape(title)
            
            if type == 'article':
                 message = f'📰 <b><a href="{url}">{escaped_title}</a></b>\n\n'
                 # 文章没有内容需要截断，直接添加（注意预留分隔符）
                 # 但下面的逻辑是基于 message 构建的，所以先根据类型区分
                 
                 # 对于文章，没有 content 部分，所以 message 就是 base_message (rstrip)
                 messages.append(message.rstrip('\n\n'))
                 # 检查总长度
                 if len('\n\n'.join(messages)) > 4000:
                     break
                 continue

            # 快讯逻辑
            escaped_content = html_lib.escape(content or '')
            
            # 构建基础消息（标题部分）
            base_message = f'⚡ <b><a href="{url}">{escaped_title}</a></b>\n\n'
            
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
async def create_api_key(request: ApiKeyCreate, user: User = Depends(get_current_user)):
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
async def delete_api_key(key_id: int, user: User = Depends(get_current_user)):
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
def set_deepseek_config_api(config: DeepSeekConfig, user: User = Depends(get_current_user)):
    """设置DeepSeek配置"""
    db.set_config("llm_api_key", config.api_key)
    db.set_config("llm_base_url", config.base_url)
    db.set_config("llm_model", config.model)
    return APIResponse.success(message="配置已保存")

@app.post("/api/deepseek/test")
async def test_deepseek_connection_api(user: User = Depends(get_current_user)):
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

# ============ 时间窗口配置 API ============

@app.get("/api/config/time_windows")
def get_time_windows_config(user: User = Depends(get_current_user)):
    """获取文章和快讯的时间窗口配置"""
    return APIResponse.success(data={
        "article": {
            "dedup_hours": int(db.get_config("article_dedup_hours") or 168),  # 7天
            "dedup_window_hours": int(db.get_config("article_dedup_window_hours") or 72),  # 3天
            "filter_hours": int(db.get_config("article_filter_hours") or 168),  # 7天
            "ai_scoring_hours": int(db.get_config("article_ai_scoring_hours") or 168),  # 7天
            "push_hours": int(db.get_config("article_push_hours") or 72)  # 3天
        },
        "news": {
            "dedup_hours": int(db.get_config("news_dedup_hours") or 2),  # 2小时
            "dedup_window_hours": int(db.get_config("news_dedup_window_hours") or 2),  # 2小时
            "filter_hours": int(db.get_config("news_filter_hours") or 24)  # 24小时
        }
    })

class TimeWindowsConfig(BaseModel):
    article: Optional[dict] = None
    news: Optional[dict] = None

@app.post("/api/config/time_windows")
def set_time_windows_config(config: TimeWindowsConfig, user: User = Depends(get_current_user)):
    """保存文章和快讯的时间窗口配置"""
    # 保存文章配置
    if config.article:
        for key, value in config.article.items():
            db.set_config(f"article_{key}", value)
    
    # 保存快讯配置
    if config.news:
        for key, value in config.news.items():
            db.set_config(f"news_{key}", value)
    
    return APIResponse.success(message="时间窗口配置已保存")

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

