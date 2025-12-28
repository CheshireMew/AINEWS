import re

def extract_entities_fixed(title):
    # Pangu spacing: Insert space between CJK and Latin
    # Latin to CJK
    title = re.sub(r'([a-zA-Z0-9])([\u4e00-\u9fa5])', r'\1 \2', title)
    # CJK to Latin
    title = re.sub(r'([\u4e00-\u9fa5])([a-zA-Z0-9])', r'\1 \2', title)
    
    print(f"Normalized Title: {title}")
    
    entities = set()
    
    # 3. 首字母大写连续词（项目名）
    cap_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    matches = re.findall(cap_pattern, title)
    entities.update(matches)
    return entities

t1 = "Lighter创始人：不会公开反女巫算法"
print(f"Original: {t1}")
print(f"Entities: {extract_entities_fixed(t1)}")
