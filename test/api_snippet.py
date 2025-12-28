# 添加到backend/main.py的Pydantic Models部分

class CheckSimilarityRequest(BaseModel):
    news_id_1: int
    news_id_2: int

# 添加到backend/main.py的API Endpoints部分（在deduplicate附近）

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
        
        # 计算相似度
        deduplicator = LocalDeduplicator()
        similarity = deduplicator.calculate_similarity(news_1['title'], news_2['title'])
        
        threshold = 0.50
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
