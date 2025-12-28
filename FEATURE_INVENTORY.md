# AINEWS 前端功能清单

生成时间: 2025-12-27
基准文件: `frontend/src/pages/Dashboard.jsx` 及各子组件

---

## 核心容器: Dashboard.jsx
**文件路径**: `frontend/src/pages/Dashboard.jsx`

### 1. 状态变量 (State)
| 变量名 | 类型 | 初始值 | 用途 | 行号 |
|---|---|---|---|---|
| stats | Array | [] | 首页顶部爬虫统计数据 | L34 |
| news | Array | [] | 数据管理Tab的新闻列表 | L35 |
| loading | Boolean | false | 数据管理Tab的加载状态 | L36 |
| spiders | Array | [] | 爬虫名称列表 | L37 |
| spiderStatus | Object | {} | 爬虫运行状态(状态与日志) | L38 |
| activeKey | String | '1' | 当前选中的 Tab | L39 |
| pagination | Object | {current:1, ...} | 数据管理Tab的分页配置 | L42 |
| filterSource | String | null | 数据管理Tab的来源筛选 | L43 |
| dedupNews | Array | [] | 去重数据Tab的列表 | L48 |
| dedupPagination | Object | {current:1, ...} | 去重数据Tab的分页配置 | L49 |
| dedupFilterSource | String | null | 去重数据Tab的来源筛选 | L50 |
| loadingDedup | Boolean | false | 去重数据Tab的加载状态 | L51 |
| rejectedPagination | Object | {current:1, ...} | AI筛选Tab(Rejected)的分页 | L54 |
| approvedPagination | Object | {current:1, ...} | AI精选Tab(Approved)的分页 | L55 |
| rejectedNews | Array | [] | AI筛选Tab的新闻列表 | L58 |
| rejectedLoading | Boolean | false | AI筛选Tab的加载状态 | L59 |
| approvedNews | Array | [] | AI精选Tab的新闻列表 | L60 |
| approvedLoading | Boolean | false | AI精选Tab的加载状态 | L61 |
| aiFilterPrompt | String | '' | AI筛选提示词 | L62 |
| aiFilterHours | Number | 8 | AI筛选时间范围 | L63 |
| aiFiltering | Boolean | false | AI筛选运行状态 | L64 |
| manuallyFeatured | Array | [] | 手动加精的新闻列表(跨Tab共享) | L67 |
| globalCounts | Object | {news:0, ...} | 各Tab标题的计数统计 | L165 |
| filteredNews | Array | [] | 过滤设置Tab的列表 | L245 |
| filteredPagination | Object | {current:1, ...} | 过滤设置Tab的分页 | L246 |
| loadingFiltered | Boolean | false | 过滤设置Tab的加载状态 | L247 |
| curatedNews | Array | [] | 精选数据Tab的列表 | L250 |
| curatedPagination | Object | {current:1, ...} | 精选数据Tab的分页 | L251 |
| loadingCurated | Boolean | false | 精选数据Tab的加载状态 | L252 |
| curatedFilterSource | String | null | 精选数据Tab的来源筛选 | L253 |
| exportVisible | Boolean | false | 导出弹窗显示状态 | L335 |
| exportLoading | Boolean | false | 导出按钮加载状态 | L336 |
| exportDates | Array | [dayjs(..), ..] | 导出时间范围 | L338 |
| exportKeyword | String | '' | 导出关键词 | L339 |
| exportTargetStage | String | 'raw' | 导出数据阶段 | L340 |
| exportFields | Array | ['title', ..] | 导出字段选择 | L341 |

### 2. API 调用 (Shared & Logic)
| 函数名 | API 方法 | 用途 | 行号 |
|---|---|---|---|
| fetchStats | getStats | 获取首页顶部统计 | L84 |
| fetchNews | getNews | 获取原始新闻列表 | L94 |
| fetchDedupNews | getDeduplicatedNews | 获取去重新闻列表 | L111 |
| fetchSpiders | getSpiders | 获取爬虫列表 | L127 |
| fetchSpiderStatus | getSpiderStatus | 获取爬虫详细状态 | L148 |
| fetchGlobalCounts | api.*(multiple) | 获取所有Tab的计数 | L178-185 |
| handleRunSpider | runSpider | 启动爬虫 | L209 |
| handleStopSpider | cancelScraper | 停止爬虫 | L221 |
| handleConfigChange | updateConfig | 更新爬虫配置 | L230 |
| fetchFilteredNews | getFilteredDedupNews | 获取已过滤(Filtered)新闻 | L259 |
| fetchCuratedNews | getCuratedNews | 获取精选(Curated)新闻 | L276 |
| fetchRejectedNews | getFilteredCurated('rejected'..) | 获取AI拒绝新闻 | L301 |
| fetchApprovedNews | getFilteredCurated('approved'..) | 获取AI批准新闻 | L317 |
| handleExport | exportNews | 执行新闻导出 | L367 |

### 3. 事件处理函数
| 函数名 | 触发事件 | 说明 | 行号 |
|---|---|---|---|
| handleAddToFeatured | 点击"加精" | 将新闻添加到手动加精列表 | L70 |
| handleLogout | 点击"退出" | 登出并跳转登录页 | L159 |
| handleShowExport | 点击Tab内"导出" | 打开导出配置弹窗 | L343 |

---

## Tab 1: 数据管理 (NewsManagementTab)
**文件**: `frontend/src/components/dashboard/NewsManagementTab.jsx`
**位置**: Dashboard.jsx L444

### 1. 功能按钮
| 按钮文本/图标 | 函数名 | 位置 | 说明 |
|---|---|---|---|
| 导出 (Toolbar) | onShowExport | L124 | 调用父组件导出功能 |
| 刷新 (Toolbar) | onRefresh (fetchNews) | L125 | 刷新当前列表 |
| 删除 (Table) | handleDeleteNews | L103 | 删除单条新闻 |

### 2. 输入框/选择器
| 名称 | 绑定状态 | 功能 | 位置 |
|---|---|---|---|
| 搜索框 | filterKeyword (via NewsToolbar) | 关键词搜索 (防抖) | L114 |
| 来源选择 | filterSource (via NewsToolbar) | 按爬虫来源筛选 | L120 |

### 3. 表格列 (Table Columns)
| 列名 | 字段 | Render 逻辑 |
|---|---|---|
| ID | id | 文本 |
| 标题 | title | 超链接到 source_url |
| 来源 | source_site | 文本 |
| 状态 | stage | Tag (Duplicate=Red, 原始=Default) |
| 发布时间 | published_at | Date.toLocaleString() |
| 重复源 | master_title | 显示主新闻标题 (仅Duplicate状态) |
| 操作 | - | [删除] |

### 4. API 调用
| 函数名 | API 方法 | 说明 |
|---|---|---|
| fetchNews | getNews | 加载新闻列表 |
| handleDeleteNews | deleteNews | 删除新闻 |

---

## Tab 2: 去重数据 (DeduplicatedTab)
**文件**: `frontend/src/components/dashboard/DeduplicatedTab.jsx`
**位置**: Dashboard.jsx L449

### 1. 功能按钮
| 按钮文本 | 函数名 | 位置 | 说明 |
|---|---|---|---|
| 手动去重 | handleDeduplicate | L194 | 触发后端去重逻辑 |
| 还原已去重数据 | handleBatchRestore | L208 | 批量还原所有去重数据到Raw |
| 加精 | onAddToFeatured | L148 | 添加到输出列表 |
| 还原 | handleRestoreNews | L155 | 还原单条到Raw |
| 删除 | handleDeleteDedupNews | L163 | 删除单条 |

### 2. 输入框/选择器
| 名称 | 绑定状态 | 功能 | 位置 |
|---|---|---|---|
| 搜索框 | filterKeyword | 关键词搜索 | L176 |
| 来源选择 | dedupFilterSource | 来源筛选 | L181 |
| 去重范围 | dedupTimeRange | 选择去重的时间窗口 (TimeRangeSelect) | L191 |
| 相似度阈值 | threshold | InputNumber (0.1-1.0) | L192 |

### 3. 表格列
| 列名 | 字段 | Render 逻辑 |
|---|---|---|
| ID | id | 文本 |
| 标题 | title | 超链接 |
| 来源 | source_site | 文本 |
| 发布时间 | published_at | LocaleString |
| 归档时间 | deduplicated_at | LocaleString |
| 操作 | - | [加精] [还原] [删除] |

### 4. API 调用
| 函数名 | API 方法 | 说明 |
|---|---|---|
| handleDeduplicate | deduplicateNews | 执行手动去重 |
| handleBatchRestore | batchRestoreDeduplicated | 批量还原 |
| handleDeleteDedupNews | deleteDeduplicatedNews | 删除 |
| handleRestoreNews | restoreNews | 还原 |
| fetchDedupNews | getDeduplicatedNews | 获取列表 |

---

## Tab 3: 过滤设置 (FilterSettingsTab)
**文件**: `frontend/src/components/dashboard/FilterSettingsTab.jsx`
**位置**: Dashboard.jsx L454

### 1. 功能按钮
| 按钮文本 | 函数名 | 位置 | 说明 |
|---|---|---|---|
| 立即执行过滤 | handleFilterNews | L237 | 触发本地关键词过滤 |
| 还原已过滤数据 | handleBatchRestoreFiltered | L247 | 批量还原Filtered到Dedup |
| 添加 (黑名单) | handleAddKeyword | L272 | 添加新关键词 |
| 删除 (黑名单) | handleDeleteKeyword | L163 | 删除关键词 |
| 加精 | onAddToFeatured | L212 | 已过滤列表操作 |
| 还原 | handleRestoreNews | L218 | 还原单条已过滤新闻 |
| 删除 | handleDeleteFilteredNews | L223 | 删除单条已过滤新闻 |

### 2. 输入框/选择器
| 名称 | 绑定状态 | 功能 | 位置 |
|---|---|---|---|
| 过滤时间范围 | filterTimeRange | 过滤扫描的时间窗口 | L236 |
| 匹配类型 | newMatchType | 选择 'contains' 或 'regex' | L261 |
| 输入屏蔽词 | newKeyword | 新关键词输入 | L265 |
| 搜索框 (已过滤) | filterKeyword | 搜索已过滤新闻 | L290 |

### 3. 表格列
**黑名单表**:
| 列名 | 字段 | 逻辑 |
|---|---|---|
| 关键词 | keyword | 文本 |
| 匹配类型 | match_type | 'contains'->包含, 'regex'->正则 |
| 操作 | - | [删除] |

**已过滤新闻表**:
| 列名 | 字段 | 逻辑 |
|---|---|---|
| ID | id | 文本 |
| 标题 | title | 超链接 |
| 过滤原因 | keyword_filter_reason | 显示命中原因 |
| 来源 | source_site | 文本 |
| 发布时间 | published_at | LocaleString |
| 操作 | - | [加精] [还原] [删除] |

---

## Tab 4: 精选数据 (CuratedNewsTab)
**文件**: `frontend/src/components/dashboard/CuratedNewsTab.jsx`
**位置**: Dashboard.jsx L459

### 1. 功能按钮
| 按钮文本 | 函数名 | 位置 | 说明 |
|---|---|---|---|
| 加精 | onAddToFeatured | L96 | 添加到输出列表 |
| 删除 | handleDeleteCuratedNews | L104 | 删除精选新闻 |

### 2. 输入框/选择器
| 名称 | 绑定状态 | 功能 | 位置 |
|---|---|---|---|
| 搜索框 | filterKeyword | 关键词搜索 | L117 |
| 来源选择 | curatedFilterSource | 来源筛选 | L123 |

### 3. 表格列
| 列名 | 字段 | Render 逻辑 |
|---|---|---|
| ID | id | 文本 |
| 标题 | title | 超链接 |
| 来源 | source_site | 文本 |
| 发布时间 | published_at | LocaleString |
| 操作 | - | [加精] [删除] |

---

## Tab 5: AI 筛选 (AIFilterTab)
**文件**: `frontend/src/components/dashboard/AIFilterTab.jsx`
**位置**: Dashboard.jsx L464

### 1. 功能按钮
| 按钮文本 | 函数名 | 位置 | 说明 |
|---|---|---|---|
| 开始AI筛选 | handleAIFilter | L289 | 触发AI分析流程 |
| 批量恢复所有rejected | handleBatchRestore | L345 | 恢复所有被拒绝的到精选 |
| 清除所有AI状态 | handleClearAllAiStatus | L353 | 重置AI处理状态 |
| 加精 | onAddToFeatured | L253 | 添加到输出 |
| 还原 | handleRestoreCurated | L255 | 还原单条到待处理 |
| 删除 | handleDeleteRejected | L261 | 永久删除 |

### 2. 输入框/选择器
| 名称 | 绑定状态 | 功能 | 位置 |
|---|---|---|---|
| 筛选提示词 | aiFilterPrompt | Prompt TextArea | L278 |
| 时间范围 | aiFilterHours | TimeRangeSelect | L287 |
| 搜索框 | filterKeyword | 搜索Rejected新闻 | L333 |

### 3. 表格列 (Rejected News)
| 列名 | 字段 | Render 逻辑 |
|---|---|---|
| ID | id | 文本 |
| 标题 | title | 超链接 |
| AI 标签 | ai_explanation | 解析 "分数-理由 #标签" 显示Tags |
| 来源 | source_site | 文本 |
| 发布时间 | published_at | LocaleString |
| 操作 | - | [加精] [还原] [删除] |

---

## Tab 6: AI 精选 (AIBestTab)
**文件**: `frontend/src/components/dashboard/AIBestTab.jsx`
**位置**: Dashboard.jsx L469

### 1. 功能按钮
| 按钮文本 | 函数名 | 位置 | 说明 |
|---|---|---|---|
| 加精 | onAddToFeatured | L104 | 添加到输出 |
| 删除 | handleDeleteApproved | L107 | 永久删除 |

### 2. 输入框/选择器
| 名称 | 绑定状态 | 功能 | 位置 |
|---|---|---|---|
| 搜索框 | filterKeyword | 关键词搜索 | L125 |
| 来源选择 | filterSource | 来源筛选 | L131 |

### 3. 表格列
与 AIFilterTab 类似，专用于显示 Approved (Score >= 6) 的新闻。

---

## Tab 7: 爬虫控制 (SpiderControlTab)
**文件**: `frontend/src/components/dashboard/SpiderControlTab.jsx`
**位置**: Dashboard.jsx L475

*此Tab主要由子组件 `ScraperCard` 构成*

### ScraperCard 组件
**文件**: `frontend/src/components/dashboard/ScraperCard.jsx`

#### 1. 功能按钮
| 按钮文本 | 函数名 | 说明 |
|---|---|---|
| 运行 | onRun (handleRunSpider) | 启动爬虫，带Limit参数 |
| 停止 | onCancel (handleStopSpider) | 停止运行中爬虫 |

#### 2. 输入框/选择器
| 名称 | 绑定状态 | 功能 |
|---|---|---|
| 限制条数 | localLimit | 选择每次运行抓取数量 (5-30) |
| 频率 | localInterval | 设置自动运行间隔 (手动-5小时) |

#### 3. Log Console
- 自动滚动的控制台日志显示区。

---

## Tab 8: API 配置 (ApiSettingsTab)
**文件**: `frontend/src/components/dashboard/ApiSettingsTab.jsx`
**位置**: Dashboard.jsx L491

### 1. 功能按钮
| 按钮文本 | 函数名 | 位置 | 说明 |
|---|---|---|---|
| 保存设置 (系统) | handleSaveTimezone | L323 | 保存时区、推送时间及自动化配置 |
| 保存配置 (DS) | handleSaveDeepSeekConfig | L396 | 保存DeepSeek Key/URL |
| 测试连接 (DS) | handleTestDeepSeekConnection | L397 | 测试AI API连通性 |
| 保存配置 (TG) | handleSaveTelegramConfig | L433 | 保存TG Bot配置 |
| 测试发送 (TG) | handleTestTelegramPush | L434 | 发送测试消息 |
| 创建新密钥 | setShowCreateModal(true) | L453 | 打开Key创建弹窗 |
| 复制 (Key) | handleCopyApiKey | L260 | 复制API Key |
| 删除 (Key) | handleDeleteApiKey | L270 | 删除API Key |

### 2. 输入框/选择器
| 名称 | 绑定状态 | 功能 | 位置 |
|---|---|---|---|
| 系统时区 | timezone | 选择系统时区 | L289 |
| 每日推送时间 | pushTime | TimePicker | L308 |
| 去重时间范围 | dedupHours | 自动化流程配置 | L331 |
| 过滤时间范围 | filterHours | 自动化流程配置 | L335 |
| AI打分时间范围 | aiScoringHours | 自动化流程配置 | L339 |
| 推送时间范围 | pushHours | 自动化流程配置 | L344 |
| API Key (DS) | deepseekConfig.api_key | DeepSeek 密钥 | L360 |
| Base URL (DS) | deepseekConfig.base_url | DeepSeek 地址 | L367 |
| Model (DS) | deepseekConfig.model | 模型选择 | L373 |
| Bot Token (TG) | telegramConfig.bot_token | TG Bot Token | L407 |
| Chat ID (TG) | telegramConfig.chat_id | TG 频道ID | L417 |
| 启用推送 (TG) | telegramConfig.enabled | 开关 | L426 |

---

## Tab 9: 新闻输出 (ExportTab)
**文件**: `frontend/src/components/dashboard/ExportTab.jsx`
**位置**: Dashboard.jsx L497

### 1. 功能按钮
| 按钮文本 | 函数名 | 位置 | 说明 |
|---|---|---|---|
| 加载新闻 | handleLoadNews | L247 | 根据条件加载供导出的新闻 |
| 推送精选日报 | triggerDailyPush | L250 | 手动触发一次每日推送 |
| 全选/取消/反选 | handleToggle.. | L278 | 批量选择操作 |
| 复制为纯文本 | handleCopyPlainText | L284 | 复制格式化文本 |
| Markdown格式 | handleCopyMarkdown | L285 | 复制MD格式 |
| TG格式 | handleCopyTG | L286 | 复制HTML超链接格式 |
| 发送到TG | handleSendToTelegram | L289 | 直接推送到Telegram |

### 2. 输入框/选择器
| 名称 | 绑定状态 | 功能 | 位置 |
|---|---|---|---|
| 时间范围 | exportTimeRange | 导出时间窗 | L229 |
| 最低评分 | exportMinScore | 最低分数筛选 | L233 |

### 3. 表格列
| 列名 | 字段 | Render 逻辑 |
|---|---|---|
| 评分 | score | Tag显示分数及"手动"标记 |
| 标题 | title | 超链接 |
| 来源 | source_site | Tag |
| AI标签 | ai_explanation | 简化显示的理由 |

---
