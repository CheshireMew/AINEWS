import re

# 模拟包含多个连续换行的内容
test = "段落1\n\n\n\n段落2"

print("原始:", repr(test))
print("方案1 结果:", repr(re.sub(r'\n\s*\n+', '\n', test)))
print("方案2 结果:", repr(re.sub(r'\n+', '\n', test)))
