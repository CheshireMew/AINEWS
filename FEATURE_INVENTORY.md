# AINews 功能清单

> 基于当前模块化架构整理，供重构和回归检查使用。

## 前台

### 页面

- `frontend/src/pages/NewsFeed.jsx`
- `frontend/src/layouts/PublicLayout.jsx`

### 内容流

- 文章流: `stream=longform`
- 快讯流: `stream=briefs`
- 文章日报
- 快讯日报
- 公开搜索

### 主要行为

- 顶部搜索
- 深浅色切换
- 无限滚动加载
- 日报弹窗查看
- 侧栏快讯同步展示

## 后台

### 入口

- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/hooks/useDashboardData.js`

### Tab 清单

1. 采集池
   文件: `frontend/src/components/dashboard/NewsManagementTab.jsx`
   能力: 列表、搜索、按来源筛选、删除、导出入口

2. 重复对照
   文件: `frontend/src/components/dashboard/DuplicateTreeTab.jsx`
   能力: 组视图、相似度检测、删除重复项

3. 归档池
   文件: `frontend/src/components/dashboard/ArchiveTab.jsx`
   能力: 列表、搜索、按来源筛选、恢复到采集池、删除、加入输出

4. 已拦截
   文件: `frontend/src/components/dashboard/BlocklistTab.jsx`
   能力: 黑名单管理、执行拦截、批量恢复、单条恢复、删除、加入输出

5. 待审核
   文件: `frontend/src/components/dashboard/ReviewQueueTab.jsx`
   能力: 列表、搜索、按来源筛选、加入输出

6. 系统配置
   文件: `frontend/src/components/dashboard/SystemSettingsTab.jsx`
   能力: 时区、自动化窗口、AI 提供方、Telegram、账户安全、分析师 API Key

7. 结果输出
   文件: `frontend/src/components/dashboard/ExportTab.jsx`
   能力: 手动精选、格式化复制、发送到 Telegram、手动触发每日日报

8. 已舍弃
   文件: `frontend/src/components/dashboard/DiscardedContentTab.jsx`
   能力: 审核配置、执行审核、恢复单条、批量恢复、清空审核结果、删除

9. 已选入
   文件: `frontend/src/components/dashboard/SelectedContentTab.jsx`
   能力: 列表、搜索、按来源筛选、删除、加入输出

### 共享前端基础

- API 封装: `frontend/src/api/*.js`
- 通用分页列表控制器: `frontend/src/hooks/dashboard/usePaginatedContentList.js`
- 爬虫运行态: `frontend/src/hooks/dashboard/useSpiderRuntime.js`
- 概览统计: `frontend/src/hooks/dashboard/useDashboardOverview.js`

## 后端

### 应用入口

- `backend/main.py`: 只负责 ASGI 启动、数据库初始化和生命周期
- `backend/app/core/runtime.py`: 数据库与 repository 的唯一装配入口

### 路由模块

- `backend/app/routers/auth.py`
- `backend/app/routers/news.py`
- `backend/app/routers/config.py`
- `backend/app/routers/pipeline.py`

### 服务模块

- `content_service`: 内容查询、公开流、导出、跨池删除恢复
- `content_admin_service`: 黑名单、审核结果重置、分析师 API Key
- `deduplication_service`: 去重、重复检测、自动去重
- `ai_pipeline_service`: AI 审核配置、批处理、连接测试
- `scraper_runtime_service`: 爬虫启动、停止、调度和状态
- `telegram_delivery_service`: 实时发送与每日日报
- `config_service`: 系统配置读写
- `auth_service`: 登录和令牌验证

## 数据模型

### 运行时 contract

- `news`: 采集源池，核心状态 `incoming`
- `archive_entries`: 归档池，核心状态 `ready / blocked / reviewed`
- `review_entries`: 审核池，核心状态 `pending / selected / discarded`
- `daily_reports`: 每日日报
- `system_config`: 系统配置
- `keyword_blacklist`: 黑名单
- `push_logs`: 发送日志

### 单一来源

- 内容状态常量: `shared/content_contract.py`
- SQLite schema: `backend/app/infrastructure/sqlite/sqlite_schema.py`
- 旧表迁移: `backend/app/infrastructure/sqlite/sqlite_migrations.py`

## 回归重点

- 前后台都只能使用 `incoming/archive/blocked/review/selected/discarded`
- 公开搜索必须走后端 `/api/public/search`
- 日报读写只能走 `daily_reports`
- 不应再引入额外的并行内容状态模型
