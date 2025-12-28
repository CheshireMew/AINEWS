import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

print("="*80)
print("调查ID 1070和1078")
print("="*80)

# 获取信息
rows = cursor.execute('''
    SELECT id, title, duplicate_of
    FROM news 
    WHERE id IN (1070, 1078)
    ORDER BY id
''').fetchall()

print("\n【新闻详情】")
for row in rows:
    print(f"\nID {row[0]}: {row[1][:70]}")
    print(f"  duplicate_of: {row[2]}")

# 查看1070的所有duplicates
dups = cursor.execute('''
    SELECT id, title
    FROM news 
    WHERE duplicate_of = 1070
    ORDER BY id
''').fetchall()

print(f"\n【ID 1070的duplicates】共{len(dups)}条:")
for dup in dups:
    print(f"  ID {dup[0]}: {dup[1][:60]}")

print("\n" + "="*80)
print("【结论】")
print("="*80)
print("ID 1078被标记为1070的duplicate")
print("但标题完全不同：")
print(f"  1070: Bitmine质押ETH")
print(f"  1078: Coinbase Prime流入ETH")
print(f"  相似度: 15.34% << 50%阈值")
print("\n这是一个BUG！需要检查:")
print("1. Master合并是否有逻辑错误")
print("2. 是否有其他中间新闻导致误合并")

conn.close()
