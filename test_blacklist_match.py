import sqlite3
from datetime import datetime, timedelta
import re

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 获取黑名单
cursor.execute("SELECT keyword, match_type FROM keyword_blacklist")
keywords = cursor.fetchall()

if not keywords:
    print("❌ 黑名单为空，无法过滤")
    exit()

print(f"黑名单关键词数量: {len(keywords)}")
print("=" * 50)

# 获取精选数据（48小时内）
cutoff = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')
cursor.execute("SELECT id, title FROM curated_news WHERE curated_at >= ? LIMIT 10", (cutoff,))
curated_samples = cursor.fetchall()

print(f"\n随机取 10 条精选数据标题进行测试：\n")

matched_count = 0
for news_id, title in curated_samples:
    print(f"[ID:{news_id}] {title}")
    
    # 测试黑名单匹配
    text_to_check = title.lower()
    matched = False
    matched_kw = None
    
    for kw, match_type in keywords:
        if match_type == 'regex':
            try:
                if re.search(kw, text_to_check, re.IGNORECASE):
                    matched = True
                    matched_kw = f"regex:{kw}"
                    break
            except re.error:
                continue
        else:
            if kw.lower() in text_to_check:
                matched = True
                matched_kw = kw
                break
    
    if matched:
        print(f"  ✅ 命中黑名单: {matched_kw}")
        matched_count += 1
    else:
        print(f"  ❌ 未命中")

print(f"\n匹配结果: {matched_count}/{len(curated_samples)} 条命中黑名单")

# 统计所有精选数据中能匹配的数量
cursor.execute("SELECT id, title FROM curated_news WHERE curated_at >= ?", (cutoff,))
all_curated = cursor.fetchall()

total_matched = 0
for news_id, title in all_curated:
    text_to_check = title.lower()
    matched = False
    
    for kw, match_type in keywords:
        if match_type == 'regex':
            try:
                if re.search(kw, text_to_check, re.IGNORECASE):
                    matched = True
                    break
            except re.error:
                continue
        else:
            if kw.lower() in text_to_check:
                matched = True
                break
    
    if matched:
        total_matched += 1

print(f"\n📊 全量统计: {total_matched}/{len(all_curated)} 条精选数据命中黑名单")

conn.close()
