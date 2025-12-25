"""测试PostgreSQL数据库连接"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("测试PostgreSQL数据库连接")
    print("=" * 60)
    
    # 1. 检查psycopg2是否安装
    try:
        import psycopg2
        print("✅ psycopg2 已安装")
    except ImportError:
        print("❌ psycopg2 未安装")
        print("   请运行: pip install psycopg2-binary")
        return False
    
    # 2. 检查.env文件是否存在
    env_file = Path(__file__).parent.parent / '.env'
    if not env_file.exists():
        print(f"❌ .env 文件不存在: {env_file}")
        print("   请创建.env文件并配置DATABASE_URL")
        return False
    else:
        print(f"✅ .env 文件存在")
    
    # 3. 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print("✅ 环境变量加载成功")
    except ImportError:
        print("⚠️ python-dotenv 未安装，尝试手动解析.env")
        # 手动解析.env
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    # 4. 获取数据库URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL 未配置")
        return False
    else:
        # 隐藏密码显示
        safe_url = db_url.replace(db_url.split('@')[0].split(':')[-1], '****')
        print(f"✅ DATABASE_URL: {safe_url}")
    
    # 5. 测试连接
    try:
        from database.db import Database
        db = Database()
        print("✅ Database 类初始化成功")
        
        # 尝试连接
        conn = db.connect()
        print("✅ 数据库连接成功")
        
        # 检查表是否存在
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        if tables:
            print(f"✅ 找到 {len(tables)} 个表:")
            for table in tables:
                print(f"   - {table}")
        else:
            print("⚠️ 数据库中没有表，需要运行初始化脚本")
            print("   运行: psql -U newsbot -d ainews -f database\\schema.sql")
        
        # 测试get_latest_news方法
        if 'news' in tables:
            latest = db.get_latest_news('techflow')
            if latest:
                print(f"\n✅ get_latest_news() 测试成功")
                print(f"   最新新闻: {latest.get('title', 'N/A')[:50]}...")
            else:
                print(f"\n⚠️ 数据库中暂无新闻数据（正常，首次运行）")
        
        print("\n" + "=" * 60)
        print("✅ 数据库连接测试通过！")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ 数据库连接失败: {e}")
        print("\n请检查:")
        print("1. PostgreSQL 服务是否运行")
        print("2. 数据库 ainews 是否已创建")
        print("3. 用户 newsbot 是否已创建")
        print("4. 密码是否正确")
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
