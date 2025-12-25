"""爬取频率配置加载器"""
import yaml
from pathlib import Path
from typing import Dict

def load_scrape_config(config_path: str = None) -> Dict:
    """
    加载爬取频率配置
    
    Args:
        config_path: 配置文件路径，默认为config/scrape_intervals.yaml
    
    Returns:
        配置字典
    """
    if config_path is None:
        config_path = Path(__file__).parent / 'config' / 'scrape_intervals.yaml'
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"配置文件不存在: {config_path}")
        # 返回默认配置
        return get_default_config()
    except Exception as e:
        print(f"加载配置失败: {e}")
        return get_default_config()

def get_default_config() -> Dict:
    """获取默认配置"""
    return {
        'scrape_intervals': {
            'blockbeats': 30,
            'techflow': 60,
            'foresight': 60,
            'marsbit': 60,
            'odaily': 90,
            'chaincatcher': 60,
            'panews': 60,
        },
        'global': {
            'default_interval': 60,
            'min_interval': 15,
            'retry_interval': 5,
            'max_retries': 3,
        }
    }

def get_interval(site_name: str, config: Dict = None) -> int:
    """
    获取指定媒体的抓取间隔（分钟）
    
    Args:
        site_name: 媒体名称
        config: 配置字典，如果为None则自动加载
    
    Returns:
        抓取间隔（分钟）
    """
    if config is None:
        config = load_scrape_config()
    
    intervals = config.get('scrape_intervals', {})
    default = config.get('global', {}).get('default_interval', 60)
    
    return intervals.get(site_name, default)

def print_config_summary():
    """打印配置摘要"""
    config = load_scrape_config()
    intervals = config.get('scrape_intervals', {})
    
    print("=" * 60)
    print("爬取频率配置")
    print("=" * 60)
    print()
    
    # 按频率排序
    sorted_sites = sorted(intervals.items(), key=lambda x: x[1])
    
    for site, interval in sorted_sites:
        freq_desc = "高频" if interval <= 30 else "中频" if interval <= 90 else "低频"
        print(f"{site:15s}: {interval:3d}分钟  [{freq_desc}]")
    
    print()
    print("=" * 60)
    
    global_config = config.get('global', {})
    print(f"默认频率: {global_config.get('default_interval', 60)}分钟")
    print(f"最小间隔: {global_config.get('min_interval', 15)}分钟")
    print("=" * 60)

if __name__ == '__main__':
    print_config_summary()
