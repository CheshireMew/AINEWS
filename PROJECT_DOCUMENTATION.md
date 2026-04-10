# AINews 项目技术文档

> 当前版本文档，只描述现行架构，不再保留旧阶段模型说明。

## 项目概述

AINews 是一个面向加密新闻场景的内容处理系统，负责：

- 多来源抓取新闻和文章
- 将原始内容写入采集池
- 执行去重和黑名单拦截
- 进入 AI 审核并产生精选结果
- 对精选内容做公开展示、人工导出和 Telegram 分发

## 技术栈

### 后端

- Python 3.10+
- FastAPI
- SQLite
- Playwright
- OpenAI SDK 兼容的 DeepSeek 接口

### 前端

- React
- Ant Design
- Vite
- Axios

## 目录与职责

### `backend/`

- `main.py`: 应用启动、数据库初始化、后台循环
- `app/core`: 配置、异常、响应、运行时装配、爬虫注册
- `app/routers`: HTTP 路由
- `app/services`: 应用服务和跨池编排

### `crawler/`

- `scrapers`: 各站点抓取实现
- `filters`: 去重和过滤逻辑
- `database/repositories`: 表级仓储
- `database/sqlite_schema.py`: schema 唯一来源
- `database/sqlite_migrations.py`: 旧表到新表的一次性迁移

### `frontend/src/`

- `api`: 接口封装
- `hooks/dashboard`: 后台领域 hook
- `hooks/newsfeed`: 前台领域 hook
- `components/dashboard`: 后台 tab 和配置卡片
- `components/newsfeed`: 前台内容组件
- `pages`: 登录、后台、公开前台

### `shared/`

- `content_contract.py`: 内容状态、配置 key、公开流映射

## 当前内容模型

### 采集池

表: `news`

- 用途: 保存抓取结果和重复关系
- 核心状态: `stage = incoming`
- 重复项仍保留在 `news` 中，通过 `duplicate_of` 和 `is_local_duplicate` 表示

### 归档池

表: `archive_entries`

- 用途: 保存去重后的可处理内容
- 状态:
  - `ready`
  - `blocked`
  - `reviewed`

### 审核池

表: `review_entries`

- 用途: 保存进入 AI 审核后的内容和结果
- 状态:
  - `pending`
  - `selected`
  - `discarded`

### 其他表

- `daily_reports`: 每日日报
- `system_config`: 系统配置
- `keyword_blacklist`: 黑名单
- `push_logs`: 发送记录
- `api_keys`: 分析师 API Key

## 运行流程

### 自动流程

应用启动后会有两个后台循环：

1. `scheduler_loop`
   负责按配置调度爬虫。

2. `auto_pipeline_loop`
   负责按顺序执行：
   - 等待当前抓取结束
   - 采集池去重
   - 归档池黑名单拦截
   - AI 审核
   - Telegram 实时发送

### 处理链路

1. Scraper 抓取内容，写入 `news`
2. Deduplication 将非重复内容写入 `archive_entries`
3. Blocklist 将命中项标记为 `blocked`
4. AI 审核更新 `review_entries.review_status`
5. Telegram 发送 `selected` 内容
6. 每日日报写入 `daily_reports`

## 后端接口概览

### 认证

- `POST /api/login`
- `POST /api/system/credentials`

### 内容

- `GET /api/content/overview`
- `GET /api/content/stats`
- `GET /api/content/incoming`
- `GET /api/content/source/groups`
- `GET /api/content/archive`
- `GET /api/content/blocked`
- `GET /api/content/review`
- `GET /api/content/decisions`
- `GET /api/content/export`
- `DELETE /api/content/incoming/{id}`
- `DELETE /api/content/source/{id}`
- `DELETE /api/content/archive/{id}`
- `DELETE /api/content/review/{id}`
- `POST /api/content/archive/{id}/restore`
- `POST /api/content/blocked/{id}/restore`

### 公开前台

- `GET /api/public/content`
- `GET /api/public/reports`
- `GET /api/public/search`

### 配置

- `GET/POST /api/system/timezone`
- `GET/POST /api/delivery/schedule`
- `GET/POST /api/config/automation`
- `GET/POST /api/integration/telegram`
- `GET/POST /api/integration/ai`
- `GET/POST /api/review/settings`

### 管理与流水线

- `GET /api/spiders`
- `GET /api/spiders/status`
- `POST /api/spiders/run/{name}`
- `POST /api/spiders/stop/{name}`
- `POST /api/spiders/config/{name}`
- `POST /api/content/archive/build`
- `POST /api/content/archive/check_similarity`
- `GET/POST/DELETE /api/content/blocklist`
- `POST /api/content/blocked/apply`
- `POST /api/content/blocked/restore`
- `POST /api/content/review/run`
- `POST /api/content/review/{id}/requeue`
- `POST /api/content/review/requeue`
- `POST /api/content/review/clear`
- `POST /api/delivery/daily/news`
- `POST /api/delivery/daily/article`
- `POST /api/delivery/send`

## 前端界面概览

### 公开前台

- 文章流
- 快讯流
- 文章日报
- 快讯日报
- 公开搜索

### 后台标签页

- 采集池
- 重复对照
- 归档池
- 已拦截
- 待审核
- 已舍弃
- 已选入
- 爬虫控制
- 系统配置
- 结果输出

## 维护约束

- 新代码不得再引入并行旧模型或额外的兼容层
- 数据库结构变更必须以 `sqlite_schema.py` 和迁移脚本为准
- 前后端内容状态只能使用 `shared/content_contract.py` 中的规范名
