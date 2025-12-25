"""主程序入口"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 添加模块路径
sys.path.append(str(Path(__file__).parent))

from database.db import Database
from filters.keyword_filter import KeywordFilter
from ai.tagger import AITagger
from ai.deduplicator import AIDuplicateDetector
from scrapers.techflow import TechFlowScraper
from scrapers.odaily import OdailyScraper
from scrapers.blockbeats import BlockBeatsScraper
from scrapers.foresight import ForesightScraper
from scrapers.chaincatcher import ChainCatcherScraper
from scrapers.panews import PANewsScraper
from scrapers.marsbit import MarsBitScraper
from scrapers.marsbit import MarsBitScraper

load_dotenv()

class NewsCrawler:
    def __init__(self):
        self.db = Database()
        self.keyword_filter = KeywordFilter()
        self.ai_tagger = AITagger()
        self.deduplicator = AIDuplicateDetector()
        
        # 初始化爬虫列表（8个加密媒体）
        self.scrapers = [
            TechFlowScraper(),
            OdailyScraper(),
            BlockBeatsScraper(),
            ForesightScraper(),
            ChainCatcherScraper(),
            PANewsScraper(),
            MarsBitScraper(),
        ]
    
    async def scrape_all_sources(self):
        """抓取所有新闻源"""
        print("\n=== 开始抓取新闻 ===")
        all_news = []
        
        for scraper in self.scrapers:
            try:
                print(f"\n抓取 {scraper.site_name}...")
                news_list = await scraper.run()
                
                for news in news_list:
                    news['source_site'] = scraper.site_name
                    all_news.append(news)
                    
            except Exception as e:
                print(f"抓取 {scraper.site_name} 失败: {e}")
        
        print(f"\n总计抓取 {len(all_news)} 条新闻")
        return all_news
    
    def save_raw_news(self, news_list: list):
        """保存原始新闻"""
        print("\n=== 保存原始新闻 ===")
        saved_count = 0
        
        for news in news_list:
            news_id = self.db.insert_news({
                'title': news['title'],
                'content': news.get('content', ''),
                'source_url': news['url'],
                'source_site': news['source_site'],
                'published_at': news.get('published_at'),
                'is_marked_important': news.get('is_marked_important', False),
                'site_importance_flag': news.get('site_importance_flag', '')
            })
            
            if news_id:
                news['id'] = news_id
                saved_count += 1
        
        print(f"成功保存 {saved_count} 条新闻")
        return [n for n in news_list if 'id' in n]
    
    def apply_keyword_filter(self, news_list: list):
        """应用关键词过滤"""
        print("\n=== 关键词过滤 ===")
        passed_news = []
        
        for news in news_list:
            result = self.keyword_filter.filter_news(news)
            
            # 更新数据库
            self.db.update_news(news['id'], {
                'keyword_filter_passed': result['passed'],
                'keyword_filter_reason': result['reason'],
                'keyword_matched_whitelist': result['matched_whitelist'],
                'filtered_at': datetime.now(),
                'processing_stage': 'keyword_filtered' if result['passed'] else 'raw'
            })
            
            # 记录日志
            self.db.log_processing(
                news['id'],
                'keyword_filter',
                'passed' if result['passed'] else 'blocked',
                result['reason']
            )
            
            # 统计规则命中
            if not result['passed']:
                self.db.increment_filter_stat(
                    result['matched_rule'],
                    result['reason'],
                    'blacklist'
                )
            elif result['matched_whitelist']:
                self.db.increment_filter_stat(
                    result['matched_rule'],
                    result['reason'],
                    'whitelist'
                )
            
            if result['passed']:
                passed_news.append(news)
        
        print(f"通过过滤: {len(passed_news)}/{len(news_list)} 条")
        return passed_news
    
    def apply_ai_tagging(self, news_list: list):
        """应用AI标签"""
        print("\n=== AI标签生成 ===")
        
        for i, news in enumerate(news_list, 1):
            print(f"处理 {i}/{len(news_list)}: {news['title'][:50]}...")
            
            try:
                ai_result = self.ai_tagger.generate_tags(news)
                
                # 更新数据库
                self.db.update_news(news['id'], {
                    'ai_processed': True,
                    'ai_score': ai_result['score'],
                    'ai_summary': ai_result['summary'],
                    'ai_processed_at': datetime.now(),
                    'processing_stage': 'ai_processed'
                })
                
                # 保存标签
                for tag_name in ai_result['tags']:
                    tag_id = self.db.insert_or_get_tag(tag_name, ai_result['category'])
                    if tag_id:
                        self.db.link_news_tag(news['id'], tag_id, 0.9)  # 默认置信度0.9
                
                # 记录日志
                self.db.log_processing(
                    news['id'],
                    'ai',
                    'processed',
                    f"评分: {ai_result['score']}, 标签: {', '.join(ai_result['tags'])}",
                    details=ai_result
                )
                
                news['ai_result'] = ai_result
                
            except Exception as e:
                print(f"  AI处理失败: {e}")
                self.db.log_processing(news['id'], 'ai', 'error', str(e))
        
        print(f"AI处理完成")
        return news_list
    
    def apply_deduplication(self, news_list: list):
        """应用去重"""
        print("\n=== AI去重检测 ===")
        
        # 获取最近24小时的新闻用于对比
        existing_news = self.db.get_recent_news_for_dedup(hours=24)
        
        duplicate_count = 0
        for news in news_list:
            try:
                result = self.deduplicator.find_duplicate(news, existing_news)
                
                if result['is_duplicate']:
                    duplicate_count += 1
                    
                    # 标记为重复
                    self.db.update_news(news['id'], {
                        'is_duplicate': True,
                        'duplicate_of': result['duplicate_of'],
                        'similarity_score': result['similarity']
                    })
                    
                    # 合并来源
                    original_news = result['matched_news']
                    sources = original_news.get('multiple_sources', [original_news['source_site']])
                    if news['source_site'] not in sources:
                        sources.append(news['source_site'])
                        self.db.update_news(result['duplicate_of'], {
                            'multiple_sources': sources
                        })
                    
                    # 记录日志
                    self.db.log_processing(
                        news['id'],
                        'dedup',
                        'duplicate_found',
                        f"与新闻#{result['duplicate_of']}重复，相似度{result['similarity']:.2%}"
                    )
                    
                    print(f"  发现重复: {news['title'][:40]}... (相似度{result['similarity']:.2%})")
                    
            except Exception as e:
                print(f"去重检测失败: {e}")
        
        print(f"发现重复: {duplicate_count}/{len(news_list)} 条")
        return news_list
    
    async def run(self, dry_run=False):
        """运行完整流程"""
        try:
            self.db.connect()
            
            # 1. 抓取新闻
            raw_news = await self.scrape_all_sources()
            if not raw_news:
                print("没有抓取到新闻")
                return
            
            # 2. 保存原始新闻
            news_with_ids = self.save_raw_news(raw_news)
            
            # 3. 关键词过滤
            filtered_news = self.apply_keyword_filter(news_with_ids)
            
            # 4. AI标签
            tagged_news = self.apply_ai_tagging(filtered_news)
            
            # 5. AI去重
            final_news = self.apply_deduplication(tagged_news)
            
            # 6. 推送（TODO）
            if not dry_run:
                print("\n TODO: 推送到Telegram")
            
            print("\n=== 处理完成 ===")
            print(f"原始: {len(raw_news)} → 过滤: {len(filtered_news)} → 最终: {len([n for n in final_news if not n.get('is_duplicate', False)])}")
            
        except Exception as e:
            print(f"运行错误: {e}")
            raise
        finally:
            self.db.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='AINews智能新闻聚合爬虫')
    parser.add_argument('--dry-run', action='store_true', help='测试模式（不推送）')
    args = parser.parse_args()
    
    crawler = NewsCrawler()
    asyncio.run(crawler.run(dry_run=args.dry_run))
