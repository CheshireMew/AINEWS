# 数据库结构与状态说明

本文档只描述当前 SQLite 运行时结构。数据库唯一来源仍然是 [sqlite_schema.py](E:/Work/Code/AINEWS/backend/app/infrastructure/sqlite/sqlite_schema.py)，这里提供的是便于理解的数据视图。

## 数据流转概览

当前运行模型只有三层内容表：

1. `news`
   抓取落点和重复关系记录

2. `archive_entries`
   去重后的归档池，也是黑名单处理入口

3. `review_entries`
   AI 审核池，同时承载审核结果和发送状态

日报单独存放在 `daily_reports`，不会再作为内容池参与流转。

## 核心表

### `news`

用途：保存抓取结果，是内容最早进入系统的地方。

关键字段：

- `id`: 主键
- `title`: 标题
- `content`: 内容
- `source_site`: 来源站点
- `source_url`: 原始链接，唯一约束
- `published_at`: 原发布时间
- `scraped_at`: 抓取时间
- `stage`: 当前采集阶段
- `type`: 内容类型，当前为 `news` 或 `article`
- `duplicate_of`: 如果是重复项，指向主内容 ID
- `is_local_duplicate`: 是否由本地去重标记
- `push_status`、`pushed_at`: 历史兼容字段，当前实时发送以 `review_entries.delivery_status` 为准

### `archive_entries`

用途：保存通过去重后的内容，作为黑名单处理和归档浏览的单一入口。

关键字段：

- `id`: 与原始内容保持同一 ID
- `title`
- `content`
- `source_site`
- `source_url`
- `published_at`
- `scraped_at`
- `archived_at`: 进入归档池的时间
- `archive_status`: 归档状态
- `content_type`: 内容类型
- `source_item_id`: 对应 `news.id`
- `restored_from_blocklist`: 是否从拦截状态人工恢复
- `block_reason`: 拦截原因

### `review_entries`

用途：保存进入审核流程的内容，以及审核和发送结果。

关键字段：

- `id`: 与原始内容保持同一 ID
- `title`
- `content`
- `source_site`
- `source_url`
- `published_at`
- `archived_at`
- `queued_at`: 进入审核池的时间
- `review_status`: 审核状态
- `review_summary`: 审核摘要
- `review_reason`: 审核理由
- `review_score`: 审核分数
- `review_category`: 审核分类
- `review_tags`: 审核标签
- `delivery_status`: Telegram 发送状态
- `delivered_at`: 实际发送时间
- `content_type`
- `source_item_id`

### `daily_reports`

用途：存储已生成并已发送的每日日报。

关键字段：

- `date`: 日报日期
- `type`: 内容类型
- `title`: 日报标题
- `content`: 完整正文
- `news_count`: 条目数
- `created_at`: 写入时间

## 配置与辅助表

- `system_config`: 系统配置
- `keyword_blacklist`: 黑名单关键词
- `push_logs`: 发送日志
- `api_keys`: 分析师 API Key
- `tags` / `news_tags`: 标签体系
- `processing_logs`: 处理日志
- `filter_stats`: 过滤统计

## 状态定义

### `news.stage`

| 值 | 含义 |
| :--- | :--- |
| `incoming` | 新抓取内容，尚未进入归档池 |
| `archived` | 已通过去重并写入归档池 |
| `duplicate` | 被判定为重复项 |

### `archive_entries.archive_status`

| 值 | 含义 |
| :--- | :--- |
| `ready` | 已归档，等待黑名单处理或人工查看 |
| `blocked` | 命中黑名单，被拦截 |
| `reviewed` | 已推进到审核池 |

### `review_entries.review_status`

| 值 | 含义 |
| :--- | :--- |
| `pending` | 待审核 |
| `selected` | 审核通过 |
| `discarded` | 审核未通过 |

### `review_entries.delivery_status`

| 值 | 含义 |
| :--- | :--- |
| `pending` | 待发送 |
| `sent` | 已发送到 Telegram |

## 处理链路

1. 爬虫写入 `news`
2. 去重把非重复内容写入 `archive_entries`
3. 黑名单把归档内容分成 `blocked` 或推进到 `review_entries`
4. AI 审核在 `review_entries` 内把内容从 `pending` 更新为 `selected / discarded`
5. Telegram 实时发送读取 `selected + pending delivery` 的内容
6. 每日日报从已选入内容汇总后写入 `daily_reports`

## 常见恢复操作

### 恢复已拦截内容

将 `archive_entries.archive_status` 从 `blocked` 改回 `ready`，并标记 `restored_from_blocklist = 1`。

### 恢复审核结果

将 `review_entries.review_status` 改回 `pending`，同时清空审核结果字段。

### 删除内容

后台删除会按 `source_url` 级联清理跨池记录，确保同一条内容不会在不同池里留下残片。

## 维护原则

- 运行时状态名称以 [content_contract.py](E:/Work/Code/AINEWS/shared/content_contract.py) 为准
- 表结构以 [sqlite_schema.py](E:/Work/Code/AINEWS/backend/app/infrastructure/sqlite/sqlite_schema.py) 为准
- 历史数据迁移以 [sqlite_migrations.py](E:/Work/Code/AINEWS/backend/app/infrastructure/sqlite/sqlite_migrations.py) 为准
