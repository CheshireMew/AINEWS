"""检查黄金新闻的时间和时间窗口逻辑"""
import sys
sys.path.insert(0, '.')
import sqlite3
from datetime import datetime

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

print("="*100)
print("检查时间窗口逻辑")
print("="*100)

# 1. 检查黄金新闻的发布时间
print("\n1. 黄金新闻（ID=10）的时间:")
c.execute("SELECT id, title, published_at, scraped_at, updated_at FROM news WHERE id = 10")
row = c.fetchone()
if row:
    print(f"  ID: {row[0]}")
    print(f"  标题: {row[1]}")
    print(f"  发布时间: {row[2]}")
    print(f"  抓取时间: {row[3]}")
    print(f"  更新时间: {row[4]}")
    
    # 计算距离现在多久
    try:
        pub_time = datetime.fromisoformat(row[2].replace('Z', '+00:00'))
        now = datetime.now().astimezone()
        hours_ago = (now - pub_time.replace(tzinfo=None)).total_seconds() / 3600
        print(f"  距现在: {hours_ago:.1f} 小时")
    except:
        print(f"  距现在: 无法计算")
else:
    print("  ⚠️ 黄金新闻不存在！")

# 2. 检查被误判的新闻时间
print("\n2. 被误判的新闻（ID 1166等）的时间:")
problem_ids = [1166, 1167, 1164, 1162]
for news_id in problem_ids:
    c.execute("SELECT id, title, published_at FROM news WHERE id = ?", (news_id,))
    row = c.fetchone()
    if row:
        print(f"\n  ID {row[0]}: {row[1][:60]}")
        print(f"    发布时间: {row[2]}")
        
        # 计算时间差
        try:
            news_time = datetime.fromisoformat(row[2].replace('Z', '+00:00'))
            gold_pub = datetime.fromisoformat(row[2].replace('Z', '+00:00'))
            # 这里需要修正，应该用黄金新闻的时间
            print(f"    距现在: {(datetime.now().astimezone() - news_time.replace(tzinfo=None)).total_seconds() / 3600:.1f} 小时")
        except:
            pass

# 3. 检查时间窗口是否被正确应用
print("\n" + "="*100)
print("3. 分析时间窗口逻辑")
print("="*100)

print("\n如果用户选择'最近2小时'，那么:")
print("  - 应该只比较最近2小时内发布的新闻")
print("  - 如果黄金新闻是很久以前的，不应该进入比较范围")

print("\n⚠️ 关键问题:")
print("  用户选择了'全部时间'(time_window_hours=0)")
print("  这导致所有pending新闻都进入比较，包括很久以前的")

conn.close()

print("\n" + "="*100)
print("结论")
print("="*100)
print("如果黄金新闻确实是很久以前的，那么问题可能在于:")
print("  1. 用户选择'全部时间'导致旧新闻也参与比较")
print("  2. 或者黄金新闻的published_at时间被错误更新")
print("="*100)
