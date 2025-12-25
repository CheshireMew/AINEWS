from crawler.filters.local_deduplicator import LocalDeduplicator

def test_similarity():
    # 构造测试数据
    title1 = "Metaplanet董事会批准增持比特币计划"
    title2 = "Metaplanet 董事会批准增持比特币计划，拟在 2027 年底前持有 21 万枚 BTC"
    
    deduper = LocalDeduplicator()
    
    # 手动调用内部计算方法（为了测试方便）
    similarity = deduper._calculate_similarity(
        {"title": title1}, 
        {"title": title2}
    )
    
    print(f"Title 1: {title1}")
    print(f"Title 2: {title2}")
    print(f"Similarity Score: {similarity}")

if __name__ == "__main__":
    test_similarity()
