
import re

def normalize(s):
    # 去除空格和标点，统一小写
    return re.sub(r'[\s，。、：；！？\-—_,]+', '', s.lower())

def test_inclusion(title1, title2):
    n1 = normalize(title1)
    n2 = normalize(title2)
    
    print(f"N1: {n1}")
    print(f"N2: {n2}")
    
    is_subset = n1 in n2 or n2 in n1
    print(f"Is subset: {is_subset}")
    
    if is_subset:
        len1 = len(n1)
        len2 = len(n2)
        ratio = min(len1, len2) / max(len1, len2)
        print(f"Length ratio: {ratio}")
        
        if ratio > 0.3:
            print("Score: 0.95 (High Confidence)")
        else:
            print("Score: Low (Ratio too small)")
    else:
        print("Not a subset")

t1 = "Metaplanet董事会批准增持比特币计划"
t2 = "Metaplanet 董事会批准增持比特币计划，拟在 2027 年底前持有 21 万枚 BTC"

test_inclusion(t1, t2)
