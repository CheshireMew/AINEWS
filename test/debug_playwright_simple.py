import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = 'https://www.theblockbeats.info/article'
        print(f"Going to {url}")
        
        try:
            await page.goto(url, timeout=30000)
            print(f"Title: {await page.title()}")
            content = await page.content()
            print(f"Content length: {len(content)}")
            
            # Check selectors
            hot = await page.query_selector('.article-hot-item')
            print(f"Found .article-hot-item: {hot is not None}")
            
            list_item = await page.query_selector('.article-item')
            print(f"Found .article-item: {list_item is not None}")
            
            if hot:
                print(f"Hot item text: {(await hot.text_content())[:50]}...")
            
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
