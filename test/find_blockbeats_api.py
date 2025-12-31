"""尝试查找 BlockBeats 的API接口"""
import sys
sys.path.insert(0, 'crawler')

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import re


async def test():
    url = 'https://www.theblockbeats.info/article'
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
    
    # 查找 __NUXT__ 数据
    print("="*70)
    print("查找 Nuxt 数据中的API模式")
    print("="*70)
    
    # 提取 __NUXT__ 中的数据
    match = re.search(r'window\.__NUXT__\s*=\s*({.+?});', html, re.DOTALL)
    if match:
        try:
            # 尝试解析（可能需要清理）
            nuxt_data = match.group(1)
            print(f"找到 __NUXT__ 数据 ({len(nuxt_data)} 字符)")
            
            # 查找可能的API端点
            api_patterns = [
                r'"/api/[^"]+',
                r'"/news/\d+',
                r'"https://[^"]+api[^"]+',
            ]
            
            for pattern in api_patterns:
                matches = re.findall(pattern, nuxt_data)
                if matches:
                    print(f"\n模式 {pattern}:")
                    for m in set(matches[:5]):  # 去重并限制显示
                        print(f"  {m}")
        except Exception as e:
            print(f"解析失败: {e}")
    else:
        print("未找到 __NUXT__ 数据")
    
    # 尝试常见的API路径
    print("\n" + "="*70)
    print("尝试可能的API端点")
    print("="*70)
    
    possible_apis = [
        'https://www.theblockbeats.info/api/articles',
        'https://www.theblockbeats.info/api/article/list',
        'https://www.theblockbeats.info/api/news/hot',
    ]
    
    async with aiohttp.ClientSession() as session:
        for api_url in possible_apis:
            try:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        print(f"\n✅ {api_url}")
                        data = await response.text()
                        print(f"   响应: {data[:200]}...")
                    else:
                        print(f"❌ {api_url} - HTTP {response.status}")
            except Exception as e:
                print(f"❌ {api_url} - {type(e).__name__}")


if __name__ == '__main__':
    asyncio.run(test())
