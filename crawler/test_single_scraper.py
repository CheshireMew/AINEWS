"""单个爬虫测试脚本 - 通用版本"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

async def test_scraper(scraper_class, scraper_name):
    """测试单个爬虫并输出结果"""
    print(f"\n{'='*80}")
    print(f"测试爬虫: {scraper_name}")
    print(f"{'='*80}\n")
    
    scraper = scraper_class()
    
    try:
        # 初始化浏览器
        await scraper.init_browser()
        print(f"✅ 浏览器初始化成功")
        
        # 抓取新闻
        print(f"🕷️ 开始抓取...")
        news_list = await scraper.scrape_important_news()
        
        print(f"\n📊 抓取结果:")
        print(f"   总数: {len(news_list)} 条")
        
        if len(news_list) == 0:
            print(f"❌ 未抓到任何新闻！需要调试识别逻辑")
            return
        
        # 统计内容情况
        has_content = sum(1 for item in news_list if item.get('content', '').strip())
        no_content = len(news_list) - has_content
        
        print(f"   有内容: {has_content} 条")
        print(f"   无内容: {no_content} 条")
        
        # 显示前3条详情
        print(f"\n📰 前3条新闻详情:\n")
        for i, item in enumerate(news_list[:3], 1):
            content = item.get('content', '').strip()
            content_len = len(content)
            content_preview = content[:100] + '...' if len(content) > 100 else content
            
            print(f"[{i}] {item['title']}")
            print(f"    URL: {item['url']}")
            print(f"    时间: {item['published_at']}")
            print(f"    标记: {item.get('site_importance_flag', 'N/A')}")
            print(f"    内容长度: {content_len} 字")
            if content:
                print(f"    内容预览: {content_preview}")
            else:
                print(f"    ⚠️ 内容为空")
            print()
        
        # 保存结果
        output_file = f"{scraper_name}_test_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(news_list, f, ensure_ascii=False, indent=2, default=str)
        print(f"💾 结果已保存到: {output_file}")
        
        # 评估
        print(f"\n✅ 评估:")
        if len(news_list) >= 5:
            print(f"   ✅ 数量充足 ({len(news_list)}条)")
        else:
            print(f"   ⚠️ 数量较少 ({len(news_list)}条)")
        
        if has_content >= len(news_list) * 0.8:
            print(f"   ✅ 内容抓取成功率高 ({has_content}/{len(news_list)})")
        elif has_content > 0:
            print(f"   ⚠️ 部分内容缺失 ({has_content}/{len(news_list)})")
        else:
            print(f"   ❌ 所有内容都为空，需要修复内容选择器")
        
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.close()
        print(f"\n✅ 浏览器已关闭")


if __name__ == '__main__':
    # 从命令行参数获取要测试的爬虫名称
    if len(sys.argv) < 2:
        print("用法: python test_single_scraper.py <scraper_name>")
        print("可选值: techflow, blockbeats, foresight, marsbit, odaily, chaincatcher, panews")
        sys.exit(1)
    
    scraper_name = sys.argv[1].lower()
    
    # 导入对应的爬虫
    scraper_map = {
        'techflow': ('scrapers.techflow', 'TechFlowScraper'),
        'blockbeats': ('scrapers.blockbeats', 'BlockBeatsScraper'),
        'foresight': ('scrapers.foresight', 'ForesightScraper'),
        'marsbit': ('scrapers.marsbit', 'MarsBitScraper'),
        'odaily': ('scrapers.odaily', 'OdailyScraper'),
        'chaincatcher': ('scrapers.chaincatcher', 'ChainCatcherScraper'),
        'panews': ('scrapers.panews', 'PANewsScraper'),
    }
    
    if scraper_name not in scraper_map:
        print(f"❌ 未知的爬虫: {scraper_name}")
        print("可选值:", ', '.join(scraper_map.keys()))
        sys.exit(1)
    
    module_name, class_name = scraper_map[scraper_name]
    
    # 动态导入
    import importlib
    module = importlib.import_module(module_name)
    scraper_class = getattr(module, class_name)
    
    # 运行测试
    asyncio.run(test_scraper(scraper_class, scraper_name))
