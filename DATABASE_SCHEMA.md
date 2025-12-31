# 数据库结构与状态说明书

本文档详细描述了 AINEWS 系统中的数据库结构、表的作用以及各个状态标签（stage, status 等）的具体含义。

## 1. 数据流转概览 (Workflow)

系统按照以下流程处理每一条新闻数据，并根据状态将其在不同的表之间移动（或复制）：

1.  **原始抓取 (Raw Ingestion)**:
    *   所有爬虫抓取的数据首先进入 `news` 总表。
    *   状态标记为 `stage='raw'`。
    
2.  **去重处理 (Deduplication)**:
    *   **重复项**: 被标记为 `is_duplicate=1`，`duplicate_of=<主新闻ID>`，状态变为 `stage='duplicate'`。
    *   **唯一项 (Survivors)**: 被**复制**一份到 `deduplicated_news` 表，`news` 表中状态变为 `stage='deduplicated'`。
    
3.  **本地过滤 (Local Filtering)**:
    *   **被过滤 (Rejected)**: `deduplicated_news` 表中的记录状态被标记为 `stage='filtered'`（保留在表中用于查阅）。
    *   **通过 (Accepted)**: `deduplicated_news` 表中的记录状态被标记为 `stage='verified'`（等待进入精选/AI 处理）。
    
4.  **精选列表 (Curation)**:
    *   通过人工点击“加精”或系统自动规则，新闻从 `deduplicated_news` **晋升**到 `curated_news` 表。
    *   `news` 表中状态变为 `stage='curated'`。
    
5.  **AI 处理 (AI Processing)**:
    *   AI 对 `curated_news` 表中的数据进行打分和评价。
    *   结果更新到 `ai_status` 字段 (`approved` 推荐 / `rejected` 拒绝)。
    
6.  **推送 (Push)**:
    *   被推荐的新闻推送到 Telegram。
    *   `push_status` 更新为 `'sent'`。

---

## 2. 核心数据表 (Key Tables)

### 2.1 `news` (数据总表)
最底层的原始数据表，**存储所有历史数据**，是数据的“唯一真理来源”。

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | INTEGER | 主键 ID。 |
| `title` | TEXT | 新闻标题。 |
| `content` | TEXT | 新闻内容。 |
| `source_site` | TEXT | 来源爬虫名 (如 'odaily')。 |
| `source_url` | TEXT | 原始链接 (用于去重)。 |
| `stage` | TEXT | **流程状态** (raw, duplicate, deduplicated, curated)。 |
| `type` | TEXT | 类型 ('news', 'article')。 |
| `is_duplicate` | BOOLEAN | 是否为重复项 (1=是, 0=否)。 |
| `duplicate_of` | INTEGER | 重复源的主新闻 ID。 |

### 2.2 `deduplicated_news` (去重池)
一个**临时/工作台**性质的表，存放所有通过了去重检查的数据。主要用于展示“已去重数据”和进行“本地过滤”。
*   **来源**: 当 `news.stage` 变为 `'deduplicated'` 时复制而来。
*   **清理**: 点击“还原已去重数据”时，此表会被清空（保留 filtered 数据）。

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | INTEGER | 本表主键。 |
| `original_news_id` | INTEGER | 对应 `news` 表的 ID。 |
| `stage` | TEXT | 通常为 'deduplicated'。如果被本地关键词过滤，则为 'filtered'。如果通过本地关键词过滤，则为 'verified'。 |
| `keyword_filter_reason`| TEXT | 被过滤的原因 (关键词)。 |

### 2.3 `curated_news` (精选/AI池)
存放**高价值数据**，用于 AI 分析和最终发布。
*   **来源**: 从 `deduplicated_news` 晋升而来。

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | INTEGER | 主键。 |
| `original_news_id` | INTEGER | 对应 `news` 表的 ID。 |
| `ai_status` | TEXT | AI 处理结果 (approved, rejected, pending)。 |
| `ai_summary` | TEXT | AI 生成的摘要。 |
| `ai_explanation` | TEXT | AI 给出的推荐/拒绝理由。 |
| `push_status` | TEXT | 推送状态 (sent, pending)。 |

---

## 3. 状态标签定义 (Tags Definition)

### 3.1 `news.stage` (主流程阶段)
定义了一条新闻当前处于生命周期的哪个位置。

| 值 (Value) | 含义 (Meaning) |
| :--- | :--- |
| **`raw`** | **原始状态**。刚抓取进来，还没进行去重检查。 |
| **`duplicate`** | **重复项**。被判定为重复，将被隐藏或仅在“重复对照”中显示。 |
| **`deduplicated`** | **已去重**。有效新闻，已进入去重池，等待筛选。 |
| **`filtered`** | **被过滤**。被本地关键词黑名单拦截 (此状态主要在 deduplicated_news 表中体现)。 |
| **`curated`** | **已精选**。已进入精选列表，正在进行 AI 分析或等待推送。 |

### 3.2 `curated_news.ai_status` (AI 状态)
AI 对新闻价值的判断结果。

| 值 (Value) | 含义 (Meaning) |
| :--- | :--- |
| **`NULL` (或 pending)** | **待处理**。显示在“精选数据” Tab，等待 AI 分析。 |
| **`approved`** | **AI 推荐**。高价值新闻，显示在“AI 精选” Tab。 |
| **`rejected`** | **AI 拒绝**。低价值或无关新闻，显示在“AI 筛选(被拒)” Tab。 |
| **`restored`** | **人工还原**。人工从被拒列表中捞回的新闻。 |

### 3.3 `curated_news.push_status` (推送状态)
新闻发布到 Telegram 的状态。

| 值 (Value) | 含义 (Meaning) |
| :--- | :--- |
| **`pending`** | **未推送**。 |
| **`sent`** | **已推送**。已成功发送到 Telegram 频道。 |
| **`failed`** | **推送失败**。发送过程中出错。 |

---

## 4. 还原逻辑说明 (Batch Restore Logic)

点击“还原已去重数据”按钮时，系统执行以下操作来**重置流程**：

1.  **重置重复项 (Reset Duplicates)**:
    *   在 `news` 表中，把所有 `stage='duplicate'` 的记录重置为 `raw`。
    *   清空 `duplicate_of` 和 `is_duplicate` 标记。
    *   *结果：清空“重复对照” Tab。*

2.  **重置已去重项 (Reset Deduplicated)**:
    *   在 `news` 表中，把所有 `stage='deduplicated'` 的记录重置为 `raw`。
    *   *结果：清空“去重数据” Tab。*

3.  **清理去重池 (Clean Deduplication Pool)**:
    *   清空 `deduplicated_news` 表。
    *   **注意**：所有记录将被删除，包括 `filtered` 的数据。
    *   *结果：清空“去重数据” Tab 以及“过滤设置/已过滤数据” Tab。*

4.  **保护精选/AI (Protect Curated/AI)**:
    *   **完全不动** `stage='curated'` 的数据。
    *   **完全不动** `curated_news` 表。
    *   *结果：您在“精选数据”、“AI 精选”、“AI 筛选”里的工作成果全部保留，不受影响。*
