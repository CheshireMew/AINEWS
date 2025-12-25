import sqlite3
from datetime import datetime, timedelta

# 连接数据库
conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 计算12小时前的时间
cutoff = (datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')

# 查询各平台新闻数量
cursor.execute('''
    SELECT source_site, COUNT(*) as count 
    FROM news 
    WHERE published_at >= ? 
    GROUP BY source_site 
    ORDER BY count DESC
''', (cutoff,))

results = cursor.fetchall()

print('\n过去12小时各平台新闻数量:')
print('=' * 50)
print(f'{"平台":<15} {"数量":<10} {"平均/小时":<12} {"建议频率"}')
print('=' * 50)

# 定义频率建议
def get_frequency_recommendation(hourly_rate):
    if hourly_rate >= 5:
        return "每10分钟"
    elif hourly_rate >= 3:
        return "每15分钟"
    elif hourly_rate >= 1.5:
        return "每30分钟"
    elif hourly_rate >= 0.5:
        return "每1小时"
    else:
        return "每2小时"

for site, count in results:
    hourly = count / 12
    freq = get_frequency_recommendation(hourly)
    print(f'{site:<15} {count:<10} {hourly:<12.1f} {freq}')

print('=' * 50)
print(f'\n总计: {sum(c for _, c in results)} 条新闻')

conn.close()
