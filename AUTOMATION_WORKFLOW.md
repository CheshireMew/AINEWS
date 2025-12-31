# AINEWS 自动化推送流程文档

## 概览

AINEWS 系统的自动化流程每 15 分钟执行一次循环，在工作时间（北京时间 08:00-24:00）自动完成从爬取到 Telegram 推送的全流程。

**总流程**：爬取 → 去重 → 关键词过滤 → AI 打分 → Telegram 推送

---

## 主orchestrator: `auto_pipeline_loop()`

**文件位置**: `backend/main.py` 第 919 行

**执行周期**: 每 15 分钟（900 秒）

**工作时间**: 08:00-24:00（北京时间），夜间（00:00-08:00）休眠

**调用顺序**:
1. `wait_for_scrapers()` - 等待爬虫完成
2. `auto_deduplication()` - 自动去重
3. `auto_keyword_filter()` - 自动关键词过滤
4. `auto_ai_scoring()` - 自动 AI 打分
5. `auto_telegram_push()` - 自动 Telegram 推送

---

## 步骤 1: 自动去重 `auto_deduplication()`

**文件位置**: `backend/main.py` 第 1002 行

### 参数配置
- **时间范围**: 从 `system_config` 表读取 `auto_dedup_hours`（默认 2 小时）
- **相似度阈值**: 从 `system_config` 表读取 `dedup_threshold`（默认 0.50）
  - **阈值来源**: 
    - 用户在前端 `DeduplicatedTab.jsx` 的"相似度阈值"输入框中设置（保存在浏览器 localStorage）
    - 执行**手动去重**时，该阈值会被自动保存到 `system_config.dedup_threshold`
    - **自动去重**会读取 `system_config.dedup_threshold` 的值
  - **更新方式**: 每次手动去重都会更新数据库中的阈值，确保自动去重使用最新设置

### 数据库操作

#### 读取的表
- **`news` 表**
  - **查询条件**: `(stage = 'raw' OR stage = 'deduplicated') AND published_at >= <时间范围>`
  - **提取字段**: `id`, `title`, `content`, `source_url`, `source_site`, `published_at`, `scraped_at`

#### 调用的方法
- `LocalDeduplicator.mark_duplicates()` - 使用 TF-IDF 向量 + 余弦相似度标记重复

#### 写入的表

**插入到 `deduplicated_news` 表**（非重复新闻）:
```sql
INSERT OR IGNORE INTO deduplicated_news 
(title, content, source_site, source_url, published_at, scraped_at, 
 deduplicated_at, stage, type, original_news_id)
VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'deduplicated', 'news', ?)
```

**更新 `news` 表**:
- **非重复**: `stage = 'deduplicated'`
- **重复**: `stage = 'duplicate'`, `duplicate_of = <主新闻ID>`, `is_local_duplicate = 1`

### 输出
- **deduplicated_news** 表新增 `stage='deduplicated'` 的记录
- **news** 表的 `stage` 被更新为 `deduplicated` 或 `duplicate`

---

## 步骤 2: 自动关键词过滤 `auto_keyword_filter()`

**文件位置**: `backend/main.py` 第 1100 行

### 参数配置
- **时间范围**: 从 `system_config` 表读取 `auto_filter_hours`（默认 24 小时）

### 调用的方法
- `db.filter_news_by_blacklist(time_range_hours=<时间范围>)`
  - 文件位置: `crawler/database/db_sqlite.py` 第 689 行

### 数据库操作（在 `filter_news_by_blacklist` 内部）

#### 读取的表
1. **`keyword_blacklist` 表** - 加载所有黑名单关键词和正则规则
2. **`deduplicated_news` 表**
   - **查询条件**: `stage = 'deduplicated' AND (type = 'news' OR type IS NULL) AND deduplicated_at >= <时间范围>`
   - **提取字段**: `id`, `title`, `content`

#### 写入的表

**更新 `deduplicated_news` 表**:

**被过滤的新闻**:
```sql
UPDATE deduplicated_news 
SET stage = 'filtered', 
    keyword_filter_reason = <匹配的关键词>
WHERE id = ?
```

**通过过滤的新闻**（同时执行两个操作）:

1. **插入到 `curated_news` 表**:
```sql
INSERT INTO curated_news (
    title, content, source_site, source_url, published_at, scraped_at, 
    deduplicated_at, curated_at, is_marked_important, site_importance_flag, 
    stage, type, original_news_id
) VALUES (...)
```

2. **更新 `deduplicated_news` 状态为 'verified'**:
```sql
UPDATE deduplicated_news 
SET stage = 'verified'
WHERE id = ?
```

### 输出
- **deduplicated_news** 表中:
  - `stage='verified'` - 通过过滤的新闻（**同时**已进入 `curated_news` 表等待 AI 打分）
  - `stage='filtered'` - 被黑名单过滤的新闻
- **curated_news** 表新增通过过滤的新闻记录（`ai_status=NULL`，等待 AI 打分）

---

## 步骤 3: 自动 AI 打分 `auto_ai_scoring()`

**文件位置**: `backend/main.py` 第 1136 行

### 参数配置
- **时间范围**: 从 `system_config` 表读取 `auto_ai_scoring_hours`（默认 10 小时）
- **API 配置**:
  - `llm_api_key` - DeepSeek API Key
  - `llm_base_url` - API 基础 URL（默认 `https://api.deepseek.com`）
  - `llm_model` - 模型名称（默认 `deepseek-chat`）
  - `ai_filter_prompt` 或 `ai_filter_prompt_news` - AI 打分提示词

### 数据库操作

#### 读取的表
- **`curated_news` 表**
  - **查询条件**: `(ai_status IS NULL OR ai_status = '' OR ai_status = 'pending') AND published_at >= <时间范围>`
  - **提取字段**: `id`, `title`
  - **批量处理**: 每批 10 条

#### 调用的方法
- `DeepSeekService.batch_filter_news(news_items, custom_prompt)` - 调用 AI API 批量打分

#### 写入的表

**更新 `curated_news` 表**:
```sql
UPDATE curated_news 
SET ai_status = <'approved' | 'rejected'>,
    ai_explanation = <分数和理由>
WHERE id = ?
```

- **ai_status = 'approved'**: 分数 ≥ 5 分
- **ai_status = 'rejected'**: 分数 < 5 分
- **ai_explanation**: 格式为 "7分-这是一条有价值的新闻..."

### 输出
- **curated_news** 表中 `ai_status` 和 `ai_explanation` 字段被填充

---

## 步骤 4: 自动 Telegram 推送 `auto_telegram_push()`

**文件位置**: `backend/main.py` 第 1247 行

### 参数配置
- **时间范围**: 从 `system_config` 表读取 `auto_push_hours`（默认 12 小时）
- **Telegram 配置**:
  - `telegram_bot_token` - Bot Token
  - `telegram_chat_id` - 频道 ID
- **去重阈值**: 从 `system_config` 表读取 `dedup_threshold`（默认 0.50）

### 数据库操作

#### 读取的表

**主查询 - `curated_news` 表**:
```sql
SELECT id, title, source_url, content, ai_explanation
FROM curated_news
WHERE ai_status = 'approved'
AND (push_status IS NULL OR push_status = 'pending')
AND published_at >= <时间范围>
ORDER BY published_at DESC
```

**去重参考 - `curated_news` 表**:
```sql
SELECT title 
FROM curated_news 
WHERE push_status = 'sent' 
ORDER BY pushed_at DESC 
LIMIT 30
```

#### 调用的方法
1. `LocalDeduplicator.extract_features(title)` - 提取标题特征
2. `LocalDeduplicator.calculate_similarity(features1, features2)` - 计算相似度
3. `TelegramBot.send_message(message, parse_mode='HTML')` - 发送消息到 Telegram

#### 推送逻辑

1. **分数筛选**: 从 `ai_explanation` 中提取分数，只推送 ≥ 5 分的新闻
2. **去重检查**: 与最近推送的 30 条新闻对比，相似度 ≥ 阈值则跳过
3. **批量推送**: 将所有通过筛选的新闻组合成一条消息推送

#### 写入的表

**成功推送 - 更新 `curated_news` 表**:
```sql
UPDATE curated_news 
SET push_status = 'sent', 
    pushed_at = CURRENT_TIMESTAMP 
WHERE id IN (...)
```

**检测到重复 - 更新 `curated_news` 表**:
```sql
UPDATE curated_news 
SET push_status = 'duplicate'
WHERE id = ?
```

**检测到重复 - 更新 `news` 表**:
```sql
UPDATE news 
SET duplicate_of = ?, 
    is_local_duplicate = 1, 
    stage = 'deduplicated'
WHERE id = ?
```

### 输出
- **curated_news** 表中 `push_status` 被更新为 `sent` 或 `duplicate`
- 消息发送到 Telegram 频道

---

## 数据流转图

```
news (stage='raw')
    ↓ [自动去重]
news (stage='deduplicated' | 'duplicate')
    ↓
deduplicated_news (stage='deduplicated')
    ↓ [自动关键词过滤]
deduplicated_news (stage='verified' | 'filtered')
    ↓ [手动或自动加精]
curated_news (ai_status=NULL)
    ↓ [自动 AI 打分]
curated_news (ai_status='approved' | 'rejected')
    ↓ [自动推送，仅 approved 且 ≥5 分]
curated_news (push_status='sent') → Telegram 频道
```

---

## 关键数据表状态字段

### `news` 表
- **stage**:
  - `raw` - 刚爬取的原始新闻
  - `deduplicated` - 已通过去重
  - `duplicate` - 被标记为重复
- **duplicate_of**: 主新闻 ID（仅当 `is_local_duplicate=1`）
- **is_local_duplicate**: 是否为本地去重标记的重复项

### `deduplicated_news` 表
- **stage**:
  - `deduplicated` - 刚去重完成，等待过滤
  - `verified` - 通过关键词过滤，等待加精
  - `filtered` - 被关键词黑名单过滤
- **keyword_filter_reason**: 触发过滤的关键词

### `curated_news` 表
- **ai_status**:
  - `NULL` / `''` / `pending` - 未打分
  - `approved` - AI 批准（≥5 分）
  - `rejected` - AI 拒绝（<5 分）
- **push_status**:
  - `NULL` / `pending` - 未推送
  - `sent` - 已推送
  - `duplicate` - 推送前被去重拦截
- **ai_explanation**: AI 打分结果（格式：`7分-理由...`）
- **pushed_at**: 推送时间戳

---

## 配置项汇总（存储在 `system_config` 表）

| 配置键 | 默认值 | 说明 |
|--------|--------|------|
| `auto_dedup_hours` | 2 | 自动去重扫描时间范围（小时） |
| `dedup_threshold` | 0.50 | 去重相似度阈值（0-1） |
| `auto_filter_hours` | 24 | 自动关键词过滤扫描时间范围（小时） |
| `auto_ai_scoring_hours` | 10 | 自动 AI 打分扫描时间范围（小时） |
| `auto_push_hours` | 12 | 自动推送扫描时间范围（小时） |
| `llm_api_key` | - | DeepSeek API Key |
| `llm_base_url` | `https://api.deepseek.com` | LLM API 基础 URL |
| `llm_model` | `deepseek-chat` | LLM 模型名称 |
| `ai_filter_prompt` | - | AI 打分提示词（旧版通用） |
| `ai_filter_prompt_news` | - | AI 打分提示词（新版按类型） |
| `telegram_bot_token` | - | Telegram Bot Token |
| `telegram_chat_id` | - | Telegram 频道 Chat ID |

---

## 日志标识

自动化流程使用以下日志前缀便于追踪：

- `🤖 [Auto-Pipeline]` - 主循环状态
- `🕐 [Auto-Pipeline]` - 等待爬虫完成
- `🔄 [Auto-Dedup]` - 自动去重过程
- `🔍 [Auto-Filter]` - 自动关键词过滤
- `🤖 [Auto-AI]` - 自动 AI 打分
- `📤 [Auto-Push]` - 自动推送过程
- `🛡️ [Auto-Push]` - 推送去重拦截

---

## 常见问题

### Q: 为什么有些新闻没有被推送？
A: 可能原因：
1. AI 打分 < 5 分（`ai_status='rejected'`）
2. 被推送前的去重检查拦截（与最近 30 条相似）
3. 发布时间超出推送时间范围（默认 12 小时）
4. 未通过关键词过滤（`deduplicated_news.stage='filtered'`）

### Q: 推送的消息格式是什么？
A: 每条新闻格式为：`⚡ <b><a href="URL">标题</a></b>`，多条新闻之间用两个换行分隔，末尾附带固定的推荐链接页脚。

### Q: 如何调整自动化流程的时间参数？
A: 在 `system_config` 表中修改对应的配置项（见上方配置项汇总表）。

### Q: 自动化流程何时启动？
A: 系统启动后 10 秒开始第一次循环，之后每 15 分钟执行一次，仅在北京时间 08:00-24:00 工作。

---

**文档版本**: 1.0  
**最后更新**: 2025-12-29  
**维护者**: Gemini
