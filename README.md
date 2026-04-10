# AINews

基于 FastAPI、React 和 SQLite 的加密新闻聚合系统。系统负责抓取多来源内容，做去重与黑名单拦截，再进入 AI 审核和 Telegram 分发，同时提供公开前台和后台管理界面。

## 当前架构

运行时只保留一套内容 contract：

- `incoming`: 采集池
- `archive`: 归档池
- `blocked`: 已拦截
- `review`: 待审核
- `selected`: 已选入
- `discarded`: 已舍弃

后端唯一应用根是 [`backend/app`](E:/Work/Code/AINEWS/backend/app)，数据库 schema 唯一来源是 [`backend/app/infrastructure/sqlite/sqlite_schema.py`](E:/Work/Code/AINEWS/backend/app/infrastructure/sqlite/sqlite_schema.py) 和 [`backend/app/infrastructure/sqlite/sqlite_migrations.py`](E:/Work/Code/AINEWS/backend/app/infrastructure/sqlite/sqlite_migrations.py)。

## 主要能力

- 多站点新闻与文章抓取，支持增量抓取和浏览器渲染
- 基于标题相似度的归档去重和重复对照
- 归档池黑名单拦截与批量恢复
- AI 审核队列、人工复核和结果重置
- Telegram 实时发送与每日日报
- 公开前台内容流、日报和搜索
- 后台内容管理、系统配置和导出

## 目录概览

```text
AINEWS/
├── backend/
│   ├── main.py
│   └── app/
│       ├── core/
│       ├── routers/
│       └── services/
├── crawler/
│   ├── database/
│   │   ├── repositories/
│   │   ├── db_sqlite.py
│   │   ├── sqlite_migrations.py
│   │   └── sqlite_schema.py
│   ├── filters/
│   └── scrapers/
├── frontend/
│   └── src/
│       ├── api/
│       ├── components/
│       ├── hooks/
│       ├── layouts/
│       └── pages/
└── shared/
    └── content_contract.py
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 安装

```bash
git clone https://github.com/your-username/AINEWS.git
cd AINEWS

pip install -r crawler/requirements.txt
playwright install chromium

cd frontend
npm install
cd ..
```

### 配置

复制并填写根目录环境变量文件：

```bash
cp .env.example .env.development
```

常用配置项：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `JWT_SECRET_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 启动

```bash
python -m backend.worker
python backend/main.py
cd frontend
npm run dev
```

访问地址：

- 公开前台: [http://localhost:5173/](http://localhost:5173/)
- 登录页: [http://localhost:5173/login](http://localhost:5173/login)
- 后台: [http://localhost:5173/admin](http://localhost:5173/admin)
- 后端: [http://localhost:8000/](http://localhost:8000/)

## 后台数据流

系统由两个 Python 进程协作：

- `backend/main.py`: API 入口，只负责接口和数据库初始化
- `backend/worker.py`: 后台 worker，负责调度和自动流水线

- `scheduler_loop`: 按爬虫配置定时拉起抓取任务
- `auto_pipeline_loop`: 在工作时段内顺序执行去重、黑名单拦截、AI 审核和 Telegram 推送

运行时处理链路如下：

1. 爬虫把内容写入 `news.stage = incoming`
2. 去重服务把非重复内容写入 `archive_entries`，把重复项保留在 `news` 中并标记重复关系
3. 黑名单服务把命中项标记为 `archive_status = blocked`
4. AI 审核服务把归档内容送入 `review_entries`
5. 审核结果落为 `pending / selected / discarded`
6. Telegram 服务发送 `selected` 内容，并生成 `daily_reports`

## 主要接口

### 公开接口

- `GET /api/public/content`
- `GET /api/public/reports`
- `GET /api/public/search`

### 后台内容接口

- `GET /api/content/overview`
- `GET /api/content/incoming`
- `GET /api/content/source/groups`
- `GET /api/content/archive`
- `GET /api/content/blocked`
- `GET /api/content/review`
- `GET /api/content/decisions`
- `GET /api/content/export`

### 后台控制接口

- `POST /api/spiders/run/{name}`
- `POST /api/content/archive/build`
- `POST /api/content/blocked/apply`
- `POST /api/content/review/run`
- `POST /api/delivery/daily/news`
- `POST /api/delivery/daily/article`

### 配置接口

- `GET/POST /api/system/timezone`
- `GET/POST /api/delivery/schedule`
- `GET/POST /api/config/automation`
- `GET/POST /api/integration/telegram`
- `GET/POST /api/integration/ai`
- `GET/POST /api/review/settings`

## 说明

- 如需了解当前数据库表结构，请以 [`sqlite_schema.py`](E:/Work/Code/AINEWS/backend/app/infrastructure/sqlite/sqlite_schema.py) 为准。
- 如需了解迁移逻辑，请以 [`sqlite_migrations.py`](E:/Work/Code/AINEWS/backend/app/infrastructure/sqlite/sqlite_migrations.py) 为准。
