# AINews - 智能新闻聚合系统

自动从多个新闻源抓取重要内容，通过关键词+AI双重筛选，推送到Telegram频道或Web展示。适用于各类垂直领域（加密货币、科技、金融等）。

## 功能特点

- 🕷️ **智能爬虫**: 自动抓取多个配置的新闻源的"重要内容"
- 🎯 **三级筛选**: 网站原生标记 → 关键词过滤 → AI智能标签
- 🤖 **AI去重**: DeepSeek语义分析，自动合并重复新闻
- 📱 **Telegram推送**: 精美格式化消息，每天3次定时推送
- 💻 **Web管理**: 新闻浏览、标签管理、数据统计、误杀审核
- 📊 **数据追溯**: 完整记录每条新闻的处理流程

## 技术栈

- **爬虫**: Python 3.10+ + Playwright
- **AI**: DeepSeek API (OpenAI SDK)
- **数据库**: PostgreSQL
- **后端**: Node.js + Express
- **前端**: React + Vite
- **推送**: python-telegram-bot

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo>
cd AINews

# 安装PostgreSQL（Debian 13）
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# 创建数据库
sudo -u postgres psql
CREATE DATABASE ainews;
CREATE USER newsbot WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ainews TO newsbot;
\q

# 初始化数据库结构
psql -U newsbot -d ainews -f database/schema.sql
```

### 2. 配置爬虫

```bash
cd crawler

# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 配置环境变量
cp .env.example .env
# 编辑.env，填入：
# - DATABASE_URL
# - DEEPSEEK_API_KEY
# - TELEGRAM_BOT_TOKEN
# - TELEGRAM_CHANNEL_ID
```

### 3. 配置Web服务

```bash
# 后端
cd backend
npm install
cp .env.example .env
# 编辑.env填入数据库连接

# 前端
cd ../frontend
npm install
```

### 4. 运行

```bash
# 测试爬虫（不推送）
cd crawler
python main.py --dry-run

# 启动后端API
cd backend
npm run dev

# 启动前端
cd frontend
npm run dev

# 生产环境：配置systemd服务
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl enable ainews-crawler
sudo systemctl start ainews-crawler
```

## 项目结构

```
AINews/
├── crawler/          # Python爬虫模块
│   ├── scrapers/    # 各网站爬虫
│   ├── filters/     # 关键词过滤
│   ├── ai/          # AI标签和去重
│   └── pusher/      # Telegram推送
├── backend/         # Node.js API
├── frontend/        # React前端
└── database/        # 数据库schema
```

## 配置说明

### 关键词过滤规则

编辑 `crawler/config/filters.yaml`:

```yaml
blacklist:
  patterns:
    - regex: "简单价格波动的正则"
      reason: "过滤原因"
```

### AI标签配置

编辑 `crawler/config/ai_prompts.yaml` 调整提示词和评分标准。

### 推送时间

编辑 `crawler/scheduler.py` 修改cron表达式。

## 许可证

MIT

## 作者

@YourName
