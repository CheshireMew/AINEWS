# 批量还原 API 端点

## 1. 批量还原去重数据 (将 stage='curated' 和 'filtered' 改回 'deduplicated')
@app.post("/api/deduplicated/batch_restore_all")
async def batch_restore_all_deduplicated():
    """批量还原所有已处理的去重数据 (curated + filtered → deduplicated)"""
    db = Database()
    try:
        conn = db.connect()
        cursor = conn.cursor()
        
        # 查询已处理的数据数量
        cursor.execute("SELECT COUNT(*) FROM deduplicated_news WHERE stage IN ('curated', 'filtered')")
        processed_count = cursor.fetchone()[0]
        
        if processed_count > 0:
            # 重置 stage 为 deduplicated
            cursor.execute("""
                UPDATE deduplicated_news 
                SET stage = 'deduplicated'
                WHERE stage IN ('curated', 'filtered')
            """)
            conn.commit()
        
        conn.close()
        
        return APIResponse.success(
            data={"restored_count": processed_count},
            message=f"成功还原 {processed_count} 条去重数据"
        )
    except Exception as e:
        logger.error(f"批量还原去重数据失败: {e}")
        raise DatabaseError(f"批量还原失败: {str(e)}")


## 2. 批量还原已过滤数据 (将 stage='filtered' 改回 'deduplicated')  
@app.post("/api/filtered/batch_restore_all")
async def batch_restore_all_filtered():
    """批量还原已过滤的数据 (filtered → deduplicated)"""
    db = Database()
    try:
        conn = db.connect()
        cursor = conn.cursor()
        
        # 查询已过滤的数据数量
        cursor.execute("SELECT COUNT(*) FROM deduplicated_news WHERE stage = 'filtered'")
        filtered_count = cursor.fetchone()[0]
        
        if filtered_count > 0:
            # 重置 stage 为 deduplicated
            cursor.execute("""
                UPDATE deduplicated_news 
                SET stage = 'deduplicated'
                WHERE stage = 'filtered'
            """)
            conn.commit()
        
        conn.close()
        
        return APIResponse.success(
            data={"restored_count": filtered_count},
            message=f"成功还原 {filtered_count} 条已过滤数据"
        )
    except Exception as e:
        logger.error(f"批量还原已过滤数据失败: {e}")
        raise DatabaseError(f"批量还原失败: {str(e)}")
