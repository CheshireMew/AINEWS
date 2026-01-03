# AINEWS 项目功能清单 (Feature Inventory)

> **生成时间**: 2026-01-02
> **基准**: Frontend Dashboard Refactoring Phase & Backend V2
> **核心文件**: `Dashboard.jsx`, `components/dashboard/*.jsx`

---

## 🖥️ 前端仪表盘深度分析 (Dashboard Deep Dive)

### 容器组件: Dashboard (frontend/src/pages/Dashboard.jsx)

*   **位置**: `frontend/src/pages/Dashboard.jsx`
*   **主要功能**: 全局状态管理、布局容器、Tab 切换、全局统计、爬虫状态轮询、API设置与数据导出入口。

#### 核心状态 (State)
| 变量名 | 类型 | 初始值 | 用途 | 行号 |
|--------|------|--------|------|------|
| `contentType` | String | 'news' | 内容类型切换 ('news'/'article') | L39 |
| `activeKey` | String | '1' | 当前激活的 Tab Key | L38 |
| `stats` | Array | [] | 数据源统计数据 | L35 |
| `spiders` | Array | [] | 爬虫配置列表 | L36 |
| `spiderStatus` | Object | {} | 爬虫实时运行状态 | L37 |
| `globalCounts` | Object | {...} | 各个阶段的数据量计数 (Badge显示) | L131 |
| `manuallyFeatured`| Array | [] | 跨Tab共享的手动加精列表 | L47 |

#### 主要 API 调用
| 函数名 | API 方法 | 参数 | 功能 | 行号 |
|--------|----------|------|------|------|
| `fetchStats` | `getStats` | contentType | 获取来源统计 | L62 |
| `fetchSpiders` | `getSpiders` | - | 获取爬虫列表 | L73 |
| `fetchSpiderStatus`| `getSpiderStatus` | - | 获取爬虫实时状态 (轮询) | L94 |
| `fetchGlobalCounts`| `getNews`, `getDeduplicatedNews`... | contentType | 获取各Tab数据计数 | L141 |
| `handleRunSpider` | `runSpider` | name, items | 启动爬虫 | L174 |
| `handleStopSpider`| `cancelScraper` | name | 停止爬虫 | L186 |

---

## Tab 1: 数据管理 (NewsManagementTab)

*   **文件**: `frontend/src/components/dashboard/NewsManagementTab.jsx`
*   **功能**: 查看原始抓取数据 ('raw' stage)，支持手动删除。

### 状态变量
| 变量名 | 类型 | 初始值 | 用途 | 行号 |
|--------|------|--------|------|------|
| `news` | Array | [] | 原始新闻列表 | L18 |
| `loading` | Boolean | false | 加载状态 | L19 |
| `filterSource` | String | undefined | 来源筛选 | L21 |
| `pagination` | Object | {current:1...} | 分页配置 | L20 |

### 功能按钮
| 按钮文本 | 事件函数 | 功能说明 | 位置 |
|----------|----------|----------|------|
| (Toolbar) 搜索 | `onSearch` | 关键词搜索 | L132 |
| (Toolbar) 导出 | `onShowExport` | 打开导出弹窗 | L143 |
| (Toolbar) 刷新 | `onRefresh` | 刷新列表 | L144 |
| (Table) 删除 | `handleDeleteNews` | 删除单条新闻 | L121 |

### 表格列定义
| 列名 | dataIndex | render | 特殊说明 |
|------|-----------|--------|----------|
| ID | id | - | - |
| 标题 | title | Link Render | 显示链接，若有 `duplicate_of` 显示橙色 Tag |
| 来源 | source_site | - | - |
| 状态 | stage | Tag Render | 显示 '原始'(Green) 或 '重复'(Orange) |
| 发布时间 | published_at | Date Render | 格式化时间 |
| 操作 | - | Button Group | [删除] |

### API 调用
| 函数名 | API 方法 | 用途 |
|--------|----------|------|
| `fetchNews` | `getNews` | 获取原始新闻列表 |
| `handleDeleteNews` | `deleteNews` | 删除新闻 |

---

## Tab 1.5: 重复对照 (DuplicateTreeTab)

*   **文件**: `frontend/src/components/dashboard/DuplicateTreeTab.jsx`
*   **功能**: 以树状结构展示去重逻辑结果 (Master -> Duplicates)，并提供相似度检测工具。

### 特有功能区域
| 区域 | 组件 | 功能 | 状态变量 |
|------|------|------|----------|
| 相似度检测 | Input + Button | 测试两个ID的相似度 | `newsId1`, `newsId2`, `similarityResult` |
| 统计提示 | Div | 显示重复/独立组数量 | `groupCount`, `independentCount` |

### API 调用
| 函数名 | API 方法 | 用途 |
|--------|----------|------|
| `fetchNews` | `getNews` | 获取所有新闻用于分组 (limit=10000) |
| `handleCheckSimilarity` | `checkNewsSimilarity` | 后端计算两个ID的相似度 |

---

## Tab 3: 去重数据 (DeduplicatedTab)

*   **文件**: `frontend/src/components/dashboard/DeduplicatedTab.jsx`
*   **功能**: 管理 'deduplicated' 阶段数据，执行本地去重逻辑。

### 状态变量
| 变量名 | 类型 | 初始值 | 用途 | 行号 |
|--------|------|--------|------|------|
| `dedupTimeRange` | Number | 8 | 去重时间范围 (小时) | L28 |
| `threshold` | Number | 0.50 | 相似度阈值 | L30 |
| `deduplicating` | Boolean | false | 去重运行中状态 | L44 |

### 功能按钮
| 按钮文本 | 事件函数 | 功能说明 |
|----------|----------|----------|
| 手动去重 | `handleDeduplicate` | 触发后端去重逻辑 |
| 批量恢复 | `BatchRestoreButton` | 恢复被标记为重复的新闻 |
| (Table) 加精 | `onAddToFeatured` | 添加到手动精选列表 |
| (Table) 还原 | `handleRestoreNews` | 还原状态至 raw |

### API 调用
| 函数名 | API 方法 | 参数 | 用途 |
|--------|----------|------|------|
| `handleDeduplicate` | `deduplicateNews` | time_range, action='mark', threshold | 执行去重 |
| `fetchDedupNews` | `getDeduplicatedNews` | - | 获取列表 |

---

## Tab 4: 过滤设置 (FilterSettingsTab)

*   **文件**: `frontend/src/components/dashboard/FilterSettingsTab.jsx`
*   **功能**: 黑名单管理 (CRUD) 和 本地过滤 (Filter Execution)。

### 核心功能区
1.  **执行本地过滤**: 设置时间范围 -> `handleFilterNews` -> 调用后端 `filterNews`。
2.  **黑名单管理**: 表格展示 `blacklistKeywords`，支持添加(Input)和删除(Popconfirm)。
3.  **已过滤新闻**: 展示被过滤掉的新闻 (`getFilteredDedupNews`)，支持还原。

### API 调用
| 函数名 | API 方法 | 用途 |
|--------|----------|------|
| `fetchBlacklistData` | `getBlacklist` | 获取黑名单 |
| `handleAddKeyword` | `addBlacklist` | 添加关键词 (match_type: contains/regex) |
| `handleFilterNews` | `filterNews` | 执行过滤扫描 |
| `handleBatchRestoreFiltered` | `batchRestoreFiltered` | 批量恢复被过滤数据 |

---

## Tab 5: 精选数据 (CuratedNewsTab)

*   **文件**: `frontend/src/components/dashboard/CuratedNewsTab.jsx`
*   **功能**: 展示通过了去重和过滤的"候选池"数据 (Stage='verified')。
*   **说明**: 这里展示的数据是去重后且未被黑名单过滤的数据，是 AI 筛选的输入源。

---

## Tab 8: AI 筛选 (AIFilterTab)

*   **文件**: `frontend/src/components/dashboard/AIFilterTab.jsx`
*   **功能**: 配置 Prompt，运行 AI 筛选，查看 Rejected 列表。

### 状态变量
| 变量名 | 类型 | 初始值 | 用途 |
|--------|------|--------|------|
| `aiFilterPrompt` | String | '' | AI 系统提示词 |
| `aiFilterHours` | Number | 8 | AI 筛选时间范围 |
| `logs` | Array | [] | 实时运行日志控制台输出 |

### 功能按钮
| 按钮文本 | 事件函数 | 功能说明 |
|----------|----------|----------|
| 开始AI筛选 | `handleAIFilter` | 启动 AI 批处理 (前端轮询模式) |
| 保存配置 | `handleSaveAiConfig` | 保存 Prompt 到后端 |
| 批量恢复所有rejected | `handleBatchRestore` | 恢复被 AI 拒绝的新闻 |
| 清除所有AI状态 | `handleClearAllAiStatus` | 重置所有 AI 打分状态 |

### API 调用
| 函数名 | API 方法 | 用途 |
|--------|----------|------|
| `handleAIFilter` | `filterCuratedNews` | 发起 AI 筛选请求 |
| `handleSaveAiConfig` | `setAiConfig` | 保存配置 |

---

## Tab 9: AI 精选 (AIBestTab)

*   **文件**: `frontend/src/components/dashboard/AIBestTab.jsx`
*   **功能**: 展示 AI 判定为 `'approved'` (High Score) 的新闻。

### 表格列定义 (特色)
| 列名 | render逻辑 |
|------|-----------|
| AI 标签 | 解析 `ai_explanation` ("8分-理由 #Tag")，展示彩色 Tag 分数和标签 |

---

## Tab 2: 爬虫控制 (SpiderControlTab)

*   **文件**: `frontend/src/components/dashboard/SpiderControlTab.jsx`
*   **功能**: 渲染 `ScraperCard` 网格。
*   **Props**: 接收 `spiders` 和 `spiderStatus`。
*   **逻辑**: 根据 `contentType` 过滤显示的爬虫卡片。

---

## Tab 6: API 配置 (ApiSettingsTab)

*   **文件**: `frontend/src/components/dashboard/ApiSettingsTab.jsx`
*   **功能**: 全局系统配置中心。

### 配置板块
1.  **系统基础配置**:
    *   `setSystemTimezone`: 时区设置。
    *   `setAutoPipelineConfig`: 自动化流程时间窗口 (News/Article 分开配置)。
    *   `setDailyPushTime`: 每日日报推送时间。
2.  **DeepSeek AI 配置**: API Key, Base URL, Model。支持 `testDeepSeekConnection`。
3.  **Telegram 配置**: Bot Token, Chat ID。支持 `testTelegramPush`。
4.  **分析师 API 密钥**: 管理多用户的 API Key 生成与删除。

---

## Tab 7: 新闻输出 (ExportTab)

*   **文件**: `frontend/src/components/dashboard/ExportTab.jsx`
*   **功能**: 最终数据的出口。支持筛选高分新闻，复制为多种格式，或发送到 Telegram。

### 功能按钮
| 按钮文本 | 功能说明 | 逻辑特色 |
|----------|----------|----------|
| 推送精选日报 | `triggerDailyPush` | 手动触发每日推送任务 |
| 复制为纯文本 | Copy Text | 格式化标题+内容 |
| Markdown格式 | Copy MD | 格式化为 Markdown 链接 |
| TG格式 | Copy HTML | 复制为带 `<a>` 标签的 HTML，粘贴到 TG 会自动渲染为超链接 |
| 发送到TG | `sendNewsToTelegram` | 调用 Bot 发送选中新闻 |

---

## 🏗️ 后端架构概览 (Backend Architecture)

*   **服务入口**: `backend/main.py`
*   **数据库**: SQLite (`crawler/database/db_sqlite.py`)
*   **爬虫基类**: `crawler/scrapers/base.py`

### 核心数据流 (Pipeline)
1.  **Scraping**: `raw` -> `news` table.
2.  **Deduplication**: `raw` -> `deduplicated` (via `LocalDeduplicator`).
3.  **Filtering**: `deduplicated` -> `verified` (via `FilterSettings`).
4.  **AI Analysis**: `verified` -> `approved`/`rejected` (via `DeepSeekService`).
5.  **Distribution**: `approved` -> Telegram / Export.

### 风险与待优化 (Risks & TODOs)

| 优先级 | 模块 | 问题描述 |
|---|---|---|
| **High** | **Scheduler** | **Score Parsing**: 依赖字符串 "X分" 提取分数，极其脆弱。需改为结构化 JSON 输出。 |
| Medium | Frontend | **Component Size**: `ApiSettingsTab.jsx` (600+ lines) 包含过多不同领域的配置逻辑，应进一步拆分。 |
| Low | **Deduplicator** | **Old-Master Problem (Mitigated)**: 已实施 4小时时间窗口策略。间隔超过4小时的相似新闻将被视为独立更新。 |
