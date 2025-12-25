# PostgreSQL 安装与配置指南 (Windows)

## 步骤1: 下载PostgreSQL

### 官方下载地址
**推荐版本**: PostgreSQL 16.x（最新稳定版）

**下载链接**: https://www.postgresql.org/download/windows/

或直接使用EDB安装器：
- 64位: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
- 选择 **PostgreSQL 16.x Windows x86-64**

## 步骤2: 安装PostgreSQL

### 安装选项
1. **安装路径**: `C:\Program Files\PostgreSQL\16` (默认)
2. **组件选择**: 全部勾选
   - ✅ PostgreSQL Server
   - ✅ pgAdmin 4
   - ✅ Stack Builder
   - ✅ Command Line Tools
3. **数据目录**: `C:\Program Files\PostgreSQL\16\data` (默认)
4. **端口**: `5432` (默认)
5. **超级用户密码**: **请设置并记住**，例如: `postgres123`
6. **Locale**: `Default locale`

### 安装后验证
```powershell
# 打开新的PowerShell窗口
psql --version
# 应该显示: psql (PostgreSQL) 16.x
```

## 步骤3: 创建数据库和用户

### 方法A: 使用pgAdmin (图形界面)
1. 打开 pgAdmin 4
2. 连接到 PostgreSQL (使用安装时设置的密码)
3. 右键 "Databases" → Create → Database
   - Database: `ainews`
   - Owner: `postgres`
4. 右键 "Login/Group Roles" → Create → Login/Group Role
   - Name: `newsbot`
   - Password: 设置密码，例如 `newsbot123`
   - Privileges: Can login

### 方法B: 使用命令行 (推荐)
```powershell
# 1. 以postgres用户登录
psql -U postgres

# 2. 在psql中执行以下命令:
CREATE DATABASE ainews;
CREATE USER newsbot WITH PASSWORD 'newsbot123';
GRANT ALL PRIVILEGES ON DATABASE ainews TO newsbot;
\q

# 3. 测试连接
psql -U newsbot -d ainews
# 输入密码: newsbot123
```

## 步骤4: 初始化数据库结构

### 运行SQL脚本
```powershell
# 进入项目目录
cd E:\Work\Code\AINEWS\AINews

# 初始化表结构
psql -U newsbot -d ainews -f database\schema.sql

# 初始化预定义标签
psql -U newsbot -d ainews -f database\init_tags.sql
```

### 验证表是否创建成功
```powershell
psql -U newsbot -d ainews

# 在psql中:
\dt   # 查看所有表
# 应该看到: news, tags, news_tags, processing_logs, push_logs, filter_stats

SELECT * FROM tags;  # 查看预定义标签
\q
```

## 步骤5: 配置环境变量

创建 `.env` 文件（在项目根目录）:
```bash
# 数据库配置
DATABASE_URL=postgresql://newsbot:newsbot123@localhost:5432/ainews

# DeepSeek API (暂时可以留空)
DEEPSEEK_API_KEY=

# Telegram配置 (暂时可以留空)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHANNEL_ID=
```

## 步骤6: 测试连接

运行Python测试脚本:
```powershell
cd E:\Work\Code\AINEWS\AINews\crawler
python test_db_connection.py
```

---

## 常见问题

### Q1: psql命令不存在
**解决**: 添加PostgreSQL到系统PATH
```
C:\Program Files\PostgreSQL\16\bin
```

### Q2: 连接被拒绝
**检查**: PostgreSQL服务是否运行
```powershell
# 查看服务状态
Get-Service postgresql*

# 启动服务
Start-Service postgresql-x64-16
```

### Q3: 密码认证失败
**解决**: 检查密码是否正确，或修改 `pg_hba.conf`:
```
C:\Program Files\PostgreSQL\16\data\pg_hba.conf
```
将 `scram-sha-256` 改为 `md5` 或 `trust`（仅开发环境）

---

## 下一步

安装完成后，运行增量爬取测试:
```powershell
cd E:\Work\Code\AINEWS\AINews\crawler
python test_incremental_scraping.py
```
