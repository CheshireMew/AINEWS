from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
import asyncio
from pathlib import Path
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

SCRAPER_STATUS: Dict[str, Dict] = {} # { "techflow": { "status": "running", "startTime": "...", "lastResult": "..." } }

async def run_scraper_task(name: str, max_items: int):
    """Refactored scraper runner for background task"""
    logger.info(f"Starting background scrape task for {name}")
    import datetime
    
    SCRAPER_STATUS[name] = {
        "status": "running", 
        "start_time": datetime.datetime.now().isoformat(),
        "items_scraped": 0
    }
    
    try:
        scraper_cls = SCRAPER_MAP.get(name)
        if not scraper_cls:
            SCRAPER_STATUS[name]["status"] = "error"
            SCRAPER_STATUS[name]["error"] = "Scraper not found"
            return
            
        scraper = scraper_cls() 
        scraper.max_items = max_items
        
        # Run
        news_list = await scraper.run()
        count_scraped = len(news_list)
        logger.info(f"Scraped {count_scraped} items from {name}")
        
        # Save to DB
        db_conn = Database() # New connection for this task
        count_saved = 0
        for news in news_list:
            if 'source_site' not in news:
                news['source_site'] = scraper.site_name
            if db_conn.insert_news(news):
                count_saved += 1
        logger.info(f"Saved {count_saved} items to DB for {name}")
        
        SCRAPER_STATUS[name] = {
            "status": "idle",
            "last_run": datetime.datetime.now().isoformat(),
            "last_result": f"Scraped {count_scraped}, Saved {count_saved}",
            "last_error": None
        }
        
    except Exception as e:
        logger.error(f"Error running scraper {name}: {e}")
        SCRAPER_STATUS[name] = {
            "status": "error",
            "last_run": datetime.datetime.now().isoformat(),
            "last_result": "Failed",
            "last_error": str(e)
        }

@app.get("/api/spiders/status")
def get_spider_status():
    """Get status of all spiders"""
    return SCRAPER_STATUS

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
def get_news(page: int = 1, limit: int = 50, source: Optional[str] = None):
    """Get news list with pagination"""
    conn = db.connect()
    cursor = conn.cursor()
    offset = (page - 1) * limit
    
    query = "SELECT * FROM news"
    params = []
    
    if source:
        query += " WHERE source_site = ?"
        params.append(source)
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Get total count
    count_query = "SELECT count(*) FROM news"
    count_params = []
    if source:
        count_query += " WHERE source_site = ?"
        count_params.append(source)
        
    cursor.execute(count_query, count_params)
    total = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "data": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "limit": limit
    }

class LoginRequest(BaseModel):
    password: str

@app.post("/api/login")
def login(req: LoginRequest):
    # Simple password check
    if req.password == "admin123": # Default password
        return {"token": "valid-session", "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid password")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
