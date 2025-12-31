"""深度调试 BlockBeats 页面结构"""
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
            
            print("="*70)
            print("1. 查找热榜容器")
            print("="*70)
            
            # 方法1: 精确选择器
            hot_container = soup.select_one('.article-hot')
            if hot_container:
                items1 = hot_container.select('.article-hot-item')
                print(f"方法1 (.article-hot > .article-hot-item): {len(items1)} 篇")
            
            # 方法2: 直接查找所有
            items2 = soup.select('.article-hot-item')
            print(f"方法2 (直接 .article-hot-item): {len(items2)} 篇")
            
            # 方法3: 查找包含 "hot" 的div
            items3 = soup.find_all('div', class_=lambda x: x and 'hot-item' in x)
            print(f"方法3 (class包含hot-item): {len(items3)} 篇")
            
            print("\n" + "="*70)
            print("2. 详细信息")
            print("="*70)
            
            for i, item in enumerate(items2, 1):
                title_elem = item.select_one('a')  # 任何链接
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    print(f"\n{i}. {title[:60]}...")
                else:
                    print(f"\n{i}. (无标题)")
            
            # 检查是否有 JavaScript 渲染的标记
            print("\n" + "="*70)
            print("3. 检查动态加载")
            print("="*70)
            
            # 查找 Nuxt/Vue 相关标记
            nuxt_data = soup.find_all(attrs={"data-v"})
            print(f"找到 {len(nuxt_data)} 个 data-v 元素（Vue组件）")
            
            # 查找 __NUXT__ 数据
            script_tags = soup.find_all('script')
            has_nuxt = any('__NUXT__' in str(tag) for tag in script_tags)
            print(f"页面使用 Nuxt.js: {has_nuxt}")


if __name__ == '__main__':
    asyncio.run(test())
