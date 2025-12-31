"""测试 BlockBeats 热榜 HTML 结构"""
import sys
sys.path.insert(0, 'crawler')

import asyncio
import aiohttp
from bs4 import BeautifulSoup


async def test():
    url = 'https://www.theblockbeats.info/article'
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找热榜容器
            hot_container = soup.select_one('.article-hot')
            if not hot_container:
                print("❌ 未找到热榜容器")
                return
            
            print(f"✅ 找到热榜容器")
            
            # 查找所有热榜文章
            hot_items = hot_container.select('.article-hot-item')
            print(f"\n找到 {len(hot_items)} 篇热榜文章:")
            
            for i, item in enumerate(hot_items, 1):
                # 提取标题
                title_elem = item.select_one('.article-hot-item-title')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get('href', '')
                    print(f"\n{i}. {title}")
                    print(f"   链接: {href}")
                else:
                    print(f"\n{i}. ❌ 未找到标题元素")
                    print(f"   HTML: {str(item)[:200]}...")


if __name__ == '__main__':
    asyncio.run(test())
