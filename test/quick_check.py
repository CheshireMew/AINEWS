import sys
sys.path.insert(0, '.')
from crawler.filters.local_deduplicator import LocalDeduplicator
import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

rows = cursor.execute('''
    SELECT id, title 
    FROM news 
    WHERE id IN (1147, 1138, 1120)
    ORDER BY id
''').fetchall()

print("检查相似度:")
print("="*80)

dedup = LocalDeduplicator()

for i, row1 in enumerate(rows):
    for row2 in rows[i+1:]:
        sim = dedup.calculate_similarity(row1[1], row2[1])
        print(f"\nID {row1[0]} vs ID {row2[0]}: {sim:.4f} ({sim*100:.2f}%)")
        print(f"  {'✅ 判重' if sim >= 0.50 else '❌ 不判重'}")
        if i == 0:
            print(f"  [{row1[0]}] {row1[1][:50]}...")
            print(f"  [{row2[0]}] {row2[1][:50]}...")

conn.close()

print("\n" + "="*80)
print("结论：这些新闻是旧数据的误判")
print("请重新运行去重以应用修复后的算法")
